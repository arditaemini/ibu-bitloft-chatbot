@echo off
rem Starts the BITLoft chatbot and opens it in the browser.
rem Created by the BITLoft Team, International Balkan University.
title BITLoft Chatbot - close this window to stop
cd /d "%~dp0"

rem Open the browser as soon as the server reports it is ready.
start "" /min powershell -NoProfile -WindowStyle Hidden -Command "for($i=0;$i -lt 120;$i++){try{if((Invoke-RestMethod http://localhost:8000/api/health).ready){break}}catch{}; Start-Sleep 1}; Start-Process http://localhost:8000"

echo Starting the BITLoft chatbot... your browser will open when it is ready.
echo Close this window to stop the chatbot.
echo.
".venv\Scripts\python.exe" app.py
pause
