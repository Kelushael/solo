const chat = document.getElementById('chat');
const form = document.getElementById('chatForm');
const input = document.getElementById('chatInput');
const engine = document.getElementById('engine');
const model = document.getElementById('model');
const live = document.getElementById('live');
const lastSignal = document.getElementById('lastSignal');
const logs = document.getElementById('logs');

function addMsg(role, text) {
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.textContent = (role === 'user' ? 'you> ' : 'solo> ') + text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

async function refreshStatus() {
  try {
    const r = await fetch('/api/status');
    const data = await r.json();
    engine.textContent = data.ok ? 'online' : 'offline';
    model.textContent = data.model || 'unknown';
    live.textContent = data.live ? 'live' : 'paper';
    lastSignal.textContent = data.last_signal ? JSON.stringify(data.last_signal) : 'none';
  } catch (e) {
    engine.textContent = 'offline';
  }
}

async function refreshLogs() {
  try {
    const r = await fetch('/api/logs');
    const text = await r.text();
    logs.textContent = text || 'waiting for logs...';
    logs.scrollTop = logs.scrollHeight;
  } catch (e) {
    logs.textContent = 'logs unavailable';
  }
}

async function sendChat(text) {
  addMsg('user', text);
  input.value = '';
  const r = await fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({message:text})
  });
  const data = await r.json();
  addMsg('solo', data.reply || JSON.stringify(data));
  refreshStatus();
  refreshLogs();
}

form.addEventListener('submit', e => {
  e.preventDefault();
  const text = input.value.trim();
  if (text) sendChat(text);
});

addMsg('solo', '1PA cloud cockpit online.');
refreshStatus();
refreshLogs();
setInterval(refreshStatus, 5000);
setInterval(refreshLogs, 3000);
