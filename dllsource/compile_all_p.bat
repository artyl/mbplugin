%~d0
cd %~p0

@C:\mbplugin\python\python -c "import os,glob;fl=[os.system(f'compile.bat p_{os.path.splitext(os.path.split(fn)[1])[0]}') for fn in glob.glob('..\\plugin\\*.py') if 'def get_balance(' in open(fn,encoding='utf8').read()]"
move C:\mbplugin\dllsource\*.dll C:\mbplugin\dllplugin

