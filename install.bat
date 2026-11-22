@echo off
REM One-time setup. Needs internet once to download the models; afterwards Mini runs fully offline.
cd /d "%~dp0.."
where python >nul 2>&1 || (echo Install Python 3.11+ from python.org first, tick "Add to PATH" & exit /b 1)
where ollama >nul 2>&1 || (echo Install Ollama from https://ollama.com first & exit /b 1)
python -m venv .venv
call .venv\Scripts\activate
pip install -r backend\requirements.txt
pip install -r backend\requirements-voice.txt
echo Downloading the brain and helper models...
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
ollama pull moondream
call scripts\download_models.bat
python -c "from faster_whisper import WhisperModel; WhisperModel('base.en', device='cpu', compute_type='int8')"
echo.
echo Done. Run scripts\start.bat
