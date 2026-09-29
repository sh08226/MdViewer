@echo off
setlocal
rem 取消 .md / .markdown 与 Markdown 查看器的关联（仅当前用户）
reg delete "HKCU\Software\Classes\MdViewer.md" /f >nul 2>&1
reg add "HKCU\Software\Classes\.md" /ve /t REG_SZ /d "txtfile" /f >nul 2>&1
reg add "HKCU\Software\Classes\.markdown" /ve /t REG_SZ /d "txtfile" /f >nul 2>&1
reg delete "HKCU\Software\Classes\.md\OpenWithProgids" /v "MdViewer.md" /f >nul 2>&1
reg delete "HKCU\Software\Classes\.markdown\OpenWithProgids" /v "MdViewer.md" /f >nul 2>&1

rem 刷新图标缓存
ie4uinit.exe -show >nul 2>&1
taskkill /im explorer.exe /f >nul 2>&1
start "" explorer.exe

echo.
echo 已取消 .md 与本查看器的关联，图标已刷新。
echo 之后双击 .md 会用记事本打开（或右键选择其它程序）。
echo.
pause
