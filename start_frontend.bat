@echo off
chcp 65001 >nul
cd /d "%~dp0\frontend"
python -m http.server 8080
pause
