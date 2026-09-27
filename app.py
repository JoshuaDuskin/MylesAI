from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import json
from datetime import datetime

app = FastAPI()

RAW_STATUS_URL = "https://raw.githubusercontent.com/MylesAI/Myles/main/status.json"

def fetch_status():
    try:
        resp = requests.get(RAW_STATUS_URL, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

@app.get("/", response_class=HTMLResponse)
def read_root():
    status = fetch_status()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Myles Dashboard</title>
    <style>
        body {{ font-family: sans-serif; margin: 2rem; background: #f5f5f5; }}
        .card {{ background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,.1); margin-bottom: 1rem; }}
        h1 {{ color: #333; }}
        .status-ok {{ color: green; }}
        .status-error {{ color: red; }}
        pre {{ background: #eee; padding: 1rem; border-radius: 4px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>Myles Runtime Dashboard</h1>
    <div class="card">
        <strong>Timestamp:</strong> {now}
    </div>
    <div class="card">
        <strong>Status:</strong> {'OK' if 'error' not in status else 'ERROR'}
    </div>
    <div class="card">
        <strong>Raw Data:</strong>
        <pre>{json.dumps(status, indent=2)}</pre>
    </div>
</body>
</html>'''
    return HTMLResponse(content=html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)