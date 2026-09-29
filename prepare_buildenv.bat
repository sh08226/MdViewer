@echo off
chcp 65001 >nul
setlocal
cd /d %~dp0

:: 构建环境用的 Python（托管版本，无需用户另行安装）
set "PY=C:\Users\SH\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "VENV=C:\Users\SH\.workbuddy\binaries\python\envs\build-ac"

if not exist "%PY%" (
  echo [错误] 未找到托管 Python：%PY%
  echo 请确认 WorkBuddy 运行环境完整，或把 PY 改成你本机的 python.exe 路径。
  pause & exit /b 1
)

if exist "%VENV%\Scripts\python.exe" (
  echo [跳过] 构建环境已存在：%VENV%
) else (
  echo === 创建构建虚拟环境 ===
  "%PY%" -m venv "%VENV%"
)

echo === 安装 PyInstaller + Pillow ===
"%VENV%\Scripts\python.exe" -m pip install --quiet --upgrade pip
"%VENV%\Scripts\pip.exe" install pyinstaller pillow
echo.
echo 构建环境就绪：%VENV%
echo 接下来双击 build.bat 即可打包。
pause
