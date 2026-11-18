@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "OLLAMA=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
if not defined MODELO set "MODELO=qwen2.5:3b"

echo ============================================
echo  Centinela - instalacion y primera ejecucion
echo ============================================

where ollama >nul 2>nul && set "OLLAMA=ollama"
if "%OLLAMA%"=="ollama" goto servidor
if exist "%OLLAMA%" goto servidor

echo [1/4] Descargando Ollama...
curl.exe -L --fail -o "%TEMP%\OllamaSetup.exe" https://ollama.com/download/OllamaSetup.exe
if errorlevel 1 (echo No se pudo descargar Ollama. Revisa tu internet. & pause & exit /b 1)
echo [1/4] Instalando Ollama (puede tardar un par de minutos)...
"%TEMP%\OllamaSetup.exe" /SILENT /NORESTART
if not exist "%OLLAMA%" (echo La instalacion no termino. Abre %TEMP%\OllamaSetup.exe a mano. & pause & exit /b 1)

:servidor
echo [2/4] Iniciando Ollama...
curl.exe -s http://localhost:11434 >nul 2>nul || start "" /B "%OLLAMA%" serve
set /a N=0
:esperar
curl.exe -s http://localhost:11434 >nul 2>nul && goto modelo
set /a N+=1
if %N% GEQ 30 (echo Ollama no respondio. Abrelo desde el menu Inicio y vuelve a ejecutar este archivo. & pause & exit /b 1)
timeout /t 2 >nul
goto esperar

:modelo
echo [3/4] Descargando el modelo %MODELO% (solo la primera vez)...
"%OLLAMA%" pull %MODELO%
if errorlevel 1 (echo No se pudo descargar el modelo. & pause & exit /b 1)

echo [4/4] Ejecutando Centinela...
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
)
if not exist resultados mkdir resultados
".venv\Scripts\python.exe" centinela.py --ver-traza > resultados\log_centinela.txt 2>&1
type resultados\log_centinela.txt
echo.
echo Listo. La salida quedo guardada en resultados\log_centinela.txt
pause
