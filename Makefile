# Video-to-Guide Pipeline Makefile
# Handles virtual environment setup, dependencies, and common tasks

.PHONY: help setup install clean test run demo process-videos check-deps docker-build docker-run

# Default target
help:
	@echo "🎬 Video-to-Guide Pipeline"
	@echo "=========================="
	@echo ""
	@echo "Available targets:"
	@echo "  setup          - Complete environment setup (venv + dependencies)"
	@echo "  install        - Install dependencies in existing venv"
	@echo "  check-deps     - Check system dependencies"
	@echo "  demo           - Run interactive demo"
	@echo "  process-videos - Process all videos in ./videos directory"
	@echo "  process-single - Process single video (VIDEO=path/to/video.mp4)"
	@echo "  test           - Run tests"
	@echo "  clean          - Clean up generated files"
	@echo "  clean-all      - Clean everything including venv"
	@echo "  docker-build   - Build Docker image"
	@echo "  docker-run     - Run in Docker container"
	@echo ""
	@echo "Examples:"
	@echo "  make setup                    # First-time setup"
	@echo "  make process-videos           # Process all videos"
	@echo "  make process-single VIDEO=videos/demo.mp4"
	@echo ""

# Python and virtual environment settings
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

# Check if we're in a virtual environment
check-venv:
	@if [ -z "$$VIRTUAL_ENV" ] && [ ! -f "$(VENV_BIN)/activate" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi

# Complete setup: create venv, install dependencies, create directories
setup:
	@echo "🚀 Setting up Video-to-Guide Pipeline..."
	@echo "========================================"
	
	# Check Python version
	@$(PYTHON) -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" || \
		(echo "❌ Python 3.8+ required" && exit 1)
	@echo "✅ Python version OK"
	
	# Check FFmpeg
	@command -v ffmpeg >/dev/null 2>&1 || \
		(echo "❌ FFmpeg not found. Install with: sudo apt install ffmpeg" && exit 1)
	@echo "✅ FFmpeg found"
	
	# Create virtual environment
	@if [ ! -d "$(VENV)" ]; then \
		echo "📦 Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
	else \
		echo "📦 Virtual environment already exists"; \
	fi
	
	# Upgrade pip
	@echo "⬆️  Upgrading pip..."
	@$(VENV_PIP) install --upgrade pip
	
	# Install PyTorch (detect GPU)
	@echo "🔥 Installing PyTorch..."
	@if command -v nvidia-smi >/dev/null 2>&1; then \
		echo "🎮 NVIDIA GPU detected - installing CUDA version"; \
		$(VENV_PIP) install torch torchaudio --index-url https://download.pytorch.org/whl/cu118; \
	else \
		echo "💻 Installing CPU version"; \
		$(VENV_PIP) install torch torchaudio --index-url https://download.pytorch.org/whl/cpu; \
	fi
	
	# Install other dependencies
	@echo "📚 Installing dependencies..."
	@$(VENV_PIP) install -r requirements.txt
	
	# Create directory structure
	@echo "📁 Creating directories..."
	@mkdir -p videos output/{audio,transcriptions,guides} logs tmp
	
	# Copy environment file
	@if [ ! -f ".env" ] && [ -f ".env.example" ]; then \
		cp .env.example .env; \
		echo "📄 Created .env file from template"; \
	fi
	
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Activate environment: source $(VENV_BIN)/activate"
	@echo "  2. Place videos in ./videos/ directory"
	@echo "  3. Run: make process-videos"

# Install dependencies only (assumes venv exists)
install: check-venv
	@echo "📚 Installing dependencies..."
	@$(VENV_PIP) install --upgrade pip
	@$(VENV_PIP) install -r requirements.txt
	@echo "✅ Dependencies installed"

# Check system dependencies
check-deps:
	@echo "🔍 Checking dependencies..."
	@echo "=========================="
	
	# Python version
	@$(PYTHON) --version
	@$(PYTHON) -c "import sys; print('✅ Python version OK' if sys.version_info >= (3, 8) else '❌ Python 3.8+ required')"
	
	# FFmpeg
	@if command -v ffmpeg >/dev/null 2>&1; then \
		echo "✅ FFmpeg: $$(ffmpeg -version 2>&1 | head -n1 | cut -d' ' -f3)"; \
	else \
		echo "❌ FFmpeg not found"; \
	fi
	
	# GPU check
	@if command -v nvidia-smi >/dev/null 2>&1; then \
		echo "🎮 NVIDIA GPU detected"; \
		nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1; \
	else \
		echo "💻 CPU processing (no GPU detected)"; \
	fi
	
	# Python packages (if venv exists)
	@if [ -f "$(VENV_BIN)/python" ]; then \
		echo ""; \
		echo "📦 Python packages:"; \
		$(VENV_PYTHON) -c "import whisper; print('✅ whisper')" 2>/dev/null || echo "❌ whisper"; \
		$(VENV_PYTHON) -c "import torch; print('✅ torch')" 2>/dev/null || echo "❌ torch"; \
		$(VENV_PYTHON) -c "import ffmpeg; print('✅ ffmpeg-python')" 2>/dev/null || echo "❌ ffmpeg-python"; \
		$(VENV_PYTHON) -c "import yaml; print('✅ yaml')" 2>/dev/null || echo "❌ yaml"; \
		$(VENV_PYTHON) -c "import jinja2; print('✅ jinja2')" 2>/dev/null || echo "❌ jinja2"; \
	fi

# Run interactive demo
demo: check-venv
	@echo "🎯 Running interactive demo..."
	@cd $(shell pwd) && $(VENV_PYTHON) scripts/demo.py --interactive

# Process all videos in ./videos directory
process-videos: check-venv
	@echo "🎬 Processing all videos..."
	@if [ ! -d "videos" ] || [ -z "$$(ls -A videos/ 2>/dev/null)" ]; then \
		echo "❌ No videos found in ./videos directory"; \
		echo "   Place video files in ./videos/ and try again"; \
		exit 1; \
	fi
	@echo "📹 Found videos:"
	@ls -la videos/
	@echo ""
	@cd $(shell pwd) && $(VENV_PYTHON) scripts/process_videos.py --batch --input videos/
	@echo ""
	@echo "✅ Processing complete! Check ./output/guides/ for results"

# Process single video
process-single: check-venv
	@if [ -z "$(VIDEO)" ]; then \
		echo "❌ Please specify VIDEO=path/to/video.mp4"; \
		echo "   Example: make process-single VIDEO=videos/demo.mp4"; \
		exit 1; \
	fi
	@if [ ! -f "$(VIDEO)" ]; then \
		echo "❌ Video file not found: $(VIDEO)"; \
		exit 1; \
	fi
	@echo "🎬 Processing video: $(VIDEO)"
	@cd $(shell pwd) && $(VENV_PYTHON) scripts/process_videos.py --input "$(VIDEO)"
	@echo "✅ Processing complete!"

# Run tests
test: check-venv
	@echo "🧪 Running tests..."
	@cd $(shell pwd) && $(VENV_PYTHON) -m pytest tests/ -v

# Clean generated files
clean:
	@echo "🧹 Cleaning generated files..."
	@rm -rf output/audio/* output/transcriptions/* output/guides/*
	@rm -rf logs/*
	@rm -rf tmp/*
	@echo "✅ Cleaned output directories"

# Clean everything including virtual environment
clean-all: clean
	@echo "🧹 Cleaning everything..."
	@rm -rf $(VENV)
	@rm -rf __pycache__ src/__pycache__ scripts/__pycache__ tests/__pycache__
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@echo "✅ Cleaned everything"

# Docker targets
docker-build:
	@echo "🐳 Building Docker image..."
	@docker build -t video-to-guide-pipeline .

docker-run:
	@echo "🐳 Running in Docker..."
	@docker run -it --rm \
		-v $(shell pwd)/videos:/app/videos \
		-v $(shell pwd)/output:/app/output \
		video-to-guide-pipeline \
		python scripts/process_videos.py --batch --input videos/

# Show system info
info: check-venv
	@cd $(shell pwd) && $(VENV_PYTHON) scripts/process_videos.py --system-info

# Activate virtual environment (helper)
activate:
	@echo "To activate the virtual environment, run:"
	@echo "  source $(VENV_BIN)/activate"
