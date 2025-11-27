// =========================
// 1. EVENTOS DOS CARDS (MODAL DE CONFIRMAR ENTRADA)
// =========================

document.querySelectorAll(".com-card").forEach(card => {
    card.addEventListener("click", () => {
        const modal = document.getElementById("modal-bg");
        const modalText = document.getElementById("modal-text");

        const name = card.dataset.name;
        modalText.innerText = `Você deseja entrar na comunidade "${name}"?`;

        modal.classList.remove("hidden");
    });
});

document.getElementById("btn-confirm").onclick = () => {
    window.location.href = "/metas/";
};

document.getElementById("btn-cancel").onclick = () => {
    document.getElementById("modal-bg").classList.add("hidden");
};


// =========================
// 2. MENU SUPERIOR
// =========================

const userIcon = document.getElementById('user-icon');
const dropdown = document.getElementById('user-dropdown');
const logoutBtn = document.getElementById('logout-btn');
const modalLogout = document.getElementById('logout-modal');
const confirmLogout = document.getElementById('confirm-logout');
const cancelLogout = document.getElementById('cancel-logout');

if (userIcon) {
    userIcon.addEventListener('click', () => {
        dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
    });

    window.addEventListener('click', (e) => {
        if (!userIcon.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });

    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        modalLogout.style.display = 'block';
        dropdown.style.display = 'none';
    });

    confirmLogout.addEventListener('click', () => {
        window.location.href = "/logout/";
    });

    cancelLogout.addEventListener('click', () => {
        modalLogout.style.display = 'none';
    });
}



// =========================
// 3. HOVER PARA MOSTRAR ADMIN + MEMBROS
// =========================

document.querySelectorAll(".com-card").forEach(card => {

    const infoBox = document.createElement("div");
    infoBox.classList.add("card-hover-info");

    const admin = card.dataset.admin;     // vindo do backend
    const membros = card.dataset.members; // vindo do backend

    infoBox.innerHTML = `
        <p><strong>Admin:</strong> ${admin}</p>
        <p><strong>Membros:</strong> ${membros}</p>
    `;

    card.appendChild(infoBox);

    card.addEventListener("mouseenter", () => {
        infoBox.classList.add("show");
    });

    card.addEventListener("mouseleave", () => {
        infoBox.classList.remove("show");
    });
});



// =========================
// 4. CAMPO DE BUSCA DAS COMUNIDADES
// =========================

const searchInput = document.getElementById("search-comunidade");

if (searchInput) {
    searchInput.addEventListener("input", () => {
        const filter = searchInput.value.toLowerCase();
        document.querySelectorAll(".com-card").forEach(card => {
            const name = card.dataset.name.toLowerCase();
            card.style.display = name.includes(filter) ? "block" : "none";
        });
    });
}

document.querySelectorAll(".card-comunidade").forEach(card => {
    card.addEventListener("click", () => {
        const comunidadeNome = card.dataset.nome;
        const comunidadeId = card.dataset.id;

        const modal = document.getElementById("modalEntrar");
        modal.style.display = "flex";

        document.getElementById("confirmarEntrada").onclick = () => {
            fetch(`/entrar_comunidade/${comunidadeId}/`)
                .then(() => location.reload());
        };
    });
});


// =========================
// 5. BOTÃO DE ADICIONAR COMUNIDADE (ADMIN)
// =========================

const btnAdd = document.getElementById("btn-add-comunidade");
const modalAdd = document.getElementById("modal-add-bg");
const closeAdd = document.getElementById("close-add");

if (btnAdd) {
    btnAdd.addEventListener("click", () => {
        modalAdd.classList.remove("hidden");
    });

    closeAdd.addEventListener("click", () => {
        modalAdd.classList.add("hidden");
    });
}
