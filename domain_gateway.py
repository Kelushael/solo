#!/usr/bin/env python3
import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse, StreamingResponse

HOME = Path.home()
BASE = HOME / '.solo-domain'
ENV = BASE / '.env'
APP = Path(__file__).resolve().parent
WEB = APP / 'web'
BASE.mkdir(parents=True, exist_ok=True)
load_dotenv(ENV)

GPU_BASE = os.getenv('GPU_SOLO_BASE', 'http://108.181.162.206:8787')
PUBLIC_BASE = os.getenv('PUBLIC_BASE_URL', 'https://axismundi.fun')
MCP_TOKEN = os.getenv('MCP_HMAC_TOKEN', '')
HOST = os.getenv('DOMAIN_HOST', '0.0.0.0')
PORT = int(os.getenv('DOMAIN_PORT', '8080'))

app = FastAPI(title='1PA Domain Gateway')


def mcp_auth_ok(auth_header: str | None) -> bool:
    if not MCP_TOKEN:
        return True
    return auth_header == f'Bearer {MCP_TOKEN}'


def mcp_text_result(msg_id, text, is_error=False):
    return {
        'jsonrpc': '2.0',
        'id': msg_id,
        'result': {
            'content': [{'type': 'text', 'text': text}],
            'isError': is_error,
        },
    }

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

@app.get('/mcp/health')
def mcp_health():
    return {'ok': True, 'name': '1PA Solo MCP', 'endpoint': PUBLIC_BASE + '/mcp/messages', 'gpu_base': GPU_BASE}

@app.get('/mcp/sse')
def mcp_sse(authorization: str | None = Header(default=None)):
    if not mcp_auth_ok(authorization):
        return JSONResponse({'error': 'unauthorized'}, status_code=401)

    def event_stream():
        endpoint_event = {'endpoint': PUBLIC_BASE + '/mcp/messages'}
        init_event = {
            'jsonrpc': '2.0',
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'claude-code', 'version': '1.0.0'},
            },
        }
        yield 'data: ' + json.dumps(endpoint_event) + '\n\n'
        yield 'data: ' + json.dumps(init_event) + '\n\n'

    return StreamingResponse(event_stream(), media_type='text/event-stream')

@app.post('/mcp/messages')
async def mcp_messages(request: Request, authorization: str | None = Header(default=None)):
    if not mcp_auth_ok(authorization):
        return JSONResponse({'error': 'unauthorized'}, status_code=401)

    msg = await request.json()
    msg_id = msg.get('id')
    method = msg.get('method')
    params = msg.get('params') or {}

    if method == 'tools/list':
        return JSONResponse({
            'jsonrpc': '2.0',
            'id': msg_id,
            'result': {
                'tools': [
                    {'name': 'solo_chat', 'description': 'Chat with the 1PA Solo GPU brain', 'inputSchema': {'type': 'object', 'properties': {'message': {'type': 'string'}}, 'required': ['message']}},
                    {'name': 'solo_status', 'description': 'Get Solo GPU status', 'inputSchema': {'type': 'object', 'properties': {}}},
                    {'name': 'solo_logs', 'description': 'Read recent Solo logs', 'inputSchema': {'type': 'object', 'properties': {}}},
                    {'name': 'solo_webhook', 'description': 'Send a TradingView-style signal to Solo', 'inputSchema': {'type': 'object', 'properties': {'payload': {'type': 'object'}}, 'required': ['payload']}},
                ]
            }
        })

    if method != 'tools/call':
        return JSONResponse(mcp_text_result(msg_id, f'Unsupported method: {method}', True))

    name = params.get('name')
    args = params.get('arguments') or {}

    try:
        if name == 'solo_chat':
            r = requests.post(GPU_BASE + '/chat', json={'message': args.get('message', '')}, timeout=90)
            text = r.json().get('reply', r.text)
            return JSONResponse(mcp_text_result(msg_id, text))
        if name == 'solo_status':
            r = requests.get(GPU_BASE + '/', timeout=8)
            return JSONResponse(mcp_text_result(msg_id, json.dumps(r.json(), indent=2)))
        if name == 'solo_logs':
            r = requests.get(GPU_BASE + '/logs', timeout=8)
            return JSONResponse(mcp_text_result(msg_id, r.text or 'no logs'))
        if name == 'solo_webhook':
            r = requests.post(GPU_BASE + '/webhook', json=args.get('payload', {}), timeout=90)
            return JSONResponse(mcp_text_result(msg_id, json.dumps(r.json(), indent=2)))
        return JSONResponse(mcp_text_result(msg_id, f'Unknown tool: {name}', True))
    except Exception as exc:
        return JSONResponse(mcp_text_result(msg_id, 'MCP tool error: ' + str(exc), True))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
