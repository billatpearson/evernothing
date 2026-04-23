@echo off
setlocal

:: Load .env file
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "line=%%A"
    if not "!line:~0,1!"=="#" if not "%%A"=="" set "%%A=%%B"
)
setlocal enabledelayedexpansion
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "line=%%A"
    if not "!line:~0,1!"=="#" if not "%%A"=="" set "%%A=%%B"
)

echo WARNING: This will permanently delete ALL objects in s3://%S3_BUCKET_NAME%
echo.
set /p CONFIRM=Type 'yes' to continue: 
if /i not "%CONFIRM%"=="yes" (
    echo Aborted.
    exit /b 1
)

python delete_s3_bucket_contents.py

endlocal
