"""
Mock voice services for development without Google Cloud credentials
"""

import asyncio
import base64
import logging
from typing import List, Optional

from app.models.schemas.voice import STTResponse, TTSResponse

logger = logging.getLogger(__name__)


class MockSTTService:
    """Mock Speech-to-Text service for development"""
    
    def __init__(self):
        """Initialize mock STT service"""
        self.mock_mode = True
        logger.info("Mock STT service initialized")
    
    async def transcribe_audio(self, 
                               audio_data: str, 
                               sample_rate: int = 16000,
                               encoding: str = "LINEAR16",
                               language_code: Optional[str] = None) -> STTResponse:
        """Mock transcribe audio data to text"""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return STTResponse(
            transcript="Mock transcription: This is a simulated response for development.",
            confidence=0.95,
            language_detected=language_code or "en-US"
        )
    
    async def transcribe_streaming(self, audio_chunks: List[bytes]) -> List[str]:
        """Mock transcribe streaming audio chunks"""
        await asyncio.sleep(0.1)
        return [
            "Mock streaming chunk 1: Hello world",
            "Mock streaming chunk 2: This is a test"
        ]
    
    def get_supported_languages(self) -> List[str]:
        """Get mock list of supported languages"""
        return [
            "en-US", "en-GB", "en-CA", "en-AU",
            "es-ES", "es-US", "fr-FR", "de-DE",
            "it-IT", "pt-BR", "ja-JP", "ko-KR"
        ]


class MockTTSService:
    """Mock Text-to-Speech service for development"""
    
    def __init__(self):
        """Initialize mock TTS service"""
        self.mock_mode = True
        logger.info("Mock TTS service initialized")
    
    async def synthesize_speech(self,
                                text: str,
                                voice_name: Optional[str] = None,
                                speaking_rate: Optional[float] = None,
                                pitch: Optional[float] = None,
                                audio_format: Optional[str] = None) -> str:
        """Mock synthesize speech from text"""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Create a simple mock audio data (base64 encoded silence)
        mock_audio = b"\x00" * 1024  # 1KB of silence
        return base64.b64encode(mock_audio).decode('utf-8')
    
    async def get_voices(self, language_code: str = "en-US") -> List[dict]:
        """Mock get available voices"""
        return [
            {
                "name": "en-US-Neural2-F",
                "ssml_gender": "FEMALE",
                "language_codes": ["en-US"]
            },
            {
                "name": "en-US-Neural2-C", 
                "ssml_gender": "FEMALE",
                "language_codes": ["en-US"]
            },
            {
                "name": "en-US-Neural2-D",
                "ssml_gender": "MALE", 
                "language_codes": ["en-US"]
            }
        ]
    
    def get_supported_formats(self) -> List[str]:
        """Get mock supported audio formats"""
        return ["MP3", "LINEAR16", "OGG_OPUS"] 