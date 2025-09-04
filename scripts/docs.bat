@echo off
REM Simple script to generate and serve documentation locally on Windows

echo 🚀 HELIOS Documentation Generator
echo ==================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    exit /b 1
)

REM Generate documentation
echo 📚 Generating API documentation...
python scripts\generate_docs.py

if %errorlevel% equ 0 (
    echo ✅ Documentation generated successfully!
    echo 📂 Documentation available at: docs\api\index.html
    
    REM Check if we should serve locally
    if "%1"=="--serve" (
        echo 🌐 Starting local server...
        cd docs\api
        python -m http.server 8080
    ) else (
        echo 💡 To serve locally, run: scripts\docs.bat --serve
        echo    Then visit: http://localhost:8080
    )
) else (
    echo ❌ Documentation generation failed
    exit /b 1
)