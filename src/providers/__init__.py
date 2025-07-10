"""
API Provider abstractions for transcription and guide generation services.
"""

from providers.base import APIProvider, TranscriptionProvider, GuideGenerationProvider
from providers.openrouter import OpenRouterProvider
from providers.ollama_provider import OllamaProvider

__all__ = [
    'APIProvider',
    'TranscriptionProvider', 
    'GuideGenerationProvider',
    'OpenRouterProvider',
    'OllamaProvider'
]
