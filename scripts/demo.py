#!/usr/bin/env python3
"""
Demo Script for Video-to-Guide Pipeline

This script demonstrates the complete pipeline functionality with example videos.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import print_system_info, validate_dependencies, create_directory_structure


def print_banner():
    """Print demo banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                 Video-to-Guide Pipeline Demo                 ║
    ║                                                              ║
    ║  Transform instructional videos into professional guides     ║
    ║  using AI-powered transcription and intelligent formatting   ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_prerequisites():
    """Check if all prerequisites are met."""
    print("🔍 Checking Prerequisites...")
    print("=" * 50)
    
    # Check dependencies
    deps = validate_dependencies()
    all_good = True
    
    for dep, available in deps.items():
        status = "✅ Available" if available else "❌ Missing"
        print(f"  {dep:15} {status}")
        if not available:
            all_good = False
    
    # Check Python packages
    required_packages = [
        'whisper', 'torch', 'ffmpeg', 'yaml', 'jinja2', 'click', 'rich'
    ]
    
    print("\n📦 Python Packages:")
    for package in required_packages:
        try:
            __import__(package)
            print(f"  {package:15} ✅ Available")
        except ImportError:
            print(f"  {package:15} ❌ Missing")
            all_good = False
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("✅ All prerequisites met!")
        return True
    else:
        print("❌ Some prerequisites are missing.")
        print("\nTo install missing components:")
        print("  1. Run: ./scripts/setup_environment.sh")
        print("  2. Or manually install missing dependencies")
        return False


def demonstrate_pipeline():
    """Demonstrate the pipeline with example content."""
    print("\n🎬 Pipeline Demonstration")
    print("=" * 50)
    
    # Check for example videos
    video_dir = Path("videos")
    video_files = list(video_dir.glob("*.mp4")) + list(video_dir.glob("*.avi"))
    
    if not video_files:
        print("📁 No video files found in videos/ directory")
        print("\nTo run the demo:")
        print("  1. Place video files in the videos/ directory")
        print("  2. Run: python scripts/process_videos.py --batch --input videos/")
        print("\nExample commands:")
        print("  # Process single video")
        print("  python scripts/process_videos.py --input videos/tutorial.mp4")
        print("  # Process all videos")
        print("  python scripts/process_videos.py --batch --input videos/")
        return
    
    print(f"📹 Found {len(video_files)} video file(s):")
    for video in video_files:
        size_mb = video.stat().st_size / (1024 * 1024)
        print(f"  • {video.name} ({size_mb:.1f} MB)")
    
    print("\n🚀 To process these videos, run:")
    print("  python scripts/process_videos.py --batch --input videos/")
    
    # Check existing outputs
    output_dir = Path("output")
    if output_dir.exists():
        guides = list(output_dir.glob("guides/*.md"))
        if guides:
            print(f"\n📄 Found {len(guides)} existing guide(s):")
            for guide in guides:
                print(f"  • {guide.name}")


def show_configuration_examples():
    """Show configuration examples."""
    print("\n⚙️  Configuration Examples")
    print("=" * 50)
    
    examples = {
        "High Quality": {
            "transcription": {"model": "large", "compute_type": "float32"},
            "audio": {"quality": "high", "normalize": True}
        },
        "Fast Processing": {
            "transcription": {"model": "tiny", "device": "cuda"},
            "processing": {"parallel_processing": True}
        },
        "Development": {
            "logging": {"level": "DEBUG"},
            "processing": {"preserve_intermediate": True}
        }
    }
    
    for name, config in examples.items():
        print(f"\n{name}:")
        print(f"  File: config/{name.lower().replace(' ', '_')}.yaml")
        for section, settings in config.items():
            print(f"  {section}:")
            for key, value in settings.items():
                print(f"    {key}: {value}")


def show_template_examples():
    """Show template examples."""
    print("\n📝 Template Examples")
    print("=" * 50)
    
    templates_dir = Path("templates")
    if templates_dir.exists():
        templates = list(templates_dir.glob("*.md"))
        if templates:
            print("Available templates:")
            for template in templates:
                print(f"  • {template.stem}")
                print(f"    Usage: --template {template.stem}")
        else:
            print("No templates found in templates/ directory")
    else:
        print("Templates directory not found")
    
    print("\nTemplate usage examples:")
    print("  python scripts/process_videos.py --input video.mp4 --template deployment_guide")
    print("  python scripts/process_videos.py --input video.mp4 --template tutorial")


def show_docker_usage():
    """Show Docker usage examples."""
    print("\n🐳 Docker Usage")
    print("=" * 50)
    
    if Path("Dockerfile").exists():
        print("Docker setup available!")
        print("\nBuild and run with Docker:")
        print("  # Build image")
        print("  docker build -t video-to-guide .")
        print("  # Run single video")
        print("  docker run -v $(pwd)/videos:/app/videos -v $(pwd)/output:/app/output video-to-guide \\")
        print("    python scripts/process_videos.py --input videos/your_video.mp4")
        
        if Path("docker-compose.yml").exists():
            print("\nOr use Docker Compose:")
            print("  # Process all videos")
            print("  docker-compose up video-to-guide")
            print("  # Development mode")
            print("  docker-compose run video-to-guide-dev")
    else:
        print("Docker setup not available")


def interactive_demo():
    """Run interactive demo."""
    print("\n🎯 Interactive Demo Mode")
    print("=" * 50)
    
    while True:
        print("\nWhat would you like to do?")
        print("  1. Check system information")
        print("  2. Process a single video")
        print("  3. Process all videos")
        print("  4. View configuration")
        print("  5. Run tests")
        print("  6. Exit")
        
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '1':
                print_system_info()
            elif choice == '2':
                video_path = input("Enter video path: ").strip()
                if video_path and Path(video_path).exists():
                    cmd = f"python scripts/process_videos.py --input {video_path}"
                    print(f"Run: {cmd}")
                else:
                    print("❌ Video file not found")
            elif choice == '3':
                cmd = "python scripts/process_videos.py --batch --input videos/"
                print(f"Run: {cmd}")
            elif choice == '4':
                config_path = input("Enter config path (default: config/default.yaml): ").strip()
                if not config_path:
                    config_path = "config/default.yaml"
                if Path(config_path).exists():
                    print(f"Configuration file: {config_path}")
                    with open(config_path) as f:
                        print(f.read())
                else:
                    print("❌ Configuration file not found")
            elif choice == '5':
                print("Running tests...")
                os.system("python -m pytest tests/ -v")
            elif choice == '6':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(
        description="Video-to-Guide Pipeline Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run interactive demo'
    )
    
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check prerequisites'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Check prerequisites
    if not check_prerequisites():
        if not args.check_only:
            print("\n⚠️  Prerequisites not met. Please run setup first.")
        return
    
    if args.check_only:
        return
    
    if args.interactive:
        interactive_demo()
    else:
        # Show full demo
        demonstrate_pipeline()
        show_configuration_examples()
        show_template_examples()
        show_docker_usage()
        
        print("\n🎉 Demo Complete!")
        print("\nNext steps:")
        print("  1. Place videos in videos/ directory")
        print("  2. Run: python scripts/process_videos.py --batch --input videos/")
        print("  3. Check output in output/guides/")
        print("\nFor interactive mode: python scripts/demo.py --interactive")


if __name__ == "__main__":
    main()
