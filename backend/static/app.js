/**
 * Lind Game Client v2 — Auth-aware WebSocket player interface.
 *
 * Flow:
 *   1. On page load → check localStorage for lind_token
 *   2. If no token → redirect to /login
 *   3. If token → show session picker overlay (existing sessions + new game)
 *   4. On session selected/created → connect WebSocket, send player_join
 */
(function () {
    'use strict';

    const token = localStorage.getItem('lind_token');
    const playerId = localStorage.getItem('lind_player_id');
    const login = localStorage.getItem('lind_login');

    // No token → redirect to login
    if (!token || !playerId) {
        window.location.href = '/login';
        return;
    }

    // ── DOM refs ──
    const sessionOverlay = document.getElementById('session-overlay');
    const playerGreeting = document.getElementById('player-greeting');
    const sessionList = document.getElementById('session-list');
    const newGameBtn = document.getElementById('new-game-btn');
    const logoutLink = document.getElementById('logout-link');
    const appEl = document.getElementById('app');
    const scrollEl = document.getElementById('scroll');
    const thinkingEl = document.getElementById('thinking');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const logoutBtn = document.getElementById('logout-btn');

    let ws = null;
    let sessionId = null;
    let pendingDiceRequest = null;

    // ── Helpers ──
    function scrollToBottom() {
        setTimeout(function () {
            scrollEl.scrollTop = scrollEl.scrollHeight;
        }, 50);
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ── Auth helpers ──
    function logout() {
        localStorage.removeItem('lind_token');
        localStorage.removeItem('lind_player_id');
        localStorage.removeItem('lind_login');
        localStorage.removeItem('lind_session_id');
        window.location.href = '/login';
    }

    // Bind logout
    if (logoutLink) logoutLink.addEventListener('click', function (e) {
        e.preventDefault();
        logout();
    });
    if (logoutBtn) logoutBtn.addEventListener('click', logout);

    // ── Session picker ──
    playerGreeting.textContent = 'Привет, ' + (login || 'путник') + '!';

    // Fetch sessions
    fetch('/api/auth/sessions?player_id=' + encodeURIComponent(playerId))
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var sessions = data.sessions || [];
            if (sessions.length === 0) {
                sessionList.innerHTML = '<p style="color:#666;">Нет активных игр</p>';
            } else {
                sessions.forEach(function (s) {
                    var card = document.createElement('div');
                    card.className = 'session-card';
                    var date = new Date(s.created_at + 'Z');
                    card.innerHTML = '<div class="wc">' + escapeHtml(s.world_name) +
                        '</div><div class="pn">' + escapeHtml(s.player_name || 'Безымянный') + '</div>' +
                        '<div class="date">' + date.toLocaleString('ru-RU') + '</div>';
                    card.addEventListener('click', function () {
                        startSession(s.id);
                    });
                    sessionList.appendChild(card);
                });
            }
        })
        .catch(function (err) {
            sessionList.innerHTML = '<p style="color:#c44;">Ошибка загрузки сессий</p>';
            console.error(err);
        });

    newGameBtn.addEventListener('click', function () {
        startSession(null);
    });

    function startSession(sid) {
        sessionId = sid;
        sessionOverlay.style.display = 'none';
        appEl.style.display = 'flex';
        connect();
    }

    // ── DOM render ──
    function addMessage(role, content) {
        var div = document.createElement('div');
        div.className = 'msg ' + role;

        var meta = document.createElement('div');
        meta.className = 'meta';
        meta.textContent = role === 'master' ? '⚜ Экс-Ис' : role === 'player' ? '🎮 Ты' : '⚙';

        var body = document.createElement('div');
        body.className = 'narrator';
        body.textContent = content;

        div.appendChild(meta);
        div.appendChild(body);
        scrollEl.appendChild(div);
        scrollToBottom();
    }

    function showDiceBanner(request) {
        var existing = document.querySelector('.dice-banner');
        if (existing) existing.remove();

        var div = document.createElement('div');
        div.className = 'dice-banner';
        div.innerHTML =
            '<div class="skill">🎲 ' + escapeHtml(request.skill) + ' (DC ' + request.dc + ')</div>' +
            '<div class="label">' + escapeHtml(request.reason) + '</div>' +
            '<button onclick="window._rollDice(\'' + request.request_id + '\')">Бросить d20</button>';
        scrollEl.appendChild(div);
        scrollToBottom();
        pendingDiceRequest = request;

        chatInput.disabled = true;
        sendBtn.disabled = true;
    }

    function showDiceResult(roll, total) {
        var existing = document.querySelector('.dice-banner');
        if (existing) existing.remove();

        var div = document.createElement('div');
        div.className = 'dice-result';
        var emoji = roll === 20 ? '✨' : roll === 1 ? '💀' : '';
        div.textContent = '🎲 d20: ' + roll + ' → ' + total + ' ' + emoji;
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

    // ── WebSocket ──
    function connect() {
        var protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        var wsUrl = protocol + '//' + location.host + '/ws';

        ws = new WebSocket(wsUrl);

        ws.onopen = function () {
            console.log('[Lind] WS connected, session_id=' + sessionId);
            sendMessage({
                type: 'player_join',
                player_name: login || 'Путник',
                session_id: sessionId,
            });
        };

        ws.onmessage = function (event) {
            try {
                var msg = JSON.parse(event.data);
                handleMessage(msg);
            } catch (err) {
                console.error('[Lind] Parse error:', err);
            }
        };

        ws.onclose = function (event) {
            console.log('[Lind] WS closed:', event.code);
            setThinking(false);
            setTimeout(function () {
                if (sessionId) connect();
            }, 3000);
        };

        ws.onerror = function (err) {
            console.error('[Lind] WS error:', err);
        };
    }

    function sendMessage(obj) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(obj));
        }
    }

    // ── Message dispatcher ──
    function handleMessage(msg) {
        console.log('[Lind] ←', msg.type);

        switch (msg.type) {
            case 'session_created':
                sessionId = msg.session_id;
                localStorage.setItem('lind_session_id', sessionId);
                // Link session to player
                fetch('/api/auth/link-session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessionId,
                        player_id: playerId,
                        token: token,
                    }),
                }).catch(function () { });
                break;

            case 'master_thinking':
                setThinking(msg.status === 'started');
                break;

            case 'master_speech':
                if (msg.backlog && Array.isArray(msg.backlog)) {
                    for (var i = 0; i < msg.backlog.length; i++) {
                        if (msg.backlog[i].role === 'system') continue;
                        addMessage(msg.backlog[i].role, msg.backlog[i].content);
                    }
                }
                if (msg.narrator) {
                    addMessage('master', msg.narrator);
                }
                if (msg.dice_request) {
                    showDiceBanner(msg.dice_request);
                }
                chatInput.focus();
                break;

            case 'dice_request':
                showDiceBanner(msg);
                break;

            default:
                // ignore
        }
    }

    // ── Player actions ──
    function sendPlayerAction(text) {
        if (!text.trim()) return;
        addMessage('player', text);
        sendMessage({ type: 'player_say', content: text });
        chatInput.value = '';
    }

    window._rollDice = function (requestId) {
        var existing = document.querySelector('.dice-banner');
        if (existing) existing.remove();

        var roll = Math.floor(Math.random() * 20) + 1;
        var modifier = 0;

        showDiceResult(roll, roll + modifier);

        sendMessage({
            type: 'dice_result',
            request_id: requestId,
            roll: roll,
            modifier: modifier,
        });
    };

    // ── Event handlers ──
    sendBtn.addEventListener('click', function () {
        sendPlayerAction(chatInput.value);
    });

    chatInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendPlayerAction(chatInput.value);
        }
    });

    console.log('[Lind] Client v2 loaded, player=' + login);

})();