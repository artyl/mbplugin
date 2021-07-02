@echo OFF
%~d0 
cd "%~dp0\..\.."
mbplugin\python\pythonw.exe mbplugin\plugin\dbengine.py update_sqlite_from_mdb_all