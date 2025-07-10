#!/usr/bin/env python3
"""
Main Video Processing Script

Orchestrates the complete video-to-guide pipeline: audio extraction, transcription, and guide generation.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio_extractor import AudioExtractor
from transcriber import Transcriber
from guide_generator import GuideGenerator
from utils import (
    load_config, setup_logging, find_files, get_file_info,
    generate_output_filename, ProgressTracker, print_system_info
)

logger = logging.getLogger(__name__)


class VideoPipeline:
    """
    Main pipeline orchestrator for video-to-guide conversion.
    """
    
    def __init__(self, config_path: str, processing_mode: str = None):
        """
        Initialize the pipeline.
        
        Args:
            config_path: Path to configuration file
            processing_mode: Override processing mode from config
        """
        self.config = load_config(config_path)
        self.logger = setup_logging(self.config)
        
        # Determine processing mode
        self.processing_mode = processing_mode or self.config.get('processing_mode', 'basic')
        logger.info(f"🔧 Pipeline mode: {self.processing_mode}")
        
        # Initialize components with processing mode
        self.audio_extractor = AudioExtractor(self.config)
        self.transcriber = Transcriber(self.config, self.processing_mode)
        self.guide_generator = GuideGenerator(self.config, self.processing_mode)
        
        # Output directories
        self.output_config = self.config.get('output', {})
        self.base_output_dir = self.output_config.get('base_dir', './output')
        self.audio_dir = os.path.join(self.base_output_dir, self.output_config.get('audio_dir', 'audio'))
        self.transcription_dir = os.path.join(self.base_output_dir, self.output_config.get('transcription_dir', 'transcriptions'))
        self.guide_dir = os.path.join(self.base_output_dir, self.output_config.get('guide_dir', 'guides'))
        
        # Processing settings
        self.processing_config = self.config.get('processing', {})
        self.preserve_intermediate = self.processing_config.get('preserve_intermediate', False)
        self.overwrite_existing = self.processing_config.get('overwrite_existing', False)
    
    def process_single_video(self, video_path: str, template_name: Optional[str] = None) -> bool:
        """
        Process a single video through the complete pipeline.
        
        Args:
            video_path: Path to the video file
            template_name: Template to use for guide generation
            
        Returns:
            bool: True if processing successful
        """
        logger.info(f"🎬 Processing video: {os.path.basename(video_path)}")
        
        # Validate video file
        is_valid, error_msg = self.audio_extractor.validate_video_file(video_path)
        if not is_valid:
            logger.error(f"❌ Video validation failed: {error_msg}")
            return False
        
        # Print video information
        self.audio_extractor.print_video_info(video_path)
        
        # Generate output filenames
        video_name = Path(video_path).stem
        audio_path = os.path.join(self.audio_dir, f"{video_name}_audio.wav")
        transcription_path = os.path.join(self.transcription_dir, f"{video_name}_transcription.txt")
        guide_path = os.path.join(self.guide_dir, f"{video_name}_guide.md")
        
        # Check if outputs already exist
        if not self.overwrite_existing:
            if os.path.exists(guide_path):
                logger.info(f"⏭️  Guide already exists: {guide_path}")
                return True
        
        progress = ProgressTracker(3, f"Processing {os.path.basename(video_path)}")
        
        try:
            # Step 1: Extract audio
            progress.update("Extracting audio...")
            if not self._extract_audio_step(video_path, audio_path):
                return False
            
            # Step 2: Transcribe audio
            progress.update("Transcribing audio...")
            transcription_result = self._transcribe_audio_step(audio_path, transcription_path)
            if not transcription_result:
                return False
            
            # Step 3: Generate guide
            progress.update("Generating guide...")
            if not self._generate_guide_step(transcription_result, guide_path, template_name):
                return False
            
            progress.finish()
            
            # Cleanup intermediate files if not preserving
            if not self.preserve_intermediate:
                self._cleanup_intermediate_files(audio_path)
            
            logger.info(f"✅ Successfully processed: {os.path.basename(video_path)}")
            logger.info(f"📄 Guide saved to: {guide_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed for {video_path}: {str(e)}")
            return False
    
    def _extract_audio_step(self, video_path: str, audio_path: str) -> bool:
        """Extract audio from video."""
        # Skip if audio already exists and not overwriting
        if os.path.exists(audio_path) and not self.overwrite_existing:
            logger.info(f"⏭️  Audio already exists: {audio_path}")
            return True
        
        return self.audio_extractor.extract_audio(video_path, audio_path)
    
    def _transcribe_audio_step(self, audio_path: str, transcription_path: str) -> Optional[Dict[str, Any]]:
        """Transcribe audio to text."""
        # Skip if transcription already exists and not overwriting
        if os.path.exists(transcription_path) and not self.overwrite_existing:
            logger.info(f"⏭️  Transcription already exists: {transcription_path}")
            # Load existing transcription
            try:
                with open(transcription_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                return {'text': text, 'metadata': {}, 'quality': {}}
            except Exception as e:
                logger.warning(f"Could not load existing transcription: {str(e)}")
        
        result = self.transcriber.transcribe_audio(audio_path, transcription_path)
        
        if result:
            # Print transcription summary
            self.transcriber.print_transcription_summary(result)
            
            # Validate transcription quality
            is_valid, issues = self.transcriber.validate_transcription(result)
            if not is_valid:
                logger.warning("⚠️  Transcription quality issues detected:")
                for issue in issues:
                    logger.warning(f"  - {issue}")
        
        return result
    
    def _generate_guide_step(self, transcription_result: Dict[str, Any], 
                           guide_path: str, template_name: Optional[str]) -> bool:
        """Generate guide from transcription."""
        # Skip if guide already exists and not overwriting
        if os.path.exists(guide_path) and not self.overwrite_existing:
            logger.info(f"⏭️  Guide already exists: {guide_path}")
            return True
        
        return self.guide_generator.generate_guide(
            transcription_result, guide_path, template_name
        )
    
    def _cleanup_intermediate_files(self, audio_path: str) -> None:
        """Clean up intermediate files."""
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                logger.debug(f"Cleaned up audio file: {audio_path}")
        except Exception as e:
            logger.warning(f"Could not clean up {audio_path}: {str(e)}")
    
    def process_batch(self, video_directory: str, template_name: Optional[str] = None) -> Dict[str, bool]:
        """
        Process all videos in a directory.
        
        Args:
            video_directory: Directory containing video files
            template_name: Template to use for guide generation
            
        Returns:
            dict: Results for each video file
        """
        logger.info(f"🎬 Processing videos in: {video_directory}")
        
        # Find video files
        video_extensions = ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm']
        video_files = find_files(video_directory, video_extensions, recursive=False)
        
        if not video_files:
            logger.error(f"No video files found in: {video_directory}")
            return {}
        
        logger.info(f"Found {len(video_files)} video files")
        
        results = {}
        
        for video_file in video_files:
            try:
                success = self.process_single_video(video_file, template_name)
                results[video_file] = success
                
                if success:
                    logger.info(f"✅ {os.path.basename(video_file)}")
                else:
                    logger.error(f"❌ {os.path.basename(video_file)}")
                    
            except KeyboardInterrupt:
                logger.info("⏹️  Processing interrupted by user")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error processing {video_file}: {str(e)}")
                results[video_file] = False
        
        # Print summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        logger.info(f"\n📊 Batch Processing Summary")
        logger.info(f"Total videos: {total}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {total - successful}")
        
        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Video-to-Guide Pipeline: Convert videos to documentation guides",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single video (basic template mode)
  python process_videos.py --input video.mp4
  
  # Process with local AI (Ollama)
  python process_videos.py --input video.mp4 --mode local_ai
  
  # Process with API transcription + template guide
  python process_videos.py --input video.mp4 --mode api_transcription
  
  # Process with full API (transcription + guide generation)
  python process_videos.py --input video.mp4 --mode full_api
  
  # Process with hybrid mode (API -> local AI -> template fallback)
  python process_videos.py --input video.mp4 --mode hybrid
  
  # Process all videos in a directory
  python process_videos.py --batch --input ./videos/ --mode local_ai
  
  # Use custom template with basic mode
  python process_videos.py --input video.mp4 --template tutorial
  
  # Use custom config
  python process_videos.py --input video.mp4 --config custom.yaml --mode hybrid
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input video file or directory'
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config/default.yaml',
        help='Configuration file path (default: config/default.yaml)'
    )
    
    parser.add_argument(
        '--template', '-t',
        help='Template name to use for guide generation'
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['basic', 'local_ai', 'api_transcription', 'api_generation', 'full_api', 'hybrid'],
        help='Processing mode: basic (template only), local_ai (Ollama), api_transcription (API transcription), api_generation (API guide gen), full_api (API for both), hybrid (fallback chain)'
    )
    
    parser.add_argument(
        '--batch', '-b',
        action='store_true',
        help='Process all videos in the input directory'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing output files'
    )
    
    parser.add_argument(
        '--preserve-intermediate',
        action='store_true',
        help='Keep intermediate files (audio, transcriptions)'
    )
    
    parser.add_argument(
        '--system-info',
        action='store_true',
        help='Print system information and exit'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Print system info if requested
    if args.system_info:
        print_system_info()
        return
    
    # Validate inputs
    if not os.path.exists(args.input):
        print(f"❌ Input path does not exist: {args.input}")
        sys.exit(1)
    
    if not os.path.exists(args.config):
        print(f"❌ Configuration file does not exist: {args.config}")
        sys.exit(1)
    
    try:
        # Initialize pipeline with processing mode
        pipeline = VideoPipeline(args.config, args.mode)
        
        # Override config with command line arguments
        if args.overwrite:
            pipeline.overwrite_existing = True
        if args.preserve_intermediate:
            pipeline.preserve_intermediate = True
        
        # Process videos
        if args.batch or os.path.isdir(args.input):
            # Batch processing
            results = pipeline.process_batch(args.input, args.template)
            
            # Exit with error code if any processing failed
            if not all(results.values()):
                sys.exit(1)
                
        else:
            # Single file processing
            success = pipeline.process_single_video(args.input, args.template)
            
            if not success:
                sys.exit(1)
        
        print("\n🎉 Pipeline completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
