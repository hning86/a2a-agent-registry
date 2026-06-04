// Session State
let sessionId = localStorage.getItem('a2a_session_id') || generateUUID();
localStorage.setItem('a2a_session_id', sessionId);

document.getElementById('session-display').textContent = sessionId.substring(0, 8) + '...';

// DOM Elements
const presetsList = document.getElementById('presets-list');
const resetSessionBtn = document.getElementById('reset-session-btn');
const inputForm = document.getElementById('input-form');
const queryInput = document.getElementById('query-input');
const sendBtn = document.getElementById('send-btn');
const messagesContainer = document.getElementById('messages-container');

// Event Listeners
presetsList.querySelectorAll('li').forEach(item => {
  item.addEventListener('click', () => {
    const prompt = item.getAttribute('data-prompt');
    queryInput.value = prompt;
    queryInput.focus();
    submitQuery(prompt);
  });
});

resetSessionBtn.addEventListener('click', () => {
  sessionId = generateUUID();
  localStorage.setItem('a2a_session_id', sessionId);
  document.getElementById('session-display').textContent = sessionId.substring(0, 8) + '...';
  messagesContainer.innerHTML = '';
  appendSystemMessage('Session cleared. Starting a new context.');
});

inputForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const query = queryInput.value.trim();
  if (query) {
    submitQuery(query);
  }
});

// Helper: UUID Generator
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Helper: Add bubble to UI
function appendSystemMessage(text) {
  const msgDiv = document.createElement('div');
  msgDiv.className = 'message system';
  msgDiv.innerHTML = `<div class="message-content">${text}</div>`;
  messagesContainer.appendChild(msgDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Main logic: SSE Chat submit
async function submitQuery(queryText) {
  // Clear input field
  queryInput.value = '';
  
  // Disable form input during submission
  queryInput.disabled = true;
  sendBtn.disabled = true;
  
  // Append User message
  const userMsgDiv = document.createElement('div');
  userMsgDiv.className = 'message user';
  userMsgDiv.innerHTML = `
    <div class="message-sender">User</div>
    <div class="message-content">${escapeHTML(queryText)}</div>
  `;
  messagesContainer.appendChild(userMsgDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  // Append Thinking indicator bubble
  const thinkingDiv = document.createElement('div');
  thinkingDiv.className = 'message assistant thinking-bubble';
  thinkingDiv.id = 'thinking-indicator';
  thinkingDiv.innerHTML = `
    <div class="message-sender">Orchestrator</div>
    <div class="message-content">
      <div class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  `;
  messagesContainer.appendChild(thinkingDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  // Staging bubble for streaming assistant response
  let activeAgentBubble = null;
  let activeAgentContent = null;
  let lastAuthor = null;

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: queryText,
        session_id: sessionId
      })
    });

    if (!response.ok) {
      throw new Error(`Server returned HTTP status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Keep last incomplete line

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.substring(6).trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);
            const author = data.author;
            const text = data.text;
            const partial = data.partial;

            if (data.error) {
              appendSystemMessage(`Error: ${data.error}`);
              continue;
            }

            const hasText = text && text.trim().length > 0;

            if (hasText) {
              removeThinkingIndicator();
            }

            // Create new bubble if the author changes or if no active bubble exists (only when there is text to render)
            if (hasText && (!activeAgentBubble || lastAuthor !== author)) {
              activeAgentBubble = document.createElement('div');
              
              let isA2A = author === 'math_agent';
              activeAgentBubble.className = `message assistant ${isA2A ? 'a2a-agent' : ''}`;
              
              let senderLabel = author === 'orchestrator_agent' ? 'Orchestrator' : 
                                author === 'math_agent' ? 'Math Agent' : author;
              
              let badgeHTML = isA2A ? '<span class="a2a-badge">A2A</span>' : '';
              
              activeAgentBubble.innerHTML = `
                <div class="message-sender">${escapeHTML(senderLabel)} ${badgeHTML}</div>
                <div class="message-content streaming-active"></div>
              `;
              
              messagesContainer.appendChild(activeAgentBubble);
              activeAgentContent = activeAgentBubble.querySelector('.message-content');
              lastAuthor = author;
            }

            // Only update bubble if we have a valid active bubble and text is present
            if (activeAgentContent && hasText) {

            // Update text content
            if (partial) {
              activeAgentContent.innerHTML = formatMarkdown(text);
              activeAgentContent.classList.add('streaming-active');
            } else {
              activeAgentContent.innerHTML = formatMarkdown(text);
              activeAgentContent.classList.remove('streaming-active');
              // Clear bubble tracker so next response block from same agent starts new bubble if separate turn
              activeAgentBubble = null;
            }
            
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }

          } catch (err) {
            console.error('Failed to parse SSE payload:', err, jsonStr);
          }
        }
      }
    }

  } catch (error) {
    console.error('Connection failed:', error);
    removeThinkingIndicator();
    appendSystemMessage(`System Error: Could not connect to the agent server. ${error.message}`);
  } finally {
    removeThinkingIndicator();
    // Re-enable form inputs
    queryInput.disabled = false;
    sendBtn.disabled = false;
    queryInput.focus();
  }
}

// Helper: Remove thinking indicator
function removeThinkingIndicator() {
  const indicator = document.getElementById('thinking-indicator');
  if (indicator) {
    indicator.remove();
  }
}

// Simple HTML Escaping
function escapeHTML(str) {
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}

// Simple Markdown Formatter
function formatMarkdown(text) {
  if (!text) return '';
  let html = escapeHTML(text);
  
  // Formats bold: **text**
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Formats code snippets: `code`
  html = html.replace(/`(.*?)`/g, '<code>$1</code>');
  
  // Formats linebreaks
  html = html.replace(/\n/g, '<br>');
  
  return html;
}
