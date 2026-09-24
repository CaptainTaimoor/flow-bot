# Setup Guide

1. Ensure Python 3.10+ is installed on Windows.
2. Open PowerShell in this project directory.
3. Run `python -m venv venv`
4. Run `.\venv\Scripts\Activate.ps1`
5. Run `pip install -r requirements.txt`
6. Run `playwright install chromium`
7. Copy `.env.example` to `.env` (or run `python init_env.py`)
8. Start the app: `python -m src.cli.main start`
