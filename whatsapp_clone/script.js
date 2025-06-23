// WhatsApp Clone JavaScript with Supabase Integration


class WhatsAppClone {
    constructor() {
        this.currentUser = null;
        this.currentSession = null;
        this.whatsappEnabled = false;
        this.whatsappPhone = '';
        this.messages = [];
        this.sessions = [];
        this.isTyping = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSettings();
        
        // Check if user is already logged in
        const savedUser = localStorage.getItem('whatsapp_user');
        if (savedUser) {
            this.currentUser = JSON.parse(savedUser);
            this.showWhatsAppInterface();
        }
    }

    setupEventListeners() {
        // Message input
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            messageInput.addEventListener('input', () => {
                this.updateSendButton();
            });
        }

        // Click outside menu to close
        document.addEventListener('click', (e) => {
            const menuOverlay = document.getElementById('menuOverlay');
            if (e.target === menuOverlay) {
                this.hideMenu();
            }
        });

        // WhatsApp toggle
        const whatsappToggle = document.getElementById('whatsappToggle');
        if (whatsappToggle) {
            whatsappToggle.addEventListener('change', (e) => {
                this.whatsappEnabled = e.target.checked;
                this.saveSettings();
            });
        }
    }

    // Google OAuth Integration with Supabase
    async handleCredentialResponse(response) {
        try {
            // Decode JWT token
            const payload = JSON.parse(atob(response.credential.split('.')[1]));
            
            const userData = {
                id: payload.sub,
                name: payload.name,
                email: payload.email,
                picture: payload.picture,
                login_method: 'google'
            };

            // Create or update user in Supabase
            const userResponse = await fetch('/whatsapp-clone/api/user/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });

            if (userResponse.ok) {
                const result = await userResponse.json();
                this.currentUser = {
                    ...userData,
                    id: result.user.id, // Use Supabase user ID
                    loginTime: new Date().toISOString()
                };

                localStorage.setItem('whatsapp_user', JSON.stringify(this.currentUser));
                this.showToast('Successfully logged in with Google!', 'success');
                await this.showWhatsAppInterface();
            } else {
                throw new Error('Failed to create user in database');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showToast('Login failed. Please try again.', 'error');
        }
    }

    // Demo login without Google OAuth
    async demoLogin() {
        const userData = {
            email: 'demo@example.com',
            name: 'Demo User',
            picture: 'https://via.placeholder.com/40',
            login_method: 'demo'
        };
  
        try {
            // Create or get demo user from Supabase
            const userResponse = await fetch('/whatsapp-clone/api/user/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });

            if (userResponse.ok) {
                const result = await userResponse.json();
                this.currentUser = {
                    ...userData,
                    id: result.user.id,
                    loginTime: new Date().toISOString()
                };

                localStorage.setItem('whatsapp_user', JSON.stringify(this.currentUser));
                this.showToast('Welcome to the demo!', 'success');
                await this.showWhatsAppInterface();
            } else {
                throw new Error('Failed to create demo user');
            }
        } catch (error) {
            console.error('Demo login error:', error);
            this.showToast('Demo login failed. Please try again.', 'error');
        }
    }

    async showWhatsAppInterface() {
        document.getElementById('loginScreen').style.display = 'none';
        document.getElementById('whatsappInterface').style.display = 'flex';
        
        // Update user info
        document.getElementById('userName').textContent = this.currentUser.name;
        document.getElementById('userAvatar').src = this.currentUser.picture;
        
        // Load user sessions and chat history
        await this.loadUserSessions();
        await this.loadChatHistory();
        
        // Focus message input
        setTimeout(() => {
            document.getElementById('messageInput').focus();
        }, 100);
    }

    async loadUserSessions() {
        try {
            const response = await fetch(`/api/user/${this.currentUser.id}/sessions`);
            if (response.ok) {
                const data = await response.json();
                this.sessions = data.sessions;
                
                // If no sessions exist, create a default one
                if (this.sessions.length === 0) {
                    await this.createNewSession();
                } else {
                    // Use the most recent session
                    this.currentSession = this.sessions[0];
                }
                
                this.updateSessionsList();
            }
        } catch (error) {
            console.error('Error loading sessions:', error);
            // Create a default session if loading fails
            await this.createNewSession();
        }
    }

    async createNewSession(title = 'New Chat') {
        try {
            const response = await fetch('/whatsapp-clone/api/session/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    title: title
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.currentSession = data.session;
                this.sessions.unshift(data.session);
                this.updateSessionsList();
                return data.session;
            }
        } catch (error) {
            console.error('Error creating session:', error);
        }
        return null;
    }

    updateSessionsList() {
        // Update the chat list in the sidebar
        const chatList = document.querySelector('.chat-list');
        if (chatList && this.sessions.length > 0) {
            chatList.innerHTML = '';
            
            this.sessions.forEach((session, index) => {
                const chatItem = document.createElement('div');
                chatItem.className = `chat-item ${index === 0 ? 'active' : ''}`;
                chatItem.dataset.sessionId = session.id;
                
                const lastMessageTime = new Date(session.updated_at).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
                
                chatItem.innerHTML = `
                    <img src="https://via.placeholder.com/50" alt="AI Assistant" class="chat-avatar">
                    <div class="chat-info">
                        <div class="chat-header">
                            <h3>🇺🇬 ${session.title}</h3>
                            <span class="chat-time">${lastMessageTime}</span>
                        </div>
                        <p class="last-message">Messages: ${session.message_count}</p>
                    </div>
                    <div class="chat-status">
                        ${session.message_count > 0 ? `<span class="unread-count">${session.message_count}</span>` : ''}
                    </div>
                `;
                
                chatItem.addEventListener('click', () => this.switchToSession(session));
                chatList.appendChild(chatItem);
            });
        }
    }

    async switchToSession(session) {
        this.currentSession = session;
        
        // Update active session in UI
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-session-id="${session.id}"]`).classList.add('active');
        
        // Load messages for this session
        await this.loadSessionMessages(session.id);
    }

    async loadSessionMessages(sessionId) {
        try {
            const response = await fetch(`/api/session/${sessionId}/messages`);
            if (response.ok) {
                const data = await response.json();
                this.messages = data.messages;
                this.displayMessages();
            }
        } catch (error) {
            console.error('Error loading session messages:', error);
        }
    }

    displayMessages() {
        const messagesContainer = document.getElementById('messagesContainer');
        messagesContainer.innerHTML = '';
        
        if (this.messages.length === 0) {
            this.addWelcomeMessage();
        } else {
            this.messages.forEach(msg => {
                this.displayMessage(msg.content, msg.message_type === 'user' ? 'sent' : 'received', msg.timestamp);
            });
        }
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const messageText = messageInput.value.trim();
        
        if (!messageText) return;

        // Clear input and disable send button
        messageInput.value = '';
        this.updateSendButton();

        // Add user message to chat immediately
        this.addMessage(messageText, 'sent');
        
        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Send to AI backend with Supabase integration
            const aiResponse = await this.sendToAI(messageText);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add AI response to chat
            this.addMessage(aiResponse.reply, 'received');
            
            // Update current session ID if it was created
            if (aiResponse.session_id && !this.currentSession) {
                this.currentSession = { id: aiResponse.session_id };
            }
            
            // Send via WhatsApp if enabled
            if (this.whatsappEnabled && this.whatsappPhone) {
                await this.sendViaWhatsApp(messageText, aiResponse.reply);
            }
            
            // Refresh sessions list to show updated message count
            await this.loadUserSessions();
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('Sorry, I encountered an error. Please try again.', 'received');
            this.showToast('Failed to send message', 'error');
        }
    }

    async sendToAI(message) {
        try {
            // Send to AI backend with user data and session info
            const response = await fetch('/whatsapp/webhook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    Body: message,
                    From: this.currentUser.id,
                    session_id: this.currentSession?.id,
                    source: 'web_clone',
                    user_data: {
                        email: this.currentUser.email,
                        name: this.currentUser.name,
                        picture: this.currentUser.picture,
                        login_method: this.currentUser.login_method || 'demo'
                    }
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
            
        } catch (error) {
            console.error('AI API error:', error);
            
            // Fallback response
            return {
                reply: `🇺🇬 Hello! I'm the Uganda E-Government assistant.

I can help you with:
• Birth Certificate (NIRA) - Check status with reference number
• Tax Status (URA) - Check balance with TIN number  
• NSSF Balance - Check contributions with membership number
• Land Verification (NLIS) - Verify ownership with plot details

Just tell me what you need help with, or provide your reference numbers directly.

Examples:
• "Check my birth certificate NIRA/2023/123456"
• "My TIN is 1234567890, what's my tax status?"
• "I need help with land verification"

Available in English, Luganda, Luo, and Runyoro.

How can I assist you today?`,
                status: 'fallback'
            };
        }
    }

    async sendViaWhatsApp(userMessage, aiResponse) {
        try {
            const response = await fetch('/api/whatsapp/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    to: this.whatsappPhone,
                    message: `User: ${userMessage}\n\nAI: ${aiResponse}`,
                    from_web: true
                })
            });

            if (response.ok) {
                this.showToast('Message sent via WhatsApp!', 'success');
            } else {
                console.error('WhatsApp send failed');
            }
        } catch (error) {
            console.error('WhatsApp error:', error);
        }
    }

    addMessage(text, type) {
        const messagesContainer = document.getElementById('messagesContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${this.formatMessageText(text)}
            </div>
            <div class="message-time">${timeString}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.updateChatPreview(text);
    }

    displayMessage(text, type, timestamp) {
        const messagesContainer = document.getElementById('messagesContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const time = new Date(timestamp);
        const timeString = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${this.formatMessageText(text)}
            </div>
            <div class="message-time">${timeString}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatMessageText(text) {
        // Convert line breaks to <br> and format lists
        return text
            .replace(/\n/g, '<br>')
            .replace(/•\s/g, '<li>')
            .replace(/(<li>.*?)(<br>|$)/g, '<ul>$1</li></ul>')
            .replace(/<\/ul><ul>/g, '');
    }

    showTypingIndicator() {
        document.getElementById('loadingIndicator').style.display = 'flex';
        this.isTyping = true;
    }

    hideTypingIndicator() {
        document.getElementById('loadingIndicator').style.display = 'none';
        this.isTyping = false;
    }

    updateSendButton() {
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        
        if (messageInput && sendBtn) {
            sendBtn.disabled = !messageInput.value.trim() || this.isTyping;
        }
    }

    updateChatPreview(lastMessage) {
        // Update the current session preview
        if (this.currentSession) {
            const chatItem = document.querySelector(`[data-session-id="${this.currentSession.id}"]`);
            if (chatItem) {
                const lastMessageEl = chatItem.querySelector('.last-message');
                const timeEl = chatItem.querySelector('.chat-time');
                
                if (lastMessageEl) {
                    lastMessageEl.textContent = lastMessage.substring(0, 50) + (lastMessage.length > 50 ? '...' : '');
                }
                
                if (timeEl) {
                    const now = new Date();
                    timeEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                }
            }
        }
    }

    // Menu functions
    showMenu() {
        document.getElementById('menuOverlay').style.display = 'flex';
    }

    hideMenu() {
        document.getElementById('menuOverlay').style.display = 'none';
    }

    async showProfile() {
        this.hideMenu();
        
        try {
            // Get user stats from Supabase
            const response = await fetch(`/api/user/${this.currentUser.id}/stats`);
            if (response.ok) {
                const data = await response.json();
                const stats = data.stats;
                
                alert(`Profile:\nName: ${this.currentUser.name}\nEmail: ${this.currentUser.email}\nLogin Time: ${new Date(this.currentUser.loginTime).toLocaleString()}\n\nStats:\nTotal Messages: ${stats.total_messages || 0}\nTotal Sessions: ${stats.total_sessions || 0}\nFirst Message: ${stats.first_message_date ? new Date(stats.first_message_date).toLocaleDateString() : 'N/A'}`);
            } else {
                alert(`Profile:\nName: ${this.currentUser.name}\nEmail: ${this.currentUser.email}\nLogin Time: ${new Date(this.currentUser.loginTime).toLocaleString()}`);
            }
        } catch (error) {
            console.error('Error loading profile stats:', error);
            alert(`Profile:\nName: ${this.currentUser.name}\nEmail: ${this.currentUser.email}\nLogin Time: ${new Date(this.currentUser.loginTime).toLocaleString()}`);
        }
    }

    showSettings() {
        this.hideMenu();
        this.showToast('Settings panel coming soon!', 'info');
    }

    showWhatsAppSettings() {
        this.hideMenu();
        document.getElementById('whatsappModal').style.display = 'flex';
        
        // Load current settings
        document.getElementById('whatsappPhone').value = this.whatsappPhone;
        document.getElementById('enableWhatsAppSync').checked = this.whatsappEnabled;
    }

    closeWhatsAppModal() {
        document.getElementById('whatsappModal').style.display = 'none';
    }

    saveWhatsAppSettings() {
        this.whatsappPhone = document.getElementById('whatsappPhone').value;
        this.whatsappEnabled = document.getElementById('enableWhatsAppSync').checked;
        
        this.saveSettings();
        this.closeWhatsAppModal();
        this.showToast('WhatsApp settings saved!', 'success');
    }

    logout() {
        this.hideMenu();
        
        if (confirm('Are you sure you want to log out?')) {
            localStorage.removeItem('whatsapp_user');
            localStorage.removeItem('whatsapp_settings');
            
            this.currentUser = null;
            this.currentSession = null;
            this.messages = [];
            this.sessions = [];
            
            document.getElementById('whatsappInterface').style.display = 'none';
            document.getElementById('loginScreen').style.display = 'flex';
            
            this.showToast('Logged out successfully', 'success');
        }
    }

    // Storage functions
    saveSettings() {
        const settings = {
            whatsappEnabled: this.whatsappEnabled,
            whatsappPhone: this.whatsappPhone
        };
        localStorage.setItem('whatsapp_settings', JSON.stringify(settings));
    }

    loadSettings() {
        const settings = localStorage.getItem('whatsapp_settings');
        if (settings) {
            const parsed = JSON.parse(settings);
            this.whatsappEnabled = parsed.whatsappEnabled || false;
            this.whatsappPhone = parsed.whatsappPhone || '';
            
            // Update UI
            const whatsappToggle = document.getElementById('whatsappToggle');
            if (whatsappToggle) {
                whatsappToggle.checked = this.whatsappEnabled;
            }
        }
    }

    async loadChatHistory() {
        // Load from Supabase instead of localStorage
        if (this.currentSession) {
            await this.loadSessionMessages(this.currentSession.id);
        } else if (this.sessions.length > 0) {
            await this.loadSessionMessages(this.sessions[0].id);
        } else {
            this.addWelcomeMessage();
        }
    }

    addWelcomeMessage() {
        const welcomeText = `🇺🇬 Hello ${this.currentUser.name}! I'm the Uganda E-Government assistant.

I can help you with:
• Birth Certificate (NIRA) - Check status with reference number
• Tax Status (URA) - Check balance with TIN number  
• NSSF Balance - Check contributions with membership number
• Land Verification (NLIS) - Verify ownership with plot details

Just tell me what you need help with, or provide your reference numbers directly.

Examples:
• "Check my birth certificate NIRA/2023/123456"
• "My TIN is 1234567890, what's my tax status?"
• "I need help with land verification"

Available in English, Luganda, Luo, and Runyoro.

How can I assist you today?`;

        this.addMessage(welcomeText, 'received');
    }

    // Toast notifications
    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? 'fas fa-check-circle' : 
                    type === 'error' ? 'fas fa-exclamation-circle' : 
                    type === 'warning' ? 'fas fa-exclamation-triangle' : 
                    'fas fa-info-circle';
        
        toast.innerHTML = `
            <i class="${icon}"></i>
            <span>${message}</span>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    // Search functionality
    async searchMessages(query) {
        try {
            const response = await fetch(`/api/search/messages?user_id=${this.currentUser.id}&query=${encodeURIComponent(query)}`);
            if (response.ok) {
                const data = await response.json();
                return data.messages;
            }
        } catch (error) {
            console.error('Error searching messages:', error);
        }
        return [];
    }
}

// Global functions for HTML onclick handlers
let whatsappClone;

function demoLogin() {
    whatsappClone.demoLogin();
}
function handleCredentialResponse(response) {
    whatsappClone.handleCredentialResponse(response);
}

function demoLogin() {
    whatsappClone.demoLogin();
}

function sendMessage() {
    whatsappClone.sendMessage();
}

function showMenu() {
    whatsappClone.showMenu();
}

function showProfile() {
    whatsappClone.showProfile();
}

function showSettings() {
    whatsappClone.showSettings();
}

function showWhatsAppSettings() {
    whatsappClone.showWhatsAppSettings();
}

function closeWhatsAppModal() {
    whatsappClone.closeWhatsAppModal();
}

function saveWhatsAppSettings() {
    whatsappClone.saveWhatsAppSettings();
}

function logout() {
    whatsappClone.logout();
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    whatsappClone = new WhatsAppClone();
});

// Service Worker for PWA functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}