#!/usr/bin/env powershell

# Download Models Script for Strategist Service
# Downloads the all-MiniLM-L6-v2 sentence transformer model
# Expected size: approximately 2.8GB

Write-Host "Starting model download for Strategist Service..." -ForegroundColor Green
Write-Host "Model: sentence-transformers/all-MiniLM-L6-v2 (~2.8GB)" -ForegroundColor Yellow

# Create models directory if it doesn't exist
$modelsDir = Join-Path $PSScriptRoot "..\models"
if (-not (Test-Path $modelsDir)) {
    Write-Host "Creating models directory: $modelsDir" -ForegroundColor Blue
    New-Item -ItemType Directory -Path $modelsDir -Force
}

# Activate virtual environment if it exists
$venvPath = Join-Path $PSScriptRoot "..\venv"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Blue
    & "$venvPath\Scripts\Activate.ps1"
} else {
    Write-Host "Warning: Virtual environment not found at $venvPath" -ForegroundColor Yellow
    Write-Host "Please ensure dependencies are installed in your active Python environment" -ForegroundColor Yellow
}

# Create Python script to download model
$pythonScript = @"
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
"@

# Write Python script to temp file
$tempPythonFile = Join-Path $PSScriptRoot "temp_download_model.py"
$pythonScript | Out-File -FilePath $tempPythonFile -Encoding UTF8

try {
    # Run the Python script
    Write-Host "Executing model download..." -ForegroundColor Blue
    python $tempPythonFile

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Model download completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Model download failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} finally {
    # Clean up temp file
    if (Test-Path $tempPythonFile) {
        Remove-Item $tempPythonFile -Force
    }
}

Write-Host "Model download script completed." -ForegroundColor Green
