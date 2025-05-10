// WebSocket functionality for real-time chat
let socket;
let isConnected = false;
let typingTimeout;
let currentRoom = '';

// Initialize WebSocket connection
function initWebSocket() {
    // Check if WebSocket is already initialized
    if (isConnected) return;
    
    // Get the current username from the page
    const username = document.querySelector('.dropdown-toggle') ? 
        document.querySelector('.dropdown-toggle').textContent.trim() : null;
    
    if (!username) {
        console.error('Username not found, cannot initialize WebSocket');
        return;
    }
    
    // Get the current room name from the URL if in a chat room
    const urlParts = window.location.pathname.split('/');
    if (urlParts.includes('chat_room')) {
        const roomIndex = urlParts.indexOf('chat_room') + 1;
        if (roomIndex < urlParts.length) {
            currentRoom = urlParts[roomIndex];
        }
    }
    
    // Initialize Socket.IO connection
    socket = io();
    
    // Connection event
    socket.on('connect', function() {
        console.log('WebSocket connected');
        isConnected = true;
        
        // Authenticate with the server
        socket.emit('authenticate', { username: username });
        
        // Join the current room if in a chat room
        if (currentRoom) {
            socket.emit('join_room', { room: currentRoom });
            console.log(`Joined room: ${currentRoom}`);
        }
    });
    
    // Disconnection event
    socket.on('disconnect', function() {
        console.log('WebSocket disconnected');
        isConnected = false;
    });
    
    // Error event
    socket.on('error', function(data) {
        console.error('WebSocket error:', data.message);
    });
    
    // Authentication response
    socket.on('authenticated', function(data) {
        console.log(`Authenticated as ${data.username}`);
    });
    
    // New message event
    socket.on('chat_message', function(data) {
        // Add message to the chat if in the same room
        if (currentRoom === data.room) {
            addMessageToChat(data);
        }
    });
    
    // User joined event
    socket.on('user_joined', function(data) {
        if (currentRoom === data.room) {
            // Add system message
            addSystemMessage(`${data.username} has joined the room`);
            
            // Add user to active users list if not already there
            addUserToActiveList(data.username);
        }
    });
    
    // User left event
    socket.on('user_left', function(data) {
        if (currentRoom === data.room) {
            // Add system message
            addSystemMessage(`${data.username} has left the room`);
            
            // Remove user from active users list
            removeUserFromActiveList(data.username);
        }
    });
    
    // User typing event
    socket.on('user_typing', function(data) {
        if (currentRoom === data.room) {
            updateTypingIndicator(data.username, data.typing);
        }
    });
    
    // User status event (online/offline)
    socket.on('user_status', function(data) {
        updateUserStatus(data.username, data.status);
    });
}

// Send a message via WebSocket
function sendMessageViaWebSocket(message) {
    if (!isConnected || !socket) {
        console.error('WebSocket not connected');
        return false;
    }
    
    socket.emit('new_message', {
        room: currentRoom,
        message: message
    });
    
    return true;
}

// Send typing indicator
function sendTypingIndicator(isTyping) {
    if (!isConnected || !socket || !currentRoom) {
        return;
    }
    
    socket.emit('typing', {
        room: currentRoom,
        typing: isTyping
    });
}

// Add a message to the chat
function addMessageToChat(data) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const isCurrentUser = data.username === document.querySelector('.dropdown-toggle').textContent.trim();
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${isCurrentUser ? 'message-self' : ''}`;
    
    // Format timestamp
    const timestamp = data.timestamp || new Date().toLocaleTimeString();
    
    // Create sentiment indicator if available
    let sentimentIcon = '';
    if (data.sentiment !== undefined && data.sentiment !== null) {
        if (data.sentiment > 0.2) {
            sentimentIcon = '<i class="bi bi-emoji-smile text-success" title="Positive"></i>';
        } else if (data.sentiment < -0.2) {
            sentimentIcon = '<i class="bi bi-emoji-frown text-danger" title="Negative"></i>';
        } else {
            sentimentIcon = '<i class="bi bi-emoji-neutral text-muted" title="Neutral"></i>';
        }
    }
    
    messageElement.innerHTML = `
        <div class="message-header">
            <span class="message-username">${data.username}</span>
            <span class="message-time">${timestamp}</span>
        </div>
        <div class="message-content">
            ${data.message}
            ${sentimentIcon}
        </div>
    `;
    
    chatMessages.appendChild(messageElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add a system message to the chat
function addSystemMessage(message) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message message-system';
    
    messageElement.innerHTML = `
        <div class="message-content text-center">
            <i class="bi bi-info-circle me-2"></i>${message}
        </div>
    `;
    
    chatMessages.appendChild(messageElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add a user to the active users list
function addUserToActiveList(username) {
    const activeUsersContainer = document.getElementById('activeUsersContainer');
    if (!activeUsersContainer) return;
    
    // Check if user is already in the list
    const existingUser = activeUsersContainer.querySelector(`[data-username="${username}"]`);
    if (existingUser) return;
    
    const userList = activeUsersContainer.querySelector('ul');
    if (!userList) return;
    
    const isCurrentUser = username === document.querySelector('.dropdown-toggle').textContent.trim();
    
    const userElement = document.createElement('li');
    userElement.className = 'list-group-item d-flex justify-content-between align-items-center';
    userElement.setAttribute('data-username', username);
    
    userElement.innerHTML = `
        ${username}
        ${isCurrentUser ? '<span class="badge bg-primary rounded-pill">You</span>' : ''}
    `;
    
    userList.appendChild(userElement);
}

// Remove a user from the active users list
function removeUserFromActiveList(username) {
    const activeUsersContainer = document.getElementById('activeUsersContainer');
    if (!activeUsersContainer) return;
    
    const userElement = activeUsersContainer.querySelector(`[data-username="${username}"]`);
    if (userElement) {
        userElement.remove();
    }
}

// Update typing indicator
function updateTypingIndicator(username, isTyping) {
    const typingIndicator = document.getElementById('typingIndicator');
    if (!typingIndicator) return;
    
    if (isTyping) {
        typingIndicator.textContent = `${username} is typing...`;
        typingIndicator.style.display = 'block';
    } else {
        typingIndicator.style.display = 'none';
    }
}

// Update user status (online/offline)
function updateUserStatus(username, status) {
    const activeUsersContainer = document.getElementById('activeUsersContainer');
    if (!activeUsersContainer) return;
    
    const userElement = activeUsersContainer.querySelector(`[data-username="${username}"]`);
    
    if (status === 'online') {
        // Add user to active list if not already there
        if (!userElement) {
            addUserToActiveList(username);
        }
    } else if (status === 'offline') {
        // Remove user from active list
        if (userElement) {
            userElement.remove();
        }
    }
}

// Handle input for typing indicator
function handleChatInput() {
    const messageInput = document.getElementById('messageInput');
    if (!messageInput) return;
    
    messageInput.addEventListener('input', function() {
        // Clear previous timeout
        if (typingTimeout) {
            clearTimeout(typingTimeout);
        }
        
        // Send typing indicator
        sendTypingIndicator(true);
        
        // Set timeout to stop typing indicator after 2 seconds of inactivity
        typingTimeout = setTimeout(function() {
            sendTypingIndicator(false);
        }, 2000);
    });
}

// Initialize WebSocket when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Add typing indicator to chat room
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        const typingIndicator = document.createElement('div');
        typingIndicator.id = 'typingIndicator';
        typingIndicator.className = 'typing-indicator';
        typingIndicator.style.display = 'none';
        chatMessages.parentNode.insertBefore(typingIndicator, chatMessages.nextSibling);
        
        // Initialize typing indicator handler
        handleChatInput();
    }
    
    // Initialize WebSocket
    initWebSocket();
    
    // Modify the message form to use WebSockets
    const messageForm = document.getElementById('messageForm');
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            // Don't prevent default - let the form submit normally as fallback
            // But also try to send via WebSocket
            const messageInput = document.getElementById('messageInput');
            if (messageInput && isConnected) {
                sendMessageViaWebSocket(messageInput.value);
            }
        });
    }
});
