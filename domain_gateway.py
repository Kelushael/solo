#!/usr/bin/env python3
import os
from pathlib import Path
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse

HOME = Path.home()
BASE = HOME / '.solo-domain'
ENV = BASE / '.env'
APP = Path(__file__).resolve().parent
WEB = APP / 'web'
BASE.mkdir(parents=True, exist_ok=True)
load_dotenv(ENV)

GPU_BASE = os.getenv('GPU_SOLO_BASE', 'http://108.181.162.206:8787')
HOST = os.getenv('DOMAIN_HOST', '0.0.0.0')
PORT = int(os.getenv('DOMAIN_PORT', '8080'))

app = FastAPI(title='1PA Domain Gateway')

@app.get('/')
def index():
    return FileResponse(WEB / 'index.html')

@app.get('/style.css')
def style():
    return FileResponse(WEB / 'style.css')

@app.get('/app.js')
def js():
    return FileResponse(WEB / 'app.js')

@app.get('/api/status')
def status():
    try:
        r = requests.get(GPU_BASE + '/', timeout=8)
        data = r.json()
        data['gpu_base'] = GPU_BASE
        return JSONResponse(data)
    except Exception as exc:
        return JSONResponse({'ok': False, 'error': str(exc), 'gpu_base': GPU_BASE})

@app.get('/api/logs')
def logs():
    try:
        r = requests.get(GPU_BASE + '/logs', timeout=8)
        return PlainTextResponse(r.text)
    except Exception as exc:
        return PlainTextResponse('logs unavailable: ' + str(exc))

@app.post('/api/chat')
async def chat(request: Request):
    data = await request.json()
    try:
        r = requests.post(GPU_BASE + '/chat', json={'message': data.get('message', '')}, timeout=90)
        return JSONResponse(r.json())
    except Exception as exc:
        return JSONResponse({'reply': 'GPU brain unavailable: ' + str(exc)})

@app.post('/webhook')
async def webhook(request: Request):
    data = await request.json()
    try:
        r = requests.post(GPU_BASE + '/webhook', json=data, timeout=90)
        return JSONResponse(r.json(), status_code=r.status_code)
    except Exception as exc:
        return JSONResponse({'error': str(exc)}, status_code=502)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
