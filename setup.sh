#!/bin/bash

# AllInApp Setup Script
# This script installs all dependencies and sets up Whisper.cpp

set -e

echo "===== AllInApp Setup Script ====="
echo "Setting up podcast processing pipeline..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m pip install --user -r requirements.txt

# Download spaCy English model
echo "Downloading spaCy English model..."
python3 -m spacy download en_core_web_sm

# Clone and compile Whisper.cpp if not already present
if [ ! -d "whisper.cpp" ]; then
    echo "Cloning Whisper.cpp..."
    git clone https://github.com/ggerganov/whisper.cpp.git
fi

if [ ! -f "whisper.cpp/build/bin/whisper-cli" ]; then
    echo "Compiling Whisper.cpp..."
    cd whisper.cpp
    make
    cd ..
fi

echo "✓ Whisper.cpp compiled successfully"

# Create models directory and download Whisper model
mkdir -p models
if [ ! -f "models/ggml-base.en.bin" ]; then
    echo "Downloading Whisper base English model (141MB)..."
    curl -L https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin -o models/ggml-base.en.bin
fi

echo "✓ Whisper model downloaded"

# Create data directory
mkdir -p data

echo ""
echo "===== Setup Complete ====="
echo "✓ Python dependencies installed"
echo "✓ spaCy English model downloaded"
echo "✓ Whisper.cpp compiled"
echo "✓ Whisper base English model downloaded"
echo "✓ Directory structure created"
echo ""
echo "You can now run the pipeline with: python3 main.py"
echo ""
