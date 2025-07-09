# Video-to-Guide Pipeline

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](https://opensource.org/licenses/Apache-2.0)

A comprehensive toolkit for transforming instructional videos into professional documentation guides through automated transcription and AI-assisted guide generation.

## 🎯 Overview

This pipeline automates the process of converting video content into structured, searchable documentation. Perfect for technical teams, content creators, and organizations looking to scale their documentation processes.

### **Complete Workflow:**
```
📹 Video Files → 🎵 Audio Extraction → 📝 Transcription → 📚 Guide Generation
```

## ✨ Features

- **🎵 High-Quality Audio Extraction** - FFmpeg-powered audio extraction optimized for speech recognition
- **🤖 Accurate Transcription** - OpenAI Whisper integration for precise speech-to-text conversion
- **📋 Template-Based Guide Generation** - Structured markdown guide creation with customizable templates
- **⚡ Batch Processing** - Process multiple videos simultaneously
- **🔧 Configurable Pipeline** - YAML-based configuration for different use cases
- **📊 Quality Assurance** - Built-in tools for reviewing and validating output
- **🐳 Docker Support** - Containerized deployment for consistent environments

## 🏗️ Architecture

### **Two-Stage Processing Pipeline**

This pipeline combines AI-powered transcription with intelligent text processing for **privacy, cost-efficiency, and offline capability**:

#### **Stage 1: Speech-to-Text (OpenAI Whisper - LOCAL)**
- **Technology**: OpenAI's open-source Whisper model
- **Execution**: Runs **locally on your machine** (no API calls)
- **Cost**: **$0.00** - completely free after initial setup
- **Privacy**: All audio processing happens offline
- **Models Available**: 
  - `tiny` - Fastest, basic accuracy (~39 MB)
  - `base` - Good balance of speed/accuracy (~74 MB) **[Default]**
  - `small` - Better accuracy (~244 MB)
  - `medium` - High accuracy (~769 MB)
  - `large` - Best accuracy (~1550 MB)

#### **Stage 2: Guide Generation (Template-Based Processing)**
- **Technology**: Template-based text processing using Jinja2
- **Method**: Intelligent pattern matching and structured formatting
- **Processing**: 
  - Extracts sections using natural language patterns
  - Identifies commands with shell syntax recognition
  - Finds URLs using regex validation
  - Structures content using template engines
- **Templates**: Customizable Markdown templates with structured formatting

### **Key Architectural Benefits**

| Aspect | Traditional API Approach | Our Architecture |
|--------|--------------------------|------------------|
| **Cost** | $0.10-$1.00+ per hour of audio | **$0.00** |
| **Privacy** | Audio sent to external servers | **100% local processing** |
| **Reliability** | Depends on internet/API availability | **Works offline** |
| **Speed** | Network latency + processing | **Local GPU/CPU only** |
| **Customization** | Limited by API constraints | **Full model control** |

### **Hardware Requirements**

- **CPU Processing**: Works on any modern CPU (slower)
- **GPU Acceleration**: CUDA-compatible GPU recommended for faster processing
- **RAM Requirements**:
  - `tiny/base` models: 2-4GB RAM
  - `small/medium` models: 4-8GB RAM  
  - `large` models: 8GB+ RAM
- **Storage**: 100MB - 2GB for model files (downloaded once)

### **No External Dependencies**

✅ **No API keys required**  
✅ **No internet connection needed** (after initial setup)  
✅ **No external service accounts**  
✅ **No usage limits or quotas**  
✅ **Complete data privacy**  

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- FFmpeg installed on your system
- 4GB+ RAM (for Whisper models)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mik-tf/video-to-guide-pipeline.git
   cd video-to-guide-pipeline
   ```

2. **Set up the environment:**
   ```bash
   ./scripts/setup_environment.sh
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Basic Usage

1. **Place your videos in the `videos/` directory**

2. **Run the complete pipeline:**
   ```bash
   python scripts/process_videos.py --config config/default.yaml
   ```

3. **Find your generated guides in `output/guides/`**

## 📁 Project Structure

```
video-to-guide-pipeline/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .gitignore                  # Git ignore rules
├── .env.example                # Environment variables template
├── docker-compose.yml          # Docker setup
├── Dockerfile                  # Container definition
│
├── config/
│   ├── default.yaml            # Default configuration
│   └── templates.yaml          # Template configurations
│
├── src/
│   ├── __init__.py
│   ├── audio_extractor.py      # FFmpeg audio extraction
│   ├── transcriber.py          # Whisper transcription
│   ├── guide_generator.py      # Guide creation logic
│   ├── template_engine.py      # Template processing
│   └── utils.py                # Common utilities
│
├── scripts/
│   ├── process_videos.py       # Main processing script
│   ├── setup_environment.sh    # Environment setup
│   └── validate_output.py      # Quality assurance
│
├── videos/                     # Input video files
├── output/
│   ├── audio/                  # Generated audio files
│   ├── transcriptions/         # Text transcriptions
│   └── guides/                 # Final markdown guides
│
├── templates/
│   ├── deployment_guide.md     # Deployment guide template
│   ├── tutorial.md             # Tutorial template
│   └── api_documentation.md    # API docs template
│
├── tests/
│   ├── test_audio_extractor.py
│   ├── test_transcriber.py
│   └── test_guide_generator.py
│
└── docs/
    ├── usage.md                # Detailed usage guide
    ├── configuration.md        # Configuration options
    ├── templates.md            # Template customization
    └── api.md                  # API documentation
```

## 🔧 Configuration

The pipeline uses YAML configuration files for customization:

```yaml
# config/default.yaml
audio:
  sample_rate: 16000
  channels: 1
  format: "wav"

transcription:
  model: "base"  # tiny, base, small, medium, large
  language: "en"

guide_generation:
  template: "deployment_guide"
  include_timestamps: false
  max_section_length: 500
```

### **AI Model Configuration**

The pipeline's AI components are fully configurable:

```yaml
# Whisper Model Settings
transcription:
  model: "base"              # Model size: tiny, base, small, medium, large
  device: "cpu"              # Processing: cpu, cuda (GPU acceleration)
  language: "en"             # Target language (auto-detect if null)
  temperature: 0.0           # Sampling randomness (0.0 = deterministic)
  beam_size: 5               # Search breadth for accuracy
  fp16: false                # Half-precision (GPU only, faster)

# Guide Processing (Template-Based)
guide_generation:
  extract_commands: true     # Find shell commands automatically
  extract_urls: true         # Identify and validate URLs
  format_code_blocks: true   # Auto-format code snippets
  auto_generate_toc: true    # Create table of contents
```

**Model Selection Guide:**
- **Production**: Use `base` or `small` for best speed/accuracy balance
- **High Accuracy**: Use `medium` or `large` for technical content
- **Fast Processing**: Use `tiny` for quick drafts or testing
- **GPU Available**: Enable `fp16: true` and `device: "cuda"` for 2x speed boost

## 📖 Usage Examples

### Process a Single Video
```bash
python scripts/process_videos.py --input videos/tutorial.mp4 --template deployment_guide
```

### Batch Process Multiple Videos
```bash
python scripts/process_videos.py --batch --config config/batch_processing.yaml
```

### Custom Template
```bash
python scripts/process_videos.py --input videos/demo.mp4 --template custom --template-file templates/my_template.md
```

## 🎯 Use Cases

- **📚 Technical Documentation** - Convert deployment videos into step-by-step guides
- **🎓 Training Materials** - Transform training videos into searchable documentation
- **📋 Process Documentation** - Document complex procedures from video demonstrations
- **🔄 Knowledge Transfer** - Preserve institutional knowledge from video content
- **📝 Content Repurposing** - Convert video content into multiple documentation formats

## 🛠️ Advanced Features

### Custom Templates
Create your own guide templates by extending the base template system. See [docs/templates.md](docs/templates.md) for details.

### Quality Assurance
Built-in validation tools help ensure transcription accuracy and guide completeness:
```bash
python scripts/validate_output.py --check-transcription --check-guides
```

### Docker Deployment
Run the entire pipeline in a containerized environment:
```bash
docker-compose up --build
```

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI Whisper** - For excellent speech recognition capabilities
- **FFmpeg** - For robust audio/video processing