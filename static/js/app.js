const API_URL = "http://10.0.1.242:5000";

// Listar Trabalhadores
function listarTrabalhadores() {
    fetch(`${API_URL}/trabalhadores`)
        .then(response => response.json())
        .then(data => {
            const lista = document.getElementById("lista-trabalhadores");
            lista.innerHTML = ""; // Limpa a lista existente

            data.forEach(trabalhador => {
                // Cria um item da lista para o trabalhador
                const item = document.createElement("li");
                item.className = "list-group-item"; // Classe para estilização básica

                // Adiciona destaque se for chefe
                if (trabalhador.chefe) { // Certifica-se de que é um chefe
                    item.innerHTML = `<span style="font-weight: bold; color: black;">${trabalhador.nome} - Secção: ${trabalhador.secao} (chefe)</span>`;
                } else {
                    item.textContent = `${trabalhador.nome} - Secção: ${trabalhador.secao}`;
                }

                // Adiciona botão de remover
                const botaoRemover = document.createElement("button");
                botaoRemover.textContent = "Remover";
                botaoRemover.className = "btn btn-danger btn-sm ms-3";
                botaoRemover.onclick = () => removerTrabalhador(trabalhador.id);
                item.appendChild(botaoRemover);

                lista.appendChild(item); // Adiciona o item à lista
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
        .then((data) => {
            alert("Palete adicionada com sucesso!");
            listarPaletes(); // Atualiza a lista
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





// Remover Palete
function removerPalete(id) {
    if (confirm("Tem certeza que deseja remover esta palete?")) {
        fetch(`${API_URL}/paletes/${id}`, {
            method: "DELETE",
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
                alert(data.message || "Palete removida com sucesso!");
                listarPaletes(); // Atualiza a lista de paletes
            })
            .catch(error => console.error("Erro ao remover palete:", error.message));
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
                item.innerHTML = `
                    <strong>Data de Entrega:</strong> ${palete.data_entrega} 
                    <strong>OP:</strong> ${palete.op} 
                    <strong>Referência:</strong> ${palete.referencia} 
                    <strong>Nome do Produto:</strong> ${palete.nome_produto} 
                    <strong>Medida:</strong> ${palete.medida} 
                    <strong>Cor do Botão:</strong> ${palete.cor_botao} 
                    <strong>Cor do Ribete:</strong> ${palete.cor_ribete}
                    <strong>Leva Embalagem:</strong> ${palete.leva_embalagem} 
                    <strong>Quantidade:</strong> ${palete.quantidade} 
                    <strong>Data e Hora:</strong> ${palete.data_hora} 
                    <strong>Número do Lote:</strong> ${palete.numero_lote}
                `;

                // Cria o botão de remover
                const botaoRemover = document.createElement("button");
                botaoRemover.textContent = "Remover";
                botaoRemover.className = "btn btn-danger btn-sm ms-2";
                botaoRemover.onclick = () => removerPalete(palete.id);

                // Adiciona o botão ao item da lista
                item.appendChild(botaoRemover);

                // Adiciona o item à lista de paletes
                lista.appendChild(item);
            });
        })
        .catch(error => console.error("Erro ao listar paletes:", error));
}





// Carregar lista de paletes ao carregar a aba
document.addEventListener("DOMContentLoaded", listarPaletes);


document.addEventListener("DOMContentLoaded", function () {
    // Configurar evento para carregar dados ao mudar de aba
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');

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

