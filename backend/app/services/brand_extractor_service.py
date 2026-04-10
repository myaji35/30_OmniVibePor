"""
Brand Extractor Service — ISS-085 Stage 1

거래처 홈페이지 URL에서 브랜드 자산을 자동 추출.
자체 Playwright 크롤러 기반 (Firecrawl 보류).

추출 필드:
    name, logo_url, brand_color, tagline, address, phone, industry

설계 원칙:
    - httpx로 HTML 가져오기 (가벼운 사이트)
    - Playwright는 SPA/네이버 등 JS 렌더링 필요 시 fallback
    - BeautifulSoup으로 파싱
    - 실패 시 빈 필드 반환 (부분 추출 허용)
    - LLM vertical 분류는 llm_profile.py 연동 (Stage 2)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ExtractedBrand:
    """추출된 브랜드 자산."""
    name: Optional[str] = None
    logo_url: Optional[str] = None
    brand_color: Optional[str] = None
    tagline: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    industry: str = "general"
    source_url: str = ""
    confidence: float = 0.0
    raw_title: Optional[str] = None
    errors: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────
# HTML 파싱 헬퍼
# ─────────────────────────────────────────────

def _extract_name(soup: BeautifulSoup, url: str) -> Optional[str]:
    """사이트명 추출: og:site_name > title > domain."""
    og = soup.find("meta", property="og:site_name")
    if og and og.get("content"):
        return og["content"].strip()
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        # " - 부제" 등 제거
        raw = title_tag.string.strip()
        name = raw.split(" - ")[0].split(" | ")[0].split(" :: ")[0].strip()
        if name:
            return name
    # fallback: domain
    parsed = urlparse(url)
    return parsed.hostname.replace("www.", "") if parsed.hostname else None


def _extract_logo(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """로고 URL 추출: og:image > link[rel=icon] > header img."""
    # og:image (보통 로고 또는 대표 이미지)
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return urljoin(base_url, og["content"])

    # favicon / apple-touch-icon
    for rel in [["icon"], ["shortcut", "icon"], ["apple-touch-icon"]]:
        link = soup.find("link", rel=rel)
        if link and link.get("href"):
            href = link["href"]
            if not href.startswith("data:"):
                return urljoin(base_url, href)

    # header 내 첫 img
    header = soup.find("header") or soup.find(class_=re.compile(r"header|nav", re.I))
    if header:
        img = header.find("img")
        if img and img.get("src"):
            return urljoin(base_url, img["src"])

    return None


def _extract_color(soup: BeautifulSoup, html: str) -> Optional[str]:
    """브랜드 컬러 추출: meta[theme-color] > CSS --primary > header 배경."""
    # theme-color
    meta = soup.find("meta", attrs={"name": "theme-color"})
    if meta and meta.get("content"):
        color = meta["content"].strip()
        if re.match(r"^#[0-9a-fA-F]{3,8}$", color):
            return color

    # CSS 변수 --primary 또는 --brand
    css_match = re.search(
        r"--(?:primary|brand|main|accent)[-_]?color\s*:\s*(#[0-9a-fA-F]{3,8})",
        html, re.I
    )
    if css_match:
        return css_match.group(1)

    return None


def _extract_tagline(soup: BeautifulSoup) -> Optional[str]:
    """태그라인 추출: meta[description] > hero h2."""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        desc = meta["content"].strip()
        if 10 < len(desc) < 200:
            return desc

    og = soup.find("meta", property="og:description")
    if og and og.get("content"):
        desc = og["content"].strip()
        if 10 < len(desc) < 200:
            return desc

    return None


# 한국 주소 패턴: "서울시", "서울특별시", "경기도" 등
_KR_ADDR_PATTERN = re.compile(
    r"(?:서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)"
    r"[가-힣\s\d\-·,]+(?:길|로|동|읍|면|리|번지|호)",
    re.UNICODE,
)

# 한국 전화번호: 02-1234-5678, 010-1234-5678, 1588-1234
_KR_PHONE_PATTERN = re.compile(
    r"(?:0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}|1\d{3}[-.\s]?\d{4})"
)


def _extract_address(soup: BeautifulSoup) -> Optional[str]:
    """한국 주소 추출: footer 텍스트 파싱."""
    # footer 우선
    footer = soup.find("footer") or soup.find(class_=re.compile(r"footer", re.I))
    search_area = footer if footer else soup

    text = search_area.get_text(separator=" ", strip=True)
    match = _KR_ADDR_PATTERN.search(text)
    if match:
        return match.group(0).strip()
    return None


def _extract_phone(soup: BeautifulSoup) -> Optional[str]:
    """전화번호 추출: tel: 링크 > footer 텍스트."""
    # tel: 링크
    tel = soup.find("a", href=re.compile(r"^tel:"))
    if tel:
        phone = tel["href"].replace("tel:", "").strip()
        if len(phone) >= 9:
            return phone

    # footer 텍스트
    footer = soup.find("footer") or soup.find(class_=re.compile(r"footer", re.I))
    search_area = footer if footer else soup
    text = search_area.get_text(separator=" ", strip=True)
    match = _KR_PHONE_PATTERN.search(text)
    if match:
        return match.group(0).strip()
    return None


# ─────────────────────────────────────────────
# 메인 추출 함수
# ─────────────────────────────────────────────

async def extract_brand_from_url(url: str, timeout: float = 15.0) -> ExtractedBrand:
    """
    URL에서 브랜드 자산 추출.

    Args:
        url: 거래처 홈페이지 URL
        timeout: HTTP 요청 타임아웃 (초)

    Returns:
        ExtractedBrand 데이터클래스
    """
    result = ExtractedBrand(source_url=url)

    # URL 정규화
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": "OmniVibe-BrandExtractor/1.0"},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
    except httpx.HTTPStatusError as e:
        result.errors.append(f"HTTP {e.response.status_code}")
        return result
    except Exception as e:
        result.errors.append(f"fetch error: {str(e)[:100]}")
        return result

    soup = BeautifulSoup(html, "html.parser")

    # 필드별 추출
    result.raw_title = soup.title.string.strip() if soup.title and soup.title.string else None
    result.name = _extract_name(soup, url)
    result.logo_url = _extract_logo(soup, url)
    result.brand_color = _extract_color(soup, html)
    result.tagline = _extract_tagline(soup)
    result.address = _extract_address(soup)
    result.phone = _extract_phone(soup)

    # confidence 계산 (채워진 필드 비율)
    fields = [result.name, result.logo_url, result.brand_color,
              result.tagline, result.address, result.phone]
    filled = sum(1 for f in fields if f)
    result.confidence = round(filled / len(fields), 2)

    logger.info(
        f"[brand_extractor] {url} → name={result.name!r}, "
        f"confidence={result.confidence}, filled={filled}/6"
    )
    return result
