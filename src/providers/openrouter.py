"""
OpenRouter API provider for transcription and guide generation.
"""

import requests
import json
import time
import os
import tempfile
from typing import Dict, Any, Optional, List
import logging

from providers.base import TranscriptionProvider, GuideGenerationProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(TranscriptionProvider, GuideGenerationProvider):
    """Hybrid provider: OpenAI for audio transcription + OpenRouter for guide generation.
    
    Note: OpenRouter doesn't support audio transcription endpoints, so we use
    OpenAI's Whisper API for transcription and OpenRouter for text generation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get('model', 'openai/whisper-large-v3')
        self.temperature = config.get('temperature', 0.1)
        self.max_tokens = config.get('max_tokens', 4000)
        
        # Audio chunking configuration - based on Whisper API research
        self.max_file_size_mb = config.get('max_file_size_mb', 5)  # Very conservative (API limit 25MB, issues >10MB)
        self.target_chunk_size_mb = config.get('target_chunk_size_mb', 2)  # Target 2MB per chunk for reliability
        self.chunk_duration_seconds = config.get('chunk_duration_seconds', 120)  # 2 minutes max per chunk
        self.chunk_overlap_seconds = config.get('chunk_overlap_seconds', 10)  # 10 seconds overlap
    
    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio using OpenRouter's Whisper models with chunking for large files.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary containing transcription result
        """
        try:
            # Check file size
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            logger.info(f"Audio file size: {file_size_mb:.1f} MB")
            
            if file_size_mb <= self.max_file_size_mb:
                # File is small enough, transcribe directly
                logger.info("File size OK, transcribing directly")
                return self._transcribe_single_file(audio_path)
            else:
                # File is too large, use chunking
                logger.info(f"File too large ({file_size_mb:.1f} MB > {self.max_file_size_mb} MB), using chunking")
                return self._transcribe_with_chunking(audio_path)
                
        except Exception as e:
            logger.error(f"OpenRouter transcription failed: {e}")
            raise
    
    def _transcribe_single_file(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe a single audio file via API."""
        with open(audio_path, 'rb') as audio_file:
            files = {'file': audio_file}
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'HTTP-Referer': 'https://github.com/video-to-guide-pipeline',
                'X-Title': 'Video-to-Guide Pipeline'
            }
            
            data = {
                'model': self.model,
                'response_format': 'json'
            }
            
            audio_url = "https://api.openai.com/v1/audio/transcriptions"
            response = requests.post(
                audio_url,
                headers=headers,
                files=files,
                data=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                'text': result.get('text', ''),
                'language': result.get('language', 'en'),
                'duration': result.get('duration'),
                'provider': 'openrouter',
                'model': self.model
            }
    
    def _transcribe_with_chunking(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe large audio file by splitting into chunks."""
        import subprocess
        
        # Create temporary directory for chunks
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Creating audio chunks in: {temp_dir}")
            
            # Split audio into chunks using ffmpeg
            chunk_paths = self._split_audio_file(audio_path, temp_dir)
            logger.info(f"Created {len(chunk_paths)} audio chunks")
            
            # Transcribe each chunk
            transcriptions = []
            successful_chunks = 0
            total_duration = 0
            
            for i, chunk_path in enumerate(chunk_paths):
                logger.info(f"Transcribing chunk {i+1}/{len(chunk_paths)}")
                try:
                    chunk_result = self._transcribe_single_file(chunk_path)
                    transcriptions.append({
                        'text': chunk_result['text'],
                        'index': i,
                        'duration': chunk_result.get('duration', 0)
                    })
                    successful_chunks += 1
                    if chunk_result.get('duration'):
                        total_duration += chunk_result['duration']
                    logger.info(f"✅ Chunk {i+1} transcribed successfully ({len(chunk_result['text'])} chars)")
                except Exception as e:
                    logger.warning(f"❌ Failed to transcribe chunk {i+1}: {e}")
                    transcriptions.append({
                        'text': '',
                        'index': i,
                        'failed': True
                    })
            
            # Combine transcriptions with overlap handling
            combined_text = self._merge_overlapping_transcriptions(transcriptions)
            logger.info(f"Combined transcription: {len(combined_text)} characters from {successful_chunks}/{len(chunk_paths)} chunks")
            
            return {
                'text': combined_text,
                'language': 'en',  # Assume English for chunked transcription
                'duration': total_duration if total_duration > 0 else None,
                'provider': 'openrouter',
                'model': self.model,
                'chunks_processed': len(chunk_paths)
            }
    
    def _split_audio_file(self, audio_path: str, output_dir: str) -> List[str]:
        """Split audio file into chunks using ffmpeg with dynamic sizing."""
        import subprocess
        
        chunk_paths = []
        
        # Get audio duration and file size
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            total_duration = float(result.stdout.strip())
            logger.info(f"Total audio duration: {total_duration:.1f} seconds")
        except Exception as e:
            logger.warning(f"Could not get audio duration: {e}")
            total_duration = 3600  # Assume 1 hour max
        
        # Calculate optimal chunk duration based on file size
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        estimated_mb_per_second = file_size_mb / total_duration
        
        # Target chunk duration to stay under size limit
        max_chunk_duration = min(
            self.chunk_duration_seconds,
            int(self.target_chunk_size_mb / estimated_mb_per_second * 0.6)  # 60% safety margin
        )
        max_chunk_duration = max(30, max_chunk_duration)  # At least 30 seconds
        
        logger.info(f"Using chunk duration: {max_chunk_duration} seconds with {self.chunk_overlap_seconds}s overlap")
        logger.info(f"Estimated: {estimated_mb_per_second:.2f} MB/sec")
        
        # Create overlapping chunks
        chunk_step = max_chunk_duration - self.chunk_overlap_seconds  # Step between chunk starts
        chunk_count = int(total_duration / chunk_step) + 1
        
        for i in range(chunk_count):
            start_time = i * chunk_step
            # Don't go beyond the end of the audio
            if start_time >= total_duration:
                break
                
            # Adjust duration for last chunk
            actual_duration = min(max_chunk_duration, total_duration - start_time)
            if actual_duration < 15:  # Skip very short chunks
                break
                
            chunk_filename = f"chunk_{i:03d}.mp3"  # Use MP3 for better compression
            chunk_path = os.path.join(output_dir, chunk_filename)
            
            # Use ffmpeg with optimal settings for Whisper transcription
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-ss', str(start_time),
                '-t', str(actual_duration),
                '-acodec', 'mp3',     # MP3 format (optimal for Whisper)
                '-ab', '16k',         # 16 kbps bitrate (research shows no quality loss)
                '-ar', '12000',       # 12kHz sample rate (Whisper downsamples to 16kHz anyway)
                '-ac', '1',           # Mono channel
                '-q:a', '9',          # Lowest quality setting for maximum compression
                '-compression_level', '9',  # Maximum MP3 compression
                '-y',                 # Overwrite output files
                chunk_path
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Verify chunk was created and check size
                if os.path.exists(chunk_path):
                    chunk_size_mb = os.path.getsize(chunk_path) / (1024 * 1024)
                    if chunk_size_mb > self.target_chunk_size_mb * 1.5:  # 50% tolerance
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
                # Try to continue with remaining chunks
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
        
        # Simple merge strategy: concatenate with overlap detection
        merged_text = valid_transcriptions[0]['text']
        
        for i in range(1, len(valid_transcriptions)):
            current_text = valid_transcriptions[i]['text']
            if not current_text.strip():
                continue
                
            # Try to find overlap between end of merged_text and start of current_text
            overlap_found = False
            
            # Look for common phrases at the boundary (last 50 chars of merged, first 50 of current)
            if len(merged_text) > 20 and len(current_text) > 20:
                merged_end = merged_text[-50:].strip().split()
                current_start = current_text[:50].strip().split()
                
                # Find longest common subsequence at boundary
                for overlap_len in range(min(len(merged_end), len(current_start)), 0, -1):
                    if merged_end[-overlap_len:] == current_start[:overlap_len]:
                        # Found overlap, merge without duplication
                        overlap_words = ' '.join(current_start[:overlap_len])
                        remaining_current = ' '.join(current_start[overlap_len:])
                        if remaining_current.strip():
                            merged_text += ' ' + remaining_current
                        overlap_found = True
                        logger.debug(f"Found {overlap_len}-word overlap: '{overlap_words}'")
                        break
            
            # If no overlap found, just concatenate with space
            if not overlap_found:
                merged_text += ' ' + current_text
        
        return merged_text.strip()
    
    def generate_guide(self, transcription: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate guide using OpenRouter's chat models.
        
        Args:
            transcription: Raw transcription text
            context: Optional context information
            
        Returns:
            Generated guide in markdown format
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/video-to-guide-pipeline',
                'X-Title': 'Video-to-Guide Pipeline'
            }
            
            messages = [
                {
                    "role": "system",
                    "content": self._build_system_prompt()
                },
                {
                    "role": "user", 
                    "content": self._build_user_prompt(transcription, context)
                }
            ]
            
            data = {
                'model': self.model,
                'messages': messages,
                'temperature': self.temperature,
                'max_tokens': self.max_tokens,
                'stream': False
            }
            
            for attempt in range(self.max_retries):
                try:
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=self.timeout
                    )
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        return content.strip()
                    else:
                        raise ValueError("No content generated")
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"OpenRouter API attempt {attempt + 1} failed: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise
            
        except Exception as e:
            logger.error(f"OpenRouter guide generation failed: {e}")
            raise
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for OpenRouter models."""
        base_prompt = super()._build_system_prompt()
        
        # Add OpenRouter-specific instructions
        openrouter_additions = [
            "",
            "Additional instructions for technical accuracy:",
            "- Fix common transcription errors (hetsnir → Hetzner, ZOS → ZeroOS, etc.)",
            "- Ensure all technical terms are correctly capitalized",
            "- Format command-line instructions properly",
            "- Include proper markdown syntax for code blocks",
            "- Add appropriate warnings and notes where needed"
        ]
        
        return base_prompt + "\n".join(openrouter_additions)
