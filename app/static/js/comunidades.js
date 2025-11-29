// static/js/comunidades.js  (substitua todo o arquivo por isto)
document.addEventListener("DOMContentLoaded", () => {

    // ---------- UTIL: calcula cor de texto (hex) com fallback
    function getTextColorFromHex(hex) {
        try {
            if (!hex) return null;
            hex = hex.replace("#", "");
            if (hex.length === 3) hex = hex.split('').map(h => h+h).join('');
            const r = parseInt(hex.substr(0,2), 16);
            const g = parseInt(hex.substr(2,2), 16);
            const b = parseInt(hex.substr(4,2), 16);
            const brightness = (r * 299 + g * 587 + b * 114) / 1000;
            return brightness > 150 ? "black" : "white";
        } catch (e) {
            return null;
        }
    }

    // fallback: calcula cor de texto a partir de background rgb
    function getTextColorFromComputed(bgRgb) {
        try {
            if (!bgRgb) return "black";
            const nums = bgRgb.match(/\d+/g).map(Number);
            const luminosidade = (nums[0]*0.299 + nums[1]*0.587 + nums[2]*0.114);
            return luminosidade > 150 ? "black" : "white";
        } catch (e) {
            return "black";
        }
    }

    // ---------- APLICA CORES AOS CARDS (seguro)
    document.querySelectorAll(".card-comunidade").forEach(card => {
        try {
            // tenta data-cor (hex) primeiro
            let hex = card.getAttribute("data-cor");
            let textColor = null;

            if (hex) {
                textColor = getTextColorFromHex(hex);
            }

            if (!textColor) {
                // fallback para computed style
                const bg = getComputedStyle(card).backgroundColor;
                textColor = getTextColorFromComputed(bg);
            }

            // aplica nos elementos
            const titulo = card.querySelector(".nome-comunidade");
            const admin = card.querySelector(".admin-comunidade");
            const hover = card.querySelector(".info-hover");

            if (titulo) titulo.style.color = textColor;
            if (admin) admin.style.color = textColor;
            if (hover) hover.style.color = textColor;
        } catch (err) {
            // Não deixe um erro quebrar os outros cards
            console.error("Erro aplicando cor no card:", err);
        }
    });


    // ---------- MODAL DE ENTRAR
    document.querySelectorAll(".card-comunidade").forEach(card => {
        const info = card.querySelector(".info-hover");
        // evita erro se info for nulo
        if (!info) return;

        // hover mais suave (apenas muda opacidade)
        card.addEventListener("mouseenter", () => info.style.opacity = "1");
        card.addEventListener("mouseleave", () => info.style.opacity = "0");

        // click abre modal de confirmação de entrada
        card.addEventListener("click", (ev) => {
            // se o click foi dentro do botão criar etc, ignore — mas aqui card cobre só o cartão.
            const comunidadeId = card.dataset.id;
            const modal = document.getElementById("modalEntrar");
            if (!modal) return;
            modal.style.display = "flex";

            const confirmar = document.getElementById("confirmarEntrada");
            if (confirmar) {
                confirmar.onclick = () => {
                    fetch(`/entrar_comunidade/${comunidadeId}/`)
                        .then(() => location.reload())
                        .catch(err => {
                            console.error("Erro entrar comunidade:", err);
                            alert("Erro ao entrar na comunidade.");
                        });
                };
            }
        });
    });

    // função global para fechar
    window.fecharModal = function () {
        const m = document.getElementById("modalEntrar");
        if (m) m.style.display = "none";
    };


    // ---------- BUSCA (robusta)
    (function () {
        const searchInput = document.getElementById("pesquisa");
        if (!searchInput) return;

        function normalize(str) {
            return (str || "")
                .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
                .trim()
                .toLowerCase();
        }

        searchInput.addEventListener("input", () => {
            const filtro = normalize(searchInput.value);
            const cards = document.querySelectorAll(".card-comunidade");

            if (!filtro) {
                cards.forEach(c => c.classList.remove("card-hidden"));
                return;
            }

            cards.forEach(card => {
                const dataNome = card.getAttribute("data-nome") || "";
                const tituloEl = card.querySelector(".nome-comunidade");
                const tituloText = tituloEl ? tituloEl.textContent : "";
                const combined = normalize(dataNome + " " + tituloText);

                if (combined.includes(filtro)) {
                    card.classList.remove("card-hidden");
                } else {
                    card.classList.add("card-hidden");
                }
            });
        });
    })();


    // ---------- MODAL CRIAR COMUNIDADE
    const btnAdd = document.getElementById("btnAdd");
    const modalCriar = document.getElementById("modalCriar");
    const criarConfirmar = document.getElementById("criarConfirmar");
    const criarCancelar = document.getElementById("criarCancelar");

    if (btnAdd && modalCriar) {
        btnAdd.addEventListener("click", () => modalCriar.style.display = "flex");
    }
    if (criarCancelar) {
        criarCancelar.addEventListener("click", () => modalCriar.style.display = "none");
    }

    if (criarConfirmar) {
        criarConfirmar.addEventListener("click", async () => {
            const nomeEl = document.getElementById("novoNome");
            const corEl = document.getElementById("novaCor");
            const nome = nomeEl ? nomeEl.value.trim() : "";
            const cor = corEl ? corEl.value : "#ffffff";

            if (!nome) { alert("Dê um nome à comunidade!"); return; }

            const csrftoken = document.cookie
                .split("; ")
                .find(row => row.startsWith("csrftoken"))
                ?.split("=")[1];

            try {
                const response = await fetch("/criar-comunidade/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrftoken
                    },
                    body: JSON.stringify({ nome, cor })
                });
                const data = await response.json();
                if (data.status === "ok") location.reload();
                else alert("Erro ao criar comunidade.");
            } catch (err) {
                console.error(err);
                alert("Erro ao criar comunidade.");
            }
        });
    }

    // Fecha modal criar ao clicar fora
    window.addEventListener("click", e => {
        if (e.target === modalCriar) modalCriar.style.display = "none";
    });

}); // DOMContentLoaded end

document.getElementById("confirmarEntrada").addEventListener("click", function () {
  const comunidadeId = document.getElementById("modalEntrar").getAttribute("data-id");
  if (comunidadeId) {
    window.location.href = `/comunidade/${comunidadeId}/metas/`;
  }
});

document.getElementById("cancelarEntrada").addEventListener("click", function () {
  document.getElementById("modalEntrar").style.display = "none";
});

document.querySelectorAll(".card-comunidade").forEach(card => {
  card.addEventListener("click", () => {
    const id = card.getAttribute("data-id");
    const modal = document.getElementById("modalEntrar");
    modal.setAttribute("data-id", id);
    modal.style.display = "flex";
  });
});
