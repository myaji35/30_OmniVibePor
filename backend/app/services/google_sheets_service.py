"""Google Sheets API 서비스"""
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from contextlib import nullcontext

from app.core.config import get_settings

settings = get_settings()

# Logfire 사용 가능 여부 확인
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class GoogleSheetsService:
    """
    Google Sheets API 클라이언트

    기능:
    - 전략 시트 읽기 (캠페인, 타겟, 톤앤매너)
    - 콘텐츠 스케줄 관리
    - 성과 데이터 기록
    """

    # Google Sheets API 스코프
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service = None
        self._initialize_client()

    def _initialize_client(self):
        """Google Sheets API 클라이언트 초기화"""
        try:
            credentials_path = Path(settings.GOOGLE_SHEETS_CREDENTIALS_PATH)

            if not credentials_path.exists():
                self.logger.warning(
                    f"Google Sheets credentials not found at {credentials_path}. "
                    "Service will be unavailable."
                )
                return

            # 서비스 계정 인증
            credentials = Credentials.from_service_account_file(
                str(credentials_path),
                scopes=self.SCOPES
            )

            # Google Sheets API 클라이언트 생성
            self.service = build('sheets', 'v4', credentials=credentials)
            self.logger.info("Google Sheets API client initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets client: {e}")
            self.service = None

    def is_available(self) -> bool:
        """서비스 사용 가능 여부"""
        return self.service is not None

    async def read_sheet(
        self,
        spreadsheet_id: str,
        range_name: str
    ) -> List[List[str]]:
        """
        시트 데이터 읽기

        Args:
            spreadsheet_id: 스프레드시트 ID (URL에서 추출)
            range_name: 읽을 범위 (예: 'Sheet1!A1:D10')

        Returns:
            2차원 배열 형태의 시트 데이터
        """
        if not self.is_available():
            raise RuntimeError("Google Sheets service is not available")

        span_context = logfire.span("google_sheets.read", spreadsheet_id=spreadsheet_id, range=range_name) if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name
                ).execute()

                values = result.get('values', [])
                self.logger.info(f"Read {len(values)} rows from {range_name}")
                return values

            except HttpError as e:
                self.logger.error(f"HTTP error reading sheet: {e}")
                raise
            except Exception as e:
                self.logger.error(f"Error reading sheet: {e}")
                raise

    async def write_sheet(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]]
    ) -> int:
        """
        시트 데이터 쓰기

        Args:
            spreadsheet_id: 스프레드시트 ID
            range_name: 쓸 범위
            values: 쓸 데이터 (2차원 배열)

        Returns:
            업데이트된 셀 개수
        """
        if not self.is_available():
            raise RuntimeError("Google Sheets service is not available")

        span_context = logfire.span("google_sheets.write", spreadsheet_id=spreadsheet_id, range=range_name) if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                body = {'values': values}
                result = self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()

                updated_cells = result.get('updatedCells', 0)
                self.logger.info(f"Updated {updated_cells} cells in {range_name}")
                return updated_cells

            except HttpError as e:
                self.logger.error(f"HTTP error writing sheet: {e}")
                raise
            except Exception as e:
                self.logger.error(f"Error writing sheet: {e}")
                raise

    async def append_rows(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]]
    ) -> int:
        """
        시트에 행 추가 (기존 데이터 뒤에)

        Args:
            spreadsheet_id: 스프레드시트 ID
            range_name: 추가할 시트 범위
            values: 추가할 데이터

        Returns:
            추가된 행 개수
        """
        if not self.is_available():
            raise RuntimeError("Google Sheets service is not available")

        span_context = logfire.span("google_sheets.append", spreadsheet_id=spreadsheet_id) if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                body = {'values': values}
                result = self.service.spreadsheets().values().append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    insertDataOption='INSERT_ROWS',
                    body=body
                ).execute()

                updated_rows = result.get('updates', {}).get('updatedRows', 0)
                self.logger.info(f"Appended {updated_rows} rows to {range_name}")
                return updated_rows

            except HttpError as e:
                self.logger.error(f"HTTP error appending rows: {e}")
                raise
            except Exception as e:
                self.logger.error(f"Error appending rows: {e}")
                raise

    async def read_strategy_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str = "전략"
    ) -> Dict[str, Any]:
        """
        전략 시트 읽기 (가로/세로 형식 자동 감지)

        캠페인 전체 전략 정보 (주제/소제목은 스케줄 시트에서 관리)

        세로 형식:
        | 항목 | 내용 |
        |------|------|
        | 캠페인명 | 2026 시력 인식 캠페인 |
        | 타겟 | 일반 대중 |
        | 톤앤매너 | 전문적이고 신뢰감 있는 |

        가로 형식:
        | 캠페인명 | 타겟 | 톤앤매너 | 플랫폼 | 시작일 |
        |----------|------|----------|--------|--------|
        | 값       | 값   | 값       | 값     | 값     |

        Args:
            spreadsheet_id: 스프레드시트 ID
            sheet_name: 시트 이름 (기본값: '전략')

        Returns:
            전략 데이터 딕셔너리
        """
        # 넓은 범위로 읽어서 자동 감지
        range_name = f"{sheet_name}!A:Z"
        rows = await self.read_sheet(spreadsheet_id, range_name)

        if not rows:
            return {}

        # 형식 자동 감지
        # 세로 형식: A열과 B열만 데이터, 여러 행
        # 가로 형식: 첫 행 헤더, 두 번째 행 값

        strategy = {}

        # 가로 형식인지 확인 (첫 행에 여러 컬럼, 두 번째 행에 값)
        if len(rows) >= 2 and len(rows[0]) > 2:
            # 가로 형식으로 판단
            headers = [h.strip() for h in rows[0] if h]
            values = rows[1] if len(rows) > 1 else []

            for i, header in enumerate(headers):
                value = values[i].strip() if i < len(values) and values[i] else ""
                strategy[header] = value

            self.logger.info(f"Detected horizontal format strategy sheet with {len(headers)} fields")
        else:
            # 세로 형식 (A열: 키, B열: 값)
            for row in rows:
                if len(row) >= 2:
                    key = row[0].strip()
                    value = row[1].strip()
                    strategy[key] = value

            self.logger.info(f"Detected vertical format strategy sheet with {len(strategy)} fields")

        return strategy

    async def read_content_schedule(
        self,
        spreadsheet_id: str,
        sheet_name: str = "스케줄"
    ) -> List[Dict[str, Any]]:
        """
        콘텐츠 스케줄 시트 읽기

        예상 구조:
        | 날짜 | 주제 | 플랫폼 | 상태 |
        |------|------|--------|------|
        | 2024-01-15 | 신제품 소개 | YouTube | 대기 |

        Args:
            spreadsheet_id: 스프레드시트 ID
            sheet_name: 시트 이름 (기본값: '스케줄')

        Returns:
            스케줄 데이터 리스트
        """
        range_name = f"{sheet_name}!A:Z"
        rows = await self.read_sheet(spreadsheet_id, range_name)

        if not rows:
            return []

        # 첫 행을 헤더로 사용
        headers = [h.strip() for h in rows[0]]

        # 데이터 행을 딕셔너리로 변환
        schedule = []
        for row in rows[1:]:
            if not row:  # 빈 행 건너뛰기
                continue

            item = {}
            for i, header in enumerate(headers):
                value = row[i] if i < len(row) else ""
                item[header] = value.strip() if isinstance(value, str) else value

            schedule.append(item)

        return schedule

    async def update_content_status(
        self,
        spreadsheet_id: str,
        row_index: int,
        status: str,
        sheet_name: str = "스케줄"
    ) -> bool:
        """
        콘텐츠 상태 업데이트

        Args:
            spreadsheet_id: 스프레드시트 ID
            row_index: 업데이트할 행 번호 (1부터 시작, 헤더 포함)
            status: 새 상태 (예: '생성중', '완료', '배포됨')
            sheet_name: 시트 이름

        Returns:
            성공 여부
        """
        # 상태 컬럼이 D열이라고 가정
        range_name = f"{sheet_name}!D{row_index}"

        try:
            await self.write_sheet(spreadsheet_id, range_name, [[status]])
            return True
        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")
            return False

    async def get_campaign_contents(
        self,
        spreadsheet_id: str,
        campaign_name: str,
        sheet_name: str = "스케줄"
    ) -> List[Dict[str, Any]]:
        """
        특정 캠페인의 콘텐츠(소제목) 목록 조회

        Args:
            spreadsheet_id: 스프레드시트 ID
            campaign_name: 캠페인명 (예: '2026 시력 인식 캠페인')
            sheet_name: 시트 이름 (기본값: '스케줄')

        Returns:
            해당 캠페인의 콘텐츠 리스트
        """
        all_schedule = await self.read_content_schedule(spreadsheet_id, sheet_name)

        # 캠페인명으로 필터링
        campaign_contents = [
            item for item in all_schedule
            if item.get('캠페인명', '').strip() == campaign_name.strip()
        ]

        self.logger.info(f"Found {len(campaign_contents)} contents for campaign '{campaign_name}'")
        return campaign_contents

    def get_spreadsheet_id_from_url(self, url: str) -> Optional[str]:
        """
        구글 시트 URL에서 스프레드시트 ID 추출

        Args:
            url: 구글 시트 URL

        Returns:
            스프레드시트 ID
        """
        try:
            # URL 형식: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit...
            if '/d/' in url:
                return url.split('/d/')[1].split('/')[0]
            return None
        except Exception as e:
            self.logger.error(f"Failed to extract spreadsheet ID from URL: {e}")
            return None
    async def read_resources_sheet(
        self,
        spreadsheet_id: str,
        campaign_name: Optional[str] = None,
        topic: Optional[str] = None,
        sheet_name: str = "리소스"
    ) -> List[Dict[str, Any]]:
        """
        리소스 시트 읽기

        예상 구조:
        | 캠페인명 | 소제목 | 리소스명 | 리소스타입 | URL/경로 | 용도 | 업로드일 |
        |---------|--------|----------|------------|----------|------|----------|
        | AI자동화 | 소개편 | logo.png | image | gs://... | 인트로 | 2026-01-01 |

        Args:
            spreadsheet_id: 스프레드시트 ID
            campaign_name: 필터링할 캠페인명 (옵션)
            topic: 필터링할 소제목 (옵션)
            sheet_name: 시트 이름 (기본값: '리소스')

        Returns:
            리소스 데이터 리스트
        """
        range_name = f"{sheet_name}!A:Z"
        rows = await self.read_sheet(spreadsheet_id, range_name)

        if not rows:
            return []

        # 첫 행을 헤더로 사용
        headers = [h.strip() for h in rows[0]]

        # 데이터 행을 딕셔너리로 변환
        resources = []
        for row in rows[1:]:
            if not row:  # 빈 행 건너뛰기
                continue

            resource = {}
            for i, header in enumerate(headers):
                value = row[i] if i < len(row) else ""
                resource[header] = value.strip() if isinstance(value, str) else value

            # 필터링 (캠페인명, 소제목)
            if campaign_name and resource.get("캠페인명") != campaign_name:
                continue
            if topic and resource.get("소제목") != topic:
                continue

            resources.append(resource)

        self.logger.info(
            f"Read {len(resources)} resources from '{sheet_name}' sheet "
            f"(campaign: {campaign_name}, topic: {topic})"
        )

        return resources

    async def add_resource_to_sheet(
        self,
        spreadsheet_id: str,
        campaign_name: str,
        topic: str,
        resource_name: str,
        resource_type: str,
        url: str,
        purpose: str = "",
        sheet_name: str = "리소스"
    ) -> bool:
        """
        리소스 시트에 새 리소스 추가

        Args:
            spreadsheet_id: 스프레드시트 ID
            campaign_name: 캠페인명
            topic: 소제목
            resource_name: 리소스명
            resource_type: 리소스 타입 (image, video, pdf, audio)
            url: 리소스 URL 또는 경로
            purpose: 용도 (인트로, 메인, CTA 등)
            sheet_name: 시트 이름 (기본값: '리소스')

        Returns:
            성공 여부
        """
        from datetime import datetime

        # 새 행 데이터
        new_row = [
            campaign_name,
            topic,
            resource_name,
            resource_type,
            url,
            purpose,
            datetime.now().strftime("%Y-%m-%d")
        ]

        # 시트의 마지막 행 찾기
        range_name = f"{sheet_name}!A:A"
        existing_rows = await self.read_sheet(spreadsheet_id, range_name)
        next_row = len(existing_rows) + 1

        # 새 행 추가
        range_to_write = f"{sheet_name}!A{next_row}:G{next_row}"
        await self.write_sheet(spreadsheet_id, range_to_write, [new_row])

        self.logger.info(
            f"Added resource '{resource_name}' to '{sheet_name}' sheet "
            f"(campaign: {campaign_name}, topic: {topic})"
        )

        return True


# 싱글톤 인스턴스
_sheets_service_instance = None


def get_sheets_service() -> GoogleSheetsService:
    """Google Sheets 서비스 싱글톤 인스턴스"""
    global _sheets_service_instance
    if _sheets_service_instance is None:
        _sheets_service_instance = GoogleSheetsService()
    return _sheets_service_instance
