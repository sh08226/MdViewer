@echo off
setlocal
rem ============================================================
rem  Markdown 查看器 - 文件关联安装（无需管理员，仅当前用户生效）
rem  作用：让电脑里的 .md / .markdown 文件显示本查看器图标，
rem        双击即用本查看器打开。
rem  注意：本文件要放在便携版根目录（与 MdViewer 文件夹同级）。
rem ============================================================
set "EXE=%~dp0MdViewer\MdViewer.exe"
if not exist "%EXE%" (
  echo [错误] 未找到 MdViewer.exe：
  echo   %EXE%
  echo 请把本文件放在便携版根目录（和 MdViewer 文件夹同一层）后再运行。
  echo.
  pause
  exit /b 1
)

rem 图标优先用便携版里的 icon.ico，没有则回退到 exe 内嵌图标
set "ICO=%~dp0MdViewer\assets\icon.ico"
if exist "%ICO%" (set "ICON=%ICO%") else (set "ICON=%EXE%")

echo 将把 .md 文件关联到本查看器：
echo   %EXE%
echo.

rem 写入当前用户注册表（HKCU\Software\Classes，无需管理员）
reg add "HKCU\Software\Classes\.md" /ve /t REG_SZ /d "MdViewer.md" /f >nul
if errorlevel 1 goto fail
reg add "HKCU\Software\Classes\.markdown" /ve /t REG_SZ /d "MdViewer.md" /f >nul
reg add "HKCU\Software\Classes\MdViewer.md" /ve /t REG_SZ /d "Markdown 文档" /f >nul
reg add "HKCU\Software\Classes\MdViewer.md\DefaultIcon" /ve /t REG_SZ /d "\"%ICON%\",0" /f >nul
reg add "HKCU\Software\Classes\MdViewer.md\shell\open\command" /ve /t REG_SZ /d "\"%EXE%\" \"%%1\"" /f >nul
rem 让系统在选择列表里优先认我们（避免被其它程序覆盖）
reg add "HKCU\Software\Classes\.md\OpenWithProgids" /v "MdViewer.md" /t REG_SZ /f >nul 2>&1
reg add "HKCU\Software\Classes\.markdown\OpenWithProgids" /v "MdViewer.md" /t REG_SZ /f >nul 2>&1

rem 清除系统记住的旧默认程序（UserChoice 不删会被它覆盖）
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.md\UserChoice" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.markdown\UserChoice" /f >nul 2>&1

rem 刷新图标缓存，并重启资源管理器彻底重绘扩展图标（任务栏会闪一下，正常）
ie4uinit.exe -show >nul 2>&1
taskkill /im explorer.exe /f >nul 2>&1
start "" explorer.exe

echo.
echo 完成！现在 .md 文件会显示本查看器图标，双击即可打开。
echo 图标重绘可能需要几秒；若仍未变，在文件夹窗口里按 F5 刷新。
echo 把整个文件夹拷到别的电脑后，重新运行本文件即可再次关联。
echo 想恢复系统默认，运行同目录下的「卸载关联.bat」。
echo.
pause
exit /b 0

:fail
echo.
echo [错误] 注册表写入失败，请截图反馈。
echo.
pause
exit /b 1
