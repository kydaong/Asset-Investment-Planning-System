@echo off
echo ====================================================================
echo Starting AIPI Backend Server
echo ====================================================================

cd /d "D:\Projects\asset-intelligence-system"

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting FastAPI server...
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 4333 --reload

pause