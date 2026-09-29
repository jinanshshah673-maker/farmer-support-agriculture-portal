@echo off
echo Starting Mandi Prices Sync...
cd /d "c:\Users\admin\OneDrive\Desktop\p\djangodemo1\pro1"
"c:\Users\admin\OneDrive\Desktop\p\.venv\Scripts\python.exe" manage.py update_mandi_prices
echo Sync complete!
