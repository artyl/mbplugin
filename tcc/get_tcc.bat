%~d0 
cd "%~dp0"

if not exist tcc.exe curl -LOk http://download.savannah.gnu.org/releases/tinycc/tcc-0.9.27-win32-bin.zip 
if not exist tcc.exe 7z x tcc-0.9.27-win32-bin.zip -o..
if exist tcc-0.9.27-win32-bin.zip del tcc-0.9.27-win32-bin.zip