// static/js/chat.js
document.addEventListener('DOMContentLoaded', function () {
    const menuBtn = document.getElementById('menu-dots-btn');
    const menuModal = document.getElementById('menu-modal');
    const overlay = document.getElementById('modal-overlay');
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
  
    // helper: get csrf from meta
    function getCSRF() {
      const m = document.querySelector('meta[name="csrf-token"]');
      return m ? m.getAttribute('content') : '';
    }
  
    // utility show/hide
    function show(el){ el.classList.remove('hidden'); el.setAttribute('aria-hidden','false'); }
    function hide(el){ el.classList.add('hidden'); el.setAttribute('aria-hidden','true'); }
  
    // posicionamento do dropdown próximo à search (melhora UX)
    function positionMenuDropdown() {
      const searchBar = document.querySelector('.search-bar');
      if(!menuModal || !searchBar) return;
      const rect = searchBar.getBoundingClientRect();
      // coloca o menu à direita do searchBar
      menuModal.style.top = (rect.bottom + window.scrollY + 8) + 'px';
      menuModal.style.left = (rect.right + window.scrollX - 60) + 'px';
    }
  
    // abrir/fechar menu de três bolinhas
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
      // mostrar checkboxes
      document.querySelectorAll('.conv-select-checkbox').forEach(cb => cb.classList.remove('hidden'));
      // mostrar ícone de lixeira no header da busca
      const trash = document.getElementById('trash-selected-btn');
      if(trash) show(trash);
      // fechar menu-overlay
      hide(menuModal);
    });
  
    // clicar em item de conversa alterna seleção quando em selection-mode
    convList && convList.addEventListener('click', function(ev) {
      const item = ev.target.closest('.conversation-item');
      if(!item) return;
      if(sidebar.classList.contains('selection-mode')) {
        ev.preventDefault();
        const checkbox = item.querySelector('.conv-select-checkbox');
        checkbox.checked = !checkbox.checked;
        item.classList.toggle('selected', checkbox.checked);
        updateTrashState();
      } else {
        // comportamento normal do link (navegar) - nada especial
      }
    });
  
    function updateTrashState() {
      const selected = convList.querySelectorAll('.conv-select-checkbox:checked');
      if(selected.length > 0) show(trashBtn);
      else {
        // se não houver selecionados, exibir só o botão de iniciar (trash permanece visível até sair do modo).
        // aqui deixamos o botão visível, mas desativado se 0 selecionados
        if(trashBtn) {
          // apenas estilização: desabilitar
          if(selected.length === 0) trashBtn.disabled = true;
          else trashBtn.disabled = false;
        }
      }
    }
  
    // clique no ícone de lixeira -> abre modal de confirmação
    trashBtn && trashBtn.addEventListener('click', () => {
      // se nenhum selecionado, ignora
      const selectedBoxes = convList.querySelectorAll('.conv-select-checkbox:checked');
      if(selectedBoxes.length === 0) return;
      show(confirmDeleteModal);
      show(overlay);
    });
  
    confirmNo && confirmNo.addEventListener('click', () => {
      hide(confirmDeleteModal);
      hide(overlay);
    });
  
    // confirmar exclusão -> envia ids para backend
    confirmYes && confirmYes.addEventListener('click', async () => {
      const selectedBoxes = convList.querySelectorAll('.conv-select-checkbox:checked');
      const ids = Array.from(selectedBoxes).map(cb => cb.closest('.conversation-item').dataset.convId);
      // chamada ao backend (implemente a view)
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
          // remover itens do DOM
          selectedBoxes.forEach(cb => {
            const item = cb.closest('.conversation-item');
            if(item) item.remove();
          });
          hide(confirmDeleteModal);
          hide(overlay);
          // sair do modo seleção
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
  
    // fechar modais com ESC
    document.addEventListener('keydown', function(e){
      if(e.key === 'Escape') {
        hide(menuModal);
        hide(confirmDeleteModal);
        hide(createGroupModal);
        hide(overlay);
        exitSelectionMode();
      }
    });
  
    // overlay click fecha modais
    overlay && overlay.addEventListener('click', () => {
      hide(menuModal);
      hide(confirmDeleteModal);
      hide(createGroupModal);
      hide(overlay);
      exitSelectionMode();
    });
  
    // === CRIAR GRUPO ===
    createGroupBtn && createGroupBtn.addEventListener('click', () => {
      // popular a lista de usuários a partir das conversas já carregadas no DOM
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
  
    // adicionar campo de meta
    addGoalBtn && addGoalBtn.addEventListener('click', () => {
      const div = document.createElement('div');
      div.className = 'goal-row';
      div.innerHTML = `<input name="goal[]" class="goal-input" type="text" placeholder="Nova meta"> <button type="button" class="btn small remove-goal">x</button>`;
      document.getElementById('group-goals').appendChild(div);
  
      // remover meta
      div.querySelector('.remove-goal').addEventListener('click', () => div.remove());
    });
  
    // submit criar grupo -> envia para backend
    createGroupForm && createGroupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const form = e.target;
      const groupName = form.querySelector('#group-name').value.trim();
      if(!groupName) return alert('Digite um nome para o grupo.');
  
      const members = Array.from(form.querySelectorAll('input[name="members"]:checked')).map(n => n.value);
      // metas
      const goals = Array.from(form.querySelectorAll('input[name="goal[]"], .goal-input')).map(g => g.value.trim()).filter(x => x);
  
      // enviar para backend
      try {
        const resp = await fetch('/chat/create_group/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRF()
          },
          body: JSON.stringify({
            name: groupName,
            members,
            goals
          })
        });
        if(resp.ok) {
          hide(createGroupModal);
          hide(overlay);
          alert('Grupo criado com sucesso!');
          // opcional: recarregar lista de conversas
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
  
    // ==========================
    // small UX: quando textarea cresce, ajusta rows automaticamente (auto-height)
    const textarea = document.getElementById('message-textarea');
    if(textarea){
      const adjust = () => {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
        // limita
        if(textarea.scrollHeight > 160) textarea.style.height = '160px';
      };
      textarea.addEventListener('input', adjust);
      // ajustar init
      adjust();
    }

        // Mostra/oculta o menu do usuário
        const userIcon = document.getElementById('user-icon');
        const dropdown = document.getElementById('user-dropdown');
        const logoutBtn = document.getElementById('logout-btn');
        const modal = document.getElementById('logout-modal');
        const confirmLogout = document.getElementById('confirm-logout');
        const cancelLogout = document.getElementById('cancel-logout');
      
        userIcon.addEventListener('click', () => {
          dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
        });
      
        // Fecha o menu se clicar fora
        window.addEventListener('click', (e) => {
          if (!userIcon.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
          }
        });
      
        // Abre o modal de confirmação
        logoutBtn.addEventListener('click', (e) => {
          e.preventDefault();
          modal.style.display = 'block';
          dropdown.style.display = 'none';
        });
      
        // Confirmar logout
        confirmLogout.addEventListener('click', () => {
          window.location.href = "{% url 'logout' %}";
        });
      
        // Cancelar logout
        cancelLogout.addEventListener('click', () => {
          modal.style.display = 'none';
        });
    
  }
);

  
  
  