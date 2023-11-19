cd  %~dp0
set D=%date:~0,4%%date:~5,2%%date:~8,2%%time:~0,2%%time:~3,2%%time:~6,2% 
echo %D%
::python sikuli_open_camera.sikuli\schedule.py  
java -jar ..\sikulixide-2.0.5.jar -r sikuli_open_camera.sikuli 
:: > "run-%D%.log" 2>&1
pause