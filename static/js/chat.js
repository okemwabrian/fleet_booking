(function () {
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatBox = document.getElementById('chat-box');
  const receiverInput = document.getElementById('chat-receiver');
  const typingIndicator = document.getElementById('chat-typing-indicator');
  const currentUserId = String(document.body.dataset.userId || '');
  const unreadDataset = document.body.dataset.unreadCounts || '{}';

  if (!chatForm || !chatInput || !chatBox || !receiverInput || !receiverInput.value) {
    return;
  }

  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const socketUrl = `${protocol}://${window.location.host}/ws/messages/`;
  const receiverId = String(receiverInput.value);
  const unreadCounts = (() => {
    try {
      return JSON.parse(unreadDataset);
    } catch (error) {
      return {};
    }
  })();
  let socket = null;
  let reconnectAttempts = 0;
  let typingTimeout = null;

  const escapeHtml = (value) => {
    const element = document.createElement('div');
    element.textContent = value ?? '';
    return element.innerHTML;
  };

  const renderMessage = (message) => {
    if (!message) return;
    const senderId = String(message.sender_id || '');
    const receiver = String(message.receiver_id || '');
    const shouldShow =
      (senderId === currentUserId && receiver === receiverId) ||
      (senderId === receiverId && receiver === currentUserId);

    if (!shouldShow) return;

    if (chatBox.querySelector(`[data-message-id="${CSS.escape(String(message.id))}"]`)) {
      return;
    }

    const card = document.createElement('div');
    card.dataset.messageId = String(message.id);
    card.className = `rounded-2xl px-3 py-2 border ${senderId === currentUserId ? 'bg-cyan-400/10 border-cyan-400/20' : 'bg-white/10 border-white/10'}`;
    const timestamp = new Date(message.created_at).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
    card.innerHTML = `
      <p class="text-xs uppercase tracking-[0.25em] text-slate-400">${escapeHtml(message.sender_username)} • ${escapeHtml(timestamp)}</p>
      <p class="mt-1 text-sm text-slate-100">${escapeHtml(message.content)}</p>
    `;
    chatBox.appendChild(card);
    chatBox.scrollTop = chatBox.scrollHeight;
  };

  const unreadBadgeNode = (contactId) => document.getElementById(`unread-${String(contactId)}`);

  const paintUnreadBadge = (contactId, value) => {
    const badge = unreadBadgeNode(contactId);
    if (!badge) return;
    const next = Math.max(Number(value || 0), 0);
    badge.textContent = String(next);
    badge.classList.toggle('hidden', next === 0);
  };

  const setUnread = (contactId, value) => {
    unreadCounts[String(contactId)] = Math.max(Number(value || 0), 0);
    paintUnreadBadge(contactId, unreadCounts[String(contactId)]);
  };

  const incrementUnread = (contactId) => {
    const current = Number(unreadCounts[String(contactId)] || 0);
    setUnread(contactId, current + 1);
  };

  const initializeUnreadBadges = () => {
    document.querySelectorAll('[id^="unread-"]').forEach((badge) => {
      const id = badge.id.replace('unread-', '');
      paintUnreadBadge(id, unreadCounts[String(id)] || 0);
    });
    setUnread(receiverId, 0);
  };

  const sendReadReceipt = () => {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(
      JSON.stringify({
        kind: 'chat.read',
        contact_id: Number(receiverId),
      }),
    );
  };

  const setTypingIndicator = (show, username) => {
    if (!typingIndicator) return;
    typingIndicator.classList.toggle('hidden', !show);
    if (show && username) {
      typingIndicator.textContent = `${username} is typing...`;
    }
  };

  const sendTypingState = (isTyping) => {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(
      JSON.stringify({
        kind: 'chat.typing',
        receiver_id: Number(receiverId),
        is_typing: Boolean(isTyping),
      }),
    );
  };

  const handleSocketMessage = (event) => {
    let payload;
    try {
      payload = JSON.parse(event.data);
    } catch (error) {
      return;
    }

    if (!payload || !payload.type) {
      return;
    }

    if (payload.type === 'chat.typing' && payload.typing) {
      const senderId = String(payload.typing.sender_id || '');
      const receiver = String(payload.typing.receiver_id || '');
      if (senderId === receiverId && receiver === currentUserId) {
        setTypingIndicator(Boolean(payload.typing.is_typing), payload.typing.sender_username);
      }
      return;
    }

    if (payload.type === 'chat.read') {
      return;
    }

    if (payload.type !== 'chat.message' || !payload.message) {
      return;
    }

    const message = payload.message;
    const senderId = String(message.sender_id || '');
    const receiver = String(message.receiver_id || '');

    if (receiver === currentUserId && senderId !== receiverId) {
      incrementUnread(senderId);
    }

    renderMessage(message);

    if (receiver === currentUserId && senderId === receiverId) {
      setUnread(receiverId, 0);
      sendReadReceipt();
    }
  };

  const connect = () => {
    socket = new WebSocket(socketUrl);

    socket.addEventListener('open', () => {
      reconnectAttempts = 0;
      sendReadReceipt();
    });

    socket.addEventListener('message', handleSocketMessage);

    socket.addEventListener('close', () => {
      reconnectAttempts += 1;
      const delay = Math.min(2000 * reconnectAttempts, 10000);
      window.setTimeout(connect, delay);
    });

    socket.addEventListener('error', () => {
      socket.close();
    });
  };

  chatForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const content = chatInput.value.trim();
    if (!content || !socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }

    socket.send(
      JSON.stringify({
        kind: 'chat.message',
        receiver_id: Number(receiverId),
        content,
      }),
    );

    setTypingIndicator(false);
    sendTypingState(false);
    chatInput.value = '';
  });

  chatInput.addEventListener('input', () => {
    sendTypingState(true);
    if (typingTimeout) {
      window.clearTimeout(typingTimeout);
    }
    typingTimeout = window.setTimeout(() => {
      sendTypingState(false);
    }, 900);
  });

  initializeUnreadBadges();

  connect();
})();
