@echo off

set "wslService=LxssManager"

sc query %wslService% >nul 2>&1
if %errorlevel% == 0 (
  echo WSL is installed
  goto questionDocker
) else (
  echo WSL is not installed
  dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux
  goto questionDocker
)

:question
echo WSL is not installed. You want to install a distribution? (s/n)
set /p install=""
if /i "%install%"=="s"  goto install
if /i "%install%"=="n"  goto exit

:questionDocker
echo Select an option:
echo 1. Installing WSL
echo 2. Install Docker (WSL required)
echo 3. Exit
set /p installDocker=""
if /i "%installDocker%"=="1"  goto install
if /i "%installDocker%"=="2"  goto installDocker
if /i "%installDocker%"=="3"  goto exit

:install
echo Choose a distribution to install:
echo 1. Ubuntu 20.04 LTS
echo 2. Debian 10
echo 3. Kali Linux
set /p distro=""
if /i "%distro%" == "1" goto ubuntu
if /i "%distro%" == "2" goto debian
if /i "%distro%" == "3" goto kali-linux

:ubuntu
powershell.exe -Command "wsl --install -d Ubuntu-20.04"
wsl --set-default Ubuntu-20.04
goto exit
:debian
powershell.exe -Command "wsl --install -d Debian"
wsl --set-default Debian
goto exit
:kali-linux
powershell.exe -Command "wsl --install -d kali-linux"
wsl --set-default kali-linux
goto exit
:installDocker
wsl curl -fsSL https://get.docker.com -o get-docker.sh
wsl sudo sh get-docker.sh

:exit

pause
