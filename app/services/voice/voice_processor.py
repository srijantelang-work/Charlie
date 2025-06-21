"""
Voice processor that combines STT, AI, and TTS services
"""

import asyncio
import logging
import time
import uuid
from typing import Optional

from app.core.exceptions import VoiceProcessingError
from app.models.schemas.voice import VoiceCommandRequest, VoiceCommandResponse, STTRequest, TTSRequest
from app.services.voice.stt_service import STTService
from app.services.voice.tts_service import TTSService
from app.services.ai.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Main voice processor combining STT, AI, and TTS"""
    
    def __init__(self):
        """Initialize voice processor"""
        self.stt_service = STTService()
        self.tts_service = TTSService()
        self.gemini_service = GeminiService()
        logger.info("Voice processor initialized")
    
    async def process_voice_command(self, request: VoiceCommandRequest, user_id: str) -> VoiceCommandResponse:
        """Process complete voice command pipeline"""
        start_time = time.time()
        session_id = request.session_id or str(uuid.uuid4())
        
        try:
            # Step 1: Speech-to-Text
            logger.info(f"Processing voice command for user {user_id}")
            
            stt_response = await self.stt_service.transcribe_audio(
                audio_data=request.audio_data,
                language_code="en-US",  # Default language code
                sample_rate=16000,
                encoding="LINEAR16"
            )
            
            transcript = stt_response.transcript.strip()
            
            if not transcript:
                raise VoiceProcessingError("No speech detected in audio")
            
            logger.info(f"Transcribed: {transcript}")
            
            # Step 2: AI Processing
            ai_response = await self.gemini_service.generate_response(
                user_input=transcript,
                user_id=user_id,
                session_id=session_id,
                context=request.context
            )
            
            logger.info(f"AI response: {ai_response[:100]}...")
            
            # Step 3: Text-to-Speech
            tts_request = TTSRequest(
                text=ai_response,
                voice_name=None,
                speaking_rate=None,
                pitch=None,
                volume_gain_db=None,
                output_format="mp3"
            )
            
            tts_response = await self.tts_service.synthesize_speech(tts_request)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            return VoiceCommandResponse(
                transcript=transcript,
                ai_response=ai_response,
                audio_response=tts_response.audio_data,
                session_id=session_id,
                confidence=stt_response.confidence,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Voice command processing failed: {e}")
            raise VoiceProcessingError(f"Voice processing failed: {e}")
    
    async def process_streaming_voice(self, audio_chunks: list, user_id: str, 
                                    session_id: Optional[str] = None) -> VoiceCommandResponse:
        """Process streaming voice input"""
        start_time = time.time()
        session_id = session_id or str(uuid.uuid4())
        
        try:
            # Process streaming audio
            transcripts = await self.stt_service.transcribe_streaming(audio_chunks)
            
            if not transcripts:
                raise VoiceProcessingError("No speech detected in audio stream")
            
            # Combine transcripts
            full_transcript = " ".join(transcripts)
            logger.info(f"Streaming transcribed: {full_transcript}")
            
            # Process with AI
            ai_response = await self.gemini_service.generate_response(
                user_input=full_transcript,
                user_id=user_id,
                session_id=session_id
            )
            
            # Convert to speech
            tts_request = TTSRequest(
                text=ai_response,
                voice_name=None,
                speaking_rate=None,
                pitch=None,
                volume_gain_db=None,
                output_format="mp3"
            )
            
            tts_response = await self.tts_service.synthesize_speech(tts_request)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return VoiceCommandResponse(
                transcript=full_transcript,
                ai_response=ai_response,
                audio_response=tts_response.audio_data,
                session_id=session_id,
                confidence=0.95,  # Approximate for streaming
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Streaming voice processing failed: {e}")
            raise VoiceProcessingError(f"Streaming processing failed: {e}")
    
    async def get_voice_capabilities(self) -> dict:
        """Get voice processing capabilities"""
        try:
            # Get available voices
            voices = await self.tts_service.get_available_voices()
            
            # Get supported languages
            languages = self.stt_service.get_supported_languages()
            
            return {
                "stt_languages": languages,
                "tts_voices": voices[:10],  # Limit to first 10 for brevity
                "audio_formats": ["mp3", "wav", "ogg"],
                "max_audio_duration": 60,  # seconds
                "streaming_supported": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get voice capabilities: {e}")
            return {
                "error": "Failed to retrieve capabilities"
            } 