"""Voice Cloning API 엔드포인트"""
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel, Field

from app.services.voice_cloning_service import get_voice_cloning_service
from app.services.neo4j_client import Neo4jClient

router = APIRouter(prefix="/voice", tags=["Voice Cloning"])
logger = logging.getLogger(__name__)


# ==================== Pydantic Models ====================

class VoiceCloneResponse(BaseModel):
    """음성 클로닝 응답"""
    voice_id: str = Field(..., description="생성된 음성 ID")
    name: str = Field(..., description="음성 이름")
    status: str = Field(..., description="상태 (ready, training)")
    message: str = Field(..., description="응답 메시지")


class VoiceInfoResponse(BaseModel):
    """음성 정보 응답"""
    voice_id: str
    name: str
    description: str = ""
    category: str = "cloned"
    created_at: str = ""


class VoiceListResponse(BaseModel):
    """음성 목록 응답"""
    voices: list[VoiceInfoResponse]
    total: int


class VoiceDeleteResponse(BaseModel):
    """음성 삭제 응답"""
    success: bool
    message: str


class AudioValidationResponse(BaseModel):
    """오디오 검증 응답"""
    valid: bool
    duration_seconds: Optional[float] = None
    file_size_mb: Optional[float] = None
    format: Optional[str] = None
    warnings: list[str] = []
    error: Optional[str] = None


# ==================== API Endpoints ====================

@router.post("/clone", response_model=VoiceCloneResponse, status_code=status.HTTP_201_CREATED)
async def clone_voice(
    user_id: str = Form(..., description="사용자 ID"),
    voice_name: str = Form(..., description="음성 이름 (예: 김대표님, narrator_voice)"),
    description: str = Form("", description="음성 설명 (선택)"),
    audio_file: UploadFile = File(..., description="녹음된 오디오 파일 (MP3, WAV 등)")
):
    """
    음성 클로닝 - 녹음된 오디오로 커스텀 음성 생성

    **요구사항**:
    - 최소 오디오 길이: 1분 이상
    - 권장 오디오 길이: 3-5분 (고품질)
    - 파일 형식: MP3, WAV, M4A, FLAC, OGG
    - 샘플레이트: 22050 Hz 이상
    - 배경 노이즈: 최소화 필요
    - 발화 내용: 다양한 문장 권장

    **예시**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/voice/clone" \\
      -F "user_id=user123" \\
      -F "voice_name=김대표님" \\
      -F "description=대표님의 목소리" \\
      -F "audio_file=@recording.mp3"
    ```

    **응답**:
    ```json
    {
      "voice_id": "V_abc123...",
      "name": "김대표님",
      "status": "ready",
      "message": "Voice cloned successfully!"
    }
    ```
    """
    with logger.span("api.voice.clone") as span:
        span.set_attribute("user_id", user_id)
        span.set_attribute("voice_name", voice_name)

        try:
            # Voice Cloning 서비스 가져오기
            vc_service = get_voice_cloning_service()

            # 업로드된 파일 읽기
            file_data = await audio_file.read()

            # 파일 저장
            file_path = await vc_service.save_uploaded_file(
                file_data=file_data,
                user_id=user_id,
                original_filename=audio_file.filename
            )

            logger.info(f"Uploaded file saved: {file_path}")

            # 오디오 파일 검증
            validation = await vc_service.validate_audio_file(file_path)

            if not validation.get("valid", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid audio file: {validation.get('error', 'Unknown error')}"
                )

            # 경고가 있으면 로그 출력
            if validation.get("warnings"):
                logger.warning(f"Audio validation warnings: {validation['warnings']}")

            # ElevenLabs Voice Cloning 실행
            voice_data = await vc_service.clone_voice(
                name=voice_name,
                audio_file_path=file_path,
                description=description,
                labels={"user_id": user_id}
            )

            # Neo4j에 저장 (GraphRAG)
            neo4j_client = Neo4jClient()
            try:
                neo4j_client.save_custom_voice(
                    user_id=user_id,
                    voice_id=voice_data["voice_id"],
                    name=voice_name,
                    description=description,
                    file_path=file_path,
                    metadata={
                        "file_size_mb": validation.get("file_size_mb", 0),
                        "duration_seconds": validation.get("duration_seconds", 0),
                        "format": validation.get("format", "unknown")
                    }
                )
            finally:
                neo4j_client.close()

            logger.info(f"Voice cloned successfully: {voice_data['voice_id']}")

            return VoiceCloneResponse(
                voice_id=voice_data["voice_id"],
                name=voice_data["name"],
                status=voice_data["status"],
                message=f"Voice '{voice_name}' cloned successfully! You can now use it for TTS generation."
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Voice cloning failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Voice cloning failed: {str(e)}"
            )


@router.get("/list/{user_id}", response_model=VoiceListResponse)
async def list_user_voices(user_id: str):
    """
    사용자의 모든 커스텀 음성 조회

    **예시**:
    ```bash
    curl "http://localhost:8000/api/v1/voice/list/user123"
    ```

    **응답**:
    ```json
    {
      "voices": [
        {
          "voice_id": "V_abc123...",
          "name": "김대표님",
          "description": "대표님의 목소리",
          "category": "cloned",
          "created_at": "2026-02-01T12:00:00Z"
        }
      ],
      "total": 1
    }
    ```
    """
    try:
        # Neo4j에서 조회
        neo4j_client = Neo4jClient()
        try:
            voices = neo4j_client.get_user_custom_voices(user_id)
        finally:
            neo4j_client.close()

        voice_list = [
            VoiceInfoResponse(
                voice_id=voice["voice_id"],
                name=voice["name"],
                description=voice.get("description", ""),
                category="cloned",
                created_at=str(voice.get("created_at", ""))
            )
            for voice in voices
        ]

        return VoiceListResponse(
            voices=voice_list,
            total=len(voice_list)
        )

    except Exception as e:
        logger.error(f"Failed to list user voices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list voices: {str(e)}"
        )


@router.get("/info/{voice_id}", response_model=VoiceInfoResponse)
async def get_voice_info(voice_id: str):
    """
    음성 정보 조회

    **예시**:
    ```bash
    curl "http://localhost:8000/api/v1/voice/info/V_abc123..."
    ```

    **응답**:
    ```json
    {
      "voice_id": "V_abc123...",
      "name": "김대표님",
      "description": "대표님의 목소리",
      "category": "cloned",
      "created_at": "2026-02-01T12:00:00Z"
    }
    ```
    """
    try:
        # Neo4j에서 조회
        neo4j_client = Neo4jClient()
        try:
            voice_data = neo4j_client.get_custom_voice_by_id(voice_id)
        finally:
            neo4j_client.close()

        if not voice_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Voice not found: {voice_id}"
            )

        return VoiceInfoResponse(
            voice_id=voice_data["voice_id"],
            name=voice_data["name"],
            description=voice_data.get("description", ""),
            category="cloned",
            created_at=str(voice_data.get("created_at", ""))
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voice info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get voice info: {str(e)}"
        )


@router.delete("/{voice_id}", response_model=VoiceDeleteResponse)
async def delete_voice(voice_id: str):
    """
    커스텀 음성 삭제

    **주의**: ElevenLabs와 Neo4j에서 모두 삭제됩니다.

    **예시**:
    ```bash
    curl -X DELETE "http://localhost:8000/api/v1/voice/V_abc123..."
    ```

    **응답**:
    ```json
    {
      "success": true,
      "message": "Voice deleted successfully"
    }
    ```
    """
    try:
        # Voice Cloning 서비스
        vc_service = get_voice_cloning_service()

        # ElevenLabs에서 삭제
        elevenlabs_deleted = await vc_service.delete_voice(voice_id)

        # Neo4j에서 삭제
        neo4j_client = Neo4jClient()
        try:
            neo4j_deleted = neo4j_client.delete_custom_voice(voice_id)
        finally:
            neo4j_client.close()

        if elevenlabs_deleted or neo4j_deleted:
            return VoiceDeleteResponse(
                success=True,
                message=f"Voice {voice_id} deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Voice not found: {voice_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete voice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete voice: {str(e)}"
        )


@router.post("/validate", response_model=AudioValidationResponse)
async def validate_audio(
    audio_file: UploadFile = File(..., description="검증할 오디오 파일")
):
    """
    오디오 파일 검증 (업로드 전 사전 확인용)

    **예시**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/voice/validate" \\
      -F "audio_file=@recording.mp3"
    ```

    **응답**:
    ```json
    {
      "valid": true,
      "duration_seconds": 185.3,
      "file_size_mb": 3.2,
      "format": "mp3",
      "warnings": [
        "Audio file is small. Recommend 3-5 minutes for best quality."
      ]
    }
    ```
    """
    try:
        vc_service = get_voice_cloning_service()

        # 임시 파일 저장
        file_data = await audio_file.read()
        temp_path = await vc_service.save_uploaded_file(
            file_data=file_data,
            user_id="temp",
            original_filename=audio_file.filename
        )

        # 검증
        validation = await vc_service.validate_audio_file(temp_path)

        # 임시 파일 삭제
        import os
        os.remove(temp_path)

        return AudioValidationResponse(**validation)

    except Exception as e:
        logger.error(f"Audio validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )
