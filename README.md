# Sistema de Registro de Trabalho por QR Code  

Este software automatiza o registro de trabalho numa fábrica utilizando QR Codes. Ele permite registrar os trabalhadores, as tarefas a serem realizadas e as paletes em uso, garantindo um controle eficiente do tempo de execução de cada atividade.  

## 📌 Funcionalidades  

- 📷 **Leitura de QR Codes** dos trabalhadores, tarefas e paletes.  
- 📝 **Registro de Trabalho** contendo os dados dos QR Codes do trabalhador, palete e tarefa.  
- ⏳ **Controle de Tempo** com registro de hora de início e fim das atividades.  
- 🔧 **Painel Administrativo** para adicionar trabalhadores, tarefas e paletes com geraçção automática de QR Codes.  

## 🛠️ Tecnologias Utilizadas  

### 📌 **Backend (API)**  
- **Linguagem:** Python  
- **Servidor da API:** Flask  
- **Banco de Dados:** Firestore Database  
- **Bibliotecas utilizadas:**  
  - `flask` → Criação do servidor da API  
  - `flask_cors` → Permitir requisições do frontend  
  - `firebase_admin` → Conexão com o Firestore Database e autenticação  
  - `qrcode` → Geração automática de QR Codes  
  - `pillow (PIL)` → Manipulação de imagens para os QR Codes  
  - `reportlab` → Geração de PDFs com cartões de trabalhadores e folhas de registro  
  - `datetime` → Controle de tempo de início e fim das atividades  
  - `pandas` → Manipulação de dados para exportação  
  - `openpyxl` → Geração e formatação de planilhas Excel (.xlsx)  
  - `base64` e `io.BytesIO` → Manipulação de imagens e arquivos temporários  
  - `re (expressões regulares)` → Validação e manipulação de strings  

### 🎨 **Frontend**  
- **HTML + CSS + Bootstrap** (interface)  
- **JavaScript** (conexão com a API e funcionalidades interativas)  
- **Biblioteca utilizada:**  
  - `html5-qrcode.min.js` → Leitura de QR Codes no navegador  


## ✅ O que já foi feito  

- [x] Leitura de QR Codes de trabalhadores, tarefas e paletes  
- [x] Registro automático com os dados escaneados  
- [x] Registro da **hora de início** e **hora de fim** do trabalho  
- [x] Painel administrativo para cadastrar novas tarefas, trabalhadores e paletes  
- [x] Geração automática de **QR Codes** para trabalhadores, tarefas e paletes  
- [x] **Exportação de dados** para planilhas Excel (.xlsx)  
- [x] **Geração de PDFs** com cartões de trabalhadores e registros de paletes/tarefas 
- [x] Implementação da **autenticação de usuários**  
- [x] Implementação da **autenticação de usuários**  
- [x] Melhorias na interface do painel administrativo  
- [x] Testes e ajustes finais  


## 📜 Licença

Este projeto está licenciado sob a **MIT License**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

Copyright (c) 2025 Tomás Pereira
