// static/js/chat.js
document.addEventListener('DOMContentLoaded', function () {

    // ==========================================
    // PARTE 1: LÓGICA DO CHAT (MANTIDA ORIGINAL)
    // ==========================================
    const menuBtn = document.getElementById('menu-dots-btn');
    const menuModal = document.getElementById('menu-modal');
    const overlay = document.getElementById('modal-overlay'); // Overlay do CHAT
    const startDeleteBtn = document.getElementById('start-delete-mode');
    const trashBtn = document.getElementById('trash-selected-btn');
    const convList = document.getElementById('conversations-list');
    const sidebar = document.querySelector('.chat-sidebar');
    const confirmDeleteModal = document.getElementById('confirm-delete-modal');
    const confirmYes = document.getElementById('confirm-delete-yes');
    const confirmNo = document.getElementById('confirm-delete-no');
  
    const createGroupBtn = document.getElementById('open-create-group-modal');
    const createGroupModal = document.getElementById('create-group-modal');
    const cancelCreateGroup = document.getElementById('cancel-create-group');
    const createGroupForm = document.getElementById('create-group-form');
    const usersToAdd = document.getElementById('users-to-add');
    const addGoalBtn = document.getElementById('add-goal-btn');
  
    // Helper: get csrf from meta
    function getCSRF() {
      const m = document.querySelector('meta[name="csrf-token"]');
      return m ? m.getAttribute('content') : '';
    }
  
    // Utility show/hide (USADO SÓ PELO CHAT)
    function show(el){ 
        if(el) { 
            el.classList.remove('hidden'); 
            el.setAttribute('aria-hidden','false'); 
            // Não forçamos display block aqui para evitar conflito se o CSS já tratar
        } 
    }
    function hide(el){ 
        if(el) { 
            el.classList.add('hidden'); 
            el.setAttribute('aria-hidden','true'); 
        } 
    }
  
    // Posicionamento do dropdown próximo à search
    function positionMenuDropdown() {
      const searchBar = document.querySelector('.search-bar');
      if(!menuModal || !searchBar) return;
      const rect = searchBar.getBoundingClientRect();
      menuModal.style.top = (rect.bottom + window.scrollY + 8) + 'px';
      menuModal.style.left = (rect.right + window.scrollX - 60) + 'px';
    }
  
    // Abrir/fechar menu de três bolinhas
    menuBtn && menuBtn.addEventListener('click', e => {
      positionMenuDropdown();
      if(menuModal.classList.contains('hidden')) {
        show(menuModal);
        document.addEventListener('click', clickAwayMenu);
      } else {
        hide(menuModal);
        document.removeEventListener('click', clickAwayMenu);
      }
    });
  
    function clickAwayMenu(ev) {
      if(!menuModal.contains(ev.target) && ev.target !== menuBtn) {
        hide(menuModal);
        document.removeEventListener('click', clickAwayMenu);
      }
    }
  
    // === MODO SELEÇÃO ===
    startDeleteBtn && startDeleteBtn.addEventListener('click', () => {
      hide(menuModal);
      sidebar.classList.add('selection-mode');
      document.querySelectorAll('.conv-select-checkbox').forEach(cb => cb.classList.remove('hidden'));
      const trash = document.getElementById('trash-selected-btn');
      if(trash) {
          trash.classList.remove('hidden'); // Força remover hidden manualmente
          trash.style.display = 'block';
      }
    });
  
    convList && convList.addEventListener('click', function(ev) {
      const item = ev.target.closest('.conversation-item');
      if(!item) return;
      if(sidebar.classList.contains('selection-mode')) {
        ev.preventDefault();
        const checkbox = item.querySelector('.conv-select-checkbox');
        checkbox.checked = !checkbox.checked;
        item.classList.toggle('selected', checkbox.checked);
        updateTrashState();
      }
    });
  
    function updateTrashState() {
      const selected = convList.querySelectorAll('.conv-select-checkbox:checked');
      if(selected.length > 0) {
          if(trashBtn) {
              trashBtn.classList.remove('hidden');
              trashBtn.disabled = false;
          }
      } else {
        if(trashBtn) {
          if(selected.length === 0) trashBtn.disabled = true;
          else trashBtn.disabled = false;
        }
      }
    }
  
    trashBtn && trashBtn.addEventListener('click', () => {
      const selectedBoxes = convList.querySelectorAll('.conv-select-checkbox:checked');
      if(selectedBoxes.length === 0) return;
      show(confirmDeleteModal);
      show(overlay);
    });
  
    confirmNo && confirmNo.addEventListener('click', () => {
      hide(confirmDeleteModal);
      hide(overlay);
    });
  
    confirmYes && confirmYes.addEventListener('click', async () => {
      const selectedBoxes = convList.querySelectorAll('.conv-select-checkbox:checked');
      const ids = Array.from(selectedBoxes).map(cb => cb.closest('.conversation-item').dataset.convId);
      try {
        const resp = await fetch('/chat/delete_conversations/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRF()
          },
          body: JSON.stringify({ conversation_ids: ids })
        });
        if(resp.ok) {
          selectedBoxes.forEach(cb => {
            const item = cb.closest('.conversation-item');
            if(item) item.remove();
          });
          hide(confirmDeleteModal);
          hide(overlay);
          exitSelectionMode();
        } else {
          const text = await resp.text();
          alert('Erro ao apagar: ' + text);
        }
      } catch (err) {
        alert('Erro de rede ao apagar conversas.');
        console.error(err);
      }
    });
  
    function exitSelectionMode() {
      sidebar.classList.remove('selection-mode');
      document.querySelectorAll('.conv-select-checkbox').forEach(cb => {
        cb.checked = false;
        cb.classList.add('hidden');
        if(cb.closest('.conversation-item')) cb.closest('.conversation-item').classList.remove('selected');
      });
      if(trashBtn) hide(trashBtn);
    }
  
    // === CRIAR GRUPO ===
    createGroupBtn && createGroupBtn.addEventListener('click', () => {
      usersToAdd.innerHTML = '';
      const items = document.querySelectorAll('.conversation-item');
      items.forEach(it => {
        const id = it.dataset.convId;
        const name = it.querySelector('.name') ? it.querySelector('.name').textContent.trim() : 'Usuário';
        const row = document.createElement('div');
        row.className = 'user-row';
        row.innerHTML = `
          <label style="flex:1;display:flex;gap:8px;align-items:center;">
            <input type="checkbox" name="members" value="${id}">
            <span>${name}</span>
          </label>
        `;
        usersToAdd.appendChild(row);
      });
      show(createGroupModal);
      show(overlay);
      hide(menuModal);
    });
  
    cancelCreateGroup && cancelCreateGroup.addEventListener('click', () => {
      hide(createGroupModal);
      hide(overlay);
    });
  
    addGoalBtn && addGoalBtn.addEventListener('click', () => {
      const div = document.createElement('div');
      div.className = 'goal-row';
      div.innerHTML = `<input name="goal[]" class="goal-input" type="text" placeholder="Nova meta"> <button type="button" class="btn small remove-goal">x</button>`;
      document.getElementById('group-goals').appendChild(div);
      div.querySelector('.remove-goal').addEventListener('click', () => div.remove());
    });
  
    createGroupForm && createGroupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const form = e.target;
      const groupName = form.querySelector('#group-name').value.trim();
      if(!groupName) return alert('Digite um nome para o grupo.');
      const members = Array.from(form.querySelectorAll('input[name="members"]:checked')).map(n => n.value);
      const goals = Array.from(form.querySelectorAll('input[name="goal[]"], .goal-input')).map(g => g.value.trim()).filter(x => x);
  
      try {
        const resp = await fetch('/chat/create_group/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRF()
          },
          body: JSON.stringify({ name: groupName, members, goals })
        });
        if(resp.ok) {
          hide(createGroupModal);
          hide(overlay);
          alert('Grupo criado com sucesso!');
          location.reload();
        } else {
          const text = await resp.text();
          alert('Falha criando grupo: ' + text);
        }
      } catch (err) {
        alert('Erro de rede ao criar grupo.');
        console.error(err);
      }
    });
  
    const textarea = document.getElementById('message-textarea');
    if(textarea){
      const adjust = () => {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
        if(textarea.scrollHeight > 160) textarea.style.height = '160px';
      };
      textarea.addEventListener('input', adjust);
      adjust();
    }

    // ==========================================
    // PARTE 2: LÓGICA DA NAVBAR (CORRIGIDA)
    // ==========================================
    
    // Variáveis da Navbar com prefixo 'nav' para não misturar com o chat
    const navUserIcon = document.getElementById('user-icon');
    const navDropdown = document.getElementById('user-dropdown');
    const navLogoutBtn = document.getElementById('logout-btn');
    const navLogoutModal = document.getElementById('logout-modal');
    const navConfirmLogout = document.getElementById('confirm-logout');
    const navCancelLogout = document.getElementById('cancel-logout');

    // 1. Toggle do Menu Dropdown (Perfil/Sair)
    if (navUserIcon && navDropdown) {
        navUserIcon.addEventListener('click', (e) => {
            e.stopPropagation(); // Impede que o clique feche imediatamente
            const isVisible = navDropdown.style.display === 'block';
            navDropdown.style.display = isVisible ? 'none' : 'block';
        });

        // Fechar ao clicar fora
        window.addEventListener('click', (e) => {
            if (!navUserIcon.contains(e.target) && !navDropdown.contains(e.target)) {
                navDropdown.style.display = 'none';
            }
        });
    }

    // 2. Abrir Modal de Logout
    if (navLogoutBtn && navLogoutModal) {
        navLogoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            // Fecha o dropdown do usuário
            if(navDropdown) navDropdown.style.display = 'none';
            // Abre o modal de logout
            navLogoutModal.style.display = 'block';
        });
    }

    // 3. Confirmar Logout
    if (navConfirmLogout) {
        navConfirmLogout.addEventListener('click', () => {
            // Pega a URL do atributo data-url que colocamos no HTML
            const logoutUrl = navConfirmLogout.getAttribute('data-url');
            if (logoutUrl) {
                window.location.href = logoutUrl;
            } else {
                // Fallback caso o atributo falhe
                window.location.href = '/logout/'; 
            }
        });
    }

    // 4. Cancelar Logout
    if (navCancelLogout && navLogoutModal) {
        navCancelLogout.addEventListener('click', () => {
            navLogoutModal.style.display = 'none';
        });
    }

    // ==========================================
    // PARTE 3: FECHAMENTO GLOBAL DE MODAIS (ESC e OVERLAY)
    // ==========================================
    
    // Fechar modais com ESC
    document.addEventListener('keydown', function(e){
      if(e.key === 'Escape') {
        // Chat Modals
        hide(menuModal);
        hide(confirmDeleteModal);
        hide(createGroupModal);
        hide(overlay);
        exitSelectionMode();

        // Navbar Modals
        if(navDropdown) navDropdown.style.display = 'none';
        if(navLogoutModal) navLogoutModal.style.display = 'none';
      }
    });
  
    // Overlay click fecha modais do chat E da navbar
    if(overlay) {
        overlay.addEventListener('click', () => {
            // Chat
            hide(menuModal);
            hide(confirmDeleteModal);
            hide(createGroupModal);
            hide(overlay);
            exitSelectionMode();
            
            // Navbar (se estiver usando o mesmo overlay, senão ignore)
            if(navLogoutModal) navLogoutModal.style.display = 'none';
        });
    }
});