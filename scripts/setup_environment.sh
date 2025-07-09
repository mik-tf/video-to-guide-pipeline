#!/bin/bash

# Video-to-Guide Pipeline Environment Setup Script
# This script sets up the complete environment for the video-to-guide pipeline

set -e  # Exit on any error

echo "🚀 Setting up Video-to-Guide Pipeline Environment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from correct directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check Python version
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.8"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_success "Python $python_version is compatible"
else
    print_error "Python 3.8+ is required. Found: $python_version"
    exit 1
fi

# Check for FFmpeg
print_status "Checking FFmpeg installation..."
if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg_version=$(ffmpeg -version 2>&1 | head -n1 | cut -d' ' -f3)
    print_success "FFmpeg $ffmpeg_version found"
else
    print_error "FFmpeg is not installed or not in PATH"
    print_status "Please install FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: Download from https://ffmpeg.org/download.html"
    exit 1
fi

# Create virtual environment
print_status "Creating Python virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        print_success "Virtual environment recreated"
    else
        print_status "Using existing virtual environment"
    fi
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install PyTorch (CPU version by default)
print_status "Installing PyTorch..."
if command -v nvidia-smi >/dev/null 2>&1; then
    print_status "NVIDIA GPU detected, installing CUDA version of PyTorch..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
else
    print_status "Installing CPU version of PyTorch..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install requirements
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Create directory structure
print_status "Creating project directory structure..."
mkdir -p videos
mkdir -p output/{audio,transcriptions,guides}
mkdir -p logs
mkdir -p tmp

# Copy example configuration if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "Created .env file from template"
        print_warning "Please edit .env file with your specific settings"
    fi
fi

# Create example template if templates directory is empty
if [ ! "$(ls -A templates/ 2>/dev/null)" ]; then
    print_status "Creating example template..."
    cat > templates/deployment_guide.md << 'EOF'
# {{ title }}

*Generated on {{ metadata.generated_date }}*

## Introduction

{{ introduction }}

{% if prerequisites %}
## Prerequisites

{% for prereq in prerequisites %}
- {{ prereq }}
{% endfor %}
{% endif %}

## Steps

{% for section in sections %}
### {{ section.title }}

{{ section.content }}

{% endfor %}

{% if commands %}
## Commands Reference

{% for command in commands %}
```bash
{{ command }}
```

{% endfor %}
{% endif %}

{% if troubleshooting %}
## Troubleshooting

{% for item in troubleshooting %}
**Issue:** {{ item.issue }}

**Solution:** {{ item.solution }}

{% endfor %}
{% endif %}

---

*This guide was automatically generated from video content using the Video-to-Guide Pipeline.*  
*Estimated reading time: {{ metadata.estimated_reading_time }} minutes*
EOF
    print_success "Created example deployment guide template"
fi

# Test the installation
print_status "Testing installation..."
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from audio_extractor import AudioExtractor
    from transcriber import Transcriber
    from guide_generator import GuideGenerator
    from utils import load_config, validate_dependencies
    print('✅ All modules imported successfully')
    
    deps = validate_dependencies()
    print('📦 Dependency Status:')
    for dep, status in deps.items():
        status_text = '✅ Available' if status else '❌ Missing'
        print(f'  {dep}: {status_text}')
        
except Exception as e:
    print(f'❌ Import test failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_success "Installation test passed"
else
    print_error "Installation test failed"
    exit 1
fi

# Create activation script
cat > activate.sh << 'EOF'
#!/bin/bash
# Activation script for Video-to-Guide Pipeline

echo "🎬 Activating Video-to-Guide Pipeline Environment"
source venv/bin/activate
echo "✅ Environment activated"
echo ""
echo "Available commands:"
echo "  python scripts/process_videos.py --help    # Show help"
echo "  python scripts/process_videos.py --system-info  # Check system"
echo ""
echo "Example usage:"
echo "  python scripts/process_videos.py --input videos/my_video.mp4"
echo "  python scripts/process_videos.py --batch --input videos/"
EOF

chmod +x activate.sh

print_success "Setup completed successfully!"
echo ""
echo "🎉 Video-to-Guide Pipeline is ready to use!"
echo ""
echo "Next steps:"
echo "1. Place your video files in the 'videos/' directory"
echo "2. Activate the environment: source activate.sh"
echo "3. Process videos: python scripts/process_videos.py --input videos/your_video.mp4"
echo ""
echo "For help: python scripts/process_videos.py --help"
echo "For system info: python scripts/process_videos.py --system-info"
