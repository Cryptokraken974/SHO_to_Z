/**
 * Chat Component
 */
window.componentManager.register('chat', (props = {}) => {
    const { 
        placeholder = 'Type a prompt...', 
        models = [{ value: 'o3', label: 'o3' }, { value: '4o', label: '4o' }],
        defaultModel = 'o3'
    } = props;
    
    return `
        <div id="chatbar" class="bg-[#1a1a1a] border-t border-[#303030] p-4">
            <div id="chat-log" class="max-h-[150px] overflow-y-auto mb-3 space-y-2"></div>
            <div id="chat-controls" class="flex gap-3">
                <textarea id="chat-input" placeholder="${placeholder}" class="flex-1 bg-[#262626] border border-[#404040] rounded-lg px-3 py-2 text-white placeholder-[#ababab] resize-none focus:outline-none focus:border-[#00bfff]"></textarea>
                <select id="chat-model" class="bg-[#262626] border border-[#404040] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-[#00bfff]">
                    ${models.map(model => `
                        <option value="${model.value}" ${model.value === defaultModel ? 'selected' : ''}>${model.label}</option>
                    `).join('')}
                </select>
                <button id="chat-send" class="bg-[#00bfff] hover:bg-[#0099cc] text-white px-6 py-2 rounded-lg font-medium transition-colors">Send</button>
            </div>
        </div>
    `;
}, {
    onRender: (element) => {
        // Set up chat functionality
        setupChatControls(element);
    }
});

function setupChatControls(container) {
    const chatInput = container.querySelector('#chat-input');
    const chatSend = container.querySelector('#chat-send');
    
    // Handle Enter key
    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatSend?.click();
            }
        });
    }
    
    // Auto-resize textarea
    if (chatInput) {
        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
        });
    }
}
