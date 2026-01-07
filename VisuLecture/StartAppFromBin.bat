@echo off
cd /d "%~dp0bin\Debug\net9.0"
echo Démarrage de VisuLecture...
echo.
echo L'application sera accessible à l'adresse : http://localhost:5188
echo.
echo ATTENTION : Si vous fermez cette fenêtre, l'application s'arrêtera.
echo.
start "" "http://localhost:5188"
VisuLecture.exe
pause

