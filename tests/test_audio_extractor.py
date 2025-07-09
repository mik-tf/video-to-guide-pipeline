#!/usr/bin/env python3
"""
Tests for AudioExtractor module
"""

import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio_extractor import AudioExtractor


class TestAudioExtractor(unittest.TestCase):
    """Test cases for AudioExtractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'audio': {
                'sample_rate': 16000,
                'channels': 1,
                'format': 'wav',
                'quality': 'medium'
            },
            'logging': {
                'level': 'INFO'
            }
        }
        self.extractor = AudioExtractor(self.config)
    
    def test_init(self):
        """Test AudioExtractor initialization."""
        self.assertEqual(self.extractor.sample_rate, 16000)
        self.assertEqual(self.extractor.channels, 1)
        self.assertEqual(self.extractor.format, 'wav')
        self.assertEqual(self.extractor.quality, 'medium')
    
    def test_build_ffmpeg_command(self):
        """Test FFmpeg command building."""
        input_path = "/path/to/video.mp4"
        output_path = "/path/to/audio.wav"
        
        command = self.extractor._build_ffmpeg_command(input_path, output_path)
        
        self.assertIn('ffmpeg', command)
        self.assertIn('-i', command)
        self.assertIn(input_path, command)
        self.assertIn(output_path, command)
        self.assertIn('-ar', command)
        self.assertIn('16000', command)
        self.assertIn('-ac', command)
        self.assertIn('1', command)
    
    def test_validate_video_file_nonexistent(self):
        """Test validation of non-existent video file."""
        is_valid, error = self.extractor.validate_video_file("/nonexistent/file.mp4")
        self.assertFalse(is_valid)
        self.assertIn("does not exist", error)
    
    def test_validate_video_file_invalid_extension(self):
        """Test validation of file with invalid extension."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name
        
        try:
            is_valid, error = self.extractor.validate_video_file(tmp_path)
            self.assertFalse(is_valid)
            self.assertIn("Unsupported video format", error)
        finally:
            os.unlink(tmp_path)
    
    @patch('subprocess.run')
    def test_extract_audio_success(self, mock_run):
        """Test successful audio extraction."""
        # Mock successful subprocess run
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        # Create temporary video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
            video_file.write(b"fake video content")
            video_path = video_file.name
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = os.path.join(temp_dir, "output.wav")
            
            try:
                result = self.extractor.extract_audio(video_path, audio_path)
                self.assertTrue(result)
                mock_run.assert_called_once()
            finally:
                os.unlink(video_path)
    
    @patch('subprocess.run')
    def test_extract_audio_failure(self, mock_run):
        """Test failed audio extraction."""
        # Mock failed subprocess run
        mock_run.return_value = MagicMock(
            returncode=1, 
            stderr="FFmpeg error: Invalid input"
        )
        
        # Create temporary video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
            video_file.write(b"fake video content")
            video_path = video_file.name
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = os.path.join(temp_dir, "output.wav")
            
            try:
                result = self.extractor.extract_audio(video_path, audio_path)
                self.assertFalse(result)
                mock_run.assert_called_once()
            finally:
                os.unlink(video_path)
    
    def test_get_quality_settings(self):
        """Test quality settings retrieval."""
        # Test high quality
        self.extractor.quality = 'high'
        settings = self.extractor._get_quality_settings()
        self.assertIn('-q:a', settings)
        
        # Test medium quality
        self.extractor.quality = 'medium'
        settings = self.extractor._get_quality_settings()
        self.assertIn('-q:a', settings)
        
        # Test low quality
        self.extractor.quality = 'low'
        settings = self.extractor._get_quality_settings()
        self.assertIn('-q:a', settings)
    
    @patch('subprocess.run')
    def test_get_video_info(self, mock_run):
        """Test video information retrieval."""
        # Mock ffprobe output
        mock_output = """
        {
            "streams": [
                {
                    "codec_type": "video",
                    "duration": "120.5",
                    "width": 1920,
                    "height": 1080
                }
            ]
        }
        """
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_output,
            stderr=""
        )
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
            video_file.write(b"fake video content")
            video_path = video_file.name
        
        try:
            info = self.extractor.get_video_info(video_path)
            self.assertIsNotNone(info)
            self.assertEqual(info['streams'][0]['duration'], "120.5")
            self.assertEqual(info['streams'][0]['width'], 1920)
        finally:
            os.unlink(video_path)


if __name__ == '__main__':
    unittest.main()
