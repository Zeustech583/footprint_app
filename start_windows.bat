@echo off
rem Startet die Footprint-App (beim ersten Mal wird alles installiert).
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo Erstelle virtuelle Umgebung ...
    py -3 -m venv .venv || python -m venv .venv
)
if not exist .venv\installiert.txt (
    echo Installiere Pakete - das dauert beim ersten Mal einige Minuten ...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt && echo ok> .venv\installiert.txt
)
.venv\Scripts\python.exe -m streamlit run startseite.py
pause
