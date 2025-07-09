# Configuration Guide

This guide explains how to configure the Video-to-Guide Pipeline for your specific needs.

## Configuration Files

### Default Configuration
The pipeline uses `config/default.yaml` as the default configuration. This file contains all available settings with sensible defaults.

### Custom Configuration
You can create custom configuration files and specify them using the `--config` option:

```bash
python scripts/process_videos.py --config my_config.yaml --input video.mp4
```

## Configuration Structure

### Audio Extraction Settings

```yaml
audio:
  sample_rate: 16000        # Audio sample rate (Hz)
  channels: 1               # Number of audio channels (1=mono, 2=stereo)
  format: "wav"             # Output audio format
  quality: "high"           # Quality preset: low, medium, high
  normalize: true           # Normalize audio levels
  noise_reduction: false    # Apply noise reduction (experimental)
```

**Recommendations:**
- Use 16000 Hz sample rate for Whisper (optimal)
- Mono audio (1 channel) is sufficient for speech
- WAV format provides best quality
- Enable normalization for consistent levels

### Transcription Settings

```yaml
transcription:
  model: "base"             # Whisper model: tiny, base, small, medium, large
  language: "en"            # Language code (auto-detect if null)
  device: "auto"            # Device: auto, cpu, cuda
  compute_type: "float16"   # Precision: float16, float32, int8
  beam_size: 5              # Beam search size (1-10)
  temperature: 0.0          # Sampling temperature (0.0-1.0)
  condition_on_previous_text: true  # Use context from previous segments
  initial_prompt: null      # Initial prompt to guide transcription
  word_timestamps: true     # Generate word-level timestamps
  vad_filter: true          # Voice activity detection
  vad_parameters:
    threshold: 0.5          # VAD threshold
    min_speech_duration_ms: 250
    max_speech_duration_s: 30
```

**Model Selection:**
- `tiny`: 39 MB, ~32x realtime, English-only
- `base`: 74 MB, ~16x realtime, multilingual
- `small`: 244 MB, ~6x realtime, multilingual
- `medium`: 769 MB, ~2x realtime, multilingual
- `large`: 1550 MB, ~1x realtime, multilingual

### Guide Generation Settings

```yaml
guide_generation:
  template: "deployment_guide"  # Default template name
  max_section_length: 500       # Maximum characters per section
  min_section_length: 50        # Minimum characters per section
  extract_commands: true        # Extract shell commands
  extract_urls: true            # Extract URLs
  extract_prerequisites: true   # Extract prerequisites
  extract_troubleshooting: true # Extract troubleshooting info
  
  # Text processing
  clean_text: true              # Clean and normalize text
  remove_filler_words: true     # Remove "um", "uh", etc.
  fix_punctuation: true         # Fix punctuation issues
  
  # Section detection
  section_keywords:             # Keywords that indicate new sections
    - "step"
    - "next"
    - "now"
    - "first"
    - "second"
    - "finally"
  
  # Command extraction patterns
  command_patterns:
    - "run"
    - "execute"
    - "type"
    - "enter"
    - "sudo"
    - "docker"
    - "git"
```

### Processing Settings

```yaml
processing:
  preserve_intermediate: false  # Keep audio and transcription files
  overwrite_existing: false    # Overwrite existing output files
  parallel_processing: false   # Process multiple videos in parallel
  max_workers: 2               # Maximum parallel workers
  timeout_seconds: 3600        # Processing timeout per video
  retry_attempts: 3            # Retry failed operations
  
  # Quality control
  min_transcription_length: 100 # Minimum transcription length
  min_confidence_threshold: 0.7 # Minimum confidence score
  validate_output: true         # Validate generated guides
```

### Output Settings

```yaml
output:
  base_dir: "./output"          # Base output directory
  audio_dir: "audio"            # Audio files subdirectory
  transcription_dir: "transcriptions"  # Transcription files subdirectory
  guide_dir: "guides"           # Guide files subdirectory
  
  # File naming
  preserve_original_names: true # Keep original video names
  add_timestamp: false          # Add timestamp to filenames
  filename_template: "{name}_{type}"  # Filename template
  
  # Format settings
  audio_format: "wav"           # Audio output format
  transcription_format: "txt"   # Transcription format: txt, json, srt
  guide_format: "md"            # Guide format: md, html, pdf
```

### Logging Settings

```yaml
logging:
  level: "INFO"                 # Log level: DEBUG, INFO, WARNING, ERROR
  format: "detailed"            # Format: simple, detailed, json
  file_logging: true            # Enable file logging
  log_dir: "./logs"             # Log directory
  max_file_size: "10MB"         # Maximum log file size
  backup_count: 5               # Number of backup log files
  console_logging: true         # Enable console logging
  
  # Component-specific logging
  components:
    audio_extractor: "INFO"
    transcriber: "INFO"
    guide_generator: "DEBUG"
    utils: "WARNING"
```

## Environment Variables

You can override configuration settings using environment variables:

```bash
# Whisper settings
export WHISPER_MODEL=base
export WHISPER_DEVICE=cuda
export WHISPER_CACHE_DIR=/path/to/cache

# Processing settings
export LOG_LEVEL=DEBUG
export OUTPUT_DIR=/path/to/output
export PRESERVE_INTERMEDIATE=true

# API keys (if using AI-enhanced features)
export OPENAI_API_KEY=your_api_key_here
```

## Template Configuration

### Template Variables
Templates have access to these variables:

```yaml
# Metadata
metadata:
  generated_date: "2024-01-15T10:30:00Z"
  video_filename: "tutorial.mp4"
  transcription_quality: "high"
  estimated_reading_time: 5

# Content
title: "Extracted from video filename"
introduction: "Auto-generated introduction"
sections: []          # List of content sections
commands: []          # Extracted commands
urls: []             # Extracted URLs
prerequisites: []     # Extracted prerequisites
troubleshooting: []   # Troubleshooting items
```

### Custom Template Settings

```yaml
templates:
  directory: "./templates"      # Template directory
  default_template: "deployment_guide"
  
  # Template-specific settings
  deployment_guide:
    include_prerequisites: true
    include_troubleshooting: true
    max_commands: 20
  
  tutorial:
    include_steps: true
    number_steps: true
    include_summary: true
```

## Advanced Configuration

### GPU Acceleration

```yaml
transcription:
  device: "cuda"                # Use GPU
  compute_type: "float16"       # Use half precision
  
# Environment variable
export CUDA_VISIBLE_DEVICES=0   # Use specific GPU
```

### Batch Processing

```yaml
processing:
  parallel_processing: true     # Enable parallel processing
  max_workers: 4                # Number of parallel workers
  batch_size: 10                # Videos per batch
  
  # Memory management
  clear_cache_between_videos: true
  max_memory_usage: "8GB"
```

### Quality Optimization

```yaml
quality:
  # Audio preprocessing
  audio_enhancement: true
  noise_reduction: true
  volume_normalization: true
  
  # Transcription quality
  use_large_model_for_final: true  # Use large model for final pass
  post_process_text: true          # Apply text post-processing
  
  # Validation
  validate_transcription: true
  min_confidence_score: 0.8
  flag_low_confidence_segments: true
```

## Configuration Examples

### High-Quality Setup
```yaml
# config/high_quality.yaml
transcription:
  model: "large"
  compute_type: "float32"
  beam_size: 10
  temperature: 0.0

audio:
  quality: "high"
  normalize: true
  noise_reduction: true

guide_generation:
  clean_text: true
  remove_filler_words: true
  fix_punctuation: true
```

### Fast Processing Setup
```yaml
# config/fast.yaml
transcription:
  model: "tiny"
  device: "cuda"
  compute_type: "int8"

processing:
  parallel_processing: true
  max_workers: 8
  preserve_intermediate: false
```

### Development Setup
```yaml
# config/development.yaml
logging:
  level: "DEBUG"
  console_logging: true

processing:
  preserve_intermediate: true
  overwrite_existing: true
  validate_output: true

output:
  add_timestamp: true
```

## Validation

The pipeline validates configuration files on startup. Common validation errors:

- Invalid model names
- Unsupported audio formats
- Missing template files
- Invalid directory paths
- Conflicting settings

Use `--system-info` to check your configuration:

```bash
python scripts/process_videos.py --system-info --config your_config.yaml
```
