#!/bin/bash

# Analyst Service Model Download Script
# Downloads required spaCy models for the Helios Career Operations System

set -e

echo "=== Analyst Service Model Download ==="
echo "Downloading required spaCy models..."

# Check if Python and pip are available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "Error: pip is not installed or not in PATH"
    exit 1
fi

# Download spaCy en_core_web_sm model
echo "Downloading spaCy en_core_web_sm model..."
python -m spacy download en_core_web_sm

# Verify the model was downloaded successfully
echo "Verifying model installation..."
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('SUCCESS: en_core_web_sm model loaded successfully')"

echo "SUCCESS: All models downloaded successfully!"
echo "Analyst service is ready for NLP processing."
