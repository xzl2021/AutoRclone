@ECHO OFF
@chcp 65001
setlocal enabledelayedexpansion

echo. >email.txt
for /f "skip=7 tokens=3,*" %%x in ('dir ".\accounts"') do (
    if "%%y"=="bytes" (
        goto :bye
    )
    set filename=%%y
    call :email
)

:email
for /f skip^=5^ tokens^=4^ delims^=^" %%i in (.\accounts\!filename!) do (
    echo %%i >>email.txt
    exit /b 0
)

:bye
exit /b 0