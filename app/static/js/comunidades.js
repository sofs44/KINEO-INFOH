document.addEventListener("DOMContentLoaded", () => {

    // ---------- Ajusta cor do texto automaticamente ----------
    function isColorDark(hex) {
        hex = hex.replace("#", "");

        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);

        // fórmula de luminosidade
        const luminancia = (0.299*r + 0.587*g + 0.114*b) / 255;

        return luminancia < 0.5; // true = escuro
    }

    document.querySelectorAll(".card-comunidade").forEach(card => {
        const bg = card.style.backgroundColor;

        let hex = bg;

        // Converte rgb para hex se necessário
        if (bg.startsWith("rgb")) {
            const nums = bg.match(/\d+/g).map(Number);
            hex = "#" + nums.map(x => x.toString(16).padStart(2, "0")).join("");
        }

        const dark = isColorDark(hex);

        // texto branco ou preto
        card.style.color = dark ? "white" : "black";

        card.querySelector(".info-hover").style.color = "white";
    });

    // modal criar comunidade
    const btnAdd = document.getElementById("btnAdd");
    const modalCriar = document.getElementById("modalCriar");
    const criarConfirmar = document.getElementById("criarConfirmar");
    const criarCancelar = document.getElementById("criarCancelar");

    btnAdd.addEventListener("click", () => {
        modalCriar.style.display = "flex";
    });

    criarCancelar.addEventListener("click", () => {
        modalCriar.style.display = "none";
    });

    criarConfirmar.addEventListener("click", async () => {
        const nome = document.getElementById("novoNome").value.trim();
        const cor = document.getElementById("novaCor").value;

        if (!nome) {
            alert("Dê um nome à comunidade!");
            return;
        }

        const csrftoken = document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken"))
            ?.split("=")[1];

        const response = await fetch("/criar-comunidade/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken
            },
            body: JSON.stringify({ nome, cor })
        });

        const data = await response.json();
        if (data.status === "ok") {
            location.reload();
        } else {
            alert("Erro ao criar comunidade.");
        }
    });

    window.addEventListener("click", e => {
        if (e.target === modalCriar)
            modalCriar.style.display = "none";
    });
});
