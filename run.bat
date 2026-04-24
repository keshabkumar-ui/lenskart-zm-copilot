@echo off
echo ========================================================
echo     Starting ZM Copilot - Lenskart Hackathon Edition
echo ========================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [!] Virtual environment not found. Please run: python -m venv venv
    echo [!] And install requirements: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b
)

if not exist ".env" (
    echo [!] WARNING: .env file not found. AI features may fail. 
    echo [!] Please copy .env.example to .env and add your AWS credentials.
    echo.
    pause
)

echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

echo [*] Launching Streamlit dashboard...
streamlit run app.py
