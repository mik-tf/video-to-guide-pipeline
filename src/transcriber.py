#!/usr/bin/env python3
"""
Transcription Module

Handles audio-to-text transcription using local Whisper or API providers with fallback support.
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("OpenAI Whisper not available. Install with: pip install openai-whisper")

from providers.openrouter import OpenRouterProvider
from providers.huggingface import HuggingFaceProvider

logger = logging.getLogger(__name__)


class Transcriber:
    """
    Handles audio transcription using local Whisper or API providers.
    
    Provides configurable transcription with quality assurance and metadata extraction.
    """
    
    def __init__(self, config: Dict[str, Any], processing_mode: str = 'basic'):
        """
        Initialize the Transcriber.
        
        Args:
            config: Configuration dictionary with transcription settings
            processing_mode: Processing mode (basic, local_ai, api_transcription, full_api, hybrid)
        """
        self.config = config.get('transcription', {})
        self.processing_mode = processing_mode
        self.model = None
        self.api_provider = None
        
        # Initialize based on processing mode
        # Local transcription setup (for basic, local_ai, hybrid, and as fallback for API modes)
        if processing_mode in ['basic', 'local_ai', 'hybrid', 'api_generation', 'full_api']:
            self._setup_local_transcription()
        
        # API transcription setup
        if processing_mode in ['api_transcription', 'full_api', 'hybrid']:
            self._setup_api_transcription()
    
    def _setup_local_transcription(self) -> None:
        """Setup local Whisper transcription."""
        if not WHISPER_AVAILABLE:
            if self.processing_mode == 'basic':
                raise ImportError("OpenAI Whisper is required but not installed")
            logger.warning("OpenAI Whisper not available, skipping local setup")
            return
        
        local_config = self.config.get('local', self.config)  # Fallback to root config for compatibility
        self.model_name = local_config.get('model', 'base')
        self.device = local_config.get('device', 'cpu')
        self.language = local_config.get('language', 'en')
        
        self._load_model()
    
    def _setup_api_transcription(self) -> None:
        """Setup API transcription provider."""
        try:
            api_config = self.config.get('api', {})
            provider_name = api_config.get('provider', 'openrouter')
            
            if provider_name == 'openrouter':
                self.api_provider = OpenRouterProvider(api_config)
                logger.info("OpenRouter transcription provider initialized")
            elif provider_name == 'huggingface':
                self.api_provider = HuggingFaceProvider(api_config)
                logger.info("HuggingFace transcription provider initialized")
            else:
                logger.warning(f"Unknown API provider: {provider_name}")
                
        except Exception as e:
            logger.error(f"Failed to setup API provider: {e}")
            if self.processing_mode in ['api_transcription', 'full_api']:
                if not self.config.get('api', {}).get('fallback_to_local', False):
                    raise
            logger.warning("Continuing without API provider")
    
    def _load_model(self) -> None:
        """Load the Whisper model."""
        try:
            logger.info(f"Loading Whisper model: {self.model_name}")
            start_time = time.time()
            
            self.model = whisper.load_model(
                self.model_name,
                device=self.device
            )
            
            load_time = time.time() - start_time
            logger.info(f"✅ Model loaded successfully in {load_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {str(e)}")
            if self.processing_mode == 'basic':
                raise
            logger.warning("Continuing without local model")
    
    def transcribe_audio(self, audio_path: str, output_path: str) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio file to text using the configured method.
        
        Args:
            audio_path: Path to the audio file
            output_path: Path to save the transcription
            
        Returns:
            dict: Transcription result with metadata or None if failed
        """
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return None
        
        # Try API transcription first if configured
        if self.processing_mode in ['api_transcription', 'full_api'] and self.api_provider:
            try:
                logger.info(f"Attempting API transcription: {os.path.basename(audio_path)}")
                start_time = time.time()
                
                api_result = self.api_provider.transcribe_audio(audio_path)
                processing_time = time.time() - start_time
                
                # Enhance API result with metadata
                enhanced_result = self._enhance_api_result(api_result, audio_path, processing_time)
                
                # Save transcription
                if self._save_transcription(enhanced_result, output_path):
                    logger.info(f"✅ API transcription completed in {processing_time:.2f} seconds")
                    logger.info(f"Text length: {len(enhanced_result['text'])} characters")
                    return enhanced_result
                    
            except Exception as e:
                logger.error(f"API transcription failed: {e}")
                if not self.config.get('api', {}).get('fallback_to_local', True):
                    return None
                logger.info("Falling back to local transcription")
        
        # Use local Whisper transcription
        return self._transcribe_local(audio_path, output_path)
    
    def _transcribe_local(self, audio_path: str, output_path: str) -> Optional[Dict[str, Any]]:
        """
        Transcribe using local Whisper model.
        
        Args:
            audio_path: Path to the audio file
            output_path: Path to save the transcription
            
        Returns:
            dict: Transcription result with metadata or None if failed
        """
        if not self.model:
            logger.error("Whisper model not loaded")
            return None
        
        try:
            logger.info(f"Transcribing audio locally: {os.path.basename(audio_path)}")
            start_time = time.time()
            
            # Prepare transcription options
            options = self._build_transcription_options()
            
            # Perform transcription
            result = self.model.transcribe(audio_path, **options)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Enhance result with metadata
            enhanced_result = self._enhance_transcription_result(
                result, audio_path, processing_time
            )
            
            # Save transcription
            if self._save_transcription(enhanced_result, output_path):
                logger.info(f"✅ Local transcription completed in {processing_time:.2f} seconds")
                logger.info(f"Text length: {len(enhanced_result['text'])} characters")
                return enhanced_result
            else:
                logger.error("❌ Failed to save transcription")
                return None
                
        except Exception as e:
            logger.error(f"❌ Local transcription failed: {str(e)}")
            return None
    
    def _build_transcription_options(self) -> Dict[str, Any]:
        """
        Build transcription options from local configuration.
        
        Returns:
            dict: Whisper transcription options
        """
        # Use local config or fallback to root config for compatibility
        local_config = self.config.get('local', self.config)
        options = {}
        
        # Language settings
        if self.language and self.language != 'auto':
            options['language'] = self.language
        
        # Performance settings
        options['fp16'] = local_config.get('fp16', False)
        options['temperature'] = local_config.get('temperature', 0.0)
        options['best_of'] = local_config.get('best_of', 5)
        options['beam_size'] = local_config.get('beam_size', 5)
        options['patience'] = local_config.get('patience', 1.0)
        options['length_penalty'] = local_config.get('length_penalty', 1.0)
        
        # Token suppression
        suppress_tokens = local_config.get('suppress_tokens', [-1])
        if suppress_tokens:
            options['suppress_tokens'] = suppress_tokens
        
        # Context and prompting
        initial_prompt = local_config.get('initial_prompt', '')
        if initial_prompt:
            options['initial_prompt'] = initial_prompt
        
        options['condition_on_previous_text'] = local_config.get(
            'condition_on_previous_text', True
        )
        
        # Timestamp settings
        options['word_timestamps'] = local_config.get('word_timestamps', False)
        
        # Punctuation settings
        prepend_punct = local_config.get('prepend_punctuations', '')
        if prepend_punct:
            options['prepend_punctuations'] = prepend_punct
        
        append_punct = local_config.get('append_punctuations', '')
        if append_punct:
            options['append_punctuations'] = append_punct
        
        return options
    
    def _enhance_api_result(self, api_result: Dict[str, Any], audio_path: str, processing_time: float) -> Dict[str, Any]:
        """
        Enhance API transcription result with additional metadata.
        
        Args:
            api_result: Raw API transcription result
            audio_path: Path to the source audio file
            processing_time: Time taken for transcription
            
        Returns:
            dict: Enhanced result with metadata
        """
        enhanced_result = {
            'text': api_result.get('text', ''),
            'language': api_result.get('language', 'unknown'),
            'segments': api_result.get('segments', []),
            'metadata': {
                'source_audio': audio_path,
                'processing_time': processing_time,
                'model_used': api_result.get('model', 'unknown'),
                'provider': api_result.get('provider', 'unknown'),
                'method': 'api',
                'character_count': len(api_result.get('text', '')),
                'word_count': len(api_result.get('text', '').split()),
                'timestamp': time.time()
            }
        }
        
        # Add quality metrics
        enhanced_result['quality'] = self._calculate_quality_metrics(enhanced_result)
        
        return enhanced_result
    
    def _enhance_transcription_result(self, result: Dict[str, Any], 
                                   audio_path: str, processing_time: float) -> Dict[str, Any]:
        """
        Enhance transcription result with additional metadata.
        
        Args:
            result: Raw Whisper transcription result
            audio_path: Path to the source audio file
            processing_time: Time taken for transcription
            
        Returns:
            dict: Enhanced result with metadata
        """
        enhanced = {
            'text': result['text'].strip(),
            'language': result.get('language', 'unknown'),
            'segments': result.get('segments', []),
            'metadata': {
                'source_audio': audio_path,
                'audio_size': os.path.getsize(audio_path),
                'model_used': self.model_name,
                'device_used': self.device,
                'processing_time': processing_time,
                'timestamp': time.time(),
                'character_count': len(result['text'].strip()),
                'word_count': len(result['text'].strip().split()),
                'estimated_duration': self._estimate_audio_duration(result.get('segments', []))
            }
        }
        
        # Add quality metrics
        enhanced['quality'] = self._calculate_quality_metrics(enhanced)
        
        return enhanced
    
    def _estimate_audio_duration(self, segments: List[Dict]) -> float:
        """Estimate audio duration from segments."""
        if not segments:
            return 0.0
        
        try:
            return max(segment.get('end', 0) for segment in segments)
        except (ValueError, TypeError):
            return 0.0
    
    def _calculate_quality_metrics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate quality metrics for the transcription.
        
        Args:
            result: Enhanced transcription result
            
        Returns:
            dict: Quality metrics
        """
        text = result['text']
        segments = result.get('segments', [])
        
        metrics = {
            'confidence_score': 0.0,
            'avg_segment_confidence': 0.0,
            'low_confidence_segments': 0,
            'text_completeness': 0.0,
            'estimated_accuracy': 'unknown'
        }
        
        if segments:
            # Calculate average confidence from segments
            confidences = []
            low_confidence_count = 0
            
            for segment in segments:
                if 'avg_logprob' in segment:
                    # Convert log probability to confidence score (0-1)
                    confidence = min(1.0, max(0.0, (segment['avg_logprob'] + 1.0)))
                    confidences.append(confidence)
                    
                    if confidence < 0.7:  # Threshold for low confidence
                        low_confidence_count += 1
            
            if confidences:
                metrics['avg_segment_confidence'] = sum(confidences) / len(confidences)
                metrics['low_confidence_segments'] = low_confidence_count
        
        # Text completeness heuristics
        word_count = result['metadata']['word_count']
        char_count = result['metadata']['character_count']
        
        if word_count > 0:
            avg_word_length = char_count / word_count
            metrics['text_completeness'] = min(1.0, avg_word_length / 5.0)  # Assume 5 chars/word average
        
        # Overall confidence score
        metrics['confidence_score'] = (
            metrics['avg_segment_confidence'] * 0.7 +
            metrics['text_completeness'] * 0.3
        )
        
        # Estimated accuracy category
        if metrics['confidence_score'] >= 0.9:
            metrics['estimated_accuracy'] = 'excellent'
        elif metrics['confidence_score'] >= 0.8:
            metrics['estimated_accuracy'] = 'good'
        elif metrics['confidence_score'] >= 0.7:
            metrics['estimated_accuracy'] = 'fair'
        else:
            metrics['estimated_accuracy'] = 'poor'
        
        return metrics
    
    def _save_transcription(self, result: Dict[str, Any], output_path: str) -> bool:
        """
        Save transcription result to file.
        
        Args:
            result: Enhanced transcription result
            output_path: Path to save the transcription
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save plain text
            text_path = output_path
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(result['text'])
            
            # Save detailed JSON with metadata
            json_path = output_path.replace('.txt', '_detailed.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Transcription saved to: {text_path}")
            logger.debug(f"Detailed data saved to: {json_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save transcription: {str(e)}")
            return False
    
    def validate_transcription(self, result: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate transcription quality and completeness.
        
        Args:
            result: Transcription result to validate
            
        Returns:
            tuple: (is_valid, list_of_issues)
        """
        issues = []
        
        # Check minimum length
        min_length = self.config.get('min_length', 100)
        if len(result['text']) < min_length:
            issues.append(f"Transcription too short: {len(result['text'])} chars (minimum: {min_length})")
        
        # Check confidence score
        min_confidence = self.config.get('min_confidence', 0.7)
        confidence = result.get('quality', {}).get('confidence_score', 0.0)
        if confidence < min_confidence:
            issues.append(f"Low confidence score: {confidence:.2f} (minimum: {min_confidence})")
        
        # Check for empty or mostly empty content
        if not result['text'].strip():
            issues.append("Transcription is empty")
        elif len(result['text'].strip().split()) < 10:
            issues.append("Transcription contains very few words")
        
        # Check language detection if specified
        if self.language and self.language != 'auto':
            detected_lang = result.get('language', 'unknown')
            if detected_lang != self.language and detected_lang != 'unknown':
                issues.append(f"Language mismatch: expected {self.language}, detected {detected_lang}")
        
        return len(issues) == 0, issues
    
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported Whisper models.
        
        Returns:
            list: Available model names
        """
        if WHISPER_AVAILABLE:
            return list(whisper.available_models())
        return []
    
    def print_transcription_summary(self, result: Dict[str, Any]) -> None:
        """
        Print a formatted summary of the transcription result.
        
        Args:
            result: Transcription result with metadata
        """
        metadata = result.get('metadata', {})
        quality = result.get('quality', {})
        
        print(f"\n📝 Transcription Summary")
        print("=" * 50)
        print(f"Source: {os.path.basename(metadata.get('source_audio', 'unknown'))}")
        print(f"Model: {metadata.get('model_used', 'unknown')}")
        print(f"Language: {result.get('language', 'unknown')}")
        print(f"Processing Time: {metadata.get('processing_time', 0):.2f} seconds")
        print(f"Text Length: {metadata.get('character_count', 0)} characters")
        print(f"Word Count: {metadata.get('word_count', 0)} words")
        print(f"Confidence Score: {quality.get('confidence_score', 0):.2f}")
        print(f"Estimated Accuracy: {quality.get('estimated_accuracy', 'unknown')}")
        
        if quality.get('low_confidence_segments', 0) > 0:
            print(f"⚠️  Low confidence segments: {quality['low_confidence_segments']}")
        
        print("=" * 50)
