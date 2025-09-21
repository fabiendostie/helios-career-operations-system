#!/bin/bash
# Simple script to generate and serve documentation locally

echo "🚀 HELIOS Documentation Generator"
echo "=================================="

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed or not in PATH"
    exit 1
fi

# Generate documentation
echo "📚 Generating API documentation..."
python scripts/generate_docs.py

if [ $? -eq 0 ]; then
    echo "✅ Documentation generated successfully!"
    echo "📂 Documentation available at: docs/api/index.html"

    # Check if we should serve locally
    if [ "$1" = "--serve" ]; then
        echo "🌐 Starting local server..."
        cd docs/api
        python -m http.server 8080
    else
        echo "💡 To serve locally, run: ./scripts/docs.sh --serve"
        echo "   Then visit: http://localhost:8080"
    fi
else
    echo "❌ Documentation generation failed"
    exit 1
fi
