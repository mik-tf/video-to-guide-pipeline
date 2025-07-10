# Video-to-Guide Pipeline Makefile
# Handles virtual environment setup, dependencies, and common tasks

.PHONY: help setup install clean test run demo process-videos process-basic process-local-ai process-api-trans process-api-gen process-full-api process-hybrid check-deps info activate _check_videos

# Default target
help:
	@echo "🎬 Video-to-Guide Pipeline"
	@echo "=========================="
	@echo ""
	@echo "Setup & Dependencies:"
	@echo "  setup          - Complete environment setup (venv + dependencies)"
	@echo "  install        - Install dependencies in existing venv"
	@echo "  check-deps     - Check system dependencies"
	@echo ""
	@echo "Processing Modes:"
	@echo "  process-basic     - Template-based processing (default)"
	@echo "  process-local-ai  - Local AI with Ollama"
	@echo "  process-api-trans - API transcription + template guide"
	@echo "  process-api-gen   - Template transcription + API guide"
	@echo "  process-full-api  - Full API (transcription + guide)"
	@echo "  process-hybrid    - Hybrid with fallback chain"
	@echo ""
	@echo "Legacy/Batch:"
	@echo "  process-videos - Process all videos (basic mode)"
	@echo "  process-single - Process single video (VIDEO=path/to/video.mp4)"
	@echo ""
	@echo "Other:"
	@echo "  demo           - Run interactive demo"
	@echo "  test           - Run tests"
	@echo "  clean          - Clean up generated files"
	@echo "  clean-all      - Clean everything including venv"
	@echo "  info           - Show system information"
	@echo ""
	@echo "Examples:"
	@echo "  make setup                    # First-time setup"
	@echo "  make process-local-ai         # Process with Ollama AI"
	@echo "  make process-hybrid           # Best quality with fallbacks"
	@echo "  make process-single VIDEO=videos/demo.mp4 MODE=local_ai"
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
	
	# Copy config file
	@if [ ! -f "config/default.yaml" ] && [ -f "config/default.yaml.example" ]; then \
		cp config/default.yaml.example config/default.yaml; \
		echo "📄 Created config/default.yaml from template"; \
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

# Process all videos in ./videos directory (basic mode)
process-videos: check-venv
	@echo "🎬 Processing all videos (basic mode)..."
	@if [ ! -d "videos" ] || [ -z "$$(ls -A videos/ 2>/dev/null)" ]; then \
		echo "❌ No videos found in ./videos directory"; \
		echo "   Place video files in ./videos/ and try again"; \
		exit 1; \
	fi
	@echo "📹 Found videos:"
	@ls -la videos/
	@echo ""
	@cd $(shell pwd) && $(VENV_PYTHON) scripts/process_videos.py --batch --input videos/ --mode basic
	@echo ""
	@echo "✅ Processing complete! Check ./output/guides/ for results"

# Processing mode targets
process-basic: check-venv
	@echo "🎬 Processing videos with template-based generation..."
	@$(MAKE) _check_videos
	@cd $(shell pwd) && $(VENV_PYTHON) scripts/process_videos.py --batch --input videos/ --mode basic
	@echo "✅ Basic processing complete!"

process-local-ai: check-venv
	@echo "🤖 Processing videos with local AI (Ollama)..."
	@echo "Note: Requires Ollama server running locally"
	@$(MAKE) _check_videos
	@cd $(shell pwd) && $(VENV_PYTHON) scripts/process_videos.py --batch --input videos/ --mode local_ai
	@echo "✅ Local AI processing complete!"

process-api-trans: check-venv
	@echo "🌐 Processing videos with API transcription + template guide..."
	@echo "Note: Requires API key in .env file"
	@$(MAKE) _check_videos
	@cd $(shell pwd) && $(VENV_PYTHON) scripts/process_videos.py --batch --input videos/ --mode api_transcription
	@echo "✅ API transcription processing complete!"

process-api-gen: check-venv
	@echo "🌐 Processing videos with local transcription + API guide generation..."
	@echo "Note: Requires API key in .env file"
	@$(MAKE) _check_videos
	@cd $(shell pwd) && $(VENV_PYTHON) scripts/process_videos.py --batch --input videos/ --mode api_generation
	@echo "✅ API guide generation processing complete!"

process-full-api: check-venv
	@echo "🌐 Processing videos with full API (transcription + guide generation)..."
	@echo "Note: Requires API key in .env file"
	@$(MAKE) _check_videos
	@cd $(shell pwd) && $(VENV_PYTHON) scripts/process_videos.py --batch --input videos/ --mode full_api
	@echo "✅ Full API processing complete!"

process-hybrid: check-venv
	@echo "🔄 Processing videos with hybrid mode (API → Local AI → Template fallback)..."
	@echo "Note: Best quality with automatic fallbacks"
	@$(MAKE) _check_videos
	@cd $(shell pwd) && $(VENV_PYTHON) scripts/process_videos.py --batch --input videos/ --mode hybrid
	@echo "✅ Hybrid processing complete!"

# Helper target to check for videos
_check_videos:
	@if [ ! -d "videos" ] || [ -z "$$(ls -A videos/ 2>/dev/null)" ]; then \
		echo "❌ No videos found in ./videos directory"; \
		echo "   Place video files in ./videos/ and try again"; \
		exit 1; \
	fi
	@echo "📹 Found videos:"
	@ls -la videos/
	@echo ""

# Process single video
process-single: check-venv
	@if [ -z "$(VIDEO)" ]; then \
		echo "❌ Please specify VIDEO=path/to/video.mp4"; \
		echo "   Example: make process-single VIDEO=videos/demo.mp4"; \
		echo "   With mode: make process-single VIDEO=videos/demo.mp4 MODE=local_ai"; \
		exit 1; \
	fi
	@if [ ! -f "$(VIDEO)" ]; then \
		echo "❌ Video file not found: $(VIDEO)"; \
		exit 1; \
	fi
	@if [ -n "$(MODE)" ]; then \
		echo "🎬 Processing video: $(VIDEO) (mode: $(MODE))"; \
		cd $(shell pwd) && $(VENV_PYTHON) scripts/process_videos.py --input "$(VIDEO)" --mode "$(MODE)"; \
	else \
		echo "🎬 Processing video: $(VIDEO) (basic mode)"; \
		cd $(shell pwd) && $(VENV_PYTHON) scripts/process_videos.py --input "$(VIDEO)"; \
	fi
	@echo "✅ Processing complete!"

# Run tests
test: check-venv
	@echo "🧪 Running tests..."
	@cd $(shell pwd) && $(VENV_PYTHON) -m pytest tests/ -v

# Show system information and processing mode status
info:
	@echo "📊 Video-to-Guide Pipeline System Information"
	@echo "============================================="
	@echo ""
	@echo "💻 System Status:"
	@python3 --version 2>/dev/null || echo "  ❌ Python 3 not found"
	@ffmpeg -version 2>/dev/null | head -1 || echo "  ❌ FFmpeg not found"
	@if [ -d "venv" ]; then echo "  ✅ Virtual environment exists"; else echo "  ❌ Virtual environment missing"; fi
	@echo ""
	@echo "🤖 AI Processing Capabilities:"
	@if command -v ollama >/dev/null 2>&1; then \
		echo "  ✅ Ollama installed"; \
		if pgrep -f "ollama serve" >/dev/null; then \
			echo "  ✅ Ollama server running"; \
			ollama list 2>/dev/null | grep -v "NAME" | head -3 | sed 's/^/    - /' || echo "    No models installed"; \
		else \
			echo "  ⚠️  Ollama server not running (run: ollama serve)"; \
		fi; \
	else \
		echo "  ❌ Ollama not installed (local AI unavailable)"; \
	fi
	@echo ""
	@echo "🌐 API Configuration:"
	@if [ -f ".env" ]; then \
		echo "  ✅ .env file exists"; \
		if grep -q "OPENROUTER_API_KEY=" .env && ! grep -q "OPENROUTER_API_KEY=your_" .env; then \
			echo "  ✅ OpenRouter API key configured"; \
		else \
			echo "  ❌ OpenRouter API key not configured"; \
		fi; \
		if grep -q "OPENAI_API_KEY=" .env && ! grep -q "OPENAI_API_KEY=your_" .env; then \
			echo "  ✅ OpenAI API key configured"; \
		else \
			echo "  ❌ OpenAI API key not configured"; \
		fi; \
	else \
		echo "  ❌ .env file missing (copy from .env.example)"; \
	fi
	@echo ""
	@echo "📹 Available Processing Modes:"
	@echo "  ✅ Basic Mode (template processing)"
	@if command -v ollama >/dev/null 2>&1 && pgrep -f "ollama serve" >/dev/null; then \
		echo "  ✅ Local AI Mode (Ollama)"; \
	else \
		echo "  ❌ Local AI Mode (requires Ollama)"; \
	fi
	@if [ -f ".env" ] && (grep -q "OPENROUTER_API_KEY=" .env || grep -q "OPENAI_API_KEY=" .env) && ! grep -q "your_" .env; then \
		echo "  ✅ API Modes (transcription/generation)"; \
		echo "  ✅ Hybrid Mode (with fallbacks)"; \
	else \
		echo "  ❌ API Modes (requires API key)"; \
		echo "  ⚠️  Hybrid Mode (limited fallback)"; \
	fi
	@echo ""
	@echo "📁 Directories:"
	@if [ -d "videos" ]; then \
		echo "  ✅ videos/ directory: $$(ls videos/ 2>/dev/null | wc -l) files"; \
	else \
		echo "  ❌ videos/ directory missing"; \
	fi
	@if [ -d "output" ]; then \
		echo "  ✅ output/ directory exists"; \
	else \
		echo "  ❌ output/ directory missing"; \
	fi
	@echo ""
	@echo "Run 'make help' for available commands"

# Clean up generated files
clean:
	@echo "🧹 Cleaning up generated files..."
	@rm -rf output/audio/* output/transcriptions/* output/guides/* tmp/* 2>/dev/null || true
	@echo "✅ Cleanup complete"

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

# Activate virtual environment (helper)
activate:
	@echo "To activate the virtual environment, run:"
	@echo "  source $(VENV_BIN)/activate"
