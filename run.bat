@echo off

REM Active le venv
call venv\Scripts\activate.bat

REM Lance le serveur dans une nouvelle fenêtre
start cmd /k python code/server.py

REM Petite pause pour laisser le serveur démarrer
timeout /t 2 > nul

REM Lance le jeu
python code/main.py