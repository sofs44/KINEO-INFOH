(async function () {
    const msgEl = document.getElementById('message');
    const chatEl = document.getElementById('chat-container');
    const chatBox = document.getElementById('chat-box');
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const token = localStorage.getItem('kineo_token');

    // 1. Verifica autenticação (exemplo: token no localStorage)
    if (!token) {
        msgEl.innerHTML = `<h3 class="mensg">Encontre seu parceiro/comunidade, faça seu<a href="login.html" class="bttLogin">Login</a> para acessar o chat.</h3>`;
        chatEl.style.display = 'none';
        return;
    }

    // 2️⃣ Usuário logado: esconde a mensagem inicial e mostra o chat
    msgEl.style.display = 'none';
    chatEl.style.display = 'flex';  // ou 'block', conforme seu layout

    // 2. Busca mensagens da comunidade (API exemplo)
    let msgs = [];
    try {
        const resp = await fetch('/api/chat', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (resp.ok) msgs = await resp.json();
    } catch (e) {
        console.error(e);
    }

    // 3. Renderiza de acordo com os dados
    if (msgs.length === 0) {
        msgEl.textContent = 'Você ainda não iniciou nenhuma conversa.';
        return;
    }

    // 4. Se houver mensagens, mostra o chat
    msgEl.style.display = 'none';
    chatEl.style.display = 'flex';

    function renderMessages() {
        chatBox.innerHTML = '';
        msgs.forEach(m => {
            const div = document.createElement('div');
            div.className = 'message ' + (m.de_mim ? 'from-me' : 'from-you');
            div.textContent = m.texto;
            chatBox.appendChild(div);
        });
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    renderMessages();

    // 5. Enviar nova mensagem
    sendBtn.addEventListener('click', async () => {
        const text = input.value.trim();
        if (!text) return;
        // Exibir imediatamente
        msgs.push({ texto: text, de_mim: true });
        renderMessages();
        input.value = '';
        // Enviar ao servidor
        try {
            await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                },
                body: JSON.stringify({ mensagem: text })
            });
        } catch (e) {
            console.error(e);
        }
    });

})();