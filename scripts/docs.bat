@echo off
REM Enhanced documentation generator and server for HELIOS Career Operations System

echo 🚀 HELIOS Documentation Generator
echo ==================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.13+ and ensure it's in your PATH
    pause
    exit /b 1
)

REM Set UTF-8 encoding for Windows console
chcp 65001 >nul

REM Check command line argument
if "%1"=="--watch" goto watch_mode
if "%1"=="--serve" goto serve_mode

REM Default: Generate documentation
echo 📚 Generating API documentation...
python scripts\generate_docs.py

if %errorlevel% equ 0 (
    echo.
    echo ✅ Documentation generated successfully!
    echo 📂 Documentation available at: docs\api\index.html
    echo.
    echo 📋 Available options:
    echo    --serve   Start local HTTP server
    echo    --watch   Watch for changes and auto-regenerate
    echo.
    echo 💡 Examples:
    echo    scripts\docs.bat --serve
    echo    scripts\docs.bat --watch
    echo.
    pause
) else (
    echo ❌ Documentation generation failed
    pause
    exit /b 1
)
goto end

:serve_mode
echo 📚 Generating documentation...
python scripts\generate_docs.py
if %errorlevel% neq 0 (
    echo ❌ Documentation generation failed
    pause
    exit /b 1
)

echo.
echo 🌐 Starting local documentation server...
echo 📖 Documentation will be available at: http://localhost:8080
echo 🔄 Press Ctrl+C to stop the server
echo.
cd docs\api
python -m http.server 8080
goto end

:watch_mode
echo 📚 Starting documentation watch mode...
echo 🔄 Watching for changes in services/ directory...
echo 📖 Will regenerate documentation automatically on changes
echo 🛑 Press Ctrl+C to stop watching
echo.

REM Initial generation
python scripts\generate_docs.py

REM Simple watch loop (basic implementation)
:watch_loop
timeout /t 5 >nul
REM Check if any Python files were modified in the last 5 seconds
forfiles /p services /m *.py /s /c "cmd /c echo @path was modified" 2>nul | findstr /i "was modified" >nul
if %errorlevel% equ 0 (
    echo 🔄 Changes detected, regenerating documentation...
    python scripts\generate_docs.py
    echo ✅ Documentation updated!
    echo.
)
goto watch_loop

:end
