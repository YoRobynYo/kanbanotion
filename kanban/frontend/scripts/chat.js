// chat.js - Enhanced with draggable, resizable chat window
document.addEventListener('DOMContentLoaded', () => {
    const chatButton = document.getElementById('chatButton');
    const chatWindow = document.getElementById('chatWindow');
    const chatHeader = document.querySelector('.chat-header');
    const chatClose = document.getElementById('chatClose');
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const resetChatBtn = document.getElementById('reset-chat-btn');
    
    const backendUrl = 'http://127.0.0.1:8000/api/chat';
    const resetUrl = 'http://127.0.0.1:8000/api/chat/reset';

    // --- DARK MODE TOGGLE ---
    const darkModeBtn = document.getElementById('dark-mode-toggle');
    let isDarkMode = localStorage.getItem('darkMode') === 'true';
    
    function toggleDarkMode() {
        isDarkMode = !isDarkMode;
        document.body.classList.toggle('dark-mode', isDarkMode);
        localStorage.setItem('darkMode', isDarkMode);
        darkModeBtn.textContent = isDarkMode ? '☀️' : '🌙';
    }
    
    if (darkModeBtn) {
        darkModeBtn.addEventListener('click', toggleDarkMode);
        if (isDarkMode) {
            document.body.classList.add('dark-mode');
            darkModeBtn.textContent = '☀️';
        }
    }

    // --- CHAT WINDOW TOGGLE ---
    chatButton.addEventListener('click', () => {
        chatWindow.classList.add('active');
    });

    chatClose.addEventListener('click', () => {
        chatWindow.classList.remove('active');
    });

    // --- DRAGGABLE CHAT WINDOW ---
    let isDragging = false;
    let currentX;
    let currentY;
    let initialX;
    let initialY;

    chatHeader.style.cursor = 'move';

    chatHeader.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', dragEnd);

    function dragStart(e) {
        // Don't drag if clicking close button
        if (e.target.closest('.chat-close')) return;
        
        isDragging = true;
        initialX = e.clientX - chatWindow.offsetLeft;
        initialY = e.clientY - chatWindow.offsetTop;
        chatHeader.style.cursor = 'grabbing';
    }

    function drag(e) {
        if (!isDragging) return;
        
        e.preventDefault();
        currentX = e.clientX - initialX;
        currentY = e.clientY - initialY;

        // Keep window within viewport
        const maxX = window.innerWidth - chatWindow.offsetWidth;
        const maxY = window.innerHeight - chatWindow.offsetHeight;
        
        currentX = Math.max(0, Math.min(currentX, maxX));
        currentY = Math.max(0, Math.min(currentY, maxY));

        chatWindow.style.left = currentX + 'px';
        chatWindow.style.top = currentY + 'px';
        chatWindow.style.right = 'auto';
        chatWindow.style.bottom = 'auto';
    }

    function dragEnd() {
        isDragging = false;
        chatHeader.style.cursor = 'move';
    }

    // --- RESIZABLE CHAT WINDOW ---
    const resizeHandle = document.createElement('div');
    resizeHandle.className = 'resize-handle';
    resizeHandle.innerHTML = '⋰';
    chatWindow.appendChild(resizeHandle);

    let isResizing = false;
    let startWidth;
    let startHeight;
    let startX;
    let startY;

    resizeHandle.addEventListener('mousedown', resizeStart);
    document.addEventListener('mousemove', resize);
    document.addEventListener('mouseup', resizeEnd);

    function resizeStart(e) {
        isResizing = true;
        startWidth = chatWindow.offsetWidth;
        startHeight = chatWindow.offsetHeight;
        startX = e.clientX;
        startY = e.clientY;
        e.preventDefault();
    }

    function resize(e) {
        if (!isResizing) return;
        
        const width = startWidth + (e.clientX - startX);
        const height = startHeight + (e.clientY - startY);

        // Min/max constraints
        if (width >= 350 && width <= 800) {
            chatWindow.style.width = width + 'px';
        }
        if (height >= 400 && height <= 800) {
            chatWindow.style.height = height + 'px';
        }
    }

    function resizeEnd() {
        isResizing = false;
    }

    // --- RESET CHAT WITH BACKEND CALL ---
    resetChatBtn.addEventListener('click', async () => {
        if (confirm("Are you sure you want to reset the chat? This will clear the conversation.")) {
            await resetChat();
        }
    });

    async function resetChat() {
        try {
            const response = await fetch(resetUrl, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
                throw new Error('Reset failed');
            }
            
            chatMessages.innerHTML = '';
            addMessage("Chat reset successfully. How can I assist you today?", 'ai');
            chatInput.value = '';
            
            console.log('✅ Chat reset successful');
        } catch (error) {
            console.error('❌ Error resetting chat:', error);
            addMessage("Failed to reset chat. Please try again.", 'ai');
        }
    }

    // --- CHAT COMMUNICATION ---
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const userMessage = chatInput.value.trim();
        if (!userMessage) return;

        addMessage(userMessage, 'user');
        chatInput.value = '';

        try {
            const response = await fetch(backendUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMessage }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            addMessage(data.reply, 'ai');
            
        } catch (error) {
            console.error("❌ Error communicating with backend:", error);
            addMessage("Sorry, I can't connect to the server. Please ensure the backend is running.", 'ai');
        }
    });

    // --- ADD MESSAGE TO CHAT ---
    function addMessage(text, sender) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message', sender);

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = text;

        messageContainer.appendChild(bubble);
        chatMessages.appendChild(messageContainer);
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // --- MOBILE DETECTION ---
    function isMobile() {
        return window.innerWidth <= 768;
    }

    // Adjust chat window for mobile
    if (isMobile()) {
        chatWindow.classList.add('mobile-fullscreen');
    }

    window.addEventListener('resize', () => {
        if (isMobile()) {
            chatWindow.classList.add('mobile-fullscreen');
        } else {
            chatWindow.classList.remove('mobile-fullscreen');
        }
    });

    // Initialize with welcome message
    addMessage("Hello! How can I assist you today?", 'ai');
    
    console.log('✅ Enhanced chat system initialized');
});

// new colomn layout for chat.js 
// console.log("--- CHAT SCRIPT HAS LOADED ---");

// document.addEventListener('DOMContentLoaded', () => {
//   const chatButton = document.getElementById('chatButton');
//   const chatWindow = document.getElementById('chatWindow');
//   const chatClose = document.getElementById('chatClose');
//   const chatForm = document.getElementById('chatForm');
//   const chatInput = document.getElementById('chatInput');
//   const chatMessages = document.getElementById('chatMessages');
//   const resetChatBtn = document.getElementById('reset-chat-btn');

//   // Auto-detect backend host

//   // Explicitly define the correct backend address
//   const API_BASE_URL = 'http://127.0.0.1:8000/api';
//   const backendUrl = `${API_BASE_URL}/chat`;
//   const resetUrl = `${API_BASE_URL}/chat/reset`;

//   chatButton.addEventListener('click', () => chatWindow.classList.add('active'));
//   // chatClose.addEventListener('click', () => chatWindow.classList.remove('active'));

//   // Replace the old line with this block:
// chatClose.addEventListener('click', () => {
//     console.log("--- CLOSE BUTTON WAS CLICKED! ---"); // The test message
//     chatWindow.classList.remove('active');
// });

//   resetChatBtn.addEventListener('click', async () => {
//     if (confirm("Reset chat history?")) await resetChat();
//   });

//   async function resetChat() {
//     try {
//       const response = await fetch(resetUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
//       if (!response.ok) throw new Error('Reset failed');
//       chatMessages.innerHTML = '';
//       addMessage("Chat reset successfully. How can I assist you today?", 'ai');
//     } catch (error) {
//       console.error('Error resetting chat:', error);
//       addMessage("Failed to reset chat. Please try again.", 'ai');
//     }
//   }

//   chatForm.addEventListener('submit', async (e) => {
//     e.preventDefault();
//     const userMessage = chatInput.value.trim();
//     if (!userMessage) return;

//     addMessage(userMessage, 'user');
//     chatInput.value = '';

//     try {
//       const response = await fetch(backendUrl, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ message: userMessage }),
//       });

//       if (!response.ok) throw new Error(`HTTP ${response.status}`);
//       const data = await response.json();
//       addMessage(data.reply, 'ai');
//     } catch (error) {
//       console.error("Error communicating with backend:", error);
//       addMessage(`Sorry, I can't reach the server (${backendUrl}).`, 'ai');
//     }
//   });

//   function addMessage(text, sender) {
//     const messageContainer = document.createElement('div');
//     messageContainer.classList.add('message', sender);
//     const bubble = document.createElement('div');
//     bubble.className = 'message-bubble';
//     bubble.textContent = text;
//     messageContainer.appendChild(bubble);
//     chatMessages.appendChild(messageContainer);
//     chatMessages.scrollTop = chatMessages.scrollHeight;
//   }

//   addMessage("Hello! How can I assist you today?", 'ai');
// });



// This is your working code with a single, small correction to the addMessage function to fix the bubble styling.
// Plus: Added reset chat functionality with confirmation.

// document.addEventListener('DOMContentLoaded', () => {
//     const chatButton = document.getElementById('chatButton');
//     const chatWindow = document.getElementById('chatWindow');
//     const chatClose = document.getElementById('chatClose');
//     const chatForm = document.getElementById('chatForm');
//     const chatInput = document.getElementById('chatInput');
//     const chatMessages = document.getElementById('chatMessages');
//     const resetChatBtn = document.getElementById('reset-chat-btn'); // 👈 Reset button

//     const backendUrl = 'http://127.0.0.1:8000/api/chat';

//     // --- CHAT WINDOW TOGGLE LOGIC ---
//     chatButton.addEventListener('click', () => {
//         chatWindow.classList.toggle('open');
//     });

//     chatClose.addEventListener('click', () => {
//         chatWindow.classList.remove('open');
//     });

//     // --- RESET CHAT WITH CONFIRMATION ---
//     resetChatBtn.addEventListener('click', () => {
//         if (confirm("Are you sure you want to reset the chat? This will clear the conversation.")) {
//             resetChat();
//         }
//     });

//     function resetChat() {
//         chatMessages.innerHTML = '';
//         addMessage("Hello! How can I assist you today?", 'ai');
//         chatInput.value = '';
//     }

//     // --- CHAT COMMUNICATION LOGIC ---
//     chatForm.addEventListener('submit', async (e) => {
//         e.preventDefault();
//         const userMessage = chatInput.value.trim();
//         if (!userMessage) return;

//         addMessage(userMessage, 'user');
//         chatInput.value = '';

//         try {
//             const response = await fetch(backendUrl, {
//                 method: 'POST',
//                 headers: { 'Content-Type': 'application/json' },
//                 body: JSON.stringify({ message: userMessage }),
//             });

//             if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

//             const data = await response.json();
//             addMessage(data.reply, 'ai'); 
//         } catch (error) {
//             console.error("Error communicating with backend:", error);
//             addMessage("Sorry, I can't connect to the server. Please ensure the Python backend is running.", 'ai');
//         }
//     });

//     // --- FUNCTION TO ADD MESSAGES TO CHAT WINDOW ---
//     function addMessage(text, sender) {
//         const messageContainer = document.createElement('div');
//         messageContainer.classList.add('message', sender);

//         const bubble = document.createElement('div');
//         bubble.className = 'message-bubble';
//         bubble.textContent = text;

//         messageContainer.appendChild(bubble);
//         chatMessages.appendChild(messageContainer);
//         chatMessages.scrollTop = chatMessages.scrollHeight;
//     }

//     // Initialize chat
//     resetChat();
// });