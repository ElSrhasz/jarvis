"""
Módulo de voz para JARVIS.
Maneja STT (Speech-to-Text), TTS (Text-to-Speech) y Wake Word detection.
Optimizado para bajo consumo de recursos en Linux.
"""

import asyncio
import logging
import subprocess
import threading
from typing import Optional, Callable, Generator
from pathlib import Path

import numpy as np
import pyaudio
import webrtcvad
from vosk import Model, KaldiRecognizer

from config.settings import Config

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Grabación de audio asíncrona con PyAudio."""
    
    def __init__(self):
        self.sample_rate = Config.AUDIO_SAMPLE_RATE
        self.channels = Config.AUDIO_CHANNELS
        self.chunk_size = Config.AUDIO_CHUNK_SIZE
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        
    def start(self) -> None:
        """Iniciar el stream de audio."""
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            self.is_recording = True
            logger.debug("Stream de audio iniciado")
        except Exception as e:
            logger.error(f"Error al iniciar el stream de audio: {e}")
            raise
    
    def stop(self) -> None:
        """Detener el stream de audio."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.is_recording = False
            logger.debug("Stream de audio detenido")
    
    def read_chunk(self) -> bytes:
        """Leer un chunk de audio."""
        if self.stream and self.is_recording:
            try:
                return self.stream.read(self.chunk_size, exception_on_overflow=False)
            except Exception as e:
                logger.error(f"Error al leer audio: {e}")
                return b""
        return b""
    
    def cleanup(self) -> None:
        """Liberar recursos de PyAudio."""
        self.stop()
        self.audio.terminate()


class VoiceActivityDetector:
    """Detección de actividad de voz usando WebRTC VAD."""
    
    def __init__(self, mode: int = 2):
        """
        Inicializar VAD.
        
        Args:
            mode: Agresividad del VAD (0-3). 
                  0 = menos agresivo, 3 = más agresivo
        """
        self.vad = webrtcvad.Vad(mode)
        self.sample_rate = Config.AUDIO_SAMPLE_RATE
        
    def is_speech(self, frame: bytes) -> bool:
        """Determinar si un frame contiene voz."""
        try:
            return self.vad.is_speech(frame, self.sample_rate)
        except Exception:
            return False


class SpeechToText:
    """Conversión de voz a texto usando Vosk."""
    
    def __init__(self):
        self.model_path = Path(Config.STT_MODEL_PATH)
        self.model = None
        self.recognizer = None
        self._load_model()
        
    def _load_model(self) -> None:
        """Cargar modelo Vosk."""
        if not self.model_path.exists():
            logger.warning(
                f"Modelo Vosk no encontrado en {self.model_path}. "
                "Descarga el modelo desde https://alphacephei.com/vosk/models/"
            )
            # Intentar usar modelo por defecto
            self.model_path = Path.home() / ".cache" / "vosk" / "model"
            
        try:
            self.model = Model(str(self.model_path))
            self.recognizer = KaldiRecognizer(self.model, Config.AUDIO_SAMPLE_RATE)
            logger.info(f"Modelo Vosk cargado desde {self.model_path}")
        except Exception as e:
            logger.error(f"Error al cargar modelo Vosk: {e}")
            raise
    
    def recognize(self, audio_data: bytes) -> Optional[str]:
        """
        Reconocer texto desde datos de audio.
        
        Args:
            audio_data: Bytes de audio en formato PCM 16-bit
            
        Returns:
            Texto reconocido o None si falla
        """
        if self.recognizer.AcceptWaveform(audio_data):
            result = self.recognizer.Result()
            if isinstance(result, str):
                import json
                result = json.loads(result)
            return result.get("text", "")
        return None
    
    def recognize_partial(self, audio_data: bytes) -> Optional[str]:
        """Reconocimiento parcial (para feedback en tiempo real)."""
        if self.recognizer.PartialResult():
            result = self.recognizer.PartialResult()
            if isinstance(result, str):
                import json
                result = json.loads(result)
            return result.get("partial", "")
        return None


class TextToSpeech:
    """Conversión de texto a voz usando múltiples engines."""
    
    def __init__(self):
        self.engine = Config.TTS_ENGINE.lower()
        self._init_engine()
        
    def _init_engine(self) -> None:
        """Inicializar el engine de TTS seleccionado."""
        if self.engine == "pyttsx3":
            try:
                import pyttsx3
                self.tts_engine = pyttsx3.init()
                voices = self.tts_engine.getProperty('voices')
                # Intentar encontrar voz en español
                for voice in voices:
                    if 'spanish' in voice.name.lower() or 'es' in voice.id.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                self.tts_engine.setProperty('rate', 175)  # Velocidad ligeramente rápida
                logger.info("Engine pyttsx3 inicializado")
            except ImportError:
                logger.warning("pyttsx3 no disponible, cambiando a espeak")
                self.engine = "espeak"
                self.tts_engine = None
        else:
            self.tts_engine = None
            logger.info(f"Usando engine TTS: {self.engine}")
    
    def speak(self, text: str, blocking: bool = False) -> Optional[threading.Thread]:
        """
        Convertir texto a voz y reproducir.
        
        Args:
            text: Texto a convertir
            blocking: Si True, espera a que termine la reproducción
            
        Returns:
            Thread si blocking=False, None si blocking=True
        """
        if not text.strip():
            return None
            
        def _speak_thread():
            try:
                if self.engine == "espeak":
                    self._speak_espeak(text)
                elif self.engine == "pyttsx3" and self.tts_engine:
                    self._speak_pyttsx3(text)
                elif self.engine == "piper":
                    self._speak_piper(text)
                else:
                    logger.warning(f"Engine TTS '{self.engine}' no soportado")
            except Exception as e:
                logger.error(f"Error en TTS: {e}")
        
        if blocking:
            _speak_thread()
            return None
        else:
            thread = threading.Thread(target=_speak_thread, daemon=True)
            thread.start()
            return thread
    
    def _speak_espeak(self, text: str) -> None:
        """Usar espeak-ng directamente."""
        try:
            # Limpiar texto para evitar inyección de comandos
            safe_text = text.replace("'", "").replace('"', '').replace(';', '')
            subprocess.run([
                'espeak-ng',
                '-v', 'es',
                '-s', '175',
                '-p', '50',
                safe_text
            ], check=True, capture_output=True)
            logger.debug(f"TTS (espeak): {text[:50]}...")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error en espeak: {e}")
        except FileNotFoundError:
            logger.error("espeak-ng no instalado. Ejecuta: sudo apt install espeak-ng")
    
    def _speak_pyttsx3(self, text: str) -> None:
        """Usar pyttsx3."""
        if self.tts_engine:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            logger.debug(f"TTS (pyttsx3): {text[:50]}...")
    
    def _speak_piper(self, text: str) -> None:
        """Usar Piper TTS (más natural pero requiere configuración)."""
        piper_path = Path.home() / "piper" / "piper"
        voice_path = Path.home() / "piper" / "voices" / "es_MX-speaker_0-medium.onnx"
        
        if not piper_path.exists():
            logger.warning("Piper no encontrado, usando espeak como fallback")
            self._speak_espeak(text)
            return
            
        try:
            safe_text = text.replace("'", "").replace('"', '')
            process = subprocess.Popen(
                [str(piper_path), '-m', str(voice_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, _ = process.communicate(input=safe_text.encode())
            
            # Reproducir audio desde stdout
            subprocess.run(['aplay', '-q', '-r', '22050', '-f', 'S16_LE'], input=stdout)
            logger.debug(f"TTS (piper): {text[:50]}...")
        except Exception as e:
            logger.error(f"Error en piper: {e}")
            self._speak_espeak(text)


class WakeWordDetector:
    """Detección de palabra de activación ligera."""
    
    def __init__(self, wake_word: str = None, sensitivity: float = 0.5):
        self.wake_word = (wake_word or Config.WAKE_WORD).lower()
        self.sensitivity = sensitivity
        self.stt = SpeechToText()
        self.vad = VoiceActivityDetector()
        self.audio_recorder = AudioRecorder()
        self.is_listening = False
        self.on_wake_word: Optional[Callable] = None
        
    def detect_in_audio(self, audio_data: bytes) -> bool:
        """Detectar wake word en un chunk de audio."""
        text = self.stt.recognize_partial(audio_data)
        if text:
            text_clean = text.lower().strip()
            if self.wake_word in text_clean:
                logger.info(f"Wake word detectada: {text}")
                return True
        return False
    
    def listen_loop(self, callback: Callable) -> None:
        """
        Bucle de escucha continua para wake word.
        Optimizado para bajo consumo.
        
        Args:
            callback: Función a llamar cuando se detecte la wake word
        """
        self.on_wake_word = callback
        self.is_listening = True
        
        logger.info(f"Escuchando para '{self.wake_word}'...")
        self.audio_recorder.start()
        
        silence_counter = 0
        max_silence = 50  # ~2 segundos de silencio antes de reducir frecuencia
        
        while self.is_listening:
            try:
                chunk = self.audio_recorder.read_chunk()
                
                if not chunk:
                    continue
                
                # Verificar si hay voz para ahorrar CPU
                if self.vad.is_speech(chunk):
                    silence_counter = 0
                    if self.detect_in_audio(chunk):
                        if self.on_wake_word:
                            self.on_wake_word()
                else:
                    silence_counter += 1
                    # Reducir frecuencia de procesamiento en silencio
                    if silence_counter > max_silence:
                        asyncio.sleep(0.1)  # Pequeña pausa para ahorrar CPU
                        
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error en detección de wake word: {e}")
                break
        
        self.audio_recorder.cleanup()
    
    def stop(self) -> None:
        """Detener la detección de wake word."""
        self.is_listening = False


class VoiceModule:
    """Módulo principal de voz que integra todos los componentes."""
    
    def __init__(self):
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.wake_word_detector = WakeWordDetector()
        self.audio_recorder = AudioRecorder()
        self.vad = VoiceActivityDetector()
        
        self._is_active = False
        self._audio_buffer = bytearray()
        
    async def listen_for_command(self, timeout: float = 10.0) -> Optional[str]:
        """
        Escuchar comando de voz después de la wake word.
        
        Args:
            timeout: Tiempo máximo de escucha en segundos
            
        Returns:
            Comando reconocido o None
        """
        logger.info("Escuchando comando...")
        self._audio_buffer = bytearray()
        self.audio_recorder.start()
        
        start_time = asyncio.get_event_loop().time()
        speech_detected = False
        silence_after_speech = 0
        
        try:
            while True:
                current_time = asyncio.get_event_loop().time()
                if current_time - start_time > timeout:
                    logger.debug("Timeout de escucha alcanzado")
                    break
                
                chunk = self.audio_recorder.read_chunk()
                if not chunk:
                    await asyncio.sleep(0.01)
                    continue
                
                if self.vad.is_speech(chunk):
                    speech_detected = True
                    silence_after_speech = 0
                    self._audio_buffer.extend(chunk)
                    
                    # Feedback parcial
                    partial = self.stt.recognize_partial(chunk)
                    if partial:
                        logger.debug(f"Parcial: {partial}")
                else:
                    if speech_detected:
                        silence_after_speech += 1
                        # 1.5 segundos de silencio después del habla = fin del comando
                        if silence_after_speech > 35:
                            break
                
                await asyncio.sleep(0.01)
            
            # Procesar audio completo
            if len(self._audio_buffer) > 0:
                result = self.stt.recognize(bytes(self._audio_buffer))
                if result:
                    logger.info(f"Comando reconocido: {result}")
                    return result
                    
        except Exception as e:
            logger.error(f"Error al escuchar comando: {e}")
        finally:
            self.audio_recorder.cleanup()
        
        return None
    
    def speak(self, text: str, blocking: bool = False) -> None:
        """
        Hablar texto.
        
        Args:
            text: Texto a hablar
            blocking: Si True, bloquea hasta terminar
        """
        logger.debug(f"Hablando: {text[:50]}...")
        self.tts.speak(text, blocking=blocking)
    
    async def activate_and_listen(self) -> Optional[str]:
        """
        Activar con wake word y escuchar comando.
        
        Returns:
            Comando reconocido o None
        """
        # Anunciar que está escuchando
        self.speak("¿Sí, señor?")
        
        # Escuchar comando
        command = await self.listen_for_command(timeout=15.0)
        return command
    
    def cleanup(self) -> None:
        """Liberar recursos."""
        self.wake_word_detector.stop()
        self.audio_recorder.cleanup()
