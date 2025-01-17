console.log("Hostname atual:", window.location.hostname);

const API_URL =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1" ||
  window.location.hostname === "10.0.1.242" // Adiciona o IP do PC explicitamente
    ? "http://10.0.1.242:5000" // IP do seu PC na rede
    : "https://gestao-fabrica.vercel.app"; // URL do Vercel

console.log(`API_URL configurada: ${API_URL}`);



// Listar Trabalhadores
function listarTrabalhadores() {
    fetch(`${API_URL}/trabalhadores`)
        .then(response => response.json())
        .then(data => {
            const lista = document.getElementById("lista-trabalhadores");
            if (!lista) {
                console.error("Elemento '#lista-trabalhadores' não encontrado no DOM.");
                return;
            }

            lista.innerHTML = ""; // Limpa a lista existente

            data.forEach(trabalhador => {
                // Cria um item da lista para o trabalhador
                const item = document.createElement("li");
                item.className = "list-group-item d-flex justify-content-between align-items-center";

                // Texto do trabalhador
                const trabalhadorInfo = document.createElement("span");
                trabalhadorInfo.textContent = `${trabalhador.nome} - Secção: ${trabalhador.secao}`;
                if (trabalhador.chefe) {
                    trabalhadorInfo.innerHTML += ` <strong>(Chefe)</strong>`;
                    trabalhadorInfo.style.fontWeight = "bold";
                }
                item.appendChild(trabalhadorInfo);

                // Container de botões
                const buttonContainer = document.createElement("div");
                buttonContainer.className = "d-flex gap-2";

                // Botão de download do cartão de trabalhador
                const botaoDownloadTrabalhador = document.createElement("button-trabalhadores");
                botaoDownloadTrabalhador.className = "btn btn-secondary btn-sm";
                botaoDownloadTrabalhador.innerHTML = `<i class="bi bi-download"></i> Cartão Trabalhador`;
                botaoDownloadTrabalhador.onclick = () => {
                    const linkTrabalhador = `${API_URL}/cartoes/trabalhadores/cartao_${trabalhador.id}.png`;
                    window.open(linkTrabalhador, "_blank");
                };
                buttonContainer.appendChild(botaoDownloadTrabalhador);

                // Botão de download do cartão de chefe (apenas para chefes)
                if (trabalhador.chefe) {
                    const botaoDownloadChefe = document.createElement("button-trabalhadores");
                    botaoDownloadChefe.className = "btn btn-warning btn-sm";
                    botaoDownloadChefe.innerHTML = `<i class="bi bi-download"></i> Cartão Chefe`;
                    botaoDownloadChefe.onclick = () => {
                        const linkChefe = `${API_URL}/cartoes/chefes/cartao_${trabalhador.id}.png`;
                        window.open(linkChefe, "_blank");
                    };
                    buttonContainer.appendChild(botaoDownloadChefe);
                }

                // Botão de remover
                const botaoRemover = document.createElement("button-trabalhadores");
                botaoRemover.className = "btn btn-danger btn-sm";
                botaoRemover.textContent = "Remover";
                botaoRemover.onclick = () => removerTrabalhador(trabalhador.id);
                buttonContainer.appendChild(botaoRemover);

                // Adiciona o container de botões ao item
                item.appendChild(buttonContainer);
                lista.appendChild(item);
            });
        })
        .catch(error => console.error("Erro ao listar trabalhadores:", error));
}




// Adicionar Trabalhador
function adicionarTrabalhador() {
    const nomeInput = document.getElementById("nome-trabalhador");
    const secaoSelect = document.getElementById("secao-trabalhador");
    const isChefe = document.getElementById("is-chefe").checked; // Verifica se o checkbox está marcado

    const nome = nomeInput.value.trim();
    const secao = secaoSelect.value;

    if (!nome) {
        alert("Por favor, preencha o nome do trabalhador!");
        return;
    }

    if (!secao) {
        alert("Por favor, selecione uma seção para o trabalhador!");
        return;
    }

    // Inclui a informação de 'chefe' no corpo da requisição
    fetch(`${API_URL}/trabalhadores`, {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify({ nome, secao, chefe: isChefe }), // Adiciona 'chefe' aqui
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.message);
                });
            }
            return response.json();
        })
        .then(data => {
            listarTrabalhadores(); // Atualiza a lista após adicionar
            nomeInput.value = ""; // Limpa o campo de entrada
            secaoSelect.value = ""; // Reseta a seleção
            document.getElementById("is-chefe").checked = false; // Reseta o checkbox

            // Mostrar mensagem temporária de sucesso
            const mensagemSucesso = document.getElementById("mensagem-sucesso");
            mensagemSucesso.textContent = data.message;
            mensagemSucesso.style.display = "block";
            setTimeout(() => {
                mensagemSucesso.style.display = "none"; // Esconde após 3 segundos
            }, 3000);
        })
        .catch(error => {
            console.error("Erro ao adicionar trabalhador:", error.message);
            alert(`Erro: ${error.message}`);
        });
}


// Remover Trabalhador
function removerTrabalhador(id) {
    if (confirm("Tem certeza que deseja remover este trabalhador?")) {
        fetch(`${API_URL}/trabalhadores/${id}`, { method: "DELETE" })
            .then(response => {
                if (!response.ok) {
                    throw new Error("Erro ao remover trabalhador.");
                }
                return response.json();
            })
            .then(data => {
                listarTrabalhadores(); // Atualiza a lista

                // Exibe mensagem de sucesso
                const mensagemSucesso = document.getElementById("mensagem-sucesso");
                mensagemSucesso.textContent = data.message || "Trabalhador removido com sucesso!";
                mensagemSucesso.style.display = "block";

                // Esconde mensagem após 3 segundos
                setTimeout(() => {
                    mensagemSucesso.style.display = "none";
                }, 3000);
            })
            .catch(error => console.error("Erro ao remover trabalhador:", error));
    }
}

// Carregar lista de trabalhadores ao carregar a página
document.addEventListener("DOMContentLoaded", listarTrabalhadores);

// Detectar Enter no campo de entrada
document.getElementById("nome-trabalhador").addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        adicionarTrabalhador(); // Chama a função de adicionar
        event.preventDefault(); // Evita comportamento padrão
    }
});

// Detectar Enter no campo de seção
document.getElementById("secao-trabalhador").addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        adicionarTrabalhador(); // Chama a função de adicionar
        event.preventDefault(); // Evita comportamento padrão
    }
});

// Listar Tarefas
function listarTarefas() {
    fetch(`${API_URL}/registro_trabalho`)
        .then(response => response.json())
        .then(data => {
            const lista = document.getElementById("lista-tarefas");
            lista.innerHTML = ""; // Limpa a lista

            data.forEach(registro => {
                const item = document.createElement("li");
                item.textContent = `Registro ID: ${registro.id}, Trabalhador: ${registro.trabalhador.nome} (ID: ${registro.trabalhador.id}),  (ID: ${registro.palete.id}), Início: ${registro.horario_inicio}, Fim: ${registro.horario_fim || "Em andamento"}`;
                lista.appendChild(item);
            });
        })
        .catch(error => console.error("Erro ao carregar os registros de trabalho:", error));
}



// Adicionar Palete
function adicionarPalete() {
    const dataEntrega = document.getElementById("data-entrega").value;
    const op = document.getElementById("op-palete").value;
    const referencia = document.getElementById("referencia-palete").value;
    const nomeProduto = document.getElementById("nome-produto-palete").value;
    const medida = document.getElementById("medida-palete").value;
    const corBotao = document.getElementById("cor-botao-palete").value;
    const corRibete = document.getElementById("cor-ribete-palete").value;
    const levaEmbalagem = document.getElementById("leva-embalagem-palete").value;
    const quantidade = document.getElementById("quantidade-palete").value;
    const dataHora = document.getElementById("data-hora-palete").value;
    const numeroLote = document.getElementById("numero-lote-palete").value;

    if (!dataEntrega || !op || !referencia || !nomeProduto || !medida || !corBotao || !corRibete || !levaEmbalagem || !quantidade || !dataHora || !numeroLote) {
        alert("Todos os campos são obrigatórios!");
        return;
    }

    const payload = {
        data_entrega: dataEntrega,
        op: op,
        referencia: referencia,
        nome_produto: nomeProduto,
        medida: medida,
        cor_botao: corBotao,
        cor_ribete: corRibete,
        leva_embalagem: levaEmbalagem === "true", // Converte string para boolean
        quantidade: parseInt(quantidade, 10),
        data_hora: dataHora,
        numero_lote: numeroLote,
    };

    fetch(`${API_URL}/paletes`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    })
        .then((response) => {
            if (!response.ok) {
                return response.json().then((err) => {
                    throw new Error(err.message);
                });
            }
            return response.json();
        })
        .then(data => {
            listarPaletes(); // Atualiza a lista após adicionar

            // Exibe mensagem de sucesso no modal
            const mensagemSucesso = document.getElementById("mensagem-sucesso-add-palete");
            if (mensagemSucesso) {
                mensagemSucesso.textContent = data.message || "Palete adicionada com sucesso!";
                mensagemSucesso.style.display = "block"; // Mostra a mensagem
                mensagemSucesso.style.visibility = "visible"; // Garante visibilidade
                mensagemSucesso.style.opacity = 1; // Garante opacidade máxima

                // Esconde a mensagem após 3 segundos
                setTimeout(() => {
                    mensagemSucesso.style.display = "none"; // Oculta o elemento
                }, 3000);
            } else {
                console.error("Elemento de mensagem de sucesso não encontrado.");
            }

            // Limpa os campos do formulário para adicionar uma nova palete
            document.getElementById("form-adicionar-palete").reset();

            // Reatualiza a data e hora
            const dataHoraInput = document.getElementById("data-hora-palete");
            if (dataHoraInput) {
                const agora = new Date();
                const ano = agora.getFullYear();
                const mes = String(agora.getMonth() + 1).padStart(2, '0');
                const dia = String(agora.getDate()).padStart(2, '0');
                const horas = String(agora.getHours()).padStart(2, '0');
                const minutos = String(agora.getMinutes()).padStart(2, '0');
                const dataHoraFormatada = `${ano}-${mes}-${dia}T${horas}:${minutos}`;
                dataHoraInput.value = dataHoraFormatada; // Atualiza o campo
            }
        })
        .catch((error) => {
            console.error("Erro ao adicionar palete:", error);
            alert(`Erro: ${error.message}`);
        });
}







// Função para limpar o formulário
function limparFormularioPalete() {
    document.getElementById("produto-palete").value = "";
    document.getElementById("cliente-palete").value = "";
    document.getElementById("medidas-palete").value = "";
    document.getElementById("quantidade-palete").value = "";
    document.getElementById("referencia-palete").value = "";
}





function removerPalete(id) {
    if (confirm("Tem certeza que deseja remover esta palete?")) {
        fetch(`${API_URL}/paletes/${id}`, { method: "DELETE" })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.message);
                    });
                }
                return response.json();
            })
            .then(data => {
                listarPaletes(); // Atualiza a lista de paletes

                // Exibe mensagem de sucesso
                const mensagemSucesso = document.getElementById("mensagem-sucesso-palete");
                if (mensagemSucesso) {
                    mensagemSucesso.textContent = data.message || "Palete removida com sucesso!";
                    mensagemSucesso.style.display = "block"; // Mostra o elemento
                    mensagemSucesso.style.visibility = "visible"; // Garante que é visível
                    mensagemSucesso.style.opacity = 1; // Garante opacidade máxima

                    // Esconde a mensagem após 3 segundos
                    setTimeout(() => {
                        mensagemSucesso.style.display = "none"; // Oculta o elemento
                    }, 3000);
                } else {
                    console.error("Elemento de mensagem de sucesso não encontrado.");
                }
            })
            .catch(error => {
                console.error("Erro ao remover palete:", error);
                alert("Ocorreu um erro ao remover a palete. Tente novamente.");
            });
    }
}






// Listar Paletes
function listarPaletes() {
    fetch(`${API_URL}/paletes`)
        .then(response => response.json())
        .then(data => {
            const lista = document.getElementById("lista-paletes");
            lista.innerHTML = ""; // Limpa a lista existente

            data.forEach(palete => {
                // Cria um item da lista para a palete
                const item = document.createElement("li");
                item.className = "list-group-item"; // Classe para estilização básica

                // Cria o conteúdo do item com as informações da palete
                item.innerHTML = `
                    <strong>ID:</strong> ${palete.id}<br>
                    <strong>Data de Entrega:</strong> ${palete.data_entrega}<br>
                    <strong>OP:</strong> ${palete.op}<br>
                    <strong>Referência:</strong> ${palete.referencia}<br>
                    <strong>Nome do Produto:</strong> ${palete.nome_produto}<br>
                    <strong>Medida:</strong> ${palete.medida}<br>
                    <strong>Cor do Botão:</strong> ${palete.cor_botao}<br>
                    <strong>Cor do Ribete:</strong> ${palete.cor_ribete}<br>
                    <strong>Leva Embalagem:</strong> ${palete.leva_embalagem ? "Sim" : "Não"}<br>
                    <strong>Quantidade:</strong> ${palete.quantidade}<br>
                    <strong>Data e Hora:</strong> ${palete.data_hora}<br>
                    <strong>Número do Lote:</strong> ${palete.numero_lote}
                `;

                // Cria o botão de download
                const botaoDownload = document.createElement("button-2");
                botaoDownload.onclick = () => {
                    const link = `${API_URL}/FolhaPalete/folha_palete_${palete.id}.pdf`;
                    window.open(link, "_blank"); // Abre o PDF em uma nova aba
                };
                botaoDownload.className = "btn btn-secondary btn-sm d-flex align-items-center";
                botaoDownload.innerHTML = `
                    <i class="bi bi-download"></i>
                `;
                // Adiciona o botão de download ao item
                item.appendChild(botaoDownload);

                // Adiciona botão de remover
                const botaoRemover = document.createElement("button");
                botaoRemover.textContent = "Remover";
                botaoRemover.className = "btn btn-danger btn-sm ms-3";
                botaoRemover.onclick = () => removerPalete(palete.id);
                item.appendChild(botaoRemover);

                lista.appendChild(item); // Adiciona o item à lista
            });
        })
        .catch(error => console.error("Erro ao listar paletes:", error));
}






// Carregar lista de paletes ao carregar a aba
document.addEventListener("DOMContentLoaded", listarPaletes);


document.addEventListener("DOMContentLoaded", function () {
    // Configurar evento para carregar dados ao mudar de aba
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    const dataHoraInput = document.getElementById("data-hora-palete");

    // Função para atualizar o campo de data e hora
    function atualizarDataHora() {
        const dataHoraInput = document.getElementById("data-hora-palete");
        if (dataHoraInput) {
            const agora = new Date();
            const ano = agora.getFullYear();
            const mes = String(agora.getMonth() + 1).padStart(2, '0'); // Adiciona zero à esquerda se necessário
            const dia = String(agora.getDate()).padStart(2, '0');
            const horas = String(agora.getHours()).padStart(2, '0');
            const minutos = String(agora.getMinutes()).padStart(2, '0');

            // Formata no padrão yyyy-MM-ddTHH:mm
            const dataHoraFormatada = `${ano}-${mes}-${dia}T${horas}:${minutos}`;
            dataHoraInput.value = dataHoraFormatada; // Preenche o campo
        }
    }

    // Atualiza o campo "Data e Hora" em tempo real a cada segundo
    setInterval(atualizarDataHora, 1000);

    

    tabs.forEach(tab => {
        tab.addEventListener("shown.bs.tab", function (event) {
            const targetId = event.target.getAttribute("href");

            // Identifica qual aba foi ativada e chama a função correspondente
            if (targetId === "#tab-trabalhadores") {
                listarTrabalhadores();
            } else if (targetId === "#tab-paletes") {
                listarPaletes();
            } else if (targetId === "#tab-tarefas") {
                listarTarefas();
            }
        });
    });
});

function autenticarChefe() {
    const idChefe = document.getElementById("id-chefe").value.trim();
    const senhaChefe = document.getElementById("senha-chefe").value.trim();

    if (!idChefe || !senhaChefe) {
        alert("Por favor, preencha todos os campos!");
        return;
    }

    fetch(`${API_URL}/chefes/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: idChefe, senha: senhaChefe }),
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.message); });
            }
            return response.json();
        })
        .then(data => {
            const mensagem = document.getElementById("mensagem-autenticacao");
            mensagem.textContent = data.message;
            mensagem.style.color = "green";
            alert(`Bem-vindo, ${data.nome}! Você tem acesso a recursos adicionais.`);
        })
        .catch(error => {
            const mensagem = document.getElementById("mensagem-autenticacao");
            mensagem.textContent = error.message;
            mensagem.style.color = "red";
        });
}


// Inicializa o leitor de QR Code
function startQRCodeScanner() {
    const html5QrCode = new Html5Qrcode("reader");
    const config = { fps: 10, qrbox: { width: 250, height: 250 } };
    
    // Inicia o scanner com a câmera traseira
    html5QrCode.start(
        { facingMode: "environment" }, // Envia 'user' para usar a câmera frontal
        config,
        (decodedText, decodedResult) => {
            console.log("QR Code lido:", decodedText);
            // Processar o texto lido aqui
        },
        (errorMessage) => {
            console.warn("Erro ao ler QR Code:", errorMessage);
        }
    ).catch(err => console.error("Erro ao iniciar o scanner:", err));
}

// Processar texto do QR Code lido
function processQRCode(decodedText) {
    console.log("Dados do QR Code:", decodedText);
    // Exemplo: Enviar para a API ou processar localmente
}

// Adiciona evento ao botão para iniciar o scanner
document.getElementById("start-scanner").addEventListener("click", startQRCodeScanner);


