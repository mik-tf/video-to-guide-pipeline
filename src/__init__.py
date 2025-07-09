"""
Video-to-Guide Pipeline

A comprehensive toolkit for transforming instructional videos into professional documentation guides.
"""

__version__ = "1.0.0"
__author__ = "Video-to-Guide Pipeline Team"
__email__ = "support@video-to-guide.com"

from .audio_extractor import AudioExtractor
from .transcriber import Transcriber
from .guide_generator import GuideGenerator
from .utils import setup_logging, load_config

__all__ = [
    "AudioExtractor",
    "Transcriber", 
    "GuideGenerator",
    "setup_logging",
    "load_config"
]
