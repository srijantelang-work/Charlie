"""
Voice processing endpoints
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_current_user
from app.services.voice.voice_processor import VoiceProcessor
from app.services.voice.stt_service import STTService
from app.services.voice.tts_service import TTSService
from app.models.schemas.voice import (
    STTRequest, STTResponse,
    TTSRequest, TTSResponse,
    VoiceCommandRequest, VoiceCommandResponse,
    VoiceCapabilities
)

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Initialize voice services
voice_processor = VoiceProcessor()
stt_service = STTService()
tts_service = TTSService()


@router.post("/command", response_model=VoiceCommandResponse)
@limiter.limit("10/minute")
async def process_voice_command(
    request: Request,
    voice_request: VoiceCommandRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Process complete voice command (STT -> AI -> TTS)"""
    try:
        user_id = current_user["id"]
        
        response = await voice_processor.process_voice_command(
            request=voice_request,
            user_id=user_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Voice command processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice command processing failed: {str(e)}"
        )


@router.post("/stt", response_model=STTResponse)
@limiter.limit("20/minute")
async def speech_to_text(
    request: Request,
    stt_request: STTRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Convert speech to text"""
    try:
        response = await stt_service.transcribe_audio(
            audio_data=stt_request.audio_data,
            sample_rate=stt_request.sample_rate,
            encoding=stt_request.encoding,
            language_code=stt_request.language_code
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Speech-to-text failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech-to-text failed: {str(e)}"
        )


@router.post("/tts", response_model=TTSResponse)
@limiter.limit("30/minute")
async def text_to_speech(
    request: Request,
    tts_request: TTSRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Convert text to speech"""
    try:
        response = await tts_service.synthesize_speech(request=tts_request)
        return response
        
    except Exception as e:
        logger.error(f"Text-to-speech failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text-to-speech failed: {str(e)}"
        )


@router.post("/upload-audio")
@limiter.limit("15/minute")
async def upload_audio_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Upload audio file for processing"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an audio file"
            )
        
        # Read and process audio data
        audio_content = await file.read()
        
        # Convert to base64 for processing
        import base64
        audio_data = base64.b64encode(audio_content).decode('utf-8')
        
        # Process with STT
        response = await stt_service.transcribe_audio(
            audio_data=audio_data,
            sample_rate=16000,  # Default sample rate
            encoding="LINEAR16"
        )
        
        return {
            "filename": file.filename,
            "transcript": response.transcript,
            "file_size": len(audio_content),
            "content_type": file.content_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio upload processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio upload processing failed: {str(e)}"
        )


@router.get("/capabilities", response_model=VoiceCapabilities)
async def get_voice_capabilities(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get voice processing capabilities"""
    return VoiceCapabilities(
        supported_languages=["en-US", "en-GB", "es-ES", "fr-FR", "de-DE"],
        supported_voices=[
            "en-US-Neural2-F", "en-US-Neural2-C", "en-US-Neural2-D",
            "en-GB-Neural2-A", "es-ES-Neural2-B", "fr-FR-Neural2-A"
        ],
        audio_formats=["LINEAR16", "MP3", "OGG_OPUS"],
        sample_rates=[8000, 16000, 22050, 44100, 48000],
        max_audio_duration_seconds=300,
        real_time_processing=True
    )


@router.get("/settings")
async def get_voice_settings(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user's voice settings"""
    # This would fetch from user preferences in database
    return {
        "default_language": "en-US",
        "preferred_voice": "en-US-Neural2-F",
        "speaking_rate": 1.0,
        "pitch": 0.0,
        "auto_detect_language": True,
        "noise_reduction": True
    }


@router.put("/settings")
async def update_voice_settings(
    settings: dict,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user's voice settings"""
    try:
        user_id = current_user["id"]
        
        # This would update user preferences in database
        # For now, just return the updated settings
        
        return {
            "message": "Voice settings updated successfully",
            "settings": settings,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Voice settings update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice settings update failed: {str(e)}"
        ) 