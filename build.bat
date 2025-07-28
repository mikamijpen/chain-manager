@echo off
CALL conda activate tools
pyinstaller --onefile --windowed --name chain-manager ui_main.py 
pause 