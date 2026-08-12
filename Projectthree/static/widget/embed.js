(function() {
    // Detect API Base URL from the script tag source
    const currentScript = document.currentScript || (function() {
        const scripts = document.getElementsByTagName('script');
        return scripts[scripts.length - 1];
    })();

    let baseUrl = "http://localhost:8000";
    if (currentScript && currentScript.src) {
        try {
            const url = new URL(currentScript.src);
            baseUrl = url.origin;
        } catch(e) {}
    }

    const courseId = (currentScript && currentScript.getAttribute('data-course-id')) || 'default';

    // Inject FontAwesome icons if not present
    if (!document.getElementById('syllabus-fa-css')) {
        const fa = document.createElement('link');
        fa.id = 'syllabus-fa-css';
        fa.rel = 'stylesheet';
        fa.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
        document.head.appendChild(fa);
    }

    // Inject Widget CSS
    if (!document.getElementById('syllabus-widget-css')) {
        const css = document.createElement('link');
        css.id = 'syllabus-widget-css';
        css.rel = 'stylesheet';
        css.href = `${baseUrl}/static/widget/widget.css`;
        document.head.appendChild(css);
    }

    // Create Container DOM Element
    const container = document.createElement('div');
    container.id = 'syllabus-bot-container';
    container.innerHTML = `
        <!-- Floating Trigger Button -->
        <button class="syllabus-bot-trigger" id="sbot-trigger-btn" aria-label="Open Course Assistant">
            <i class="fa-solid fa-graduation-cap"></i>
            <div class="syllabus-bot-pulse"></div>
        </button>

        <!-- Chat Window -->
        <div class="syllabus-bot-window" id="sbot-window">
            <div class="bot-header">
                <div class="bot-profile">
                    <div class="bot-avatar"><i class="fa-solid fa-robot"></i></div>
                    <div class="bot-info">
                        <h3 id="sbot-title">Course Assistant</h3>
                        <p><span class="online-dot"></span> <span id="sbot-subtitle">Online • Syllabus AI</span></p>
                    </div>
                </div>
                <button class="bot-close-btn" id="sbot-close-btn" title="Close"><i class="fa-solid fa-xmark"></i></button>
            </div>

            <!-- Suggested Questions Bar -->
            <div class="bot-suggestions" id="sbot-suggestions">
                <button class="chip-btn" data-q="When is Assignment 2 due?">📅 Assignment 2 Due?</button>
                <button class="chip-btn" data-q="What is the late submission policy?">⏳ Late Policy?</button>
                <button class="chip-btn" data-q="What are the TA office hours?">🕒 Office Hours?</button>
            </div>

            <!-- Messages Area -->
            <div class="bot-messages" id="sbot-messages">
                <div class="widget-msg bot">
                    <div class="msg-bubble">
                        👋 Hi! I am your AI Course Assistant. Ask me anything about course policies, grading, office hours, or assignment deadlines!
                    </div>
                </div>
            </div>

            <!-- Input Area -->
            <div class="bot-input-area">
                <input type="text" id="sbot-input" placeholder="Ask a question about the course..." />
                <button class="bot-send-btn" id="sbot-send-btn"><i class="fa-solid fa-paper-plane"></i></button>
            </div>
            <div class="widget-footer-credit">
                Powered by <span>Gemini 3.6 Flash & RAG</span>
            </div>
        </div>
    `;

    document.body.appendChild(container);

    // DOM Elements
    const triggerBtn = document.getElementById('sbot-trigger-btn');
    const windowEl = document.getElementById('sbot-window');
    const closeBtn = document.getElementById('sbot-close-btn');
    const messagesEl = document.getElementById('sbot-messages');
    const inputEl = document.getElementById('sbot-input');
    const sendBtn = document.getElementById('sbot-send-btn');
    const suggestionsEl = document.getElementById('sbot-suggestions');

    // Toggle Chat Window
    triggerBtn.addEventListener('click', () => {
        windowEl.classList.toggle('open');
        if (windowEl.classList.contains('open')) {
            inputEl.focus();
        }
    });

    closeBtn.addEventListener('click', () => {
        windowEl.classList.remove('open');
    });

    // Fetch Widget Config
    fetch(`${baseUrl}/api/chat/widget-config?course_id=${courseId}`)
        .then(res => res.json())
        .then(cfg => {
            if (cfg.title) document.getElementById('sbot-title').textContent = cfg.title;
            if (cfg.subtitle) document.getElementById('sbot-subtitle').textContent = cfg.subtitle;
        })
        .catch(err => console.error("Widget config error:", err));

    // Fetch Suggested Questions
    fetch(`${baseUrl}/api/chat/suggested-questions?course_id=${courseId}`)
        .then(res => res.json())
        .then(data => {
            if (data.suggested_questions && data.suggested_questions.length) {
                suggestionsEl.innerHTML = data.suggested_questions.map(q => 
                    `<button class="chip-btn" data-q="${q}">${q}</button>`
                ).join("");
                attachSuggestionEvents();
            }
        })
        .catch(err => console.error("Suggestions fetch error:", err));

    function attachSuggestionEvents() {
        suggestionsEl.querySelectorAll('.chip-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const q = btn.getAttribute('data-q');
                if (q) {
                    inputEl.value = q;
                    handleSend();
                }
            });
        });
    }
    attachSuggestionEvents();

    // Handle Sending Messages
    sendBtn.addEventListener('click', handleSend);
    inputEl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });

    function handleSend() {
        const text = inputEl.value.trim();
        if (!text) return;

        inputEl.value = '';
        appendMessage(text, 'user');

        const typingId = appendMessage('<i class="fa-solid fa-spinner fa-spin"></i> Checking syllabus...', 'bot');

        fetch(`${baseUrl}/api/chat/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: text, course_id: courseId })
        })
        .then(res => res.json())
        .then(data => {
            removeMessage(typingId);
            appendMessage(data.answer, 'bot', data.sources);
        })
        .catch(err => {
            removeMessage(typingId);
            appendMessage("Sorry, I ran into an issue connecting to the AI assistant.", 'bot');
        });
    }

    function appendMessage(text, sender, sources = []) {
        const msgDiv = document.createElement('div');
        const id = 'msg_' + Date.now();
        msgDiv.id = id;
        msgDiv.className = `widget-msg ${sender}`;

        let formattedText = text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        let sourcesHtml = '';
        if (sources && sources.length) {
            sourcesHtml = `<div class="msg-sources"><i class="fa-solid fa-bookmark"></i> Source: ${sources.join(', ')}</div>`;
        }

        msgDiv.innerHTML = `
            <div class="msg-bubble">${formattedText}${sourcesHtml}</div>
        `;

        messagesEl.appendChild(msgDiv);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        return id;
    }

    function removeMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
})();
