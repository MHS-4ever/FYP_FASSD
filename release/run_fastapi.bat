cd /d %~dp0
python -m uvicorn app_fastapi:app --host 127.0.0.1 --port 8000
