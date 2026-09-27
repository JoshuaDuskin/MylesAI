import asyncio
import json
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import psutil

app = FastAPI()

# Configure CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (adjust in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the current directory
static_path = Path(__file__).parent.resolve()
app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")


async def get_metrics():
    """Gather CPU, Memory, and Network metrics using psutil."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    network = psutil.net_io_counters()

    return {
        "cpu": cpu_percent,
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent
        },
        "network": {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
    }


@app.get("/")
async def root():
    return {"message": "Metrics WebSocket server running. Connect to /ws/metrics"}


@app.websocket("/ws/metrics")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            metrics = await get_metrics()
            # Send metrics as JSON over WebSocket
            await websocket.send_text(json.dumps(metrics))
            await asyncio.sleep(1)  # Update every second
    except WebSocketDisconnect:
        print("Client disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)