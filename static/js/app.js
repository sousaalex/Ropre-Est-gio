console.log("Hostname atual:", window.location.hostname);

const API_URL = window.location.hostname.includes("localhost") || 
                window.location.hostname.includes("127.0.0.1") ||
                window.location.hostname.includes("192.168.30.20")
  ? "http://localhost:8000" // URL do backend local
  : `https://ropre-est-gio.onrender.com`; // URL de produção

console.log(`API_URL configurada: ${API_URL}`);

// Aguarda o carregamento completo do DOM
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ DOM totalmente carregado!");

    const token = localStorage.getItem("authToken");
    if (token) {
        verificarToken(token);
    } else {
        mostrarTelaLogin();
    }

    document.getElementById("login-button").addEventListener("click", () => {
        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-password").value;
        if (email && password) {
            login(email, password);
        } else {
            mostrarMensagem("Por favor, preencha todos os campos!", "login", "erro");
        }
    });

    document.getElementById("register-button").addEventListener("click", () => {
        const email = document.getElementById("register-email").value;
        const password = document.getElementById("register-password").value;
        if (email && password) {
            register(email, password, "admin");
        } else {
            mostrarMensagem("Por favor, preencha todos os campos!", "register", "erro");
        }
    });

    document.getElementById("show-register").addEventListener("click", () => toggleForms(true));
    document.getElementById("show-login").addEventListener("click", () => toggleForms(false));
    document.getElementById("logout-button").addEventListener("click", logout);

    document.getElementById("form-adicionar-trabalhador").addEventListener("submit", adicionarTrabalhador);
    document.getElementById("form-palete").addEventListener("submit", adicionarPalete);
    document.getElementById("form-tarefa").addEventListener("submit", adicionarTarefa);
    document.getElementById("form-adicionar-usuario").addEventListener("submit", adicionarUsuario);
    document.getElementById("exportar-registros").addEventListener("click", exportarRegistros);
});

// Função para verificar o token
function verificarToken(token) {
    fetch(`${API_URL}/verify-token`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
    })
    .then(response => response.json())
    .then(data => {
        if (data.valid) {
            console.log("✅ Token válido, carregando interface...");
            mostrarInterface(data.tipo_usuario);
            listarTrabalhadores();
            listarPaletes();
            listarTarefas();
            listarRegistros();
            if (data.tipo_usuario === "admin") listarUsuarios();
        } else {
            console.log("❌ Token inválido ou expirado");
            localStorage.removeItem("authToken");
            mostrarTelaLogin();
        }
    })
    .catch(error => {
        console.error("Erro ao verificar token:", error);
        mostrarTelaLogin();
    });
}

// Função de Login
function login(email, password) {
    fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.token) {
            localStorage.setItem("authToken", data.token);
            mostrarMensagem("Login bem-sucedido!", "login", "sucesso");
            setTimeout(() => mostrarInterface(data.tipo_usuario), 1000);
        } else {
            mostrarMensagem(data.message, "login", "erro");
        }
    })
    .catch(error => {
        console.error("Erro ao fazer login:", error);
        mostrarMensagem("Erro ao autenticar. Tente novamente.", "login", "erro");
    });
}

// Função de Registro (apenas admin inicial)
function register(email, password, tipo_usuario) {
    fetch(`${API_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, tipo_usuario })
    })
    .then(response => response.json())
    .then(data => {
        if (data.token) {
            localStorage.setItem("authToken", data.token);
            mostrarMensagem("Admin registrado com sucesso!", "register", "sucesso");
            setTimeout(() => mostrarInterface(data.tipo_usuario), 1000);
        } else {
            mostrarMensagem(data.message, "register", "erro");
        }
    })
    .catch(error => {
        console.error("Erro ao registrar:", error);
        mostrarMensagem("Erro ao registrar. Tente novamente.", "register", "erro");
    });
}

// Função para adicionar usuário (apenas admin) - Corrigida
function adicionarUsuario(event) {
    event.preventDefault();
    const email = document.getElementById("usuario-email").value;
    const password = document.getElementById("usuario-senha").value;
    const tipo_usuario = document.getElementById("usuario-tipo").value;
    const mensagemSucesso = document.getElementById("mensagem-sucesso-modal-usuarios");

    fetch(`${API_URL}/register`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("authToken")}`
        },
        body: JSON.stringify({ email, password, tipo_usuario })
    })
    .then(response => {
        if (response.status === 201) {
            return response.json().then(data => ({ status: 201, data }));
        } else if (response.status === 409) {
            return response.json().then(data => ({ status: 409, data }));
        } else if (response.status === 400) {
            return response.json().then(data => ({ status: 400, data }));
        } else {
            return response.json().then(data => ({ status: 500, data }));
        }
    })
    .then(({ status, data }) => {
        // Selecionar o formulário dentro do modal, não o modal em si
        const form = document.querySelector("#form-adicionar-usuario form");
        form.reset(); // Resetar o formulário correto
        if (status === 201) {
            mensagemSucesso.textContent = "Usuário adicionado com sucesso!";
            mensagemSucesso.style.color = "green";
            listarUsuarios(); // Atualizar a lista de usuários
        } else if (status === 409) {
            mensagemSucesso.textContent = "Erro: Email já cadastrado!";
            mensagemSucesso.style.color = "red";
        } else if (status === 400) {
            mensagemSucesso.textContent = "Erro: Dados inválidos!";
            mensagemSucesso.style.color = "red";
        } else {
            mensagemSucesso.textContent = "Erro interno ao adicionar usuário!";
            mensagemSucesso.style.color = "red";
        }
        mensagemSucesso.style.display = "block";
        setTimeout(() => mensagemSucesso.style.display = "none", 3000);
        const modal = bootstrap.Modal.getInstance(document.getElementById("form-adicionar-usuario"));
        modal.hide();
    })
    .catch(error => {
        console.error("Erro ao adicionar usuário:", error);
        mensagemSucesso.textContent = "Erro ao adicionar usuário.";
        mensagemSucesso.style.color = "red";
        mensagemSucesso.style.display = "block";
        setTimeout(() => mensagemSucesso.style.display = "none", 3000);
    });
}

// Função para listar usuários (apenas admin)
// Função para listar usuários (apenas admin)
function listarUsuarios() {
    fetch(`${API_URL}/users`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}` }
    })
    .then(response => response.json())
    .then(data => {
        const lista = document.getElementById("lista-usuarios");
        lista.innerHTML = "";
        data.forEach(usuario => {
            const item = document.createElement("li");
            item.className = "list-group-item d-flex justify-content-between align-items-center";
            item.innerHTML = `
                ${usuario.email} - ${usuario.tipo_usuario}
                <button class="btn btn-sm btn-danger" onclick="deletarUsuario('${usuario.id}')">Excluir</button>
            `;
            lista.appendChild(item);
        });
    })
    .catch(error => console.error("Erro ao listar usuários:", error));
}

// Função para deletar usuário
function deletarUsuario(userId) {
    if (confirm("Tem certeza que deseja excluir este usuário?")) {
        fetch(`${API_URL}/users/${userId}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}` }
        })
        .then(response => response.json())
        .then(data => {
            if (response.ok) {
                alert(data.message);
                listarUsuarios(); // Atualiza a lista após exclusão
            } else {
                alert(data.message);
            }
        })
        .catch(error => console.error("Erro ao deletar usuário:", error));
    }
}

// Função para mostrar a interface
function mostrarInterface(tipoUsuario) {
    document.getElementById("login-container").style.display = "none";
    document.getElementById("main-container").style.display = "block";
    definirLayout(tipoUsuario);
    configurarScanner(tipoUsuario);
}

// Função para definir o layout
function definirLayout(tipoUsuario) {
    const layouts = ["layout-compartilhado", "funcionario-layout"];
    layouts.forEach(id => {
        const layout = document.getElementById(id);
        if (layout) layout.style.display = "none";
    });

    if (tipoUsuario === "admin" || tipoUsuario === "chefe") {
        document.getElementById("layout-compartilhado").style.display = "block";
        if (tipoUsuario === "admin") {
            const scannerElements = document.querySelectorAll("#start-scanner-compartilhado, #reader-compartilhado, #mensagem-qr-compartilhado");
            scannerElements.forEach(el => el.style.display = "none");
            document.getElementById("tab-usuarios-li").style.display = "block";
        } else {
            document.getElementById("tab-usuarios-li").style.display = "none";
        }
    } else if (tipoUsuario === "funcionario") {
        document.getElementById("funcionario-layout").style.display = "block";
    } else {
        console.error("Tipo de usuário inválido:", tipoUsuario);
    }
}

// Função para configurar o scanner
function configurarScanner(tipoUsuario) {
    let botaoScannerId = tipoUsuario === "chefe" ? "start-scanner-compartilhado" : "start-scanner-funcionario";
    let readerId = tipoUsuario === "chefe" ? "reader-compartilhado" : "reader-funcionario";
    let mensagemId = tipoUsuario === "chefe" ? "mensagem-qr-compartilhado" : "mensagem-qr-funcionario";

    if (tipoUsuario === "admin") return;

    const botaoScanner = document.getElementById(botaoScannerId);
    if (botaoScanner) {
        botaoScanner.addEventListener("click", () => startQRCodeScanner(readerId, mensagemId));
    }
}

// Função para alternar entre login e registro
function toggleForms(isRegister) {
    if (isRegister) {
        document.getElementById("login-form").style.display = "none";
        document.getElementById("register-form").style.display = "block";
        document.getElementById("auth-title").textContent = "Registrar Admin";
    } else {
        document.getElementById("login-form").style.display = "block";
        document.getElementById("register-form").style.display = "none";
        document.getElementById("auth-title").textContent = "Login";
    }
}

// Função para mostrar mensagens
function mostrarMensagem(mensagem, tipo, status) {
    const mensagemElement = document.getElementById(`auth-message-${tipo}`);
    mensagemElement.textContent = mensagem;
    mensagemElement.style.color = status === "sucesso" ? "green" : "red";
    mensagemElement.style.display = "block";
    setTimeout(() => mensagemElement.style.display = "none", 3000);
}

// Função para mostrar a tela de login
function mostrarTelaLogin() {
    document.getElementById("login-container").style.display = "flex";
    document.getElementById("main-container").style.display = "none";
}

// Função de logout
function logout() {
    localStorage.removeItem("authToken");
    mostrarTelaLogin();
}

// Função para adicionar trabalhador
function adicionarTrabalhador(event) {
    event.preventDefault();
    const nome = document.getElementById("nome-trabalhador").value.trim();
    const isChefe = document.getElementById("is-chefe").checked;

    fetch(`${API_URL}/trabalhadores`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("authToken")}`
        },
        body: JSON.stringify({ nome, chefe: isChefe })
    })
    .then(response => response.json())
    .then(data => {
        listarTrabalhadores();
        document.getElementById("form-adicionar-trabalhador").reset();
        const mensagemSucesso = document.getElementById("mensagem-sucesso-modal-trabalhadores");
        mensagemSucesso.textContent = data.message;
        mensagemSucesso.style.display = "block";
        setTimeout(() => mensagemSucesso.style.display = "none", 3000);
        const modal = bootstrap.Modal.getInstance(document.getElementById("form-adicionar-trabalhador"));
        modal.hide();
    })
    .catch(error => console.error("Erro ao adicionar trabalhador:", error));
}

// Função para listar trabalhadores
function listarTrabalhadores() {
    fetch(`${API_URL}/trabalhadores`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}` }
    })
    .then(response => response.json())
    .then(data => {
        const lista = document.getElementById("lista-trabalhadores");
        lista.innerHTML = "";
        data.forEach(trabalhador => {
            const item = document.createElement("li");
            item.className = "list-group-item d-flex justify-content-between align-items-center";
            item.innerHTML = `
                ${trabalhador.nome} ${trabalhador.chefe ? "(Chefe)" : ""}
                <div>
                    <button class="btn btn-sm btn-success me-2" onclick="downloadCartao('${trabalhador.id}', 'trabalhador')">Cartão Trabalhador</button>
                    ${trabalhador.chefe ? `<button class="btn btn-sm btn-warning me-2" onclick="downloadCartao('${trabalhador.id}', 'chefe')">Cartão Chefe</button>` : ""}
                    <button class="btn btn-sm btn-danger" onclick="deletarTrabalhador('${trabalhador.id}')">Excluir</button>
                </div>
            `;
            lista.appendChild(item);
        });
    })
    .catch(error => console.error("Erro ao listar trabalhadores:", error));
}

// Função para deletar trabalhador
function deletarTrabalhador(id) {
    fetch(`${API_URL}/trabalhadores/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}` }
    })
    .then(response => response.json())
    .then(data => {
        listarTrabalhadores();
        document.getElementById("mensagem-sucesso-trabalhadores").textContent = data.message;
        document.getElementById("mensagem-sucesso-trabalhadores").style.display = "block";
        setTimeout(() => document.getElementById("mensagem-sucesso-trabalhadores").style.display = "none", 3000);
    })
    .catch(error => console.error("Erro ao deletar trabalhador:", error));
}

// Função para baixar cartão
function downloadCartao(trabalhadorId, tipoCartao) {
    fetch(`${API_URL}/cartao/${trabalhadorId}/${tipoCartao}`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}` }
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `cartao_${trabalhadorId}_${tipoCartao}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    })
    .catch(error => console.error("Erro ao baixar cartão:", error));
}

// Função para adicionar palete
function adicionarPalete(event) {
    event.preventDefault();
    const paleteData = {
        data_entrega: document.getElementById("data-entrega").value,
        op: document.getElementById("op").value,
        referencia: document.getElementById("referencia").value,
        nome_produto: document.getElementById("nome-produto").value,
        medida: document.getElementById("medida").value,
        cor_botao: document.getElementById("cor-botao").value,
        cor_ribete: document.getElementById("cor-ribete").value,
        leva_embalagem: document.getElementById("leva-embalagem").checked,
        quantidade: parseInt(document.getElementById("quantidade").value),
        data_hora: new Date().toISOString(),
        numero_lote: document.getElementById("numero-lote").value
    };

    fetch(`${API_URL}/paletes`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("authToken")}`
        },
        body: JSON.stringify(paleteData)
    })
    .then(response => response.json())
    .then(data => {
        listarPaletes();
        document.getElementById("form-palete").reset();
        const mensagemSucesso = document.getElementById("mensagem-sucesso-modal-paletes");
        mensagemSucesso.textContent = data.message;
        mensagemSucesso.style.display = "block";
        setTimeout(() => mensagemSucesso.style.display = "none", 3000);
        const modal = bootstrap.Modal.getInstance(document.getElementById("form-adicionar-palete"));
        modal.hide();
    })
    .catch(error => console.error("Erro ao adicionar palete:", error));
}

// Função para listar paletes
function listarPaletes() {
    fetch(`${API_URL}/paletes`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}` }
    })
    .then(response => response.json())
    .then(data => {
        const lista = document.getElementById("lista-paletes");
        lista.innerHTML = "";
        data.forEach(palete => {
            const item = document.createElement("li");
            item.className = "list-group-item d-flex justify-content-between align-items-center";
            item.innerHTML = `
                ${palete.referencia} - ${palete.nome_produto} (Lote: ${palete.numero_lote})
                <div>
                    <button class="btn btn-sm btn-success me-2" onclick="downloadPDFPalete('${palete.id}')">PDF</button>
                    <button class="btn btn-sm btn-danger" onclick="deletarPalete('${palete.id}')">Excluir</button>
                </div>
            `;
            lista.appendChild(item);
        });
    })
    .catch(error => console.error("Erro ao listar paletes:", error));
}

// Função para deletar palete
function deletarPalete(id) {
    fetch(`${API_URL}/paletes/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}` }
    })
    .then(response => response.json())
    .then(data => {
        listarPaletes();
        document.getElementById("mensagem-sucesso-paletes").textContent = data.message;
        document.getElementById("mensagem-sucesso-paletes").style.display = "block";
        setTimeout(() => document.getElementById("mensagem-sucesso-paletes").style.display = "none", 3000);
    })
    .catch(error => console.error("Erro ao deletar palete:", error));
}

// Função para baixar PDF da palete
function downloadPDFPalete(paleteId) {
    fetch(`${API_URL}/paletes/${paleteId}/pdf`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}` }
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `palete_${paleteId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    })
    .catch(error => console.error("Erro ao baixar PDF da palete:", error));
}

// Função para adicionar tarefa
function adicionarTarefa(event) {
    event.preventDefault();
    const tarefaData = {
        nome_tarefa: document.getElementById("nome-tarefa").value,
        secao: document.getElementById("secao").value
    };

    fetch(`${API_URL}/tarefas`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("authToken")}`
        },
        body: JSON.stringify(tarefaData)
    })
    .then(response => response.json())
    .then(data => {
        listarTarefas();
        document.getElementById("form-tarefa").reset();
        const mensagemSucesso = document.getElementById("mensagem-sucesso-modal-tarefas");
        mensagemSucesso.textContent = data.message;
        mensagemSucesso.style.display = "block";
        setTimeout(() => mensagemSucesso.style.display = "none", 3000);
        const modal = bootstrap.Modal.getInstance(document.getElementById("form-adicionar-tarefa"));
        modal.hide();
    })
    .catch(error => console.error("Erro ao adicionar tarefa:", error));
}

// Função para listar tarefas
function listarTarefas() {
    fetch(`${API_URL}/tarefas`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}` }
    })
    .then(response => response.json())
    .then(data => {
        const lista = document.getElementById("lista-tarefas");
        lista.innerHTML = "";
        data.forEach(tarefa => {
            const item = document.createElement("li");
            item.className = "list-group-item d-flex justify-content-between align-items-center";
            item.innerHTML = `
                ${tarefa.nome} - ${tarefa.secao}
                <div>
                    <button class="btn btn-sm btn-success me-2" onclick="downloadPDFTarefa('${tarefa.id}')">PDF</button>
                    <button class="btn btn-sm btn-danger" onclick="deletarTarefa('${tarefa.id}')">Excluir</button>
                </div>
            `;
            lista.appendChild(item);
        });
    })
    .catch(error => console.error("Erro ao listar tarefas:", error));
}

// Função para deletar tarefa
function deletarTarefa(id) {
    fetch(`${API_URL}/tarefas/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}` }
    })
    .then(response => response.json())
    .then(data => {
        listarTarefas();
        document.getElementById("mensagem-sucesso-tarefas").textContent = data.message;
        document.getElementById("mensagem-sucesso-tarefas").style.display = "block";
        setTimeout(() => document.getElementById("mensagem-sucesso-tarefas").style.display = "none", 3000);
    })
    .catch(error => console.error("Erro ao deletar tarefa:", error));
}

// Função para baixar PDF da tarefa
function downloadPDFTarefa(tarefaId) {
    fetch(`${API_URL}/tarefas/${tarefaId}/pdf`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}` }
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `tarefa_${tarefaId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    })
    .catch(error => console.error("Erro ao baixar PDF da tarefa:", error));
}

// Função para listar registros de trabalho
function listarRegistros() {
    fetch(`${API_URL}/registro_trabalho`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}` }
    })
    .then(response => response.json())
    .then(data => {
        const lista = document.getElementById("lista-registros");
        lista.innerHTML = "";
        data.forEach(registro => {
            const item = document.createElement("li");
            item.className = "list-group-item";
            item.textContent = `${registro.data} - ${registro.palete.referencia} - ${registro.tarefa.nome} - ${registro.trabalhador.nome} - Início: ${registro.hora_inicio} - Fim: ${registro.hora_fim || "Em andamento"}`;
            lista.appendChild(item);
        });
    })
    .catch(error => console.error("Erro ao listar registros:", error));
}

// Função para exportar registros
function exportarRegistros() {
    fetch(`${API_URL}/exportar_registros`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("authToken")}` }
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "registros_trabalho.xlsx";
        document.body.appendChild(a);
        a.click();
        a.remove();
    })
    .catch(error => console.error("Erro ao exportar registros:", error));
}

// Função para iniciar o scanner de QR Code
function startQRCodeScanner(readerId, mensagemId) {
    const html5QrCode = new Html5Qrcode(readerId);
    const qrCodeSuccessCallback = (decodedText) => {
        html5QrCode.stop().then(() => {
            document.getElementById(mensagemId).textContent = `QR Code escaneado: ${decodedText}`;
            registrarTrabalho(decodedText);
        }).catch(err => console.error("Erro ao parar scanner:", err));
    };
    const qrCodeErrorCallback = (error) => {
        console.warn(`Erro ao escanear QR Code: ${error}`);
    };

    html5QrCode.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        qrCodeSuccessCallback,
        qrCodeErrorCallback
    ).catch(err => console.error("Erro ao iniciar scanner:", err));
}

// Função para registrar trabalho
function registrarTrabalho(qrCodeText) {
    const qrData = qrCodeText.split(";");
    const tarefaQr = qrCodeText;
    const trabalhadorQr = prompt("Escaneie o QR Code do trabalhador:");
    const paleteQr = prompt("Escaneie o QR Code da palete:");

    if (trabalhadorQr && paleteQr) {
        fetch(`${API_URL}/registro_trabalho`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("authToken")}`
            },
            body: JSON.stringify({
                tarefa_qr: tarefaQr,
                trabalhador_qr: trabalhadorQr,
                palete_qr: paleteQr
            })
        })
        .then(response => response.json())
        .then(data => {
            listarRegistros();
            document.getElementById("mensagem-qr-compartilhado").textContent = data.message;
            document.getElementById("mensagem-qr-funcionario").textContent = data.message;
        })
        .catch(error => console.error("Erro ao registrar trabalho:", error));
    } else {
        document.getElementById("mensagem-qr-compartilhado").textContent = "Escaneamento cancelado.";
        document.getElementById("mensagem-qr-funcionario").textContent = "Escaneamento cancelado.";
    }
}