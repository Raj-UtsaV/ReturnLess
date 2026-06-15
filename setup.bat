@echo off
REM ReturnLess - Setup Script (Windows)
echo ♻️  Setting up ReturnLess...
echo ================================

REM Create virtual environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing core dependencies...
pip install Flask==3.1.0 Flask-SQLAlchemy==3.1.1 Flask-Migrate==4.0.7 Flask-Login==0.6.3
pip install SQLAlchemy==2.0.36 Werkzeug==3.1.3 python-dotenv==1.0.1
pip install pytest==8.3.4 pytest-flask==1.3.0

REM Optional AI dependencies
echo 📥 Installing AI dependencies (optional)...
pip install sentence-transformers==3.3.1 scikit-learn==1.6.1 numpy==2.2.1 || echo ⚠️  AI dependencies failed - mock mode will be used

REM Create directories
if not exist "instance" mkdir instance
if not exist "static\uploads" mkdir static\uploads

REM Seed the database
echo 🌱 Seeding database...
python seed_data.py

echo.
echo ================================
echo ✅ Setup complete!
echo.
echo To start the application:
echo   venv\Scripts\activate.bat
echo   python run.py
echo.
echo Then open: http://localhost:5000
echo.
echo 🔑 Demo: demo@returnless.ai / demo123
echo 🛠️  Admin: admin@returnless.ai / admin123
echo ================================
