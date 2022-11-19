@ECHO OFF
cd /D "%~dp0"

..\python\python -c "import browsercontroller;browsercontroller.hide_chrome(hide=False)"
