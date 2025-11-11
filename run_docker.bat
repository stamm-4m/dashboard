@echo off
setlocal enabledelayedexpansion

set URL=http://localhost:8050
set MAX_WAIT=60
set COUNTER=0

echo Building and starting Dashboard STAMM container...
docker compose up --build -d

echo Waiting for Dash STAMM to start...

:wait_loop
powershell -Command "(Invoke-WebRequest -Uri '%URL%' -UseBasicParsing -TimeoutSec 2).StatusCode" >nul 2>&1
if %errorlevel%==0 (
    echo Dashboard STAMM is up and running!
    echo Opening %URL% in your default browser...
    start %URL%
    goto :done
) else (
    timeout /t 2 >nul
    set /a COUNTER+=2
    echo Waiting... (!COUNTER! seconds)
    if !COUNTER! GEQ %MAX_WAIT% (
        echo App did not start within %MAX_WAIT% seconds.
        echo To check logs, run: docker compose logs -f
        goto :done
    )
    goto :wait_loop
)

:done
endlocal
pause
