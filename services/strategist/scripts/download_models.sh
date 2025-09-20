#!/bin/bash

# Download Models Script for Strategist Service
# Downloads the all-MiniLM-L6-v2 sentence transformer model
# Expected size: approximately 2.8GB

echo "Starting model download for Strategist Service..."
echo "Model: sentence-transformers/all-MiniLM-L6-v2 (~2.8GB)"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS_DIR="$SCRIPT_DIR/../models"

# Create models directory if it doesn't exist
if [ ! -d "$MODELS_DIR" ]; then
    echo "Creating models directory: $MODELS_DIR"
    mkdir -p "$MODELS_DIR"
fi

# Activate virtual environment if it exists
VENV_PATH="$SCRIPT_DIR/../venv"
if [ -d "$VENV_PATH" ]; then
    echo "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
else
    echo "Warning: Virtual environment not found at $VENV_PATH"
    echo "Please ensure dependencies are installed in your active Python environment"
fi

# Create temporary Python script to download model
TEMP_PYTHON_FILE="$SCRIPT_DIR/temp_download_model.py"

cat > "$TEMP_PYTHON_FILE" << 'EOF'
import os
import sys
from sentence_transformers import SentenceTransformer

def download_model():
    model_name = 'all-MiniLM-L6-v2'
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')

    print(f'Downloading model: {model_name}')
    print(f'Target directory: {os.path.abspath(models_dir)}')

    try:
        # Download and cache the model
        print('Initializing SentenceTransformer (this will download the model)...')
        model = SentenceTransformer(model_name, cache_folder=models_dir)

        # Test the model with a simple encoding
        print('Testing model with sample text...')
        test_sentences = ['This is a test sentence.', 'Machine learning is fascinating.']
        embeddings = model.encode(test_sentences)

        print(f'Model downloaded successfully!')
        print(f'Model dimensions: {embeddings.shape}')
        print(f'Model name: {model_name}')
        print(f'Cache directory: {models_dir}')

        return True

    except Exception as e:
        print(f'Error downloading model: {str(e)}')
        return False

if __name__ == '__main__':
    success = download_model()
    sys.exit(0 if success else 1)
EOF

# Run the Python script
echo "Executing model download..."
python "$TEMP_PYTHON_FILE"
EXIT_CODE=$?

# Clean up temp file
rm -f "$TEMP_PYTHON_FILE"

if [ $EXIT_CODE -eq 0 ]; then
    echo "Model download completed successfully!"
else
    echo "Model download failed with exit code: $EXIT_CODE"
    exit $EXIT_CODE
fi

echo "Model download script completed."
