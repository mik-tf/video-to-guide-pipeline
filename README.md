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

### **Core Processing Capabilities**
- **🎵 High-Quality Audio Extraction** - FFmpeg-powered audio extraction optimized for speech recognition
- **🤖 Multi-Mode Transcription** - Local Whisper + API transcription with intelligent fallback
- **🧠 AI-Powered Guide Generation** - Local AI (Ollama) + API-based guide creation with template fallback
- **🔄 Intelligent Fallback System** - Automatic degradation: API → Local AI → Template processing

### **Processing Modes**
- **📝 Basic Mode** - Template-based processing (original functionality)
- **🤖 Local AI Mode** - Ollama LLM for enhanced guide generation
- **🌐 API Modes** - OpenRouter/OpenAI integration for transcription and/or guide generation
- **🔄 Hybrid Mode** - Best quality with automatic fallbacks across all methods

### **Operational Features**
- **⚡ Batch Processing** - Process multiple videos simultaneously
- **🔧 Configurable Pipeline** - YAML-based configuration for different use cases
- **📊 Quality Assurance** - Built-in tools for reviewing and validating output
- **🔒 Privacy Control** - Choose between local-only, API-based, or hybrid processing
- **💰 Cost Control** - Local processing ($0) vs API processing (pay-per-use)

## 🏗️ Architecture

### **Multi-Mode Processing Pipeline**

This pipeline offers **6 processing modes** combining local AI, API services, and template processing with intelligent fallback mechanisms for **flexibility, quality, and reliability**:

### **Processing Modes Available**

#### **1. Basic Mode** (`basic`) - Template Processing
- **Transcription**: Local Whisper (OpenAI)
- **Guide Generation**: Template-based processing with Jinja2
- **Cost**: $0.00 (completely free)
- **Privacy**: 100% local processing
- **Use Case**: Cost-effective processing with basic quality

#### **2. Local AI Mode** (`local_ai`) - Enhanced Local Processing
- **Transcription**: Local Whisper (OpenAI)
- **Guide Generation**: Local AI via Ollama (Llama2, Mistral, etc.)
- **Cost**: $0.00 (completely free)
- **Privacy**: 100% local processing
- **Requirements**: Ollama server running locally
- **Use Case**: High-quality guides without API costs

#### **3. API Transcription Mode** (`api_transcription`) - Hybrid Transcription
- **Transcription**: API-based (OpenRouter/OpenAI)
- **Guide Generation**: Template-based processing
- **Cost**: ~$0.006 per minute of audio
- **Use Case**: Better transcription quality with template guides

#### **4. API Generation Mode** (`api_generation`) - Hybrid Guide Generation
- **Transcription**: Local Whisper (OpenAI)
- **Guide Generation**: API-based (OpenRouter/OpenAI)
- **Cost**: ~$0.01-0.05 per guide
- **Use Case**: Local transcription with professional guide quality

#### **5. Full API Mode** (`full_api`) - Complete API Processing
- **Transcription**: API-based (OpenRouter/OpenAI)
- **Guide Generation**: API-based (OpenRouter/OpenAI)
- **Cost**: ~$0.02-0.08 per video
- **Use Case**: Highest quality processing for critical content

#### **6. Hybrid Mode** (`hybrid`) - Intelligent Fallback
- **Fallback Chain**: API → Local AI → Template
- **Automatic Degradation**: Ensures processing always completes
- **Cost**: Variable (depends on successful fallback level)
- **Use Case**: Best reliability with quality optimization

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

## 📋 Prerequisites

### **Core Requirements (All Modes)**
- **Python 3.8+** - Check with `python3 --version`
- **FFmpeg** - Install with `sudo apt install ffmpeg` (Ubuntu) or `brew install ffmpeg` (macOS)
- **4GB+ RAM** - For Whisper model processing
- **Git** - For cloning the repository

### **Mode-Specific Requirements**

#### **Basic Mode** - No additional requirements

#### **Local AI Mode**
- **Ollama Server** - Install from [ollama.ai](https://ollama.ai)
- **8GB+ RAM** - For running local LLM models
- **Model Download** - `ollama pull llama2:7b-chat` (or preferred model)

#### **API Modes**
- **API Key** - OpenRouter (recommended) or OpenAI account
- **Internet Connection** - For API calls
- **Environment Variables** - Set in `.env` file

#### **Hybrid Mode**
- **All of the above** - For complete fallback capability

### **Optional Enhancements**
- **NVIDIA GPU** - For faster local transcription (auto-detected)
- **16GB+ RAM** - For larger Whisper + LLM models simultaneously

## 🚀 Quick Start

### 1. Basic Setup (All Modes)

```bash
# Clone and setup everything
git clone https://github.com/mik-tf/video-to-guide-pipeline.git
cd video-to-guide-pipeline
make setup

# Copy configuration template
cp config/default.yaml.example config/default.yaml
cp .env.example .env
```

**That's it for basic mode!** The Makefile handles:
- Virtual environment creation
- Python dependency installation
- System dependency verification
- Configuration file setup

### 2. Mode-Specific Setup

#### **For Local AI Mode**
```bash
# Install Ollama (one-time setup)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve &

# Download a model (choose one)
ollama pull llama2:7b-chat      # Recommended: Good balance
ollama pull mistral:7b          # Alternative: Fast and capable
ollama pull codellama:7b        # For technical content
```

#### **For API Modes**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your API key
# Option 1: OpenRouter (recommended - cost-effective)
OPENROUTER_API_KEY=your_key_here

# Option 2: OpenAI (direct)
OPENAI_API_KEY=your_key_here
```

**Get API Keys:**
- **OpenRouter**: Sign up at [openrouter.ai](https://openrouter.ai) (recommended)
- **OpenAI**: Sign up at [platform.openai.com](https://platform.openai.com)

### 3. Process Videos with Different Modes

#### **Basic Mode (Template Processing)**
```bash
# Add videos to ./videos directory
cp ~/my-tutorial.mp4 videos/

# Process with basic template mode
make process-basic

# Or process single video
make process-single VIDEO=videos/tutorial.mp4
```

#### **Local AI Mode (Best Quality, No Cost)**
```bash
# Ensure Ollama is running
ollama serve &

# Process with local AI
make process-local-ai

# Or single video with local AI
make process-single VIDEO=videos/tutorial.mp4 MODE=local_ai
```

#### **API Modes (Professional Quality)**
```bash
# Ensure API key is set in .env file

# API transcription + template guide
make process-api-trans

# Local transcription + API guide generation
make process-api-gen

# Full API processing (highest quality)
make process-full-api
```

#### **Hybrid Mode (Best Reliability)**
```bash
# Automatic fallback: API → Local AI → Template
make process-hybrid

# This mode ensures processing always completes
# with the best quality possible given available resources
```

#### **Check Results**
```bash
# View generated guides
ls output/guides/

# View processing logs
tail -f logs/pipeline.log
```

## 🛠️ Makefile Commands

### **Setup & Dependencies**
| Command | Description |
|---------|-------------|
| `make setup` | **Complete setup** - Creates venv, installs dependencies, sets up directories |
| `make info` | **System status** - Shows AI capabilities, API config, available modes |
| `make check-deps` | **Check system dependencies** (Python, FFmpeg, GPU) |
| `make clean` | **Clean output files** (keeps venv) |
| `make clean-all` | **Clean everything** including venv |

### **Processing Modes**
| Command | Description | Requirements |
|---------|-------------|-------------|
| `make process-basic` | **Template processing** (original) | None |
| `make process-local-ai` | **Local AI processing** with Ollama | Ollama server |
| `make process-api-trans` | **API transcription** + template guide | API key |
| `make process-api-gen` | **Local transcription** + API guide | API key |
| `make process-full-api` | **Full API processing** (highest quality) | API key |
| `make process-hybrid` | **Hybrid with fallbacks** (best reliability) | Optional: API key + Ollama |

### **Legacy/Utilities**
| Command | Description |
|---------|-------------|
| `make process-videos` | **Process all videos** (basic mode) |
| `make process-single VIDEO=path.mp4` | **Process single video** |
| `make process-single VIDEO=path.mp4 MODE=local_ai` | **Process single video** with specific mode |
| `make demo` | **Interactive demo** with examples |
| `make help` | **Show all commands** with examples |

### Usage Examples

#### **Quick Start (Basic Mode)**
```bash
# First time setup
make setup

# Add videos to ./videos/ directory
cp ~/my-tutorial.mp4 videos/

# Process with template mode (free)
make process-basic

# Check results
ls output/guides/
```

#### **High Quality Processing**
```bash
# Setup Ollama for local AI
ollama serve &
ollama pull llama2:7b-chat

# Process with local AI (free, high quality)
make process-local-ai

# Or use API for best quality (requires API key)
make process-full-api
```

#### **Reliable Processing**
```bash
# Hybrid mode with automatic fallbacks
# Will try API → Local AI → Template until success
make process-hybrid

# Single video with specific mode
make process-single VIDEO=videos/tutorial.mp4 MODE=hybrid
```

#### **Monitoring and Debugging**
```bash
# Watch processing logs in real-time
tail -f logs/pipeline.log

# Check system status
make check-deps

# View all available commands
make help
```

## 📁 Project Structure

```
video-to-guide-pipeline/
├── README.md                    # This file
├── Makefile                     # 🎯 Main entry point - all commands
├── requirements.txt             # Python dependencies
├── .gitignore                  # Git ignore rules
├── .env.example                # Environment variables template
├── docker-compose.yml          # Docker setup
├── Dockerfile                  # Container definition
│
├── config/
│   ├── default.yaml.example    # Configuration template
│   └── default.yaml            # Your local config (git-ignored)
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

## 🎯 Mode Selection Guide

### **Which Mode Should I Use?**

#### **For Learning/Testing**
- **Basic Mode** (`make process-basic`)
  - ✅ Free and fast
  - ✅ No setup required
  - ❌ Basic quality output
  - **Best for**: Quick tests, learning the pipeline

#### **For Regular Use**
- **Local AI Mode** (`make process-local-ai`)
  - ✅ Free after setup
  - ✅ High quality output
  - ✅ Complete privacy
  - ❌ Requires Ollama setup
  - **Best for**: Regular processing, privacy-conscious users

#### **For Professional Content**
- **Hybrid Mode** (`make process-hybrid`)
  - ✅ Best reliability (always completes)
  - ✅ Automatic quality optimization
  - ✅ Fallback to free options
  - ❌ May incur API costs
  - **Best for**: Important content, production use

- **Full API Mode** (`make process-full-api`)
  - ✅ Highest quality output
  - ✅ Professional transcription
  - ❌ Requires API key and costs money
  - **Best for**: Critical documentation, client work

### **Cost Comparison**

| Mode | Transcription Cost | Guide Generation Cost | Total per Hour |
|------|-------------------|----------------------|----------------|
| **Basic** | $0.00 | $0.00 | **$0.00** |
| **Local AI** | $0.00 | $0.00 | **$0.00** |
| **API Trans** | ~$0.36 | $0.00 | **~$0.36** |
| **API Gen** | $0.00 | ~$0.02 | **~$0.02** |
| **Full API** | ~$0.36 | ~$0.02 | **~$0.38** |
| **Hybrid** | Variable | Variable | **$0.00-$0.38** |

*Costs based on OpenRouter pricing for 1 hour of video content*

### **Quality Hierarchy** (Best to Basic)

| Rank | Mode | Transcription | Guide Generation | Cost/Hour | Best For |
|------|------|---------------|------------------|-----------|----------|
| **🥇 1st** | **Full API** | **Excellent** | **Excellent** | ~$0.38 | Critical documentation, client work |
| **🥈 2nd** | **Hybrid** | **Best Available** | **Best Available** | $0.00-$0.38 | Production use, important content |
| **🥉 3rd** | **Local AI** | Good | **Excellent** | $0.00 | Regular processing, privacy-focused |
| **4th** | **Basic** | Good | Basic | $0.00 | Quick tests, learning |

### **Quality Comparison by Aspect**

| Aspect | Basic | Local AI | **Full API** | Hybrid |
|--------|-------|----------|-------------|--------|
| **Transcription** | Good | Good | **Excellent** | **Best Available** |
| **Guide Structure** | Basic | Excellent | **Excellent** | **Best Available** |
| **Technical Terms** | Poor | Good | **Excellent** | **Best Available** |
| **Error Correction** | None | Good | **Excellent** | **Best Available** |
| **Consistency** | High | High | **Highest** | **Highest** |

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

## 📚 Usage Examples

### Process a Single Video
```bash
# Simple single video processing
make process-single VIDEO=videos/tutorial.mp4

# Or activate venv and use Python directly
source venv/bin/activate
python scripts/process_videos.py --input videos/tutorial.mp4
```

### Batch Process Multiple Videos
```bash
# Process all videos in ./videos directory
make process-videos

# Check system before processing
make check-deps
make process-videos
```

### Advanced Usage
```bash
# Interactive demo with examples
make demo

# Clean previous results and reprocess
make clean
make process-videos

# Check what's available
make help
```

## 🎯 Use Cases

- **📚 Technical Documentation** - Convert deployment videos into step-by-step guides
- **🎓 Training Materials** - Transform training videos into searchable documentation
- **📋 Process Documentation** - Document complex procedures from video demonstrations
- **🔄 Knowledge Transfer** - Preserve institutional knowledge from video content
- **📝 Content Repurposing** - Convert video content into multiple documentation formats

## 🔧 Troubleshooting

### Common Issues

**❌ "FFmpeg not found"**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Verify installation
ffmpeg -version
```

**❌ "Python 3.8+ required"**
```bash
# Check current version
python3 --version

# Ubuntu: Install newer Python
sudo apt install python3.9 python3.9-venv
```

**❌ "No videos found"**
```bash
# Check videos directory
ls -la videos/

# Copy videos to correct location
cp ~/Downloads/*.mp4 videos/
```

**❌ "Virtual environment issues"**
```bash
# Clean and recreate
make clean-all
make setup
```

**❌ "Out of memory during processing"**
```bash
# Use smaller Whisper model
# Edit config/default.yaml:
# model_name: "tiny"  # or "base"
```

### Getting Help

```bash
# Check system status
make check-deps

# Show all available commands
make help

# Run interactive demo
make demo
```

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
# Build Docker image
make docker-build

# Run with Docker (processes videos/ directory)
make docker-run

# Or use docker-compose
docker-compose up --build
```

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI Whisper** - For excellent speech recognition capabilities
- **FFmpeg** - For robust audio/video processing