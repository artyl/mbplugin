%~d0 
cd "%~dp0"

curl -LOk http://download.savannah.gnu.org/releases/tinycc/tcc-0.9.27-win32-bin.zip 
7z x tcc-0.9.27-win32-bin.zip -o..
del tcc-0.9.27-win32-bin.zip