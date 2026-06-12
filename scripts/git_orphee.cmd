@echo off
setlocal
set "PORTABLE_GIT=%~dp0..\.tools\git\cmd\git.exe"

if exist "%PORTABLE_GIT%" (
    "%PORTABLE_GIT%" %*
) else (
    git %*
)

exit /b %errorlevel%
