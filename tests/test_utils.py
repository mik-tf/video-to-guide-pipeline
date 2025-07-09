#!/usr/bin/env python3
"""
Tests for utility functions
"""

import os
import sys
import unittest
import tempfile
import yaml
from unittest.mock import patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import (
    load_config, find_files, get_file_info, 
    generate_output_filename, validate_dependencies
)


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""
    
    def test_load_config_valid(self):
        """Test loading valid configuration file."""
        config_data = {
            'audio': {'sample_rate': 16000},
            'transcription': {'model': 'base'},
            'logging': {'level': 'INFO'}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            self.assertEqual(config['audio']['sample_rate'], 16000)
            self.assertEqual(config['transcription']['model'], 'base')
            self.assertEqual(config['logging']['level'], 'INFO')
        finally:
            os.unlink(config_path)
    
    def test_load_config_nonexistent(self):
        """Test loading non-existent configuration file."""
        with self.assertRaises(FileNotFoundError):
            load_config('/nonexistent/config.yaml')
    
    def test_load_config_invalid_yaml(self):
        """Test loading invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name
        
        try:
            with self.assertRaises(yaml.YAMLError):
                load_config(config_path)
        finally:
            os.unlink(config_path)
    
    def test_find_files(self):
        """Test file finding functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = [
                'video1.mp4',
                'video2.avi',
                'document.txt',
                'audio.wav'
            ]
            
            for filename in test_files:
                with open(os.path.join(temp_dir, filename), 'w') as f:
                    f.write("test content")
            
            # Test finding video files
            video_files = find_files(temp_dir, ['mp4', 'avi'])
            self.assertEqual(len(video_files), 2)
            
            # Test finding all files
            all_files = find_files(temp_dir, ['mp4', 'avi', 'txt', 'wav'])
            self.assertEqual(len(all_files), 4)
            
            # Test finding non-existent extension
            no_files = find_files(temp_dir, ['xyz'])
            self.assertEqual(len(no_files), 0)
    
    def test_get_file_info(self):
        """Test file information retrieval."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content for file info")
            file_path = f.name
        
        try:
            info = get_file_info(file_path)
            self.assertIn('size', info)
            self.assertIn('modified', info)
            self.assertIn('name', info)
            self.assertIn('extension', info)
            self.assertGreater(info['size'], 0)
        finally:
            os.unlink(file_path)
    
    def test_get_file_info_nonexistent(self):
        """Test file info for non-existent file."""
        info = get_file_info('/nonexistent/file.txt')
        self.assertIsNone(info)
    
    def test_generate_output_filename(self):
        """Test output filename generation."""
        # Test basic filename generation
        filename = generate_output_filename('video.mp4', 'audio', 'wav')
        self.assertEqual(filename, 'video_audio.wav')
        
        # Test with path
        filename = generate_output_filename('/path/to/video.mp4', 'transcription', 'txt')
        self.assertEqual(filename, 'video_transcription.txt')
        
        # Test with complex filename
        filename = generate_output_filename('my-video_file.mp4', 'guide', 'md')
        self.assertEqual(filename, 'my-video_file_guide.md')
    
    @patch('shutil.which')
    def test_validate_dependencies(self, mock_which):
        """Test dependency validation."""
        # Mock ffmpeg as available
        def mock_which_side_effect(cmd):
            if cmd == 'ffmpeg':
                return '/usr/bin/ffmpeg'
            return None
        
        mock_which.side_effect = mock_which_side_effect
        
        deps = validate_dependencies()
        self.assertIn('ffmpeg', deps)
        self.assertTrue(deps['ffmpeg'])
    
    def test_create_directory_structure(self):
        """Test directory structure creation."""
        from utils import create_directory_structure
        
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = os.path.join(temp_dir, 'test_project')
            
            create_directory_structure(base_path)
            
            # Check that directories were created
            expected_dirs = [
                'videos',
                'output/audio',
                'output/transcriptions', 
                'output/guides',
                'logs',
                'tmp'
            ]
            
            for dir_path in expected_dirs:
                full_path = os.path.join(base_path, dir_path)
                self.assertTrue(os.path.exists(full_path), f"Directory {dir_path} was not created")
                self.assertTrue(os.path.isdir(full_path), f"{dir_path} is not a directory")


class TestProgressTracker(unittest.TestCase):
    """Test cases for ProgressTracker class."""
    
    def test_progress_tracker_init(self):
        """Test ProgressTracker initialization."""
        from utils import ProgressTracker
        
        tracker = ProgressTracker(5, "Test Task")
        self.assertEqual(tracker.total_steps, 5)
        self.assertEqual(tracker.task_name, "Test Task")
        self.assertEqual(tracker.current_step, 0)
    
    def test_progress_tracker_update(self):
        """Test ProgressTracker update functionality."""
        from utils import ProgressTracker
        
        tracker = ProgressTracker(3, "Test Task")
        
        # Test update with message
        tracker.update("Step 1")
        self.assertEqual(tracker.current_step, 1)
        
        # Test update without message
        tracker.update()
        self.assertEqual(tracker.current_step, 2)
        
        # Test finish
        tracker.finish()
        self.assertEqual(tracker.current_step, 3)


if __name__ == '__main__':
    unittest.main()
