"""플랫폼별 영상 프리셋 상수 정의"""
from typing import Dict, Any


# 플랫폼별 프리셋 정의
PLATFORM_PRESETS: Dict[str, Dict[str, Any]] = {
    "youtube": {
        "platform": "youtube",
        "name": "YouTube 쇼츠",
        "description": "YouTube Shorts 최적화 프리셋 (9:16 세로형)",
        "resolution": {
            "width": 1080,
            "height": 1920
        },
        "aspect_ratio": "9:16",
        "frame_rate": 30,
        "bitrate": 8000000,  # 8 Mbps
        "subtitle_style": {
            "font_size": 42,
            "font_family": "Pretendard",
            "position": "bottom",
            "background_opacity": 0.7,
            "background_color": "#000000",
            "font_color": "#FFFFFF",
            "outline_width": 2,
            "outline_color": "#000000"
        },
        "bgm_settings": {
            "volume": 0.3,
            "ducking_enabled": True,
            "ducking_level": 0.5,
            "fade_in_duration": 0.5,
            "fade_out_duration": 1.0
        },
        "transition_style": "fade",
        "transition_duration": 0.3,
        "color_grading": "vibrant",
        "max_duration": 60  # 초
    },
    "instagram": {
        "platform": "instagram",
        "name": "Instagram Reels",
        "description": "Instagram Reels 최적화 프리셋 (9:16 세로형)",
        "resolution": {
            "width": 1080,
            "height": 1920
        },
        "aspect_ratio": "9:16",
        "frame_rate": 30,
        "bitrate": 5000000,  # 5 Mbps
        "subtitle_style": {
            "font_size": 36,
            "font_family": "Pretendard",
            "position": "center",
            "background_opacity": 0.0,  # 투명 배경
            "background_color": "#000000",
            "font_color": "#FFFFFF",
            "outline_width": 3,
            "outline_color": "#000000"
        },
        "bgm_settings": {
            "volume": 0.25,
            "ducking_enabled": True,
            "ducking_level": 0.6,
            "fade_in_duration": 1.0,
            "fade_out_duration": 1.5
        },
        "transition_style": "slide",
        "transition_duration": 0.4,
        "color_grading": "warm",
        "max_duration": 90  # 초
    },
    "tiktok": {
        "platform": "tiktok",
        "name": "TikTok",
        "description": "TikTok 최적화 프리셋 (9:16 세로형)",
        "resolution": {
            "width": 1080,
            "height": 1920
        },
        "aspect_ratio": "9:16",
        "frame_rate": 30,
        "bitrate": 6000000,  # 6 Mbps
        "subtitle_style": {
            "font_size": 48,
            "font_family": "Pretendard",
            "position": "center",
            "background_opacity": 0.0,  # 투명 배경
            "background_color": "#000000",
            "font_color": "#FFFFFF",
            "outline_width": 3,
            "outline_color": "#000000"
        },
        "bgm_settings": {
            "volume": 0.4,
            "ducking_enabled": True,
            "ducking_level": 0.5,
            "fade_in_duration": 0.5,
            "fade_out_duration": 1.0
        },
        "transition_style": "zoom",
        "transition_duration": 0.3,
        "color_grading": "cool",
        "max_duration": 180  # 초 (3분)
    },
    "facebook": {
        "platform": "facebook",
        "name": "Facebook Reels",
        "description": "Facebook Reels 최적화 프리셋 (9:16 세로형)",
        "resolution": {
            "width": 1080,
            "height": 1920
        },
        "aspect_ratio": "9:16",
        "frame_rate": 30,
        "bitrate": 4000000,  # 4 Mbps
        "subtitle_style": {
            "font_size": 38,
            "font_family": "Pretendard",
            "position": "bottom",
            "background_opacity": 0.6,
            "background_color": "#000000",
            "font_color": "#FFFFFF",
            "outline_width": 2,
            "outline_color": "#000000"
        },
        "bgm_settings": {
            "volume": 0.3,
            "ducking_enabled": True,
            "ducking_level": 0.5,
            "fade_in_duration": 0.5,
            "fade_out_duration": 1.0
        },
        "transition_style": "fade",
        "transition_duration": 0.3,
        "color_grading": "natural",
        "max_duration": 90  # 초
    }
}


# 색보정 프리셋 (Cloudinary 변환용)
COLOR_GRADING_PRESETS = {
    "vibrant": {
        "saturation": 20,
        "contrast": 10,
        "brightness": 5,
        "sharpen": 50
    },
    "warm": {
        "saturation": 10,
        "hue": 10,  # 따뜻한 색조
        "contrast": 5,
        "brightness": 3
    },
    "cool": {
        "saturation": 15,
        "hue": -10,  # 차가운 색조
        "contrast": 8,
        "brightness": 0
    },
    "natural": {
        "saturation": 0,
        "contrast": 0,
        "brightness": 0,
        "sharpen": 30
    }
}


# 트랜지션 스타일 정의
TRANSITION_STYLES = {
    "fade": {
        "type": "crossfade",
        "ease": "linear"
    },
    "slide": {
        "type": "slide",
        "direction": "left",
        "ease": "ease-in-out"
    },
    "zoom": {
        "type": "zoom",
        "scale": 1.1,
        "ease": "ease-out"
    }
}


def get_preset(platform: str) -> Dict[str, Any]:
    """
    플랫폼 프리셋 조회

    Args:
        platform: 플랫폼 이름 (youtube, instagram, tiktok, facebook)

    Returns:
        프리셋 딕셔너리

    Raises:
        ValueError: 지원하지 않는 플랫폼
    """
    platform = platform.lower()
    if platform not in PLATFORM_PRESETS:
        raise ValueError(
            f"Unsupported platform: {platform}. "
            f"Supported platforms: {', '.join(PLATFORM_PRESETS.keys())}"
        )
    return PLATFORM_PRESETS[platform]


def get_all_platforms() -> list[str]:
    """지원하는 모든 플랫폼 목록 반환"""
    return list(PLATFORM_PRESETS.keys())
