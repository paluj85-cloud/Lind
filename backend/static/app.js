/**
 * Lind Game Client — WebSocket-based player interface.
 * Protocol: WS → { type, ... }
 *   Client → Server: player_join, player_say, dice_result
 *   Server → Client: session_created, master_speech, dice_request, master_thinking
 */

// ── State ───────────────────────────────────────────────────────────────────
let ws = null;
let sessionId = localStorage.getItem('lind_session_id') || null;
let playerName = '';
let pendingDiceRequest = null; // { request_id, ... }

// ── DOM refs ────────────────────────────────────────────────────────────────
const nameOverlay = document.getElementById('name-overlay');
const nameForm = document.getElementById('name-form');
const nameInput = document.getElementById('name-input');
const appEl = document.getElementById('app');
const scrollEl = document.getElementById('scroll');
const thinkingEl = document.getElementById('thinking');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

// ── Helpers ─────────────────────────────────────────────────────────────────
function scrollToBottom() {
  setTimeout(() => {
    scrollEl.scrollTop = scrollEl.scrollHeight;
  }, 50);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ── DOM render ──────────────────────────────────────────────────────────────
function addMessage(role, content) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;

  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.textContent = role === 'master' ? '⚜ Экс-Ис' : role === 'player' ? '🎮 Ты' : '⚙';

  const body = document.createElement('div');
  body.className = 'narrator';
  body.textContent = content;

  div.appendChild(meta);
  div.appendChild(body);
  scrollEl.appendChild(div);
  scrollToBottom();
}

function showDiceBanner(request) {
  // Remove any existing banner
  const existing = document.querySelector('.dice-banner');
  if (existing) existing.remove();

  const div = document.createElement('div');
  div.className = 'dice-banner';
  div.innerHTML = `
    <div class="skill">🎲 ${escapeHtml(request.skill)} (DC ${request.dc})</div>
    <div class="label">${escapeHtml(request.reason)}</div>
    <button onclick="rollDice('${request.request_id}')">Бросить d20</button>
  `;
  scrollEl.appendChild(div);
  scrollToBottom();
  pendingDiceRequest = request;

  // Disable text input while dice roll is pending
  chatInput.disabled = true;
  sendBtn.disabled = true;
}

function showDiceResult(roll, total) {
  const existing = document.querySelector('.dice-banner');
  if (existing) existing.remove();

  const div = document.createElement('div');
  div.className = 'dice-result';
  const emoji = roll === 20 ? '✨' : roll === 1 ? '💀' : '';
  div.textContent = `🎲 d20: ${roll} → ${total} ${emoji}`;
  scrollEl.appendChild(div);
  scrollToBottom();

  pendingDiceRequest = null;
  chatInput.disabled = false;
  sendBtn.disabled = false;
  chatInput.focus();
}

function setThinking(visible) {
  if (visible) {
    thinkingEl.classList.add('visible');
  } else {
    thinkingEl.classList.remove('visible');
  }
}

// ── WebSocket ───────────────────────────────────────────────────────────────
function connect() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('[Lind] WebSocket connected');
    // Send player_join as soon as the player has entered their name.
    // session_id is null for new sessions, uuid for reconnects.
    if (playerName) {
      sendMessage({
        type: 'player_join',
        player_name: playerName,
        session_id: sessionId,
      });
    }
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      handleMessage(msg);
    } catch (err) {
      console.error('[Lind] Failed to parse message:', err);
    }
  };

  ws.onclose = (event) => {
    console.log('[Lind] WebSocket closed:', event.code, event.reason);
    setThinking(false);
    // Auto-reconnect after 3 seconds
    setTimeout(() => {
      if (sessionId) connect();
    }, 3000);
  };

  ws.onerror = (err) => {
    console.error('[Lind] WebSocket error:', err);
  };
}

function sendMessage(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(obj));
  }
}

// ── Message dispatcher ──────────────────────────────────────────────────────
function handleMessage(msg) {
  console.log('[Lind] ←', msg.type);

  switch (msg.type) {
    case 'session_created':
      sessionId = msg.session_id;
      localStorage.setItem('lind_session_id', sessionId);
      break;

    case 'master_thinking':
      setThinking(msg.status === 'started');
      break;

    case 'master_speech':
      // Render backlog (history) if present
      if (msg.backlog && Array.isArray(msg.backlog)) {
        for (const entry of msg.backlog) {
          addMessage(entry.role, entry.content);
        }
      }
      // Narrator content (master's words to player)
      if (msg.narrator) {
        addMessage('master', msg.narrator);
      }
      // Dice request embedded in the speech
      if (msg.dice_request) {
        showDiceBanner(msg.dice_request);
      }
      chatInput.focus();
      break;

    case 'dice_request':
      // Explicit dice request (legacy, but kept for compatibility)
      showDiceBanner(msg);
      break;

    default:
      console.log('[Lind] Unknown message type:', msg.type);
  }
}

// ── Player actions ──────────────────────────────────────────────────────────
function sendPlayerAction(text) {
  if (!text.trim()) return;
  addMessage('player', text);
  sendMessage({ type: 'player_say', content: text });
  chatInput.value = '';
}

function rollDice(requestId) {
  // Remove dice banner
  const existing = document.querySelector('.dice-banner');
  if (existing) existing.remove();

  // Generate random d20 roll (client-side for instant feedback)
  const roll = Math.floor(Math.random() * 20) + 1;
  const modifier = 0; // TODO: character modifiers from server

  showDiceResult(roll, roll + modifier);

  // Send result to server for second LLM pass
  sendMessage({
    type: 'dice_result',
    request_id: requestId,
    roll: roll,
    modifier: modifier,
  });
}

// ── Event handlers ──────────────────────────────────────────────────────────
nameForm.addEventListener('submit', (e) => {
  e.preventDefault();
  playerName = nameInput.value.trim();
  if (!playerName) return;

  nameOverlay.style.display = 'none';
  appEl.style.display = 'flex';

  connect();
  // session_created → handleMessage sends player_join automatically (single source of truth)
});

sendBtn.addEventListener('click', () => {
  sendPlayerAction(chatInput.value);
});

chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    sendPlayerAction(chatInput.value);
  }
});

// ── Init ────────────────────────────────────────────────────────────────────
console.log('[Lind] Client loaded');
nameInput.focus();