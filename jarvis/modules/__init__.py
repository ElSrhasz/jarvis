"""
Módulos de JARVIS.
"""

from .voice_module import VoiceModule, SpeechToText, TextToSpeech, WakeWordDetector
from .llm_module import LLMModule, ConversationHistory, OpenRouterClient
from .system_module import SystemController, SystemCommand, get_system_controller
from .ui_module import JarvisUI, MinimalUI, create_ui

__all__ = [
    'VoiceModule',
    'SpeechToText', 
    'TextToSpeech',
    'WakeWordDetector',
    'LLMModule',
    'ConversationHistory',
    'OpenRouterClient',
    'SystemController',
    'SystemCommand',
    'get_system_controller',
    'JarvisUI',
    'MinimalUI',
    'create_ui',
]
