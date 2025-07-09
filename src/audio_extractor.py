#!/usr/bin/env python3
"""
Audio Extraction Module

Extracts high-quality audio from video files using FFmpeg, optimized for speech recognition.
"""

import subprocess
import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)


class AudioExtractor:
    """
    Handles audio extraction from video files using FFmpeg.
    
    Optimized for speech recognition with configurable quality settings.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AudioExtractor.
        
        Args:
            config: Configuration dictionary with audio settings
        """
        self.config = config.get('audio', {})
        self.sample_rate = self.config.get('sample_rate', 16000)
        self.channels = self.config.get('channels', 1)
        self.format = self.config.get('format', 'wav')
        self.codec = self.config.get('codec', 'pcm_s16le')
        
    def extract_audio(self, video_path: str, audio_path: str) -> bool:
        """
        Extract audio from video using FFmpeg.
        
        Args:
            video_path: Path to the input video file
            audio_path: Path to save the extracted audio file
            
        Returns:
            bool: True if extraction successful, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            
            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(video_path, audio_path)
            
            logger.info(f"Extracting audio from: {video_path}")
            logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            
            # Execute FFmpeg
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                # Verify output file exists and has content
                if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                    file_size = os.path.getsize(audio_path)
                    logger.info(f"✅ Audio extracted successfully: {audio_path}")
                    logger.info(f"Audio file size: {file_size / (1024*1024):.1f} MB")
                    return True
                else:
                    logger.error("❌ Audio file was not created or is empty")
                    return False
            else:
                logger.error(f"❌ FFmpeg error (exit code {result.returncode}):")
                logger.error(f"STDERR: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Audio extraction timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Exception during audio extraction: {str(e)}")
            return False
    
    def _build_ffmpeg_command(self, video_path: str, audio_path: str) -> list:
        """
        Build the FFmpeg command based on configuration.
        
        Args:
            video_path: Input video file path
            audio_path: Output audio file path
            
        Returns:
            list: FFmpeg command as list of arguments
        """
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # No video stream
            '-acodec', self.codec,
            '-ar', str(self.sample_rate),
            '-ac', str(self.channels),
            '-y',  # Overwrite output file
        ]
        
        # Add quality settings based on configuration
        quality = self.config.get('quality', 'high')
        if quality == 'high':
            cmd.extend(['-q:a', '0'])  # Highest quality
        elif quality == 'medium':
            cmd.extend(['-q:a', '2'])
        elif quality == 'low':
            cmd.extend(['-q:a', '4'])
            
        cmd.append(audio_path)
        return cmd
    
    def get_video_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about the video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            dict: Video information or None if error
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                return self._parse_video_info(info, video_path)
            else:
                logger.error(f"Failed to get video info: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Exception getting video info: {str(e)}")
            return None
    
    def _parse_video_info(self, raw_info: Dict, video_path: str) -> Dict[str, Any]:
        """
        Parse raw FFprobe output into structured information.
        
        Args:
            raw_info: Raw FFprobe JSON output
            video_path: Original video file path
            
        Returns:
            dict: Parsed video information
        """
        info = {
            'file_path': video_path,
            'file_size': os.path.getsize(video_path),
            'duration': 0,
            'video_stream': None,
            'audio_stream': None,
            'format': raw_info.get('format', {}),
            'streams': raw_info.get('streams', [])
        }
        
        # Extract duration
        format_info = raw_info.get('format', {})
        if 'duration' in format_info:
            info['duration'] = float(format_info['duration'])
        
        # Find video and audio streams
        for stream in raw_info.get('streams', []):
            if stream.get('codec_type') == 'video' and not info['video_stream']:
                info['video_stream'] = {
                    'codec': stream.get('codec_name', 'unknown'),
                    'width': stream.get('width', 0),
                    'height': stream.get('height', 0),
                    'fps': self._parse_fps(stream.get('r_frame_rate', '0/1')),
                    'bitrate': stream.get('bit_rate', 0)
                }
            elif stream.get('codec_type') == 'audio' and not info['audio_stream']:
                info['audio_stream'] = {
                    'codec': stream.get('codec_name', 'unknown'),
                    'sample_rate': stream.get('sample_rate', 0),
                    'channels': stream.get('channels', 0),
                    'bitrate': stream.get('bit_rate', 0)
                }
        
        return info
    
    def _parse_fps(self, fps_string: str) -> float:
        """Parse FPS from FFprobe fraction format."""
        try:
            if '/' in fps_string:
                num, den = fps_string.split('/')
                return float(num) / float(den) if float(den) != 0 else 0
            return float(fps_string)
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def validate_video_file(self, video_path: str) -> Tuple[bool, str]:
        """
        Validate that a video file is suitable for processing.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not os.path.exists(video_path):
            return False, f"Video file does not exist: {video_path}"
        
        if os.path.getsize(video_path) == 0:
            return False, f"Video file is empty: {video_path}"
        
        # Get video info to validate format
        info = self.get_video_info(video_path)
        if not info:
            return False, f"Could not read video file information: {video_path}"
        
        # Check duration
        duration = info.get('duration', 0)
        min_duration = self.config.get('min_duration', 1)
        max_duration = self.config.get('max_duration', 7200)  # 2 hours
        
        if duration < min_duration:
            return False, f"Video too short: {duration:.1f}s (minimum: {min_duration}s)"
        
        if duration > max_duration:
            return False, f"Video too long: {duration:.1f}s (maximum: {max_duration}s)"
        
        # Check if audio stream exists
        if not info.get('audio_stream'):
            return False, f"No audio stream found in video: {video_path}"
        
        return True, "Video file is valid"
    
    def print_video_info(self, video_path: str) -> None:
        """
        Print formatted video information to console.
        
        Args:
            video_path: Path to the video file
        """
        info = self.get_video_info(video_path)
        if not info:
            logger.error(f"Could not get information for: {video_path}")
            return
        
        print(f"\n📹 Video Information: {os.path.basename(video_path)}")
        print("=" * 50)
        print(f"File Size: {info['file_size'] / (1024*1024):.1f} MB")
        print(f"Duration: {info['duration']:.2f} seconds ({info['duration']/60:.1f} minutes)")
        
        if info['video_stream']:
            vs = info['video_stream']
            print(f"Video: {vs['codec']} {vs['width']}x{vs['height']} @ {vs['fps']:.1f} fps")
        
        if info['audio_stream']:
            aus = info['audio_stream']
            print(f"Audio: {aus['codec']} {aus['sample_rate']} Hz, {aus['channels']} channel(s)")
        
        print("=" * 50)
