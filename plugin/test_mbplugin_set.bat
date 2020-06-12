@echo OFF
%~d0 
cd "%~dp0"

@SET RequestVariable="<Request><ParentWindow>007F09DA</ParentWindow><Login>loginlogin</Login><Password>password123456</Password></Request>"
@..\plugin\mbplugin.bat p_test1
