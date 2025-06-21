"""
Voice processing utilities for Charlie CLI
"""

import asyncio
import tempfile
import os
import io
from typing import Optional, Union
from pathlib import Path

# Try importing voice processing libraries
try:
    from google.cloud import speech
    from google.cloud import texttospeech
    import pyaudio
    import wave
    HAS_VOICE_DEPS = True
except ImportError:
    HAS_VOICE_DEPS = False

class VoiceProcessor:
    """Handles speech-to-text and text-to-speech operations"""
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.stt_client = None
        self.tts_client = None
        
        if HAS_VOICE_DEPS:
            self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Google Cloud clients"""
        
        try:
            # Initialize Speech-to-Text client
            self.stt_client = speech.SpeechClient()
            
            # Initialize Text-to-Speech client
            self.tts_client = texttospeech.TextToSpeechClient()
            
        except Exception as e:
            if self.ctx.debug:
                print(f"Failed to initialize voice clients: {e}")
    
    async def speech_to_text(self, audio_data: bytes) -> Optional[str]:
        """Convert speech audio data to text"""
        
        if not HAS_VOICE_DEPS or not self.stt_client:
            return "Voice processing not available - missing dependencies"
        
        try:
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=self.ctx.config.get('stt_language'),
                audio_channel_count=1,
                enable_automatic_punctuation=True,
                enable_word_confidence=True,
                enable_word_time_offsets=False,
            )
            
            # Create audio object
            audio = speech.RecognitionAudio(content=audio_data)
            
            # Perform recognition
            loop = asyncio.get_event_loop()
            
            def _recognize():
                # Type assertion since we checked stt_client is not None above
                assert self.stt_client is not None
                return self.stt_client.recognize(config=config, audio=audio)
            
            response = await loop.run_in_executor(None, _recognize)  # type: ignore
            
            # Extract text from response
            if response.results:
                transcript = response.results[0].alternatives[0].transcript
                confidence = response.results[0].alternatives[0].confidence
                
                if self.ctx.debug:
                    print(f"STT Confidence: {confidence:.2f}")
                
                return transcript.strip()
            
            return None
            
        except Exception as e:
            if self.ctx.debug:
                print(f"STT Error: {e}")
            return None
    
    async def text_to_speech(self, text: str, play_audio: bool = True) -> Optional[bytes]:
        """Convert text to speech audio"""
        
        if not HAS_VOICE_DEPS or not self.tts_client:
            print(f"Charlie: {text}")  # Fallback to text output
            return None
        
        try:
            # Configure synthesis
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=self.ctx.config.get('stt_language'),
                name=self.ctx.config.get('tts_voice'),
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                effects_profile_id=['telephony-class-application'],
                pitch=0.0,
                speaking_rate=1.0,
                volume_gain_db=0.0
            )
            
            # Perform synthesis
            loop = asyncio.get_event_loop()
            
            def _synthesize():
                # Type assertion since we checked tts_client is not None above
                assert self.tts_client is not None
                return self.tts_client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice, 
                    audio_config=audio_config
                )
            
            response = await loop.run_in_executor(None, _synthesize)  # type: ignore
            
            # Play audio if requested
            if play_audio and response.audio_content:
                await self._play_audio(response.audio_content)
            
            return response.audio_content
            
        except Exception as e:
            if self.ctx.debug:
                print(f"TTS Error: {e}")
            # Fallback to text output
            print(f"Charlie: {text}")
            return None
    
    async def _play_audio(self, audio_data: bytes):
        """Play audio data through speakers"""
        
        if not HAS_VOICE_DEPS:
            return
        
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # Play audio using PyAudio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._play_wav_file, temp_path)
            
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
                
        except Exception as e:
            if self.ctx.debug:
                print(f"Audio playback error: {e}")
    
    def _play_wav_file(self, file_path: str):
        """Play WAV file using PyAudio"""
        
        try:
            # Open WAV file
            with wave.open(file_path, 'rb') as wav_file:
                # Initialize PyAudio
                audio = pyaudio.PyAudio()
                
                # Open stream
                stream = audio.open(
                    format=audio.get_format_from_width(wav_file.getsampwidth()),
                    channels=wav_file.getnchannels(),
                    rate=wav_file.getframerate(),
                    output=True
                )
                
                # Play audio
                chunk_size = 1024
                data = wav_file.readframes(chunk_size)
                
                while data:
                    stream.write(data)
                    data = wav_file.readframes(chunk_size)
                
                # Cleanup
                stream.stop_stream()
                stream.close()
                audio.terminate()
                
        except Exception as e:
            if self.ctx.debug:
                print(f"WAV playback error: {e}")
    
    async def test_stt(self) -> bool:
        """Test speech-to-text functionality"""
        
        if not HAS_VOICE_DEPS or not self.stt_client:
            return False
        
        try:
            # Create test audio (silence)
            test_audio = b'\x00' * 32000  # 1 second of silence at 16kHz
            
            # Try to process it
            result = await self.speech_to_text(test_audio)
            return True  # If no exception, STT is working
            
        except Exception:
            return False
    
    async def test_tts(self) -> bool:
        """Test text-to-speech functionality"""
        
        if not HAS_VOICE_DEPS or not self.tts_client:
            return False
        
        try:
            # Try to synthesize test text
            await self.text_to_speech("Test", play_audio=False)
            return True
            
        except Exception:
            return False
    
    def check_microphone(self) -> bool:
        """Check if microphone is available"""
        
        if not HAS_VOICE_DEPS:
            return False
        
        try:
            audio = pyaudio.PyAudio()
            
            # Try to open input stream
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            stream.close()
            audio.terminate()
            return True
            
        except Exception:
            return False
    
    def list_audio_devices(self):
        """List available audio devices"""
        
        if not HAS_VOICE_DEPS:
            return []
        
        devices = []
        
        try:
            audio = pyaudio.PyAudio()
            
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                devices.append({
                    'index': i,
                    'name': device_info['name'],
                    'channels': device_info['maxInputChannels'],
                    'rate': device_info['defaultSampleRate']
                })
            
            audio.terminate()
            
        except Exception:
            pass
        
        return devices
    
    def get_voice_commands_help(self) -> str:
        """Get help text for voice commands"""
        
        return """
Voice Commands Help:

🎤 Basic Usage:
• Say "Hey Charlie" to wake up (in continuous mode)
• Speak clearly and pause briefly after your command
• Commands are processed the same as text chat

🗣️ Voice Tips:
• Speak 2-3 feet from your microphone
• Minimize background noise
• Use natural speech patterns
• Wait for Charlie to respond before speaking again

⚙️ Voice Settings:
• Wake word: {wake_word}
• Language: {language}  
• Threshold: {threshold}

Use 'charlie config set' to adjust voice settings.
        """.format(
            wake_word=self.ctx.config.get('wake_word'),
            language=self.ctx.config.get('stt_language'),
            threshold=self.ctx.config.get('voice_threshold')
        ) 