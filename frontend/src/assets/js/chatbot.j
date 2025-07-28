// Chatbot functionality

// Chatbot toggle function
function toggleChatbot() {
    const chatbot = document.getElementById('chatbot');
    chatbot.classList.toggle('translate-y-full');
    chatbot.classList.toggle('translate-y-0');
    
    const toggleButton = document.getElementById('chatbot-toggle');
    if (chatbot.classList.contains('translate-y-0')) {
        toggleButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>';
        appState.chatbotOpen = true;
    } else {
        toggleButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>';
        appState.chatbotOpen = false;
    }
}

// Send chat message function
function sendChatMessage() {
    const input = document.getElementById('chatbot-input');
    const message = input.value.trim();
    
    if (message) {
        const chatContainer = document.querySelector('.chatbot-container');
        
        // Add user message
        const userMessage = document.createElement('div');
        userMessage.className = 'user-message mb-3 p-3 ml-auto max-w-[80%]';
        userMessage.innerHTML = `<p class="text-sm">${message}</p>`;
        chatContainer.appendChild(userMessage);
        
        // Clear input
        input.value = '';
        
        // Show typing indicator
        showTypingIndicator(chatContainer);
        
        // Simulate bot response after a short delay
        setTimeout(() => {
            removeTypingIndicator(chatContainer);
            const botMessage = createBotResponse(message);
            chatContainer.appendChild(botMessage);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 1000);
        
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Show typing indicator
function showTypingIndicator(container) {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'bot-message mb-3 p-3 typing-indicator';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="flex items-center space-x-1">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    container.appendChild(typingDiv);
}

// Remove typing indicator
function removeTypingIndicator(container) {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Create bot response based on user message
function createBotResponse(message) {
    const botMessage = document.createElement('div');
    botMessage.className = 'bot-message mb-3 p-3';
    
    const lowerMessage = message.toLowerCase();
    
    // Simple response logic based on keywords
    if (lowerMessage.includes('trí tuệ nhân tạo') || lowerMessage.includes('ai')) {
        botMessage.innerHTML = `
            <p class="text-sm">Học phần Trí tuệ nhân tạo (IT4060) có 2 lớp:</p>
            <ul class="text-sm list-disc pl-5 mt-1">
                <li>Lớp 1: Thứ 3 (13:00 - 16:00), Phòng D5-301, GV: PGS.TS. Trần Thị B</li>
                <li>Lớp 2: Thứ 4 (7:00 - 10:00), Phòng D3-201, GV: TS. Lê Văn G</li>
            </ul>
            <p class="text-sm mt-2">Bạn muốn đăng ký lớp nào?</p>
        `;
    } else if (lowerMessage.includes('học máy') || lowerMessage.includes('machine learning')) {
        botMessage.innerHTML = `
            <p class="text-sm">Học phần Học máy (IT4995) là một môn học nâng cao về AI/ML. Môn học này có các nội dung:</p>
            <ul class="text-sm list-disc pl-5 mt-1">
                <li>Các thuật toán học có giám sát và không giám sát</li>
                <li>Mạng neural và học sâu</li>
                <li>Ứng dụng thực tế của học máy</li>
            </ul>
            <p class="text-sm mt-2">Môn học này rất phù hợp với định hướng AI/ML của bạn.</p>
        `;
    } else if (lowerMessage.includes('đăng ký') || lowerMessage.includes('register')) {
        botMessage.innerHTML = `
            <p class="text-sm">Để đăng ký học phần, bạn cần:</p>
            <ol class="text-sm list-decimal pl-5 mt-1">
                <li>Chọn tab "Đăng ký học phần" trên menu</li>
                <li>Tìm kiếm học phần bạn muốn đăng ký</li>
                <li>Chọn lớp học phù hợp</li>
                <li>Nhấn "Xác nhận đăng ký" để hoàn tất</li>
            </ol>
            <p class="text-sm mt-2">Bạn cần giúp đỡ với học phần cụ thể nào không?</p>
        `;
    } else if (lowerMessage.includes('thời khóa biểu') || lowerMessage.includes('lịch học')) {
        botMessage.innerHTML = `
            <p class="text-sm">Thời khóa biểu của bạn hiện có 6 học phần với tổng 16 tín chỉ. Bạn học 5 ngày/tuần, với ngày học nhiều nhất là thứ 5 (6 tiết).</p>
            <p class="text-sm mt-2">Bạn có muốn tối ưu hóa thời khóa biểu không? Tôi có thể giúp bạn sắp xếp lịch học hiệu quả hơn.</p>
        `;
    } else if (lowerMessage.includes('gpa') || lowerMessage.includes('điểm')) {
        botMessage.innerHTML = `
            <p class="text-sm">GPA hiện tại của bạn là ${appState.user.gpa}, xếp loại Giỏi. Bạn đã hoàn thành ${appState.user.creditsCompleted}/${appState.user.totalCredits} tín chỉ.</p>
            <p class="text-sm mt-2">Bạn có muốn xem chi tiết kết quả học tập không?</p>
        `;
    } else {
        botMessage.innerHTML = `
            <p class="text-sm">Tôi có thể giúp bạn với các vấn đề sau:</p>
            <ul class="text-sm list-disc pl-5 mt-1">
                <li>Tư vấn về các học phần phù hợp</li>
                <li>Giải đáp thắc mắc về đăng ký học phần</li>
                <li>Thông tin về giảng viên và lớp học</li>
                <li>Gợi ý lịch học tối ưu</li>
                <li>Xem thông tin GPA và kết quả học tập</li>
            </ul>
            <p class="text-sm mt-2">Bạn cần hỗ trợ cụ thể về vấn đề nào?</p>
        `;
    }
    
    return botMessage;
}

// Handle Enter key in chatbot input
document.addEventListener('DOMContentLoaded', function() {
    const chatbotInput = document.getElementById('chatbot-input');
    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
});

// Export functions
window.toggleChatbot = toggleChatbot;
window.sendChatMessage = sendChatMessage; 