// View Switching
document.addEventListener('DOMContentLoaded', function() {
    // Navigation items
    const navItems = document.querySelectorAll('.nav-item');
    const viewContents = document.querySelectorAll('.view-content');
    
    // Modal elements
    const modal = document.getElementById('createProjectModal');
    const newBtn = document.getElementById('newBtn');
    const closeModal = document.getElementById('closeModal');
    const cancelModal = document.getElementById('cancelModal');
    const createProject = document.getElementById('createProject');
    
    // File explorer
    const fileItems = document.querySelectorAll('.file-item');
    
    // Search functionality
    const searchInput = document.querySelector('.search-bar input');
    
    // Notifications
    const notificationsBtn = document.getElementById('notificationsBtn');
    const profileBtn = document.getElementById('profileBtn');
    
    // AI Assistant
    const aiInput = document.querySelector('.ai-input input');
    const aiSendBtn = document.querySelector('.ai-input button');
    
    // Environment variables
    const envVars = document.querySelectorAll('.env-var');
    
    // Quick actions
    const quickActions = document.querySelectorAll('.quick-actions button');
    
    // View switching functionality
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const targetView = this.getAttribute('data-view');
            
            // Remove active class from all nav items
            navItems.forEach(nav => nav.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Hide all view contents
            viewContents.forEach(view => view.classList.add('hidden'));
            
            // Show target view
            const targetElement = document.getElementById(`${targetView}-view`);
            if (targetElement) {
                targetElement.classList.remove('hidden');
            }
            
            // Update right sidebar context based on view
            updateRightSidebar(targetView);
        });
    });
    
    // File explorer functionality
    fileItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all file items
            fileItems.forEach(file => file.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Update editor header with file name
            const fileName = this.querySelector('span').textContent;
            const editorHeader = document.querySelector('.editor-header span');
            if (editorHeader) {
                editorHeader.textContent = fileName;
            }
            
            // Simulate loading file content
            loadFileContent(fileName);
        });
    });
    
    // Load file content (simulation)
    function loadFileContent(fileName) {
        const editorContent = document.querySelector('.editor-content pre code');
        if (!editorContent) return;
        
        const fileContents = {
            'index.html': `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My App</title>
</head>
<body>
    <h1>Hello World!</h1>
    <script src="app.js"></script>
</body>
</html>`,
            'styles.css': `body {
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
    background: #f0f0f0;
}

h1 {
    color: #333;
    text-align: center;
    margin-top: 50px;
}`,
            'app.js': `function app() {
    console.log('Hello World!');
    return 'Welcome to my app';
}

document.addEventListener('DOMContentLoaded', function() {
    const message = app();
    console.log(message);
});`
        };
        
        editorContent.textContent = fileContents[fileName] || '// File content not available';
    }
    
    // Modal functionality
    newBtn.addEventListener('click', function() {
        modal.classList.remove('hidden');
    });
    
    closeModal.addEventListener('click', function() {
        modal.classList.add('hidden');
    });
    
    cancelModal.addEventListener('click', function() {
        modal.classList.add('hidden');
    });
    
    createProject.addEventListener('click', function() {
        const projectName = document.getElementById('projectName').value;
        const projectTemplate = document.getElementById('projectTemplate').value;
        
        if (projectName.trim()) {
            // Simulate project creation
            console.log('Creating project:', projectName, 'Template:', projectTemplate);
            
            // Add to project dropdown
            const projectSelector = document.getElementById('projectSelector');
            const newOption = document.createElement('option');
            newOption.textContent = projectName;
            newOption.selected = true;
            projectSelector.appendChild(newOption);
            
            // Clear form and close modal
            document.getElementById('projectName').value = '';
            modal.classList.add('hidden');
            
            // Show success notification
            showNotification('Project created successfully!', 'success');
        }
    });
    
    // Search functionality
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        
        if (searchTerm.length > 2) {
            // Simulate search results
            console.log('Searching for:', searchTerm);
            // In a real app, this would filter content or show search results
        }
    });
    
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const searchTerm = e.target.value;
            if (searchTerm) {
                console.log('Execute search:', searchTerm);
                // In a real app, this would perform the search
            }
        }
    });
    
    // Notifications
    notificationsBtn.addEventListener('click', function() {
        showNotification('You have 3 new notifications', 'info');
    });
    
    profileBtn.addEventListener('click', function() {
        showNotification('Profile settings coming soon!', 'info');
    });
    
    // AI Assistant
    aiSendBtn.addEventListener('click', function() {
        const question = aiInput.value.trim();
        if (question) {
            // Simulate AI response
            addAIMessage(question);
            aiInput.value = '';
            
            // Simulate AI thinking and responding
            setTimeout(() => {
                addAIResponse(getAIResponse(question));
            }, 1000);
        }
    });
    
    aiInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            aiSendBtn.click();
        }
    });
    
    function addAIMessage(message) {
        const aiSuggestion = document.querySelector('.ai-suggestion');
        if (aiSuggestion) {
            aiSuggestion.innerHTML = `<p>You: ${message}</p>`;
        }
    }
    
    function addAIResponse(response) {
        const aiSuggestion = document.querySelector('.ai-suggestion');
        if (aiSuggestion) {
            aiSuggestion.innerHTML += `<p style="color: #4a9eff; margin-top: 8px;">AI: ${response}</p>`;
        }
    }
    
    function getAIResponse(question) {
        const responses = {
            'summarize this code': 'This code appears to be a basic HTML structure with JavaScript integration.',
            'how to deploy': 'You can deploy by clicking the Deploy button in the repository view.',
            'database help': 'Use the Database view to manage your tables and data.',
            'default': 'I\'m here to help! Ask me about your code, deployment, or any development questions.'
        };
        
        const lowerQuestion = question.toLowerCase();
        for (const [key, value] of Object.entries(responses)) {
            if (lowerQuestion.includes(key)) {
                return value;
            }
        }
        return responses.default;
    }
    
    // Environment variables (click to reveal)
    envVars.forEach(envVar => {
        envVar.addEventListener('click', function() {
            const valueElement = this.querySelector('.env-value');
            if (valueElement.textContent === '********') {
                // Simulate revealing the value
                valueElement.textContent = 'hidden-value-revealed';
                setTimeout(() => {
                    valueElement.textContent = '********';
                }, 2000);
            }
        });
    });
    
    // Quick actions
    quickActions.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.textContent.trim();
            handleQuickAction(action);
        });
    });
    
    function handleQuickAction(action) {
        switch(action) {
            case 'Restart':
                showNotification('Restarting server...', 'info');
                addLog('> Server restarting...');
                setTimeout(() => {
                    addLog('> Server restarted successfully');
                    showNotification('Server restarted!', 'success');
                }, 2000);
                break;
            case 'Stop':
                showNotification('Stopping server...', 'info');
                addLog('> Server stopping...');
                setTimeout(() => {
                    addLog('> Server stopped');
                    showNotification('Server stopped!', 'warning');
                }, 1500);
                break;
            case 'Clear Logs':
                const logsContainer = document.querySelector('.logs');
                if (logsContainer) {
                    logsContainer.innerHTML = '';
                    addLog('> Logs cleared');
                }
                break;
        }
    }
    
    function addLog(message) {
        const logsContainer = document.querySelector('.logs');
        if (logsContainer) {
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.innerHTML = `
                <span class="timestamp">${timestamp}</span>
                <span class="log-text">${message}</span>
            `;
            logsContainer.appendChild(logEntry);
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
    }
    
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '80px',
            right: '20px',
            background: type === 'success' ? '#4caf50' : type === 'warning' ? '#ff9800' : '#4a9eff',
            color: 'white',
            padding: '12px 20px',
            borderRadius: '6px',
            zIndex: '3000',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    // Update right sidebar based on current view
    function updateRightSidebar(viewName) {
        // This would update the right sidebar content based on the current view
        // For now, we'll just add some context-specific logs
        const logsContainer = document.querySelector('.logs');
        if (logsContainer) {
            addLog(`> Switched to ${viewName} view`);
        }
    }
    
    // Close modal when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.classList.add('hidden');
        }
    });
    
    // Database table interactions
    const tableRows = document.querySelectorAll('.data-table tbody tr');
    tableRows.forEach(row => {
        const editBtn = row.querySelector('.btn-secondary');
        const deleteBtn = row.querySelector('.btn-danger');
        
        if (editBtn) {
            editBtn.addEventListener('click', function() {
                showNotification('Edit functionality coming soon!', 'info');
            });
        }
        
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function() {
                if (confirm('Are you sure you want to delete this row?')) {
                    row.remove();
                    showNotification('Row deleted successfully!', 'success');
                    addLog('> Database row deleted');
                }
            });
        }
    });
    
    // Deployment actions
    const deploymentButtons = document.querySelectorAll('.deployment-item button');
    deploymentButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.textContent.trim();
            if (action === 'View Logs') {
                addLog('> Opening deployment logs...');
                showNotification('Deployment logs opened!', 'info');
            } else if (action === 'Retry') {
                addLog('> Retrying deployment...');
                showNotification('Deployment retry initiated!', 'info');
                setTimeout(() => {
                    addLog('> Deployment completed successfully');
                    showNotification('Deployment successful!', 'success');
                }, 3000);
            }
        });
    });
    
    // Initialize with dashboard view
    addLog('> Application started successfully');
    addLog('> Welcome to Xenitide Dashboard');
});
