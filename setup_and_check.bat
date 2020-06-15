@echo OFF
%~d0 

cd "%~dp0"
echo Пересобираем DLL 
call dllsource\compile_all_p.bat

cd "%~dp0"
echo Проверяем что все работает
call plugin\test_mbplugin_dll_call.bat p_test1 123 456 
