#!/usr/bin/env python3
"""
Guide Generation Module

Transforms transcriptions into structured markdown guides using templates, local AI, or API providers.
"""

import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

try:
    from jinja2 import Template, Environment, FileSystemLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logging.warning("Jinja2 not available. Install with: pip install Jinja2")

from providers.ollama_provider import OllamaProvider
from providers.openrouter import OpenRouterProvider

logger = logging.getLogger(__name__)


class GuideGenerator:
    """
    Generates structured markdown guides from transcriptions using templates, local AI, or API providers.
    
    Provides intelligent text processing, section extraction, and AI-powered guide generation.
    """
    
    def __init__(self, config: Dict[str, Any], processing_mode: str = 'basic'):
        """
        Initialize the GuideGenerator.
        
        Args:
            config: Configuration dictionary with guide generation settings
            processing_mode: Processing mode (basic, local_ai, api_generation, full_api, hybrid)
        """
        self.config = config.get('guide_generation', {})
        self.processing_mode = processing_mode
        self.template_dir = config.get('templates', {}).get('base_dir', './templates')
        
        # AI providers
        self.ollama_provider = None
        self.api_provider = None
        
        # Initialize based on processing mode
        # Template generation setup (for basic, hybrid, and as fallback for all modes)
        if processing_mode in ['basic', 'hybrid', 'local_ai', 'api_generation', 'full_api']:
            self._setup_template_generation()
        
        # Local AI setup
        if processing_mode in ['local_ai', 'hybrid']:
            self._setup_local_ai()
        
        # API generation setup
        if processing_mode in ['api_generation', 'full_api', 'hybrid']:
            self._setup_api_generation()
    
    def _setup_template_generation(self):
        """Setup template-based generation."""
        template_config = self.config.get('template', {})
        self.default_template = template_config.get('name', 'deployment_guide')
        
        # Initialize Jinja2 environment
        if JINJA2_AVAILABLE:
            self.jinja_env = Environment(
                loader=FileSystemLoader(self.template_dir),
                trim_blocks=True,
                lstrip_blocks=True
            )
            logger.info("Template generation initialized")
        else:
            self.jinja_env = None
            logger.warning("Jinja2 not available - template functionality limited")
    
    def _setup_local_ai(self):
        """Setup local AI generation with Ollama."""
        try:
            local_ai_config = self.config.get('local_ai', {})
            self.ollama_provider = OllamaProvider(local_ai_config)
            
            if self.ollama_provider.is_available():
                logger.info("Local AI (Ollama) generation initialized")
            else:
                logger.warning("Ollama server not available")
                if self.processing_mode == 'local_ai':
                    if not local_ai_config.get('fallback_to_template', True):
                        raise ConnectionError("Ollama required but not available")
                
        except Exception as e:
            logger.error(f"Failed to setup local AI: {e}")
            if self.processing_mode == 'local_ai':
                if not self.config.get('local_ai', {}).get('fallback_to_template', True):
                    raise
            logger.warning("Continuing without local AI")
    
    def _setup_api_generation(self):
        """Setup API-based guide generation."""
        try:
            api_config = self.config.get('api', {})
            provider_name = api_config.get('provider', 'openrouter')
            
            if provider_name == 'openrouter':
                self.api_provider = OpenRouterProvider(api_config)
                logger.info("API guide generation (OpenRouter) initialized")
            else:
                logger.warning(f"Unknown API provider: {provider_name}")
                
        except Exception as e:
            logger.error(f"Failed to setup API provider: {e}")
            if self.processing_mode in ['api_generation', 'full_api']:
                if not self.config.get('api', {}).get('fallback_to_local_ai', True):
                    raise
            logger.warning("Continuing without API provider")
    
    def generate_guide(self, transcription_result: Dict[str, Any], 
                      output_path: str, template_name: Optional[str] = None) -> bool:
        """
        Generate a markdown guide from transcription result using the configured method.
        
        Args:
            transcription_result: Enhanced transcription result with metadata
            output_path: Path to save the generated guide
            template_name: Template to use (optional, for template mode)
            
        Returns:
            bool: True if guide generated successfully
        """
        try:
            transcription_text = transcription_result['text']
            context = {
                'title': self._extract_title(transcription_text),
                'metadata': transcription_result.get('metadata', {})
            }
            
            # Try API generation first if configured
            if self.processing_mode in ['api_generation', 'full_api'] and self.api_provider:
                try:
                    logger.info("Attempting API guide generation")
                    guide_content = self.api_provider.generate_guide(transcription_text, context)
                    
                    if self._save_guide(guide_content, output_path):
                        logger.info(f"✅ API guide generated successfully: {output_path}")
                        return True
                        
                except Exception as e:
                    logger.error(f"API guide generation failed: {e}")
                    if not self.config.get('api', {}).get('fallback_to_local_ai', True):
                        return False
                    logger.info("Falling back to local AI generation")
            
            # Try local AI generation
            if self.processing_mode in ['local_ai', 'hybrid'] and self.ollama_provider:
                try:
                    if self.ollama_provider.is_available():
                        logger.info("Attempting local AI guide generation")
                        guide_content = self.ollama_provider.generate_guide(transcription_text, context)
                        
                        if self._save_guide(guide_content, output_path):
                            logger.info(f"✅ Local AI guide generated successfully: {output_path}")
                            return True
                            
                except Exception as e:
                    logger.error(f"Local AI guide generation failed: {e}")
                    if not self.config.get('local_ai', {}).get('fallback_to_template', True):
                        return False
                    logger.info("Falling back to template generation")
            
            # Use template-based generation as fallback
            return self._generate_template_guide(transcription_result, output_path, template_name)
                
        except Exception as e:
            logger.error(f"❌ Guide generation failed: {str(e)}")
            return False
    
    def _generate_template_guide(self, transcription_result: Dict[str, Any], 
                               output_path: str, template_name: Optional[str] = None) -> bool:
        """
        Generate guide using template-based approach.
        
        Args:
            transcription_result: Enhanced transcription result with metadata
            output_path: Path to save the generated guide
            template_name: Template to use (optional)
            
        Returns:
            bool: True if guide generated successfully
        """
        try:
            template_name = template_name or self.default_template
            
            logger.info(f"Generating guide using template: {template_name}")
            
            # Process transcription text
            processed_content = self._process_transcription_text(
                transcription_result['text']
            )
            
            # Extract structured information
            guide_data = self._extract_guide_structure(
                processed_content, transcription_result
            )
            
            # Generate guide content
            guide_content = self._render_template(template_name, guide_data)
            
            if guide_content:
                # Save the guide
                if self._save_guide(guide_content, output_path):
                    logger.info(f"✅ Template guide generated successfully: {output_path}")
                    return True
                else:
                    logger.error("❌ Failed to save guide")
                    return False
            else:
                logger.error("❌ Failed to render template")
                return False
                
        except Exception as e:
            logger.error(f"❌ Template guide generation failed: {str(e)}")
            return False
    
    def _process_transcription_text(self, text: str) -> str:
        """
        Clean and process transcription text for guide generation.
        
        Args:
            text: Raw transcription text
            
        Returns:
            str: Processed text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Fix common transcription issues
        text = self._fix_common_transcription_errors(text)
        
        # Improve punctuation
        text = self._improve_punctuation(text)
        
        return text
    
    def _fix_common_transcription_errors(self, text: str) -> str:
        """Fix common speech-to-text transcription errors."""
        
        # Common technical term corrections
        corrections = {
            r'\bip address\b': 'IP address',
            r'\bapi\b': 'API',
            r'\burl\b': 'URL',
            r'\bhttp\b': 'HTTP',
            r'\bhttps\b': 'HTTPS',
            r'\bssh\b': 'SSH',
            r'\bgit\b': 'Git',
            r'\bdocker\b': 'Docker',
            r'\bkubernetes\b': 'Kubernetes',
            r'\blinux\b': 'Linux',
            r'\bubuntu\b': 'Ubuntu',
            r'\bcentos\b': 'CentOS',
            r'\baws\b': 'AWS',
            r'\bgcp\b': 'GCP',
            r'\bazure\b': 'Azure',
        }
        
        for pattern, replacement in corrections.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _improve_punctuation(self, text: str) -> str:
        """Improve punctuation in transcribed text."""
        
        # Add periods after common sentence endings
        text = re.sub(r'(\w+)\s+(now|next|then|so|okay|alright)\s+', r'\1. \2 ', text, flags=re.IGNORECASE)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([,.!?;:])\s*', r'\1 ', text)
        
        # Ensure sentences start with capital letters
        sentences = text.split('. ')
        sentences = [s.strip().capitalize() for s in sentences if s.strip()]
        text = '. '.join(sentences)
        
        return text
    
    def _extract_guide_structure(self, text: str, transcription_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured information from processed text.
        
        Args:
            text: Processed transcription text
            transcription_result: Original transcription result with metadata
            
        Returns:
            dict: Structured guide data
        """
        guide_data = {
            'title': self._extract_title(text),
            'introduction': self._extract_introduction(text),
            'sections': self._extract_sections(text),
            'commands': self._extract_commands(text) if self.config.get('extract_commands', True) else [],
            'urls': self._extract_urls(text) if self.config.get('extract_urls', True) else [],
            'prerequisites': self._extract_prerequisites(text),
            'troubleshooting': self._extract_troubleshooting(text),
            'metadata': {
                'generated_date': datetime.now().isoformat(),
                'source_video': transcription_result.get('metadata', {}).get('source_audio', ''),
                'transcription_quality': transcription_result.get('quality', {}),
                'word_count': len(text.split()),
                'estimated_reading_time': self._estimate_reading_time(text)
            }
        }
        
        return guide_data
    
    def _extract_title(self, text: str) -> str:
        """Extract or generate a title from the text."""
        # Look for common title patterns
        title_patterns = [
            r'(?:how to|guide to|tutorial on|setting up|deploying|installing)\s+([^.!?]+)',
            r'(?:this video|today we|we will|we\'re going to)\s+(?:show|demonstrate|explain|cover)\s+([^.!?]+)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text[:500], re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                return title.title()
        
        # Fallback: use first meaningful sentence
        sentences = text.split('.')[:3]
        for sentence in sentences:
            if len(sentence.strip()) > 10:
                return sentence.strip().title()
        
        return "Generated Guide"
    
    def _extract_introduction(self, text: str) -> str:
        """Extract introduction from the beginning of the text."""
        # Take first few sentences as introduction
        sentences = text.split('.')[:3]
        intro = '. '.join(s.strip() for s in sentences if s.strip())
        return intro + '.' if intro and not intro.endswith('.') else intro
    
    def _extract_sections(self, text: str) -> List[Dict[str, str]]:
        """Extract logical sections from the text."""
        max_section_length = self.config.get('max_section_length', 500)
        min_section_length = self.config.get('min_section_length', 50)
        
        # Split text into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if not paragraphs:
            # Fallback: split by sentences
            sentences = [s.strip() + '.' for s in text.split('.') if s.strip()]
            paragraphs = self._group_sentences_into_paragraphs(sentences, max_section_length)
        
        sections = []
        current_section = ""
        section_count = 1
        
        for paragraph in paragraphs:
            if len(current_section) + len(paragraph) > max_section_length and current_section:
                # Save current section
                if len(current_section) >= min_section_length:
                    sections.append({
                        'title': f"Step {section_count}",
                        'content': current_section.strip()
                    })
                    section_count += 1
                current_section = paragraph
            else:
                current_section += "\n\n" + paragraph if current_section else paragraph
        
        # Add final section
        if current_section and len(current_section) >= min_section_length:
            sections.append({
                'title': f"Step {section_count}",
                'content': current_section.strip()
            })
        
        return sections
    
    def _group_sentences_into_paragraphs(self, sentences: List[str], max_length: int) -> List[str]:
        """Group sentences into logical paragraphs."""
        paragraphs = []
        current_paragraph = ""
        
        for sentence in sentences:
            if len(current_paragraph) + len(sentence) > max_length and current_paragraph:
                paragraphs.append(current_paragraph.strip())
                current_paragraph = sentence
            else:
                current_paragraph += " " + sentence if current_paragraph else sentence
        
        if current_paragraph:
            paragraphs.append(current_paragraph.strip())
        
        return paragraphs
    
    def _extract_commands(self, text: str) -> List[str]:
        """Extract shell commands from the text."""
        commands = []
        
        # Common command patterns
        command_patterns = [
            r'(?:run|execute|type|enter)\s+["`]([^"`]+)["`]',
            r'(?:command|cmd):\s*([^\n.]+)',
            r'\$\s*([^\n]+)',
            r'sudo\s+([^\n.]+)',
            r'(?:apt|yum|pip|npm|docker|git)\s+[^\n.]+',
        ]
        
        for pattern in command_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            commands.extend(matches)
        
        # Clean and deduplicate commands
        cleaned_commands = []
        for cmd in commands:
            cmd = cmd.strip()
            if cmd and len(cmd) > 3 and cmd not in cleaned_commands:
                cleaned_commands.append(cmd)
        
        return cleaned_commands[:10]  # Limit to 10 commands
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from the text."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
        urls = re.findall(url_pattern, text)
        return list(set(urls))  # Remove duplicates
    
    def _extract_prerequisites(self, text: str) -> List[str]:
        """Extract prerequisites from the text."""
        prereq_patterns = [
            r'(?:prerequisite|requirement|need|must have|should have)\s*:?\s*([^.!?]+)',
            r'(?:before|first|initially)\s+(?:you|we)\s+(?:need|must|should)\s+([^.!?]+)',
            r'(?:make sure|ensure)\s+(?:you|we)\s+(?:have|install|setup)\s+([^.!?]+)',
        ]
        
        prerequisites = []
        for pattern in prereq_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            prerequisites.extend(matches)
        
        # Clean prerequisites
        cleaned_prereqs = []
        for prereq in prerequisites:
            prereq = prereq.strip()
            if prereq and len(prereq) > 5:
                cleaned_prereqs.append(prereq)
        
        return cleaned_prereqs[:5]  # Limit to 5 prerequisites
    
    def _extract_troubleshooting(self, text: str) -> List[Dict[str, str]]:
        """Extract troubleshooting information from the text."""
        troubleshooting = []
        
        # Look for error/problem patterns
        error_patterns = [
            r'(?:error|problem|issue|fail|wrong)\s*:?\s*([^.!?]+)',
            r'(?:if|when)\s+(?:you see|you get|this happens)\s*:?\s*([^.!?]+)',
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 10:
                    troubleshooting.append({
                        'issue': match.strip(),
                        'solution': 'Refer to the documentation or check the logs for more details.'
                    })
        
        return troubleshooting[:3]  # Limit to 3 troubleshooting items
    
    def _estimate_reading_time(self, text: str) -> int:
        """Estimate reading time in minutes (assuming 200 words per minute)."""
        word_count = len(text.split())
        return max(1, round(word_count / 200))
    
    def _render_template(self, template_name: str, guide_data: Dict[str, Any]) -> Optional[str]:
        """
        Render guide using Jinja2 template.
        
        Args:
            template_name: Name of the template to use
            guide_data: Data to populate the template
            
        Returns:
            str: Rendered guide content or None if failed
        """
        if not self.jinja_env:
            # Fallback to basic template
            return self._render_basic_template(guide_data)
        
        try:
            template_file = f"{template_name}.md"
            template = self.jinja_env.get_template(template_file)
            return template.render(**guide_data)
            
        except Exception as e:
            logger.error(f"Template rendering failed: {str(e)}")
            logger.info("Falling back to basic template")
            return self._render_basic_template(guide_data)
    
    def _render_basic_template(self, guide_data: Dict[str, Any]) -> str:
        """Render a basic template without Jinja2."""
        
        content = f"""# {guide_data['title']}

## Introduction

{guide_data['introduction']}

"""
        
        # Add prerequisites if any
        if guide_data.get('prerequisites'):
            content += "## Prerequisites\n\n"
            for prereq in guide_data['prerequisites']:
                content += f"- {prereq}\n"
            content += "\n"
        
        # Add sections
        if guide_data.get('sections'):
            content += "## Steps\n\n"
            for section in guide_data['sections']:
                content += f"### {section['title']}\n\n{section['content']}\n\n"
        
        # Add commands if any
        if guide_data.get('commands'):
            content += "## Commands Reference\n\n"
            for cmd in guide_data['commands']:
                content += f"```bash\n{cmd}\n```\n\n"
        
        # Add troubleshooting if any
        if guide_data.get('troubleshooting'):
            content += "## Troubleshooting\n\n"
            for item in guide_data['troubleshooting']:
                content += f"**Issue:** {item['issue']}\n\n"
                content += f"**Solution:** {item['solution']}\n\n"
        
        # Add metadata
        metadata = guide_data.get('metadata', {})
        content += f"""---

*Generated on {metadata.get('generated_date', 'unknown date')}*  
*Estimated reading time: {metadata.get('estimated_reading_time', 'unknown')} minutes*
"""
        
        return content
    
    def _save_guide(self, content: str, output_path: str) -> bool:
        """
        Save guide content to file.
        
        Args:
            content: Guide content to save
            output_path: Path to save the guide
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the guide
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.debug(f"Guide saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save guide: {str(e)}")
            return False
