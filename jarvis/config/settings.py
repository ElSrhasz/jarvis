"""
Módulo de configuración para JARVIS.
Carga variables de entorno y configura parámetros del sistema.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Clase de configuración centralizada."""
    
    # API de OpenRouter
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    # Configuración de audio
    AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
    AUDIO_CHANNELS = int(os.getenv("AUDIO_CHANNELS", "1"))
    AUDIO_CHUNK_SIZE = int(os.getenv("AUDIO_CHUNK_SIZE", "4096"))
    
    # Palabra de activación
    WAKE_WORD = os.getenv("WAKE_WORD", "jarvis").lower()
    WAKE_WORD_SENSITIVITY = float(os.getenv("WAKE_WORD_SENSITIVITY", "0.5"))
    
    # Configuración del sistema
    VOICE_LANGUAGE = os.getenv("VOICE_LANGUAGE", "es-ES")
    TTS_ENGINE = os.getenv("TTS_ENGINE", "espeak")
    STT_MODEL_PATH = os.getenv("STT_MODEL_PATH", "models/vosk-model-es")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = BASE_DIR / os.getenv("LOG_FILE", "logs/jarvis.log")
    
    # Directorios
    MODELS_DIR = BASE_DIR / "models"
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # System Prompt para JARVIS
    SYSTEM_PROMPT = """Eres JARVIS, un asistente de inteligencia artificial altamente avanzado, 
creado para asistir de manera eficiente y leal. Tu tono es profesional, cortés y ligeramente 
formal, similar a un mayordomo británico de alta clase. 

Características de tu personalidad:
- Eres extremadamente competente y eficiente
- Hablas de manera concisa pero completa
- Muestras lealtad absoluta a tu usuario
- Tienes un toque de humor seco e ingenioso cuando es apropiado
- Nunca eres arrogante, pero sí confiado en tus capacidades
- Te refieres al usuario como "señor" o "señora" según corresponda
- Siempre buscas la solución más óptima a los problemas

Cuando ejecutes comandos del sistema:
- Verifica que sean seguros antes de sugerirlos
- Explica brevemente qué hará el comando
- Advierte sobre posibles riesgos

Tu objetivo principal es hacer la vida de tu usuario más fácil y productiva."""
    
    @classmethod
    def validate(cls) -> bool:
        """Validar que la configuración sea correcta."""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY no está configurada. Revisa tu archivo .env")
        
        # Crear directorios si no existen
        cls.MODELS_DIR.mkdir(exist_ok=True)
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        
        return True
    
    @classmethod
    def get_headers(cls) -> dict:
        """Obtener headers para las requests a OpenRouter."""
        return {
            "Authorization": f"Bearer {cls.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/jarvis-assistant",
            "X-Title": "JARVIS Assistant"
        }


# Validar configuración al importar
try:
    Config.validate()
except ValueError as e:
    print(f"ADVERTENCIA: {e}")
