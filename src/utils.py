#!/usr/bin/env python3
"""
Utility Functions

Common utilities for the video-to-guide pipeline including configuration, logging, and file operations.
"""

import os
import yaml
import json
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        dict: Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Validate required sections
        required_sections = ['audio', 'transcription', 'guide_generation', 'processing']
        for section in required_sections:
            if section not in config:
                config[section] = {}
        
        return config
        
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {str(e)}")


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    Set up logging based on configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        logging.Logger: Configured logger
    """
    log_config = config.get('logging', {})
    
    # Create logs directory if it doesn't exist
    log_file = log_config.get('file', './logs/pipeline.log')
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging level
    level_str = log_config.get('level', 'INFO').upper()
    level = getattr(logging, level_str, logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add file handler with rotation
    if log_file:
        max_bytes = parse_size(log_config.get('max_file_size', '10MB'))
        backup_count = log_config.get('backup_count', 5)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Add console handler if enabled
    if log_config.get('console_output', True):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    return root_logger


def parse_size(size_str: str) -> int:
    """
    Parse size string (e.g., '10MB', '1GB') to bytes.
    
    Args:
        size_str: Size string with unit
        
    Returns:
        int: Size in bytes
    """
    size_str = size_str.upper().strip()
    
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4
    }
    
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                number = float(size_str[:-len(unit)])
                return int(number * multiplier)
            except ValueError:
                break
    
    # Fallback: assume bytes
    try:
        return int(size_str)
    except ValueError:
        return 10 * 1024 * 1024  # Default 10MB


def ensure_directory(path: str) -> None:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        path: Directory path to ensure
    """
    os.makedirs(path, exist_ok=True)


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get detailed information about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        dict: File information
    """
    if not os.path.exists(file_path):
        return {'exists': False}
    
    stat = os.stat(file_path)
    
    return {
        'exists': True,
        'size': stat.st_size,
        'size_mb': stat.st_size / (1024 * 1024),
        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        'extension': Path(file_path).suffix.lower(),
        'basename': os.path.basename(file_path),
        'dirname': os.path.dirname(file_path)
    }


def find_files(directory: str, extensions: List[str], recursive: bool = True) -> List[str]:
    """
    Find files with specific extensions in a directory.
    
    Args:
        directory: Directory to search
        extensions: List of file extensions (with or without dots)
        recursive: Whether to search recursively
        
    Returns:
        list: List of matching file paths
    """
    if not os.path.exists(directory):
        return []
    
    # Normalize extensions
    extensions = [ext.lower().lstrip('.') for ext in extensions]
    
    files = []
    
    if recursive:
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if any(filename.lower().endswith(f'.{ext}') for ext in extensions):
                    files.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                if any(filename.lower().endswith(f'.{ext}') for ext in extensions):
                    files.append(file_path)
    
    return sorted(files)


def clean_filename(filename: str) -> str:
    """
    Clean filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Cleaned filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove multiple underscores
    filename = '_'.join(part for part in filename.split('_') if part)
    
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    
    return filename


def generate_output_filename(input_path: str, suffix: str, extension: str, 
                           timestamp: bool = False) -> str:
    """
    Generate output filename based on input file.
    
    Args:
        input_path: Path to input file
        suffix: Suffix to add to filename
        extension: New file extension
        timestamp: Whether to include timestamp
        
    Returns:
        str: Generated filename
    """
    base_name = Path(input_path).stem
    
    if timestamp:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{base_name}_{suffix}_{ts}.{extension.lstrip('.')}"
    else:
        filename = f"{base_name}_{suffix}.{extension.lstrip('.')}"
    
    return clean_filename(filename)


def save_json(data: Any, file_path: str, indent: int = 2) -> bool:
    """
    Save data as JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save JSON file
        indent: JSON indentation
        
    Returns:
        bool: True if saved successfully
    """
    try:
        ensure_directory(os.path.dirname(file_path))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to save JSON to {file_path}: {str(e)}")
        return False


def load_json(file_path: str) -> Optional[Any]:
    """
    Load data from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Data from JSON file or None if failed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        logging.error(f"Failed to load JSON from {file_path}: {str(e)}")
        return None


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"


def format_file_size(bytes_size: int) -> str:
    """
    Format file size in bytes to human-readable string.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_size)
    
    for unit in units:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    
    return f"{size:.1f} PB"


def validate_dependencies() -> Dict[str, bool]:
    """
    Check if required dependencies are available.
    
    Returns:
        dict: Dependency availability status
    """
    dependencies = {}
    
    # Check FFmpeg
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        dependencies['ffmpeg'] = result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        dependencies['ffmpeg'] = False
    
    # Check Whisper
    try:
        import whisper
        dependencies['whisper'] = True
    except ImportError:
        dependencies['whisper'] = False
    
    # Check Jinja2
    try:
        import jinja2
        dependencies['jinja2'] = True
    except ImportError:
        dependencies['jinja2'] = False
    
    # Check PyYAML
    try:
        import yaml
        dependencies['yaml'] = True
    except ImportError:
        dependencies['yaml'] = False
    
    return dependencies


def print_system_info() -> None:
    """Print system information and dependency status."""
    import platform
    import sys
    
    print("🔧 System Information")
    print("=" * 50)
    print(f"Python Version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()[0]}")
    
    print("\n📦 Dependencies")
    print("-" * 30)
    
    deps = validate_dependencies()
    for dep, available in deps.items():
        status = "✅ Available" if available else "❌ Missing"
        print(f"{dep.capitalize()}: {status}")
    
    print("=" * 50)


class ProgressTracker:
    """Simple progress tracking utility."""
    
    def __init__(self, total_steps: int, description: str = "Processing"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = datetime.now()
    
    def update(self, step_description: str = "") -> None:
        """Update progress."""
        self.current_step += 1
        progress = (self.current_step / self.total_steps) * 100
        
        elapsed = datetime.now() - self.start_time
        
        print(f"\r{self.description}: {progress:.1f}% ({self.current_step}/{self.total_steps}) - {step_description}", end="")
        
        if self.current_step >= self.total_steps:
            print(f"\n✅ Completed in {elapsed.total_seconds():.2f} seconds")
    
    def finish(self) -> None:
        """Mark as finished."""
        if self.current_step < self.total_steps:
            self.current_step = self.total_steps
            self.update("Finished")


def create_project_structure(base_dir: str) -> None:
    """
    Create the standard project directory structure.
    
    Args:
        base_dir: Base directory for the project
    """
    directories = [
        'videos',
        'output/audio',
        'output/transcriptions', 
        'output/guides',
        'templates',
        'config',
        'logs',
        'tmp'
    ]
    
    for directory in directories:
        full_path = os.path.join(base_dir, directory)
        ensure_directory(full_path)
        
    print(f"✅ Project structure created in: {base_dir}")
