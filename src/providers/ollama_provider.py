"""
Ollama local AI provider for guide generation.
"""

import requests
import json
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OllamaProvider:
    """Ollama local AI provider for guide generation."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get('model', 'llama3.2:3b')
        self.host = config.get('host', 'http://localhost:11434')
        self.temperature = config.get('temperature', 0.1)
        self.max_tokens = config.get('max_tokens', 4000)
        self.timeout = config.get('timeout', 120)
        self.system_prompt = config.get('system_prompt', self._default_system_prompt())
    
    def _default_system_prompt(self) -> str:
        """Default system prompt for guide generation."""
        return (
            "You are a technical documentation expert specializing in cloud infrastructure, "
            "virtualization, and deployment guides. Create clear, structured, step-by-step "
            "guides from video transcriptions. Focus on accuracy, clarity, and proper formatting."
        )
    
    def is_available(self) -> bool:
        """Check if Ollama server is available."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_model(self) -> bool:
        """Check if the specified model is available."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(model['name'] == self.model for model in models)
            return False
        except:
            return False
    
    def pull_model(self) -> bool:
        """Pull the model if it's not available."""
        try:
            logger.info(f"Pulling Ollama model: {self.model}")
            
            data = {'name': self.model}
            response = requests.post(
                f"{self.host}/api/pull",
                json=data,
                timeout=600  # Model pulling can take a while
            )
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to pull model {self.model}: {e}")
            return False
    
    def generate_guide(self, transcription: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate guide using Ollama.
        
        Args:
            transcription: Raw transcription text
            context: Optional context information
            
        Returns:
            Generated guide in markdown format
        """
        try:
            # Check if Ollama is available
            if not self.is_available():
                raise ConnectionError("Ollama server is not available")
            
            # Check if model exists, pull if needed
            if not self.check_model():
                logger.info(f"Model {self.model} not found, attempting to pull...")
                if not self.pull_model():
                    raise ValueError(f"Failed to pull model {self.model}")
            
            # Build the prompt
            user_prompt = self._build_user_prompt(transcription, context)
            
            # Prepare the request
            data = {
                'model': self.model,
                'prompt': user_prompt,
                'system': self.system_prompt,
                'stream': False,
                'options': {
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens
                }
            }
            
            # Make the request
            response = requests.post(
                f"{self.host}/api/generate",
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'response' in result:
                return result['response'].strip()
            else:
                raise ValueError("No response generated")
                
        except Exception as e:
            logger.error(f"Ollama guide generation failed: {e}")
            raise
    
    def _build_user_prompt(self, transcription: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build user prompt with transcription and context."""
        prompt_parts = [
            "Transform the following video transcription into a professional technical guide.",
            "",
            "Requirements:",
            "1. Create a clear title and overview",
            "2. Add prerequisites section",
            "3. Break into numbered steps",
            "4. Format commands in code blocks",
            "5. Fix transcription errors (e.g., 'hetsnir' → 'Hetzner', 'ZOS' → 'ZeroOS')",
            "6. Add troubleshooting section",
            "7. Include summary",
            "8. Use proper markdown formatting",
            "",
            "Focus on technical accuracy and clarity. The guide should be professional and easy to follow.",
            ""
        ]
        
        if context:
            if context.get('title'):
                prompt_parts.append(f"Video Title: {context['title']}")
            if context.get('description'):
                prompt_parts.append(f"Description: {context['description']}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            "Transcription:",
            "---",
            transcription,
            "---",
            "",
            "Generate the technical guide:"
        ])
        
        return "\n".join(prompt_parts)
