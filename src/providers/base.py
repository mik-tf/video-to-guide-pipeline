"""
Base classes for API providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class APIProvider(ABC):
    """Base class for all API providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = self._get_api_key()
        self.base_url = config.get('base_url', '')
        self.timeout = config.get('timeout', 60)
        self.max_retries = config.get('max_retries', 3)
    
    def _get_api_key(self) -> str:
        """Get API key from environment variable."""
        import os
        api_key_env = self.config.get('api_key_env')
        if not api_key_env:
            raise ValueError("API key environment variable not specified")
        
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"API key not found in environment variable: {api_key_env}")
        
        return api_key


class TranscriptionProvider(APIProvider):
    """Base class for transcription API providers."""
    
    @abstractmethod
    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary containing transcription result with 'text' key
        """
        pass


class GuideGenerationProvider(APIProvider):
    """Base class for guide generation API providers."""
    
    @abstractmethod
    def generate_guide(self, transcription: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a structured guide from transcription text.
        
        Args:
            transcription: Raw transcription text
            context: Optional context information (video title, etc.)
            
        Returns:
            Generated guide in markdown format
        """
        pass
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for guide generation."""
        return self.config.get('system_prompt', 
            "You are a technical documentation expert. Transform video transcriptions "
            "into professional, structured deployment guides with clear steps, "
            "code blocks, and troubleshooting sections."
        )
    
    def _build_user_prompt(self, transcription: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build user prompt with transcription and context."""
        prompt_parts = [
            "Please transform the following video transcription into a professional, "
            "structured technical guide. Follow these requirements:",
            "",
            "1. Create a clear title and overview section",
            "2. Add proper prerequisites section", 
            "3. Break content into logical, numbered steps",
            "4. Format shell commands in code blocks",
            "5. Extract and properly format URLs",
            "6. Add troubleshooting section for common issues",
            "7. Include a summary section",
            "8. Use proper markdown formatting throughout",
            "9. Fix any transcription errors (e.g., 'hetsnir' → 'Hetzner')",
            "10. Ensure technical accuracy and clarity",
            "",
            "Video Transcription:",
            "---",
            transcription,
            "---",
            "",
            "Generate a professional technical guide in markdown format:"
        ]
        
        if context:
            if context.get('title'):
                prompt_parts.insert(-4, f"Video Title: {context['title']}")
            if context.get('description'):
                prompt_parts.insert(-4, f"Description: {context['description']}")
        
        return "\n".join(prompt_parts)
