"""
Text-to-Speech service using Google Cloud TTS API with fallback support
"""

import asyncio
import base64
import functools
import logging
import os
from typing import List, Dict, Any, Optional, Union

# Google Cloud imports with fallback
try:
    from google.cloud import texttospeech as gcloud_tts
    from google.auth.exceptions import DefaultCredentialsError
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    gcloud_tts = None
    DefaultCredentialsError = Exception
    GOOGLE_TTS_AVAILABLE = False

from app.core.config import settings
from app.core.exceptions import VoiceProcessingError
from app.models.schemas.voice import TTSRequest, TTSResponse

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service with Google Cloud TTS and fallback support"""
    
    def __init__(self):
        """Initialize TTS service with graceful degradation"""
        self.client: Optional[Any] = None
        self._initialized = False
        self._mock_mode = False
        
        if not GOOGLE_TTS_AVAILABLE:
            logger.warning("Google Cloud TTS library not available. Running in mock mode.")
            self._mock_mode = True
            return
            
        self._initialize_google_client()
    
    def _initialize_google_client(self):
        """Initialize Google Cloud TTS client"""
        try:
            # Check for credentials file
            credentials_path = getattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS', None)
            if credentials_path and not os.path.exists(credentials_path):
                logger.warning(f"Google Cloud credentials file not found at: {credentials_path}. Running in mock mode.")
                self._mock_mode = True
                return
            
            # Initialize client
            if gcloud_tts is not None:
                self.client = gcloud_tts.TextToSpeechClient()
                self._initialized = True
                logger.info("Google Cloud TTS service initialized successfully")
            else:
                self._mock_mode = True
                
        except DefaultCredentialsError:
            logger.warning("Google Cloud credentials not found. Running in mock mode.")
            self._mock_mode = True
        except Exception as e:
            logger.warning(f"Failed to initialize Google Cloud TTS client: {e}. Running in mock mode.")
            self._mock_mode = True
    
    async def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        """Synthesize text to speech with automatic fallback"""
        if self._mock_mode or not self._initialized or self.client is None:
            return self._create_mock_response(request)
            
        try:
            return await self._synthesize_with_google(request)
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}. Falling back to mock response.")
            return self._create_mock_response(request)
    
    async def _synthesize_with_google(self, request: TTSRequest) -> TTSResponse:
        """Synthesize using Google Cloud TTS"""
        if gcloud_tts is None or self.client is None:
            return self._create_mock_response(request)
            
        # Prepare synthesis input
        input_text = gcloud_tts.SynthesisInput(text=request.text)
        
        # Configure voice
        voice = gcloud_tts.VoiceSelectionParams(
            language_code=self._extract_language_code(
                request.voice_name or settings.TTS_VOICE_NAME
            ),
            name=request.voice_name or settings.TTS_VOICE_NAME,
            ssml_gender=gcloud_tts.SsmlVoiceGender.NEUTRAL,
        )
        
        # Configure audio output
        audio_config = gcloud_tts.AudioConfig(
            audio_encoding=self._get_google_audio_encoding(request.output_format),
            speaking_rate=request.speaking_rate or settings.TTS_SPEAKING_RATE,
            pitch=request.pitch or settings.TTS_PITCH,
            volume_gain_db=request.volume_gain_db or 0.0,
        )
        
        # Perform synthesis in executor with type-safe client reference
        client = self.client  # Create local reference for type checker
        assert client is not None, "Client should not be None here"
        
        def synthesize_call():
            return client.synthesize_speech(
                input=input_text,
                voice=voice,
                audio_config=audio_config
            )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, synthesize_call)  # type: ignore[arg-type]
        
        # Encode audio data
        audio_data = base64.b64encode(response.audio_content).decode('utf-8')
        
        # Calculate approximate duration
        duration = len(request.text) * 0.1  # ~100ms per character
        
        return TTSResponse(
            audio_data=audio_data,
            content_type=self._get_content_type(request.output_format),
            duration_seconds=duration
        )
    
    def _create_mock_response(self, request: TTSRequest) -> TTSResponse:
        """Create a mock response when TTS is not available"""
        # Create minimal audio data
        mock_audio = b'\x00' * 1024  # 1KB of silence
        audio_data = base64.b64encode(mock_audio).decode('utf-8')
        
        return TTSResponse(
            audio_data=audio_data,
            content_type=self._get_content_type(request.output_format),
            duration_seconds=len(request.text) * 0.1
        )
    
    async def synthesize_ssml(self, ssml: str, voice_name: Optional[str] = None, 
                            output_format: str = "mp3") -> TTSResponse:
        """Synthesize SSML to speech with fallback"""
        if self._mock_mode or not self._initialized or self.client is None:
            return self._create_mock_ssml_response(ssml, output_format)
            
        try:
            return await self._synthesize_ssml_with_google(ssml, voice_name, output_format)
        except Exception as e:
            logger.error(f"SSML synthesis failed: {e}. Falling back to mock response.")
            return self._create_mock_ssml_response(ssml, output_format)
    
    async def _synthesize_ssml_with_google(self, ssml: str, voice_name: Optional[str], 
                                         output_format: str) -> TTSResponse:
        """Synthesize SSML using Google Cloud TTS"""
        if gcloud_tts is None or self.client is None:
            return self._create_mock_ssml_response(ssml, output_format)
            
        # Prepare SSML input
        input_ssml = gcloud_tts.SynthesisInput(ssml=ssml)
        
        # Configure voice
        voice = gcloud_tts.VoiceSelectionParams(
            language_code=self._extract_language_code(
                voice_name or settings.TTS_VOICE_NAME
            ),
            name=voice_name or settings.TTS_VOICE_NAME,
        )
        
        # Configure audio output
        audio_config = gcloud_tts.AudioConfig(
            audio_encoding=self._get_google_audio_encoding(output_format)
        )
        
        # Perform synthesis in executor with type-safe client reference
        client = self.client  # Create local reference for type checker
        assert client is not None, "Client should not be None here"
        
        def synthesize_ssml_call():
            return client.synthesize_speech(
                input=input_ssml,
                voice=voice,
                audio_config=audio_config
            )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, synthesize_ssml_call)  # type: ignore[arg-type]
        
        # Encode audio data
        audio_data = base64.b64encode(response.audio_content).decode('utf-8')
        
        return TTSResponse(
            audio_data=audio_data,
            content_type=self._get_content_type(output_format),
            duration_seconds=0.0  # Cannot estimate from SSML
        )
    
    def _create_mock_ssml_response(self, ssml: str, output_format: str) -> TTSResponse:
        """Create mock response for SSML synthesis"""
        # Extract text from SSML for duration calculation
        text = ssml.replace('<speak>', '').replace('</speak>', '')
        
        # Create minimal audio data
        mock_audio = b'\x00' * 1024
        audio_data = base64.b64encode(mock_audio).decode('utf-8')
        
        return TTSResponse(
            audio_data=audio_data,
            content_type=self._get_content_type(output_format),
            duration_seconds=len(text) * 0.1
        )
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices with fallback"""
        if self._mock_mode or not self._initialized or self.client is None:
            return self._get_mock_voices()
            
        try:
            # Create type-safe client reference
            client = self.client
            assert client is not None, "Client should not be None here"
            
            def list_voices_call():
                return client.list_voices()
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, list_voices_call)  # type: ignore[arg-type]
            
            voices = []
            for voice in response.voices:
                voices.append({
                    "name": voice.name,
                    "language_codes": list(voice.language_codes),
                    "ssml_gender": voice.ssml_gender.name,
                    "natural_sample_rate_hertz": voice.natural_sample_rate_hertz,
                })
            
            return voices
            
        except Exception as e:
            logger.error(f"Failed to get available voices: {e}")
            return self._get_mock_voices()
    
    def _get_mock_voices(self) -> List[Dict[str, Any]]:
        """Return mock voices for development/testing"""
        return [
            {
                "name": "en-US-Neural2-F",
                "language_codes": ["en-US"],
                "ssml_gender": "FEMALE",
                "natural_sample_rate_hertz": 24000,
            },
            {
                "name": "en-US-Neural2-M",
                "language_codes": ["en-US"],
                "ssml_gender": "MALE",
                "natural_sample_rate_hertz": 24000,
            }
        ]
    
    def _extract_language_code(self, voice_name: str) -> str:
        """Extract language code from voice name"""
        if voice_name and voice_name.startswith("en-"):
            return voice_name[:5]  # e.g., "en-US"
        return "en-US"  # Default fallback
    
    def _get_google_audio_encoding(self, format: str):
        """Get Google Cloud audio encoding from format string"""
        if gcloud_tts is None:
            return None
            
        format_map = {
            "mp3": gcloud_tts.AudioEncoding.MP3,
            "wav": gcloud_tts.AudioEncoding.LINEAR16,
            "ogg": gcloud_tts.AudioEncoding.OGG_OPUS,
        }
        return format_map.get(format.lower(), gcloud_tts.AudioEncoding.MP3)
    
    def _get_content_type(self, format: str) -> str:
        """Get content type from format string"""
        content_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
        }
        return content_types.get(format.lower(), "audio/mpeg") 