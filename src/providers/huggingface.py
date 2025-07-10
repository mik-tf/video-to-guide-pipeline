"""
Hugging Face Inference API provider for audio transcription.
"""

import os
import logging
import requests
import tempfile
import subprocess
from typing import Dict, Any, List
from .base import TranscriptionProvider

logger = logging.getLogger(__name__)


class HuggingFaceProvider(TranscriptionProvider):
    """Hugging Face Inference API provider for audio transcription using Whisper models."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = os.getenv('HUGGINGFACE_API_KEY')
        if not self.api_key:
            raise ValueError("HUGGINGFACE_API_KEY environment variable is required")
        
        self.model = config.get('model', 'openai/whisper-large-v3')
        self.base_url = "https://api-inference.huggingface.co/models"
        self.timeout = config.get('timeout', 300)
        
        # Audio chunking parameters for large files
        self.max_file_size_mb = config.get('max_file_size_mb', 25)  # HF limit is ~25MB
        self.target_chunk_size_mb = config.get('target_chunk_size_mb', 20)
        self.chunk_duration_seconds = config.get('chunk_duration_seconds', 300)  # 5 minutes
        self.chunk_overlap_seconds = config.get('chunk_overlap_seconds', 10)
        
        logger.info(f"HuggingFace transcription provider initialized with model: {self.model}")
    
    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio file using Hugging Face Inference API."""
        try:
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            logger.info(f"Audio file size: {file_size_mb:.2f}MB (limit: {self.max_file_size_mb}MB)")
            
            if file_size_mb <= self.max_file_size_mb:
                return self._transcribe_single_file(audio_path)
            else:
                logger.info(f"File too large ({file_size_mb:.2f}MB), using chunking approach")
                return self._transcribe_with_chunking(audio_path)
                
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                'text': f"[Transcription failed: {str(e)}]",
                'language': 'en',
                'provider': 'huggingface',
                'model': self.model,
                'failed': True
            }
    
    def _transcribe_single_file(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe a single audio file via Hugging Face API."""
        with open(audio_path, 'rb') as audio_file:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'audio/mpeg'  # Required for HF Inference API
            }
            
            # Use the correct API endpoint format
            response = requests.post(
                f"{self.base_url}/{self.model}",
                headers=headers,
                data=audio_file.read(),
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Handle different response formats
            if isinstance(result, dict) and 'text' in result:
                text = result['text']
            elif isinstance(result, list) and len(result) > 0:
                # Some models return array format
                if isinstance(result[0], dict) and 'text' in result[0]:
                    text = result[0]['text']
                else:
                    text = str(result[0])
            else:
                text = str(result)
            
            return {
                'text': text.strip(),
                'language': 'en',  # Default language
                'confidence': 0.8,  # Default confidence
                'provider': 'huggingface',
                'model': self.model
            }
    
    def _transcribe_with_chunking(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe large audio file by splitting into chunks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info("🔪 Splitting audio into chunks for transcription...")
            
            # Split audio into compressed chunks
            chunk_paths = self._split_audio_file(audio_path, temp_dir)
            
            if not chunk_paths:
                logger.error("No audio chunks created")
                return {
                    'text': "[No audio chunks created]",
                    'language': 'en',
                    'provider': 'huggingface',
                    'model': self.model,
                    'failed': True
                }
            
            # Transcribe each chunk
            transcriptions = []
            for i, chunk_path in enumerate(chunk_paths):
                logger.info(f"Transcribing chunk {i+1}/{len(chunk_paths)}")
                try:
                    result = self._transcribe_single_file(chunk_path)
                    transcriptions.append(result)
                except Exception as e:
                    logger.warning(f"❌ Failed to transcribe chunk {i+1}: {e}")
                    transcriptions.append({
                        'text': '',
                        'failed': True,
                        'error': str(e)
                    })
            
            # Merge transcriptions
            combined_text = self._merge_overlapping_transcriptions(transcriptions)
            successful_chunks = len([t for t in transcriptions if not t.get('failed', False)])
            
            logger.info(f"Combined transcription: {len(combined_text)} characters from {successful_chunks}/{len(transcriptions)} chunks")
            
            return {
                'text': combined_text,
                'language': 'en',
                'provider': 'huggingface',
                'model': self.model,
                'chunks_total': len(transcriptions),
                'chunks_successful': successful_chunks
            }
    
    def _split_audio_file(self, audio_path: str, output_dir: str) -> List[str]:
        """Split audio file into compressed chunks with overlap."""
        # Get total duration
        cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        total_duration = float(result.stdout.strip())
        
        # Calculate dynamic chunk duration based on file size
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        estimated_mb_per_second = file_size_mb / total_duration
        max_chunk_duration = min(
            self.chunk_duration_seconds,
            int(self.target_chunk_size_mb / estimated_mb_per_second * 0.6)  # 60% safety margin
        )
        
        chunk_step = max_chunk_duration - self.chunk_overlap_seconds
        chunk_count = int(total_duration / chunk_step) + 1
        
        logger.info(f"📊 Audio duration: {total_duration:.1f}s, chunk duration: {max_chunk_duration}s, overlap: {self.chunk_overlap_seconds}s")
        logger.info(f"🔪 Creating {chunk_count} chunks with {chunk_step}s step")
        
        chunk_paths = []
        for i in range(chunk_count):
            start_time = i * chunk_step
            actual_duration = min(max_chunk_duration, total_duration - start_time)
            
            if actual_duration <= 0:
                break
            
            chunk_filename = f"chunk_{i+1:03d}.mp3"
            chunk_path = os.path.join(output_dir, chunk_filename)
            
            # Create highly compressed MP3 chunk
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-ss', str(start_time),
                '-t', str(actual_duration),
                '-acodec', 'mp3',
                '-ab', '32k',        # 32kbps bitrate (higher than OpenRouter for HF)
                '-ar', '16000',      # 16kHz sample rate (Whisper's native rate)
                '-ac', '1',          # Mono channel
                '-q:a', '7',         # Good quality/compression balance
                '-y',                # Overwrite output files
                chunk_path
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Verify chunk was created and check size
                if os.path.exists(chunk_path):
                    chunk_size_mb = os.path.getsize(chunk_path) / (1024 * 1024)
                    if chunk_size_mb > self.target_chunk_size_mb * 1.2:  # 20% tolerance
                        logger.warning(f"⚠️  Chunk {i+1} is large: {chunk_size_mb:.2f}MB (target: {self.target_chunk_size_mb}MB)")
                    elif chunk_size_mb > 0.1:  # At least 100KB
                        logger.info(f"✅ Chunk {i+1}: {chunk_filename} ({chunk_size_mb:.2f}MB, {start_time:.1f}s-{start_time + actual_duration:.1f}s)")
                    else:
                        logger.warning(f"⚠️  Chunk {i+1} is very small: {chunk_size_mb:.2f}MB")
                    chunk_paths.append(chunk_path)
                else:
                    logger.error(f"❌ Chunk file not created: {chunk_path}")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to create chunk {i+1}: {e}")
                if hasattr(e, 'stderr') and e.stderr:
                    logger.error(f"FFmpeg stderr: {e.stderr}")
                continue
        
        logger.info(f"Successfully created {len(chunk_paths)} audio chunks")
        return chunk_paths
    
    def _merge_overlapping_transcriptions(self, transcriptions: List[Dict[str, Any]]) -> str:
        """Merge overlapping transcriptions intelligently."""
        if not transcriptions:
            return ""
        
        # Filter out failed transcriptions
        valid_transcriptions = [t for t in transcriptions if not t.get('failed', False) and t.get('text', '').strip()]
        
        if not valid_transcriptions:
            return "[All chunks failed transcription]"
        
        if len(valid_transcriptions) == 1:
            return valid_transcriptions[0]['text']
        
        # Start with first transcription
        merged_text = valid_transcriptions[0]['text']
        
        # Merge subsequent transcriptions
        for i in range(1, len(valid_transcriptions)):
            current_text = valid_transcriptions[i]['text']
            
            # Try to find overlap between end of merged_text and start of current_text
            merged_words = merged_text.split()
            current_words = current_text.split()
            
            # Look for longest common sequence at the boundary
            max_overlap = min(50, len(merged_words), len(current_words))  # Check up to 50 words
            best_overlap = 0
            
            for overlap_len in range(max_overlap, 0, -1):
                if merged_words[-overlap_len:] == current_words[:overlap_len]:
                    best_overlap = overlap_len
                    break
            
            if best_overlap > 0:
                # Remove overlapping words from current text
                merged_text += " " + " ".join(current_words[best_overlap:])
                logger.debug(f"Found {best_overlap} word overlap between chunks {i} and {i+1}")
            else:
                # No overlap found, just concatenate with space
                merged_text += " " + current_text
        
        return merged_text.strip()
