console.log("Hostname atual:", window.location.hostname);

const API_URL = window.location.hostname.includes("localhost") || 
                window.location.hostname.includes("127.0.0.1") ||
                window.location.hostname.includes("192.168.30.20")
  ? "http://localhost:5000" // URL do backend local
  : `https://gestao-fabrica.vercel.app/`; // URL do Vercel (produção ou preview)

console.log("Verificando se o JavaScript está sendo carregado corretamente...");
console.log(`API_URL configurada: ${API_URL}`);

let secaoGlobal = null;  // Armazena a seção corretamente


// Aguarda o carregamento completo do DOM
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ DOM totalmente carregado! Isso significa que os eventos devem estar funcionais.");

    // Solicitar o tipo de usuário e configurar o layout
    const tipoUsuario = prompt("Digite o tipo de usuário (admin, chefe, funcionario):").toLowerCase();
    definirLayout(tipoUsuario);
    configurarScanner(tipoUsuario);

    // Se o tipo de usuário for admin, mostrar o modal de login
    if (tipoUsuario === "admin") {
        const modal = new bootstrap.Modal(document.getElementById("authModal"), {
            backdrop: 'static', // Impede o fechamento ao clicar fora
            keyboard: false // Impede o fechamento ao pressionar Esc
        });
        modal.show();
    }

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

    // Adicionar eventos aos botões do modal
    const loginButton = document.getElementById("login-button-admin");
    if (loginButton) {
        loginButton.addEventListener("click", () => {
            const email = document.getElementById("admin-email")?.value;
            const password = document.getElementById("admin-password")?.value;
            if (email && password) {
                loginAdmin(email, password);
            }
        });
    }

    const registerButton = document.getElementById("register-button-admin");
    if (registerButton) {
        registerButton.addEventListener("click", () => {
            const email = document.getElementById("register-email")?.value;
            const password = document.getElementById("register-password")?.value;
            if (email && password) {
                registerAdmin(email, password);
            }
        });
    }

    const showRegisterLink = document.getElementById("show-register");
    if (showRegisterLink) {
        showRegisterLink.addEventListener("click", (e) => {
            e.preventDefault();
            toggleFields(true);
        });
    }

    const showLoginLink = document.getElementById("show-login");
    if (showLoginLink) {
        showLoginLink.addEventListener("click", (e) => {
            e.preventDefault();
            toggleFields(false);
        });
    }

    const loginButtonTrabalhador = document.getElementById("login-button-trabalhador");
    if (loginButtonTrabalhador) {
        loginButtonTrabalhador.addEventListener("click", () => {
            loginAsTrabalhador();
        });
    }

    const loginButtonChefe = document.getElementById("login-button-chefe");
    if (loginButtonChefe) {
        loginButtonChefe.addEventListener("click", () => {
            loginAsChefe();
        });
    }

    // Evento de clique para exportar registros
    const btnExportarRegistros = document.querySelector(".btn-exportar-registros");
    if (btnExportarRegistros) {
        btnExportarRegistros.addEventListener("click", function() {
            console.log("Botão de exportar clicado"); // Debug
            fetch(`${API_URL}/exportar_registros`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error("Erro ao exportar registros.");
                    }
                    return response.blob(); // Recebe o arquivo como blob
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.style.display = "none";
                    a.href = url;

                    // Obter o nome do mês anterior
                    const data = new Date();
                    data.setMonth(data.getMonth() - 1);
                    const nomeMesAnterior = data.toLocaleString('pt-BR', { month: 'long', year: 'numeric' });
                    
                    a.download = `registros_trabalho_${nomeMesAnterior}.xlsx`; // Nome do arquivo com o mês anterior
                    console.log("Baixando arquivo:", a.download); // Debug

                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                })
                .catch(error => {
                    console.error("Erro ao baixar o arquivo:", error);
                    alert("Erro ao baixar os registros. Por favor, tente novamente.");
                });
        });
    } else {
        console.warn("Botão de exportar registros não encontrado"); // Debug
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
                trabalhadorInfo.innerHTML = `
                <strong>ID:</strong> ${trabalhador.id}<br>
                <strong>Nome:</strong> ${trabalhador.nome}
                `;
                if (trabalhador.chefe) {
                trabalhadorInfo.innerHTML += ` <strong>(Chefe)</strong>`;
                trabalhadorInfo.style.fontWeight = "bold";
                }
                item.appendChild(trabalhadorInfo);

                // Container de botões
                const buttonContainer = document.createElement("div");
                buttonContainer.className = "d-flex gap-2";

                // Botão de download do cartão de trabalhador
                const botaoDownloadTrabalhador = document.createElement("button");
                botaoDownloadTrabalhador.className = "btn btn-secondary btn-sm";
                botaoDownloadTrabalhador.innerHTML = `<i class="bi bi-download"></i> Cartão Trabalhador`;
                botaoDownloadTrabalhador.onclick = () => {
                    const linkTrabalhador = `${API_URL}/cartao/${trabalhador.id}/trabalhador`;
                    window.open(linkTrabalhador, "_blank");
                };
                buttonContainer.appendChild(botaoDownloadTrabalhador);

                // Se for chefe, criar também o botão de download do cartão de chefe
                if (trabalhador.chefe) {
                    const botaoDownloadChefe = document.createElement("button");
                    botaoDownloadChefe.className = "btn btn-secondary btn-sm"; 
                    botaoDownloadChefe.innerHTML = `<i class="bi bi-download"></i> Cartão Chefe`;
                    botaoDownloadChefe.onclick = () => {
                        const linkChefe = `${API_URL}/cartao/${trabalhador.id}/chefe`;
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
                    <strong>Secção:</strong> ${tarefa.secao}<br>
                `;


                // Contêiner para botões
                const botoesContainer = document.createElement("div");
                botoesContainer.className = "d-flex justify-content-end gap-2 align-items-center";
                botoesContainer.style.marginRight = "15px"; // Margem à direita

                // Adiciona botão de baixar QR Code
                const botaoBaixarPDF = document.createElement("button");
                botaoBaixarPDF.innerHTML = '<i class="bi bi-download"></i> Baixar PDF';
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





// **Estado inicial dos dados**
let dadosRegistro = {
    tarefa: null,
    trabalhador: null,
    palete: null
};

let estadoLeitura = "tarefa"; // Define o estado inicial como "tarefa"
let scannerAtivo = false; // Evita múltiplas inicializações
let html5QrCode; // Variável global para o scanner

// **Função para resetar o scanner e o estado**
function resetarEstadoScanner() {
    dadosRegistro = {
        tarefa: null,
        trabalhador: null,
        palete: null
    };
    estadoLeitura = "tarefa"; // Reinicia o estado para "tarefa"
    scannerAtivo = false; // Permite reiniciar o scanner
    atualizarProgresso(0); // Reseta a barra de progresso
    exibirMensagemRegistro("📷 Escaneie o QR Code da Tarefa para começar.", "info");

    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            console.log("🔄 Scanner reiniciado.");
        }).catch(err => console.error("❌ Erro ao parar o scanner:", err));
    }
}

// **Inicializa o scanner de QR Code**
function startQRCodeScanner(readerId) {
    const readerElement = document.getElementById(readerId);
    if (!readerElement) {
        console.error(`Elemento HTML com id=${readerId} não encontrado.`);
        return;
    }

    if (scannerAtivo) return; // Evita iniciar o scanner mais de uma vez
    scannerAtivo = true;

    exibirMensagemRegistro("📷 Escaneie o QR Code da Tarefa para começar.", "info");
    atualizarProgresso(0); // Reinicia a barra de progresso

    html5QrCode = new Html5Qrcode(readerId);
    const config = { fps: 10, qrbox: { width: 250, height: 250 } };

    html5QrCode
        .start(
            { facingMode: "user" },
            config,
            (decodedText) => processQRCode(decodedText),
            (errorMessage) => {
                if (!errorMessage.includes("No MultiFormat Readers were able to detect the code.")) {
                    console.warn("Erro ao ler QR Code:", errorMessage);
                }
            }
        )
        .catch(err => console.error("Erro ao iniciar o scanner:", err));
}

// **Processar a leitura dos QR Codes**
function processQRCode(decodedText) {
    console.log("📸 QR Code lido:", decodedText);

    const { tipoQR, idQR, secao } = identificarTipoQR(decodedText);

    console.log("🛠 Tipo identificado:", tipoQR, "ID:", idQR, "Seção:", secao);

    if (tipoQR === "desconhecido") {
        exibirMensagemRegistro("⚠️ QR Code não reconhecido. Tente novamente.", "erro");
        return;
    }

    if (estadoLeitura === "tarefa" && tipoQR === "tarefa" && !dadosRegistro.tarefa) {
        dadosRegistro.tarefa = idQR;
        if (secao) {
            dadosRegistro.secao = secao;
            console.log("✅ Seção armazenada:", dadosRegistro.secao);
        }
        estadoLeitura = "trabalhador";
        exibirMensagemRegistro("📌 Tarefa lida com sucesso! Agora escaneie o cartão do trabalhador.", "info");
        atualizarProgresso(33);

    } else if (estadoLeitura === "trabalhador" && (tipoQR === "trabalhador" || tipoQR === "chefe") && !dadosRegistro.trabalhador) {
        dadosRegistro.trabalhador = idQR;
        estadoLeitura = "palete";
        exibirMensagemRegistro("📌 Trabalhador lido com sucesso! Agora escaneie a palete.", "info");
        atualizarProgresso(66);

    } else if (estadoLeitura === "palete" && tipoQR === "palete" && !dadosRegistro.palete) {
        dadosRegistro.palete = idQR;
        exibirMensagemRegistro("✅ Palete lida com sucesso! Registrando trabalho...", "sucesso");
        atualizarProgresso(100);

        registrarTrabalho(); // Envia os dados para a API
        resetarEstadoScanner(); // Reseta o estado após registro

    } else {
        exibirMensagemRegistro("⚠️ QR Code incorreto ou já lido. Escaneie o correto.", "erro");
    }
}





// **Identificar o tipo de QR Code**
function identificarTipoQR(qrCodeText) {
    console.log("🔍 Analisando QR Code:", qrCodeText);

    const partes = qrCodeText.split(";");
    let idQR = "";
    let tipoQR = "desconhecido";
    let secao = null;

    partes.forEach(parte => {
        const [chave, valor] = parte.split(":").map(str => str.trim());

        if (chave === "ID") idQR = valor;
        if (chave === "Tarefa") tipoQR = "tarefa";
        if (chave === "Tipo") {
            if (valor === "Trabalhador") tipoQR = "trabalhador";
            if (valor === "Chefe") tipoQR = "chefe";
        }
        if (chave === "Secao" && tipoQR === "tarefa") {
            secaoGlobal = valor;  // Apenas define se for uma tarefa
            console.log("🔵 Secção atualizada globalmente:", secaoGlobal);
        }
        if (chave === "Referencia" || chave === "NumeroLote") tipoQR = "palete";
    });

    // Usa a seção global caso seja null (garante que mantenha o valor certo)
    secao = secaoGlobal;

    console.log("✅ Resultado da análise:", { tipoQR, idQR, secao });
    return { tipoQR, idQR, secao };
}




// **Enviar os dados do registro para a API**
function registrarTrabalho() {
    console.log("📡 Enviando registro de trabalho...");

    const payload = {
        tarefa_qr: `ID:${dadosRegistro.tarefa};Secao:${dadosRegistro.secao}`,
        trabalhador_qr: `ID:${dadosRegistro.trabalhador}`,
        palete_qr: `ID:${dadosRegistro.palete}`
    };

    console.log("📤 Payload enviado para API:", payload);

    fetch(`${API_URL}/registro_trabalho`, { // ✅ Usa a variável API_URL corretamente
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        console.log("✅ Resposta da API:", data);
        exibirMensagemRegistro("✅ Trabalho registrado com sucesso!", "sucesso");
    })
    .catch(error => {
        console.error("❌ Erro ao registrar trabalho:", error);
        exibirMensagemRegistro("❌ Erro ao registrar trabalho.", "erro");
    });
}


// **Exibir mensagens de progresso no registro**
function exibirMensagemRegistro(mensagem, tipo = "info") {
    let mensagemRegistro = document.getElementById("mensagem-registro");

    if (!mensagemRegistro) {
        mensagemRegistro = document.createElement("div");
        mensagemRegistro.id = "mensagem-registro";
        mensagemRegistro.style.position = "fixed";
        mensagemRegistro.style.bottom = "20px";
        mensagemRegistro.style.left = "50%";
        mensagemRegistro.style.transform = "translateX(-50%)";
        mensagemRegistro.style.backgroundColor = "white";
        mensagemRegistro.style.padding = "10px";
        mensagemRegistro.style.border = "1px solid black";
        mensagemRegistro.style.borderRadius = "5px";
        mensagemRegistro.style.fontWeight = "bold";
        mensagemRegistro.style.zIndex = "1000";
        document.body.appendChild(mensagemRegistro);
    }

    mensagemRegistro.textContent = mensagem;
    mensagemRegistro.style.display = "block";
    mensagemRegistro.style.color = tipo === "sucesso" ? "green" : tipo === "erro" ? "red" : "black";

    setTimeout(() => {
        mensagemRegistro.style.display = "none";
    }, 3000);
}

// **Atualizar a barra de progresso**
function atualizarProgresso(porcentagem) {
    let progressBar = document.getElementById("qr-progress-bar");

    if (!progressBar) {
        progressBar = document.createElement("div");
        progressBar.id = "qr-progress-bar";
        progressBar.style.width = "0%";
        progressBar.style.height = "20px";
        progressBar.style.backgroundColor = "#4CAF50"; // Verde
        progressBar.style.transition = "width 0.3s ease-in-out";
        document.body.appendChild(progressBar);
    }

    progressBar.style.width = `${porcentagem}%`;
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
                        secaoItem.innerHTML = `<h5>📍 Secção: ${secaoNome}</h5>`;
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

// Função auxiliar para obter o nome do mês anterior
function obterNomeMesAnterior() {
    const dataAtual = new Date();
    const mesAnterior = new Date(dataAtual.getFullYear(), dataAtual.getMonth() - 1, 1);
    const opcoes = { month: 'long' }; // Formato longo para o nome do mês
    return mesAnterior.toLocaleString('pt-BR', opcoes); // Formata o mês em português
}

// Evento de clique para exportar registros
const btnExportarRegistros = document.getElementById("btn-exportar-registros");
if (btnExportarRegistros) {
    btnExportarRegistros.addEventListener("click", function() {
        fetch(`${API_URL}/exportar_registros`)
            .then(response => {
                if (!response.ok) {
                    throw new Error("Erro ao exportar registros.");
                }
                return response.blob(); // Recebe o arquivo como blob
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.style.display = "none";
                a.href = url;

                // Obter o nome do mês anterior
                const nomeMesAnterior = obterNomeMesAnterior();
                a.download = `registros_trabalho_${nomeMesAnterior}.xlsx`; // Nome do arquivo com o mês anterior

                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            })
            .catch(error => console.error("Erro ao baixar o arquivo:", error));
    });
}

// Função para alternar os campos de login e registro
function toggleFields(isRegister) {
    if (isRegister) {
        document.getElementById("login-fields").style.display = "none"; // Oculta os campos de login
        document.getElementById("register-fields").style.display = "block"; // Mostra os campos de registro
        document.getElementById("authModalLabel").textContent = "Registrar como Admin"; // Atualiza o título do modal
    } else {
        document.getElementById("login-fields").style.display = "block"; // Mostra os campos de login
        document.getElementById("register-fields").style.display = "none"; // Oculta os campos de registro
        document.getElementById("authModalLabel").textContent = "Login como Admin"; // Atualiza o título do modal
    }
}

// Função para registrar um novo admin
function registerAdmin(email, password) {
    fetch(`${API_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.message || 'Falha no registro');
            });
        }
        return response.json();
    })
    .then(data => {
        document.getElementById("auth-message").textContent = data.message;
        const modal = bootstrap.Modal.getInstance(document.getElementById("authModal"));
        if (modal) {
            modal.hide();
        }
    })
    .catch(error => {
        document.getElementById("auth-message").textContent = `Erro: ${error.message}`;
    });
}

// Função para fazer login como admin
function loginAdmin(email, password) {
    fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.message || 'Falha na autenticação');
            });
        }
        return response.json();
    })
    .then(data => {
        document.getElementById("auth-message").textContent = data.message;
        const modal = bootstrap.Modal.getInstance(document.getElementById("authModal"));
        if (modal) {
            modal.hide();
        }
        document.getElementById("layout-compartilhado").style.display = "block";
    })
    .catch(error => {
        document.getElementById("auth-message").textContent = `Erro: ${error.message}`;
    });
}