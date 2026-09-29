@echo off
chcp 65001 >nul
setlocal
cd /d %~dp0

:: 构建用 Python 虚拟环境（由 prepare_buildenv.bat 创建，含 pyinstaller + pillow）
set "VENV=C:\Users\SH\.workbuddy\binaries\python\envs\build-ac"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%PY%" (
  echo [错误] 未找到构建环境：%PY%
  echo 请先双击本目录下的 prepare_buildenv.bat 创建构建环境。
  pause
  exit /b 1
)

echo === 清理旧构建 ===
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo === PyInstaller 打包（单文件夹 / 无控制台 / 科技蓝图标）===
echo     说明：本工具只读取 .md 渲染，无需写入系统目录，故不带管理员清单，
echo           双击 exe 直接运行，不再弹 UAC 确认。
"%PY%" -m PyInstaller --noconsole --onedir --clean ^
  --name MdViewer --icon assets/icon.ico --add-data "assets/icon.ico;assets" --paths . ^
  mdviewer.py
if errorlevel 1 (
  echo [错误] PyInstaller 打包失败，请查看上方输出。
  pause
  exit /b 1
)

echo === 创建桌面快捷方式（科技蓝图标）===
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws=New-Object -ComObject WScript.Shell; $d=[Environment]::GetFolderPath('Desktop'); $lnk=$ws.CreateShortcut($d+'\Markdown查看器.lnk'); $lnk.TargetPath='%cd%\dist\MdViewer\MdViewer.exe'; $lnk.WorkingDirectory='%cd%\dist\MdViewer'; $lnk.IconLocation='%cd%\dist\MdViewer\assets\icon.ico'; $lnk.Description='Markdown 查看器'; $lnk.Save()"

echo.
echo 构建完成！
echo   双击 dist\MdViewer\MdViewer.exe 即可使用。
echo   桌面已生成快捷方式：Markdown查看器.lnk
echo.
echo 若要拷贝到其它电脑：把整个 dist\MdViewer 文件夹压缩发出即可，
echo   对方解压后双击 MdViewer.exe 即可，无需安装任何软件。
echo.
pause
