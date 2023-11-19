cd /d %~dp0
set D=%date:~0,4%%date:~5,2%%date:~8,2%%time:~0,2%%time:~3,2%%time:~6,2% 
echo %D%
.\venv\Scripts\python detect_meteor.py
:: >"run-%D%.log" 2>&1
pause
