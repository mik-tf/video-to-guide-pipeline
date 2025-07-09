# Usage Guide

This guide covers how to use the Video-to-Guide Pipeline effectively.

## Quick Start

1. **Setup Environment**
   ```bash
   ./scripts/setup_environment.sh
   source activate.sh
   ```

2. **Add Videos**
   Place your video files in the `videos/` directory.

3. **Process Videos**
   ```bash
   # Single video
   python scripts/process_videos.py --input videos/my_video.mp4
   
   # All videos in directory
   python scripts/process_videos.py --batch --input videos/
   ```

## Command Line Options

### Basic Usage
```bash
python scripts/process_videos.py [OPTIONS]
```

### Options

- `--input, -i`: Input video file or directory (required)
- `--config, -c`: Configuration file path (default: config/default.yaml)
- `--template, -t`: Template name for guide generation
- `--batch, -b`: Process all videos in input directory
- `--overwrite`: Overwrite existing output files
- `--preserve-intermediate`: Keep audio and transcription files
- `--system-info`: Print system information and dependencies
- `--verbose, -v`: Enable verbose logging

### Examples

**Process a single video:**
```bash
python scripts/process_videos.py --input videos/tutorial.mp4
```

**Batch process with custom template:**
```bash
python scripts/process_videos.py --batch --input videos/ --template tutorial
```

**Overwrite existing files:**
```bash
python scripts/process_videos.py --input videos/demo.mp4 --overwrite
```

**Keep intermediate files:**
```bash
python scripts/process_videos.py --input videos/demo.mp4 --preserve-intermediate
```

## Configuration

### Default Configuration
The pipeline uses `config/default.yaml` by default. Key settings:

```yaml
audio:
  sample_rate: 16000
  channels: 1
  format: "wav"

transcription:
  model: "base"  # tiny, base, small, medium, large
  language: "en"

guide_generation:
  template: "deployment_guide"
  max_section_length: 500
```

### Custom Configuration
Create a custom config file and use it:

```bash
python scripts/process_videos.py --input video.mp4 --config my_config.yaml
```

## Templates

### Available Templates
- `deployment_guide`: For deployment/setup instructions
- `tutorial`: For tutorial content
- `api_documentation`: For API documentation

### Using Templates
```bash
python scripts/process_videos.py --input video.mp4 --template tutorial
```

### Custom Templates
1. Create a new template file in `templates/`
2. Use Jinja2 syntax for variables
3. Reference it by filename (without .md extension)

## Output Structure

```
output/
├── audio/              # Extracted audio files
├── transcriptions/     # Text transcriptions
└── guides/            # Generated markdown guides
```

## Quality Control

### Transcription Quality
The pipeline provides quality metrics:
- Confidence scores
- Estimated accuracy ratings
- Low confidence segment detection

### Validation
Built-in validation checks:
- Minimum transcription length
- Confidence thresholds
- Language detection

## Troubleshooting

### Common Issues

**FFmpeg not found:**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

**Whisper model download fails:**
- Check internet connection
- Ensure sufficient disk space
- Try smaller model (tiny, base)

**Low transcription quality:**
- Use larger Whisper model (medium, large)
- Improve audio quality
- Check language settings

**Memory issues:**
- Use smaller Whisper model
- Process videos individually
- Increase system RAM

### Getting Help

1. Check system info: `python scripts/process_videos.py --system-info`
2. Enable verbose logging: `--verbose`
3. Check log files in `logs/`
4. Review configuration settings

## Performance Tips

### Model Selection
- **tiny**: Fastest, lowest quality
- **base**: Good balance (recommended)
- **small**: Better quality, slower
- **medium**: High quality, much slower
- **large**: Best quality, very slow

### Hardware Optimization
- Use GPU for faster transcription (CUDA)
- More RAM allows larger models
- SSD storage improves I/O performance

### Batch Processing
- Process multiple videos efficiently
- Automatic progress tracking
- Error handling and recovery
