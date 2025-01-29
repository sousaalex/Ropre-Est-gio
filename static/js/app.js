console.log("Hostname atual:", window.location.hostname);

const API_URL = window.location.hostname.includes("localhost") || 
                window.location.hostname.includes("127.0.0.1") ||
                window.location.hostname.includes("10.0.1.242")
  ? "http://10.0.1.242:5000" // URL do backend local
  : `https://${window.location.hostname}/`; // URL do Vercel (produção ou preview)

console.log(`API_URL configurada: ${API_URL}`);


// Aguarda o carregamento completo do DOM
document.addEventListener("DOMContentLoaded", () => {
    // Solicitar o tipo de usuário e configurar o layout
    const tipoUsuario = prompt("Digite o tipo de usuário (admin, chefe, funcionario):").toLowerCase();
    definirLayout(tipoUsuario);
    configurarScanner(tipoUsuario);

    // Adicionar evento ao formulário para adicionar trabalhador
    const formAdicionarTrabalhador = document.getElementById("form-adicionar-trabalhador");
    if (formAdicionarTrabalhador) {
        formAdicionarTrabalhador.addEventListener("submit", adicionarTrabalhador);
        console.log("Evento de submit adicionado ao formulário.");
    } else {
        console.error("Formulário 'form-adicionar-trabalhador' não encontrado.");
    }

    const formAdicionarTarefa = document.getElementById("formAdicionarTarefa");
    if (formAdicionarTarefa) {
        formAdicionarTarefa.addEventListener("submit", adicionarTarefa);
    } else {
        console.error("Formulário 'formAdicionarTarefa' não encontrado.");
    }

    // Lista trabalhadores e paletes ao carregar
    listarTrabalhadores();

    // Configurar evento para carregar dados ao mudar de aba
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener("shown.bs.tab", function (event) {
            const targetId = event.target.getAttribute("href");
            console.log(`Aba ativada: ${targetId}`);  // Log para verificar qual aba está sendo ativada



            // Identifica qual aba foi ativada e chama a função correspondente
            if (targetId === "#tab-trabalhadores") {
                listarTrabalhadores();
            } else if (targetId === "#tab-paletes") {
                listarPaletes();
            } else if (targetId === "#tab-registro_trabalho") {
                listarRegistro();
            } else if (targetId === "#tab-tarefas") {
                listarTarefas();
            }
        });
    });

    // Atualiza o campo "Data e Hora" em tempo real
    const dataHoraInput = document.getElementById("data-hora-palete");
    if (dataHoraInput) {
        function atualizarDataHora() {
            const agora = new Date();
            const ano = agora.getFullYear();
            const mes = String(agora.getMonth() + 1).padStart(2, '0');
            const dia = String(agora.getDate()).padStart(2, '0');
            const horas = String(agora.getHours()).padStart(2, '0');
            const minutos = String(agora.getMinutes()).padStart(2, '0');

            // Formata no padrão yyyy-MM-ddTHH:mm
            const dataHoraFormatada = `${ano}-${mes}-${dia}T${horas}:${minutos}`;
            dataHoraInput.value = dataHoraFormatada; // Preenche o campo
        }

        // Atualiza o campo "Data e Hora" a cada segundo
        setInterval(atualizarDataHora, 1000);
    }
});


// Função para definir o layout com base no tipo de usuário
function definirLayout(tipoUsuario) {
    // Ocultar todos os layouts inicialmente
    const layouts = ["layout-compartilhado", "funcionario-layout"];
    layouts.forEach((id) => {
        const layout = document.getElementById(id);
        if (layout) layout.style.display = "none";
    });

    // Exibe o layout correspondente
    if (tipoUsuario === "admin" || tipoUsuario === "chefe") {
        document.getElementById("layout-compartilhado").style.display = "block";

        // Esconde os elementos de scanner se for admin
        if (tipoUsuario === "admin") {
            const scannerElements = document.querySelectorAll("#start-scanner-compartilhado, #reader-compartilhado, #mensagem-qr");
            scannerElements.forEach((el) => el.style.display = "none");
        }
    } else if (tipoUsuario === "funcionario") {
        document.getElementById("funcionario-layout").style.display = "block";
    } else {
        console.error("Tipo de usuário inválido:", tipoUsuario);
    }
}

// Função para configurar o scanner de QR Code
function configurarScanner(tipoUsuario) {
    let botaoScannerId = null;
    let readerId = null;

    if (tipoUsuario === "chefe") {
        botaoScannerId = "start-scanner-compartilhado";
        readerId = "reader-compartilhado";
    } else if (tipoUsuario === "funcionario") {
        botaoScannerId = "start-scanner-funcionario";
        readerId = "reader-funcionario";
    }

    // Configurar scanner se os IDs forem válidos
    if (botaoScannerId && readerId) {
        const botaoScanner = document.getElementById(botaoScannerId);
        if (botaoScanner) {
            botaoScanner.addEventListener("click", () => {
                startQRCodeScanner(readerId);
            });
        } else {
            console.error(`Botão de scanner com ID '${botaoScannerId}' não encontrado.`);
        }
    }
}



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
                trabalhadorInfo.textContent = `${trabalhador.nome}`;
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
                    const linkTrabalhador = `${API_URL}/cartao/${trabalhador.id}`;
                    window.open(linkTrabalhador, "_blank");
                };
                buttonContainer.appendChild(botaoDownloadTrabalhador);

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




// Função para adicionar trabalhador
function adicionarTrabalhador(event) {
    if (event) {
        event.preventDefault();
    } else {
        console.error("O evento não foi passado corretamente para a função adicionarTrabalhador.");
        return;
    }

    const nomeInput = document.getElementById("nome-trabalhador");
    const isChefeCheckbox = document.getElementById("is-chefe");

    const nome = nomeInput?.value.trim();
    const isChefe = isChefeCheckbox?.checked;

    // Validação dos campos
    if (!nome) {
        exibirMensagem("Por favor, preencha o nome do trabalhador!", "erro");
        return;
    }


    // Desabilitar botão enquanto a requisição é feita
    const botaoAdicionar = document.getElementById("botao-adicionar");
    if (botaoAdicionar) {
        botaoAdicionar.disabled = true;
    }

    // Enviar requisição à API
    fetch(`${API_URL}/trabalhadores`, {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify({ nome, chefe: isChefe }),
    })
        .then((response) => {
            if (botaoAdicionar) {
                botaoAdicionar.disabled = false; // Reativar botão
            }
            if (!response.ok) {
                return response.json().then((err) => {
                    throw new Error(err.message);
                });
            }
            return response.json();
        })
        .then((data) => {
            listarTrabalhadores(); // Atualiza a lista
            limparFormulario();
            
            // Exibe a mensagem retornada pela API
            const mensagemSucesso = document.getElementById("mensagem-sucesso");
            if (mensagemSucesso) {
                mensagemSucesso.textContent = data.message;
                mensagemSucesso.style.display = "block";
                

                // Esconde a mensagem após 3 segundos
                setTimeout(() => {
                    mensagemSucesso.style.display = "none";
                }, 3000);
            }
        })
        .catch((error) => {
            if (botaoAdicionar) {
                botaoAdicionar.disabled = false;
            }
            console.error("Erro ao adicionar trabalhador:", error.message);
            exibirMensagem(`Erro: ${error.message}`, "erro");
        });
}

// Função para limpar o formulário
function limparFormulario() {
    document.getElementById("nome-trabalhador").value = "";
    document.getElementById("is-chefe").checked = false;
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



// Detectar Enter no campo de entrada
document.getElementById("nome-trabalhador").addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        adicionarTrabalhador(); // Chama a função de adicionar
        event.preventDefault(); // Evita comportamento padrão
    }
});


function adicionarTarefa(event) {
    // Impedir o comportamento padrão do formulário
    if (event) {
        event.preventDefault();
    }

    // Capturar os valores do formulário
    const nomeTarefa = document.getElementById("nomeTarefa").value.trim();
    const secao = document.getElementById("secao").value;

    // Validação dos campos
    if (!nomeTarefa || !secao) {
        alert("Por favor, preencha todos os campos obrigatórios!");
        return;
    }

    // Enviar os dados para a API
    fetch(`${API_URL}/tarefas`, {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify({
            nome_tarefa: nomeTarefa,
            secao: secao,
        }),
    })
        .then((response) => {
            if (!response.ok) {
                return response.json().then((err) => {
                    throw new Error(err.message);
                });
            }
            return response.json();
        })
        .then((data) => {
            listarTarefas(); // Atualiza a lista de tarefas
            document.getElementById("formAdicionarTarefa").reset(); // Limpa o formulário

            // Exibir mensagem de sucesso dentro do modal
            const mensagemSucesso = document.getElementById("mensagem-sucesso-tarefa");
            mensagemSucesso.textContent = "Tarefa adicionada com sucesso!";
            mensagemSucesso.style.display = "block";

            // Esconde a mensagem após 3 segundos
            setTimeout(() => {
                mensagemSucesso.style.display = "none";
                const modal = bootstrap.Modal.getInstance(document.getElementById("modalAdicionarTarefa"));
            }, 3000);
        })
        .catch((error) => {
            console.error("Erro ao adicionar tarefa:", error.message);
            alert(`Erro: ${error.message}`);
        });
}


// Função auxiliar para limpar o formulário de tarefas
function limparFormularioTarefa() {
    const nomeTarefaInput = document.getElementById("nome-tarefa");
    const secaoInput = document.getElementById("secao-tarefa");

    if (nomeTarefaInput) nomeTarefaInput.value = "";
    if (secaoInput) secaoInput.value = "";
}



function listarTarefas() {
    fetch(`${API_URL}/tarefas`) // Endpoint para obter todas as tarefas
        .then(response => response.json())
        .then(data => {
            const lista = document.getElementById("lista-tarefas"); // Elemento da lista de tarefas no HTML
            lista.innerHTML = ""; // Limpa a lista existente

            data.forEach(tarefa => {
                // Cria um item da lista para a tarefa
                const item = document.createElement("li");
                item.className = "list-group-item"; // Classe para estilização básica

                // Cria o conteúdo do item com as informações da tarefa
                item.innerHTML = `
                    <strong>ID:</strong> ${tarefa.id}<br>
                    <strong>Nome:</strong> ${tarefa.nome}<br>
                    <strong>Seção:</strong> ${tarefa.secao}<br>
                `;


                // Contêiner para botões
                const botoesContainer = document.createElement("div");
                botoesContainer.className = "d-flex justify-content-end gap-2 align-items-center";
                botoesContainer.style.marginRight = "15px"; // Margem à direita

                // Adiciona botão de baixar QR Code
                const botaoBaixarPDF = document.createElement("button");
                botaoBaixarPDF.textContent = "Baixar PDF";
                botaoBaixarPDF.className = "btn btn-secondary btn-sm";
                botaoBaixarPDF.onclick = () => {
                    window.open(`${API_URL}/tarefas/${tarefa.id}/pdf`, "_blank");
                };
                botoesContainer.appendChild(botaoBaixarPDF);

                // Adiciona botão de remover
                const botaoRemover = document.createElement("button");
                botaoRemover.textContent = "Remover";
                botaoRemover.className = "btn btn-danger btn-sm";
                botaoRemover.onclick = () => removerTarefa(tarefa.id);
                botoesContainer.appendChild(botaoRemover);

                // Adiciona o contêiner de botões ao item
                item.appendChild(botoesContainer);

                // Adiciona o item à lista
                lista.appendChild(item);

            });
        })
        .catch(error => console.error("Erro ao listar tarefas:", error));
}

function removerTarefa(tarefaId) {

    // Exibe uma caixa de confirmação antes de remover
    if (!confirm("Tem certeza de que deseja remover esta tarefa?")) {
        return; // Cancela a remoção se o usuário não confirmar
    }


    fetch(`${API_URL}/tarefas/${tarefaId}`, {
        method: "DELETE"
    })
        .then(response => {
            if (!response.ok) {
                throw new Error("Erro ao remover tarefa");
            }
            listarTarefas(); // Atualiza a lista após a remoção

            // Exibir mensagem de sucesso abaixo da lista de tarefas
            const mensagemSucesso = document.getElementById("mensagem-sucesso-lista");
            mensagemSucesso.textContent = "Tarefa removida com sucesso!";
            mensagemSucesso.style.display = "block";

            // Esconde a mensagem após 3 segundos
            setTimeout(() => {
                mensagemSucesso.style.display = "none";
            }, 3000);
        })
        .catch(error => console.error("Erro ao remover tarefa:", error));
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
                item.className = "list-group-item d-flex justify-content-between align-items-center"; // Estilo para alinhamento básico

                // Cria o conteúdo do item com as informações da palete
                const infoContainer = document.createElement("div");
                infoContainer.innerHTML = `
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
                item.appendChild(infoContainer);

                // Contêiner para botões
                const botoesContainer = document.createElement("div");
                botoesContainer.className = "d-flex gap-2 align-items-center";
                botoesContainer.style.marginRight = "15px"; // Margem à direita

                // Botão de baixar o PDF
                const botaoBaixarPDF = document.createElement("button");
                botaoBaixarPDF.innerHTML = '<i class="bi bi-download"></i> Baixar PDF';
                botaoBaixarPDF.className = "btn btn-secondary btn-sm";
                botaoBaixarPDF.onclick = () => {
                    const linkPDF = `${API_URL}/paletes/${palete.id}/pdf`;
                    window.open(linkPDF, "_blank"); // Abre o link do PDF em uma nova aba
                };
                botoesContainer.appendChild(botaoBaixarPDF);

                // Botão de remover
                const botaoRemover = document.createElement("button");
                botaoRemover.textContent = "Remover";
                botaoRemover.className = "btn btn-danger btn-sm";
                botaoRemover.onclick = () => removerPalete(palete.id);
                botoesContainer.appendChild(botaoRemover);

                // Adiciona o contêiner de botões ao item
                item.appendChild(botoesContainer);

                lista.appendChild(item); // Adiciona o item à lista
            });
        })
        .catch(error => console.error("Erro ao listar paletes:", error));
}





let dadosRegistro = {
    tarefa: null,
    trabalhador: null,
    palete: null
};

let estadoLeitura = "tarefa"; // Define o estado inicial como "tarefa"

// Inicializa o leitor de QR Code
function startQRCodeScanner(readerId) {
    const readerElement = document.getElementById(readerId);
    if (!readerElement) {
        console.error(`Elemento HTML com id=${readerId} não encontrado.`);
        return;
    }

    const html5QrCode = new Html5Qrcode(readerId);
    const config = { fps: 10, qrbox: { width: 250, height: 250 } };

    html5QrCode
        .start(
            { facingMode: "environment" }, // Usa a câmera traseira
            config,
            (decodedText) => processQRCode(decodedText),
            (errorMessage) => console.warn("Erro ao ler QR Code:", errorMessage)
        )
        .catch((err) => console.error("Erro ao iniciar o scanner:", err));
}

// Processar leitura dos QR Codes
function processQRCode(decodedText) {
    console.log("Estado atual:", estadoLeitura);
    console.log("QR Code lido:", decodedText);

    if (estadoLeitura === "tarefa" && !dadosRegistro.tarefa) {
        dadosRegistro.tarefa = decodedText;
        estadoLeitura = "trabalhador"; // Atualiza o estado
        exibirMensagemRegistro("📌 Tarefa lida com sucesso! Agora escaneie o cartão do trabalhador.", "info");

    } else if (estadoLeitura === "trabalhador" && !dadosRegistro.trabalhador) {
        dadosRegistro.trabalhador = decodedText;
        estadoLeitura = "palete"; // Atualiza o estado
        exibirMensagemRegistro("📌 Trabalhador lido com sucesso! Agora escaneie a palete.", "info");

    } else if (estadoLeitura === "palete" && !dadosRegistro.palete) {
        dadosRegistro.palete = decodedText;
        exibirMensagemRegistro("✅ Palete lida com sucesso! Registrando trabalho...", "sucesso");

        // Enviar os dados para a API
        registrarTrabalho();

        // Resetar os dados para um novo registro
        setTimeout(() => {
            dadosRegistro = { tarefa: null, trabalhador: null, palete: null };
            estadoLeitura = "tarefa"; // Reinicia o estado
            exibirMensagemRegistro("📷 Escaneie o QR Code da tarefa para iniciar um novo registro.", "info");
        }, 3000);
    } else {
        exibirMensagemRegistro("⚠️ QR Code já lido ou fora de sequência. Escaneie o próximo QR Code.", "erro");
    }
}

// Função para enviar os dados do registro para a API
function registrarTrabalho() {
    console.log("Dados preparados para envio:", JSON.stringify(dadosRegistro));

    fetch(`${API_URL}/registro_trabalho`, {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify({
            tarefa_qr: dadosRegistro.tarefa,
            trabalhador_qr: dadosRegistro.trabalhador,
            palete_qr: dadosRegistro.palete
        })
    })
        .then(response => response.json())
        .then(data => {
            console.log("Resposta da API:", data);
            exibirMensagemRegistro(`✅ ${data.message}`, "sucesso");
        })
        .catch(error => {
            console.error("Erro ao registrar trabalho:", error);
            exibirMensagemRegistro("❌ Erro ao registrar trabalho. Tente novamente.", "erro");
        });
}

// Exibir mensagens de progresso no registro
function exibirMensagemRegistro(mensagem, tipo = "info") {
    console.log("Mensagem exibida:", mensagem); // Log da mensagem para depuração

    const mensagemRegistro = document.getElementById("mensagem-registro");
    if (!mensagemRegistro) {
        console.error("Elemento para mensagens de registro não encontrado.");
        return;
    }

    mensagemRegistro.textContent = mensagem;
    mensagemRegistro.style.display = "block";
    mensagemRegistro.style.color = tipo === "sucesso" ? "green" : tipo === "erro" ? "red" : "black";
}




// Listar Registros de Trabalho
function listarRegistro() {
    fetch(`${API_URL}/registro_trabalho`)
        .then(response => response.json())
        .then(data => {
            const lista = document.getElementById("lista-registro");
            lista.innerHTML = ""; // Limpa a lista

            data.forEach(registroDia => {
                const diaItem = document.createElement("li");
                diaItem.innerHTML = `<h4>📅 ${registroDia.data}</h4>`;
                lista.appendChild(diaItem);

                Object.entries(registroDia.paletes_trabalhadas).forEach(([paleteId, paleteData]) => {
                    const paleteItem = document.createElement("ul");
                    paleteItem.innerHTML = `<strong>📦 Palete ID:</strong> ${paleteId}`;
                    diaItem.appendChild(paleteItem);

                    Object.entries(paleteData.secoes).forEach(([secaoNome, secaoData]) => {
                        const secaoItem = document.createElement("li");
                        secaoItem.innerHTML = `<h5>📍 Seção: ${secaoNome}</h5>`;
                        paleteItem.appendChild(secaoItem);

                        Object.entries(secaoData.tarefas).forEach(([tarefaId, tarefaInfo]) => {
                            const tarefaItem = document.createElement("ul");
                            tarefaItem.innerHTML = `
                                <li>⚙️ <strong>${tarefaInfo.nome}</strong></li>
                                <li>👷 Trabalhador: ${tarefaInfo.trabalhador_id}</li>
                                <li>⏳ Início: ${tarefaInfo.hora_inicio}</li>
                                <li>✅ Fim: ${tarefaInfo.hora_fim || "Em andamento"}</li>
                            `;
                            secaoItem.appendChild(tarefaItem);
                        });
                    });
                });
            });
        })
        .catch(error => console.error("Erro ao carregar os registros de trabalho:", error));
}
