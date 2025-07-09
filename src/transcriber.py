#!/usr/bin/env python3
"""
Transcription Module

Handles audio-to-text transcription using OpenAI Whisper with advanced configuration options.
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

logger = logging.getLogger(__name__)


class Transcriber:
    """
    Handles audio transcription using OpenAI Whisper.
    
    Provides configurable transcription with quality assurance and metadata extraction.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Transcriber.
        
        Args:
            config: Configuration dictionary with transcription settings
        """
        if not WHISPER_AVAILABLE:
            raise ImportError("OpenAI Whisper is required but not installed")
            
        self.config = config.get('transcription', {})
        self.model_name = self.config.get('model', 'base')
        self.device = self.config.get('device', 'cpu')
        self.language = self.config.get('language', 'en')
        
        # Load model
        self.model = None
        self._load_model()
    
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
            raise
    
    def transcribe_audio(self, audio_path: str, output_path: str) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to the audio file
            output_path: Path to save the transcription
            
        Returns:
            dict: Transcription result with metadata or None if failed
        """
        if not self.model:
            logger.error("Whisper model not loaded")
            return None
        
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return None
        
        try:
            logger.info(f"Transcribing audio: {os.path.basename(audio_path)}")
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
                logger.info(f"✅ Transcription completed in {processing_time:.2f} seconds")
                logger.info(f"Text length: {len(enhanced_result['text'])} characters")
                return enhanced_result
            else:
                logger.error("❌ Failed to save transcription")
                return None
                
        except Exception as e:
            logger.error(f"❌ Transcription failed: {str(e)}")
            return None
    
    def _build_transcription_options(self) -> Dict[str, Any]:
        """
        Build transcription options from configuration.
        
        Returns:
            dict: Whisper transcription options
        """
        options = {}
        
        # Language setting
        if self.language and self.language != 'auto':
            options['language'] = self.language
        
        # Advanced options
        for key in ['temperature', 'best_of', 'beam_size', 'patience', 
                   'length_penalty', 'suppress_tokens', 'initial_prompt',
                   'condition_on_previous_text', 'word_timestamps',
                   'prepend_punctuations', 'append_punctuations']:
            if key in self.config:
                options[key] = self.config[key]
        
        # FP16 precision (GPU only)
        if self.device != 'cpu' and self.config.get('fp16', False):
            options['fp16'] = True
        
        return options
    
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
