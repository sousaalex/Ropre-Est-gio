from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import re  # Importar o módulo de expressões regulares
import os
import json
import qrcode
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import auth
import base64
from io import BytesIO
import tempfile
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import PatternFill, Font, Border, Side
import sys  # Certifique-se de importar sys



app = Flask(__name__)
CORS(app)



# Configuração do Firebase
print("Iniciando configuração do Firebase...")
if os.getenv('VERCEL_ENV'):
    print("Usando credenciais do ambiente Vercel")
    firebase_credentials = json.loads(os.getenv('FIREBASE_CREDENTIALS'))
    cred = credentials.Certificate(firebase_credentials)
else:
    print("Usando credenciais do arquivo local")
    cred = credentials.Certificate("firebase_credentials.json")

try:
    firebase_admin.initialize_app(cred)
    print("✅ Firebase inicializado com sucesso!")
    db = firestore.client()
    print("✅ Cliente Firestore criado!")
except Exception as e:
    print(f"❌ Erro ao inicializar Firebase: {e}")
    raise e






# Rota para o index.html
@app.route('/')
def home():
    try:
        print("Tentando servir o index.html")
        return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')
    except Exception as e:
        print(f"Erro ao servir index.html: {e}")
        return "Erro ao servir a página inicial.", 500



@app.route('/favicon.ico')
def no_favicon():
    return '', 204

@app.route('/favicon.png')
def no_favicon_png():
    return '', 204



def gerar_qr_code_base64(conteudo):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(conteudo)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para Base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        base64_qr = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return base64_qr
    except Exception as e:
        print(f"Erro ao gerar QR Code: {e}")
        raise





# Rota para listar trabalhadores
@app.route('/trabalhadores', methods=['GET'])
def get_trabalhadores():
    try:
        trabalhadores_ref = db.collection('trabalhadores').stream()
        trabalhadores = [{'id': doc.id, **doc.to_dict()} for doc in trabalhadores_ref]
        return jsonify(trabalhadores), 200
    except Exception as e:
        return jsonify({'message': 'Erro ao listar trabalhadores.', 'details': str(e)}), 500




# Rota para adicionar trabalhador
@app.route('/trabalhadores', methods=['POST'])
def add_trabalhador():
    try:
        data = request.get_json()
        nome = data.get('nome')
        is_chefe = data.get('chefe', False)

        if not nome:
            return jsonify({'message': 'Nome do trabalhador é obrigatório.'}), 400

        # Criar trabalhador no Firestore para obter o ID
        trabalhador_ref = db.collection('trabalhadores').add({'nome': nome, 'chefe': is_chefe})
        trabalhador_id = trabalhador_ref[1].id  # Obtém o ID gerado automaticamente

       # **Gerar QR Code para Trabalhador**
        qr_code_trabalhador_data = f"ID:{trabalhador_id};Tipo:Trabalhador;Nome:{nome}"
        qr_code_trabalhador = gerar_qr_code_base64(qr_code_trabalhador_data)

        # **Gerar QR Code para Chefe (se aplicável)**
        qr_code_chefe = None
        if is_chefe:
            qr_code_chefe_data = f"ID:{trabalhador_id};Tipo:Chefe;Nome:{nome}"
            qr_code_chefe = gerar_qr_code_base64(qr_code_chefe_data)

        # Atualizar Firestore com os QR Codes corretos
        trabalhador_data = {
            'nome': nome,
            'chefe': is_chefe,
            'qr_code_trabalhador': qr_code_trabalhador,
            'qr_code_chefe': qr_code_chefe  # Pode ser None se não for chefe
        }
        db.collection('trabalhadores').document(trabalhador_id).set(trabalhador_data)

        return jsonify({
            'message': 'Trabalhador adicionado com sucesso!',
            'id': trabalhador_id,
            'qr_code_trabalhador': qr_code_trabalhador,
            'qr_code_chefe': qr_code_chefe
        }), 201

    except Exception as e:
        print(f"Erro ao adicionar trabalhador: {e}")
        return jsonify({'message': 'Erro ao adicionar trabalhador.', 'details': str(e)}), 500






@app.route('/cartao/<string:trabalhador_id>/<string:tipo_cartao>', methods=['GET'])
def gerar_cartao_pdf(trabalhador_id, tipo_cartao):
    try:
        # Buscar informações do trabalhador no Firestore
        trabalhador_ref = db.collection('trabalhadores').document(trabalhador_id).get()
        if not trabalhador_ref.exists:
            return jsonify({'message': 'Trabalhador não encontrado.'}), 404

        trabalhador = trabalhador_ref.to_dict()

        # Escolher o QR Code com base no tipo de cartão
        if tipo_cartao == "chefe" and trabalhador.get("chefe"):
            qr_code_base64 = trabalhador.get('qr_code_chefe')
            cor_cartao = colors.red  # Cartão vermelho para chefes
            titulo_cartao = "Cartão de Chefe"
        else:
            qr_code_base64 = trabalhador.get('qr_code_trabalhador')
            cor_cartao = colors.blue  # Cartão azul para trabalhadores
            titulo_cartao = "Cartão de Trabalhador"

        if not qr_code_base64:
            return jsonify({'message': 'QR Code não encontrado para este tipo de cartão.'}), 404

        # Converter QR Code Base64 em imagem
        qr_code_data = base64.b64decode(qr_code_base64)
        qr_code_img = Image.open(BytesIO(qr_code_data))

        # Criar o PDF
        temp_dir = tempfile.gettempdir()
        pdf_path = f"{temp_dir}/cartao_{trabalhador_id}_{tipo_cartao}.pdf"
        largura, altura = 7 * cm, 10 * cm
        pdf = canvas.Canvas(pdf_path, pagesize=(largura, altura))

        # Adicionar cor de fundo
        pdf.setFillColor(cor_cartao)
        pdf.rect(0, 0, largura, altura, fill=True, stroke=False)

        # Adicionar QR Code
        qr_code_img = qr_code_img.resize((100, 100))
        qr_code_buffer = BytesIO()
        qr_code_img.save(qr_code_buffer, format="PNG")
        pdf.drawImage(ImageReader(qr_code_buffer), (largura - 100) / 2, altura - 120, width=100, height=100)

        # Adicionar texto
        pdf.setFillColor(colors.white)  # Texto branco para visibilidade
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(20, altura - 150, f"Nome: {trabalhador['nome']}")
        pdf.drawString(20, altura - 170, f"ID: {trabalhador_id}")
        pdf.drawString(20, altura - 190, titulo_cartao)

        # Finalizar PDF
        pdf.save()

        return send_from_directory(temp_dir, f"cartao_{trabalhador_id}_{tipo_cartao}.pdf", as_attachment=True)

    except Exception as e:
        print(f"Erro ao gerar cartão: {e}")
        return jsonify({'message': 'Erro ao gerar cartão.', 'details': str(e)}), 500




    
# Rota para remover trabalhador
@app.route('/trabalhadores/<string:id>', methods=['DELETE'])
def delete_trabalhador(id):
    try:
        # Buscar trabalhador no Firestore
        trabalhador_ref = db.collection('trabalhadores').document(id)
        trabalhador = trabalhador_ref.get()
        if not trabalhador.exists:
            return jsonify({'message': 'Trabalhador não encontrado'}), 404

        

        # Remover trabalhador do Firestore
        trabalhador_ref.delete()

        return jsonify({'message': 'Trabalhador removido com sucesso!'}), 200
    except Exception as e:
        return jsonify({'message': 'Erro ao remover trabalhador.', 'details': str(e)}), 500


       
# Rota para listar todas as paletes
@app.route('/paletes', methods=['GET'])
def get_paletes():
    try:
        paletes_ref = db.collection('paletes').stream()
        paletes = [{'id': doc.id, **doc.to_dict()} for doc in paletes_ref]
        return jsonify(paletes), 200
    except Exception as e:
        return jsonify({'message': 'Erro ao listar paletes.', 'details': str(e)}), 500



# Rota para adicionar palete com geração de QR code
@app.route('/paletes', methods=['POST'])
def add_palete():
    try:
        data = request.get_json()

        # Validar campos obrigatórios
        required_fields = ['data_entrega', 'op', 'referencia', 'nome_produto', 'medida',
                           'cor_botao', 'cor_ribete', 'leva_embalagem', 'quantidade',
                           'data_hora', 'numero_lote']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            return jsonify({'message': f'Campos obrigatórios ausentes: {", ".join(missing_fields)}'}), 400

        # Criar o documento da palete primeiro para obter o ID
        palete_ref = db.collection('paletes').add(data)
        palete_id = palete_ref[1].id  # Obtém o ID gerado automaticamente

        # **Correção aplicada: Gerar QR Code com todas as informações necessárias**
        conteudo_qr = (
            f"ID:{palete_id};"
            f"Referencia:{data['referencia']};"
            f"Nome:{data['nome_produto']};"
            f"NumeroLote:{data['numero_lote']}"
        )
        qr_code_base64 = gerar_qr_code_base64(conteudo_qr)

        # Atualizar Firestore com o QR Code correto
        db.collection('paletes').document(palete_id).set({
            **data, 'qr_code': qr_code_base64
        })

        return jsonify({
            'message': 'Palete adicionada com sucesso!',
            'palete_id': palete_id,
            'qr_code': qr_code_base64
        }), 201

    except Exception as e:
        print(f"Erro ao adicionar palete: {e}")
        return jsonify({'message': 'Erro ao adicionar palete.', 'details': str(e)}), 500





# Rota para gerar o PDF da palete
@app.route('/paletes/<string:palete_id>/pdf', methods=['GET'])
def gerar_pdf_palete(palete_id):
    try:
        # Buscar informações da palete no Firestore
        palete_ref = db.collection('paletes').document(palete_id).get()
        if not palete_ref.exists:
            return jsonify({'message': 'Palete não encontrada.'}), 404

        palete = palete_ref.to_dict()

        # Gerar QR Code a partir do Base64
        qr_code_base64 = palete['qr_code']
        qr_code_data = base64.b64decode(qr_code_base64)
        qr_code_img = Image.open(BytesIO(qr_code_data))

        # Configurações do PDF
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, f"palete_{palete_id}.pdf")
        pdf = canvas.Canvas(pdf_path, pagesize=A4)
        largura, altura = A4  # Dimensões do papel A4 em pontos

        # Adicionar QR Code no topo
        qr_code_size = 250  # Tamanho do QR Code
        qr_code_buffer = BytesIO()
        qr_code_img = qr_code_img.resize((qr_code_size, qr_code_size))
        qr_code_img.save(qr_code_buffer, format="PNG")
        pdf.drawImage(ImageReader(qr_code_buffer), (largura - qr_code_size) / 2, altura - 260, width=qr_code_size, height=qr_code_size)

        # Adicionar informações da palete abaixo do QR Code
        pdf.setFont("Helvetica", 20)
        x_info_start = 50  # Posição fixa no eixo X (margem esquerda)
        y_info_start = altura - 300
        line_spacing = 25

        informacoes = [
            f"Data de Entrega: {palete['data_entrega']}",
            f"OP: {palete['op']}",
            f"Referência: {palete['referencia']}",
            f"Nome do Produto: {palete['nome_produto']}",
            f"Medida: {palete['medida']}",
            f"Cor do Botão: {palete['cor_botao']}",
            f"Cor do Ribete: {palete['cor_ribete']}",
            f"Leva Embalagem: {'Sim' if palete['leva_embalagem'] else 'Não'}",
            f"Quantidade: {palete['quantidade']}",
            f"Data e Hora: {palete['data_hora']}",
            f"Número do Lote: {palete['numero_lote']}"
        ]

        # Adicionar informações ao PDF
        for info in informacoes:
            pdf.drawString(x_info_start, y_info_start, info)
            y_info_start -= line_spacing

        # Adicionar conteúdo predefinido no final
        y_info_start -= 30  # Espaçamento adicional antes do conteúdo
        pdf.setFont("Helvetica-Bold", 17)
        pdf.drawString(x_info_start, y_info_start, "Secção de destino inicial e as próximas secções:")
        y_info_start -= 20
        pdf.setFont("Helvetica", 17)

        secao_destinos = [
            "(   ) Corte e vinco",
            "(   ) Secção da cola",
            "(   ) Acabamento",
            "(   ) Confeção",
            "(   ) Acabamento"
        ]

        for secao in secao_destinos:
            pdf.drawString(x_info_start, y_info_start, secao)
            y_info_start -= line_spacing

        # Finalizar e salvar o PDF
        pdf.save()

        # Retornar o PDF como arquivo para download
        return send_from_directory(temp_dir, f"palete_{palete_id}.pdf", as_attachment=True)

    except Exception as e:
        print(f"Erro ao gerar PDF da palete: {e}")
        return jsonify({'message': 'Erro ao gerar PDF.', 'details': str(e)}), 500



        
# Rota para remover palete
@app.route('/paletes/<string:palete_id>', methods=['DELETE'])
def delete_palete(palete_id):
    try:
        # Buscar a palete pelo ID no Firebase Firestore
        palete_ref = db.collection('paletes').document(palete_id)
        palete = palete_ref.get()
        if not palete.exists:
            return jsonify({'message': 'Palete não encontrada'}), 404

        
        # Remover a palete da base de dados Firestore
        palete_ref.delete()
        print(f"Palete removida do Firestore: {palete_id}")

        return jsonify({'message': 'Palete removida com sucesso!'}), 200
    except Exception as e:
        print(f"Erro ao remover palete: {e}")
        return jsonify({'message': 'Erro ao remover palete', 'details': str(e)}), 500


# Rota para listar tarefas
@app.route('/tarefas', methods=['GET'])
def get_tarefas():
    try:
        # Buscar todas as tarefas no Firestore
        tarefas_ref = db.collection('tarefas').stream()
        
        # Criar a lista de tarefas com seus dados
        tarefas = [{'id': doc.id, **doc.to_dict()} for doc in tarefas_ref]
        
        # Retornar as tarefas como resposta JSON
        return jsonify(tarefas), 200
    except Exception as e:
        print(f"Erro ao listar tarefas: {e}")
        return jsonify({'message': 'Erro ao listar tarefas.', 'details': str(e)}), 500



# Rota para gerar QR Code de tarefas
@app.route('/tarefas', methods=['POST'])
def add_tarefa():
    try:
        data = request.get_json()
        nome_tarefa = data.get('nome_tarefa')
        secao = data.get('secao')

        if not nome_tarefa or not secao:
            return jsonify({'message': 'Nome da tarefa e secção são obrigatórios.'}), 400

        # Criar a tarefa no Firestore primeiro para obter o ID
        tarefa_ref = db.collection('tarefas').add({'nome': nome_tarefa, 'secao': secao})
        tarefa_id = tarefa_ref[1].id  # Obter o ID gerado automaticamente

        # Gerar QR Code que inclui o ID da tarefa
        qr_code_data = f"ID:{tarefa_id};Tarefa:{nome_tarefa};Secao:{secao}"
        qr_code_base64 = gerar_qr_code_base64(qr_code_data)

        # Atualizar a tarefa no Firestore com o QR Code correto
        db.collection('tarefas').document(tarefa_id).set({
            'nome': nome_tarefa,
            'secao': secao,
            'qr_code': qr_code_base64
        })

        return jsonify({
            'message': 'Tarefa adicionada com sucesso!',
            'tarefa_id': tarefa_id,
            'qr_code': qr_code_base64
        }), 201

    except Exception as e:
        print(f"Erro ao adicionar tarefa: {e}")
        return jsonify({'message': 'Erro ao adicionar tarefa.', 'details': str(e)}), 500



# Rota para gerar o PDF da tarefa
@app.route('/tarefas/<string:tarefa_id>/pdf', methods=['GET'])
def gerar_pdf_tarefa(tarefa_id):
    try:
        # Buscar informações da tarefa no Firestore
        tarefa_ref = db.collection('tarefas').document(tarefa_id).get()
        if not tarefa_ref.exists:
            return jsonify({'message': 'Tarefa não encontrada.'}), 404

        tarefa = tarefa_ref.to_dict()

        # Gerar QR Code a partir do Base64
        qr_code_base64 = tarefa['qr_code']
        qr_code_data = base64.b64decode(qr_code_base64)
        qr_code_img = Image.open(BytesIO(qr_code_data))

       # Configurações do PDF
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, f"tarefa_{tarefa_id}.pdf")
        pdf = canvas.Canvas(pdf_path, pagesize=(14 * cm, 21 * cm))
        largura, altura = (14 * cm, 21 * cm)  # Dimensões do papel A5 em pontos

        # Adicionar QR Code no topo, maior e centralizado
        qr_code_size = 300  # Tamanho do QR Code maior
        qr_code_buffer = BytesIO()
        qr_code_img = qr_code_img.resize((qr_code_size, qr_code_size))
        qr_code_img.save(qr_code_buffer, format="PNG")
        pdf.drawImage(
            ImageReader(qr_code_buffer),
            (largura - qr_code_size) / 2,  # Centralizar horizontalmente
            altura - qr_code_size - 50,   # Distância do topo
            width=qr_code_size,
            height=qr_code_size
        )

        # Adicionar informações da tarefa abaixo do QR Code, maiores
        pdf.setFont("Helvetica", 20)  # Fonte maior e negrito
        y_info_start = altura - qr_code_size - 100  # Ajustar para abaixo do QR Code
        line_spacing = 30  # Maior espaçamento entre linhas

        informacoes = [
            f"Nome da Tarefa: {tarefa['nome']}",
            f"Secção: {tarefa.get('secao', 'Não especificada')}",
        ]

        # Adicionar as informações ao PDF
        for info in informacoes:
            pdf.drawString(30, y_info_start, info)  # Alinhar o texto à esquerda
            y_info_start -= line_spacing

        # Finalizar e salvar o PDF
        pdf.save()


        # Retornar o PDF como arquivo para download
        return send_from_directory(temp_dir, f"tarefa_{tarefa_id}.pdf", as_attachment=True)

    except Exception as e:
        print(f"Erro ao gerar PDF da tarefa: {e}")
        return jsonify({'message': 'Erro ao gerar PDF.', 'details': str(e)}), 500
    

    # Rota para remover tarefa
@app.route('/tarefas/<string:tarefa_id>', methods=['DELETE'])
def delete_tarefa(tarefa_id):
    try:
        # Buscar a tarefa pelo ID no Firestore
        tarefa_ref = db.collection('tarefas').document(tarefa_id)
        tarefa = tarefa_ref.get()
        if not tarefa.exists:
            return jsonify({'message': 'Tarefa não encontrada'}), 404

        # Remover a tarefa do Firestore
        tarefa_ref.delete()

        return jsonify({'message': 'Tarefa removida com sucesso!'}), 200
    except Exception as e:
        print(f"Erro ao remover tarefa: {e}")
        return jsonify({'message': 'Erro ao remover tarefa.', 'details': str(e)}), 500

    


# Rota para listar todos os registros de trabalho
@app.route('/registro_trabalho', methods=['GET'])
def get_registro_trabalho():
    try:
        registros_ref = db.collection('registros_trabalho').stream()
        registros = []

        for dia_doc in registros_ref:
            dia_id = dia_doc.id
            dia_data = dia_doc.to_dict().get('data', 'Desconhecido')
            print(f"📅 Buscando registros para o dia: {dia_id}")

            registro_dia = {
                "data": dia_data,
                "paletes_trabalhadas": {}
            }

            paletes_ref = db.collection('registros_trabalho').document(dia_id).collection('paletes_trabalhadas').stream()
            for palete_doc in paletes_ref:
                palete_id = palete_doc.id
                print(f"📦 Palete encontrada: {palete_id}")

                registro_dia["paletes_trabalhadas"][palete_id] = {"secoes": {}}

                secoes_ref = db.collection('registros_trabalho').document(dia_id).collection('paletes_trabalhadas').document(palete_id).collection('secoes').stream()
                for secao_doc in secoes_ref:
                    secao_id = secao_doc.id
                    print(f"📍 Secção encontrada: {secao_id}")

                    registro_dia["paletes_trabalhadas"][palete_id]["secoes"][secao_id] = {"tarefas": {}}

                    tarefas_ref = db.collection('registros_trabalho').document(dia_id).collection('paletes_trabalhadas').document(palete_id).collection('secoes').document(secao_id).collection('tarefas').stream()
                    for tarefa_doc in tarefas_ref:
                        tarefa_id = tarefa_doc.id
                        tarefa_data = tarefa_doc.to_dict()
                        print(f"⚙️ Tarefa encontrada: {tarefa_id}")

                        registro_dia["paletes_trabalhadas"][palete_id]["secoes"][secao_id]["tarefas"][tarefa_id] = {
                            "nome": tarefa_data.get('nome', 'Nome Desconhecido'),
                            "trabalhador_id": tarefa_data.get('trabalhador_id', 'ID Desconhecido'),
                            "hora_inicio": tarefa_data.get('hora_inicio', 'Não informado'),
                            "hora_fim": tarefa_data.get('hora_fim', 'Em andamento')
                        }

            registros.append(registro_dia)

        return jsonify(registros), 200

    except Exception as e:
        print(f"❌ Erro ao listar registros de trabalho: {e}")
        return jsonify({'message': 'Erro ao listar registros de trabalho.', 'details': str(e)}), 500





# Função para formatar a data sem o "+00:00"
def formatar_horario():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def extrair_valor(qr_text, chave):
    """ Função para extrair um valor específico de um QR Code """
    for item in qr_text.split(';'):
        if chave in item:
            return item.replace(chave, '').strip()
    return None  # Retorna None se não encontrar

@app.route('/registro_trabalho', methods=['POST'])
def registrar_trabalho():
    try:
        data = request.get_json()

        # Verificar se todos os QR Codes estão presentes
        tarefa_qr = data.get('tarefa_qr')
        trabalhador_qr = data.get('trabalhador_qr')
        palete_qr = data.get('palete_qr')

        if not tarefa_qr or not trabalhador_qr or not palete_qr:
            return jsonify({'message': 'QR Codes de tarefa, trabalhador e palete são obrigatórios.'}), 400

        # Extrair informações dos QR Codes
        tarefa_id = extrair_valor(tarefa_qr, "ID:")
        trabalhador_id = extrair_valor(trabalhador_qr, "ID:")
        palete_id = extrair_valor(palete_qr, "ID:")
        secao = extrair_valor(tarefa_qr, "Secao:") or "Default"

        print(f"✅ Secção extraída: {secao}")

        # Verificar se a tarefa existe
        tarefa_ref = db.collection('tarefas').document(tarefa_id)
        if not tarefa_ref.get().exists:
            return jsonify({'message': f'Tarefa com ID {tarefa_id} não encontrada.'}), 404
        tarefa_data = tarefa_ref.get().to_dict()

        # Verificar se o trabalhador existe
        trabalhador_ref = db.collection('trabalhadores').document(trabalhador_id)
        if not trabalhador_ref.get().exists:
            return jsonify({'message': f'Trabalhador com ID {trabalhador_id} não encontrado.'}), 404

        # Criar registro do dia
        data_atual = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        dia_ref = db.collection('registros_trabalho').document(data_atual)

        if not dia_ref.get().exists:
            dia_ref.set({'data': data_atual})
        print(f"📅 Registro do dia criado/atualizado: {data_atual}")

        # Criar registro da palete
        palete_ref = dia_ref.collection('paletes_trabalhadas').document(palete_id)
        if not palete_ref.get().exists:
            palete_ref.set({})
        print(f"📦 Registro da palete criado/atualizado: {palete_id}")

        # Criar registro da seção
        secao_ref = palete_ref.collection('secoes').document(secao)
        if not secao_ref.get().exists:
            secao_ref.set({'nome': secao})
        print(f"📍 Registro da secção criado/atualizado: {secao}")

        # Registrar a tarefa
        tarefa_ref = secao_ref.collection('tarefas').document(tarefa_id)
        if tarefa_ref.get().exists:
            tarefa_ref.update({'hora_fim': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')})
            print(f"✅ Tarefa finalizada: {tarefa_id}")
            return jsonify({'message': 'Tarefa finalizada com sucesso!'}), 200

        tarefa_ref.set({
            'nome': tarefa_data['nome'],
            'trabalhador_id': trabalhador_id,
            'hora_inicio': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'hora_fim': None
        })
        print(f"✅ Nova tarefa registrada: {tarefa_id}")

        return jsonify({
            'message': 'Registro de trabalho adicionado com sucesso!',
            'tarefa_id': tarefa_id,
            'trabalhador_id': trabalhador_id,
            'palete_id': palete_id,
            'secao': secao
        }), 201

    except Exception as e:
        print(f"❌ Erro ao registrar trabalho: {e}")
        return jsonify({'message': 'Erro ao registrar trabalho.', 'details': str(e)}), 500



# Rota para exportar registros de trabalho para Excel
@app.route('/exportar_registros', methods=['GET'])
def exportar_registros():
    try:
        registros_ref = db.collection('registros_trabalho').stream()
        registros = []

        for dia_doc in registros_ref:
            dia_id = dia_doc.id
            dia_data = dia_doc.to_dict().get('data', 'Desconhecido')

            paletes_ref = db.collection('registros_trabalho').document(dia_id).collection('paletes_trabalhadas').stream()
            for palete_doc in paletes_ref:
                palete_id = palete_doc.id
                secoes_ref = db.collection('registros_trabalho').document(dia_id).collection('paletes_trabalhadas').document(palete_id).collection('secoes').stream()
                for secao_doc in secoes_ref:
                    secao_id = secao_doc.id
                    tarefas_ref = db.collection('registros_trabalho').document(dia_id).collection('paletes_trabalhadas').document(palete_id).collection('secoes').document(secao_id).collection('tarefas').stream()
                    for tarefa_doc in tarefas_ref:
                        tarefa_data = tarefa_doc.to_dict()
                        registros.append({
                            'Data': dia_data,
                            'Palete ID': palete_id,
                            'Secção': secao_id,
                            'Tarefa Nome': tarefa_data.get('nome', 'Desconhecido'),
                            'Trabalhador ID': tarefa_data.get('trabalhador_id', 'Desconhecido'),
                            'Hora Início': tarefa_data.get('hora_inicio', 'Não informado'),
                            'Hora Fim': tarefa_data.get('hora_fim', 'Em andamento')
                        })

        # Criar um DataFrame do pandas
        df = pd.DataFrame(registros)

        # Criar um objeto BytesIO para armazenar o arquivo Excel em memória
        output = BytesIO()
        workbook = Workbook()
        worksheet = workbook.active

        # Adicionar os dados do DataFrame ao worksheet
        for r in dataframe_to_rows(df, index=False, header=True):
            worksheet.append(r)

        # Definir estilos para o cabeçalho
        header_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")  # Cor de fundo amarela
        header_font = Font(bold=True)  # Texto em negrito
        border_style = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))  # Bordas finas

        # Aplicar estilos ao cabeçalho
        for cell in worksheet[1]:  # A primeira linha é o cabeçalho
            cell.fill = header_fill
            cell.font = header_font
            cell.border = border_style

        # Aplicar bordas a todas as células
        for row in worksheet.iter_rows(min_row=1, max_row=worksheet.max_row, min_col=1, max_col=worksheet.max_column):
            for cell in row:
                cell.border = border_style

        # Ajustar a largura das colunas
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter  # Obter a letra da coluna
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)  # Adiciona um pouco de espaço
            worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)  # Voltar ao início do objeto BytesIO
        workbook.save(output)  # Salvar o workbook no objeto BytesIO
        output.seek(0)  # Voltar ao início do objeto BytesIO

        # Limpar os registros após o download (opcional)
        for dia_doc in registros_ref:
            db.collection('registros_trabalho').document(dia_doc.id).delete()

        # Definir o nome do arquivo aqui
        return send_file(output, as_attachment=True, download_name='registros_trabalho.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        print(f"Erro ao exportar registros: {e}")
        return jsonify({'message': 'Erro ao exportar registros.', 'details': str(e)}), 500
    


@app.route('/register', methods=['POST'])
def register():
    print("Requisição de registro recebida", flush=True)
    try:
        if not request.is_json:
            print("Request não é JSON.", flush=True)
            return jsonify({'message': 'Content-Type deve ser application/json'}), 400

        data = request.get_json()
        print(f"Dados recebidos: {data}", flush=True)
        if not data or 'email' not in data or 'password' not in data:
            print("Dados incompletos: email ou password ausentes.", flush=True)
            return jsonify({'message': 'Email e password são obrigatórios'}), 400

        email = data['email']
        password = data['password']
        if not email or not password:
            print("Email ou password vazios.", flush=True)
            return jsonify({'message': 'Email e password não podem estar vazios'}), 400

        user = auth.create_user(
            email=email,
            password=password
        )
        print(f"Usuário criado com sucesso: {user.uid}", flush=True)
        return jsonify({
            'message': 'Usuário registrado com sucesso!',
            'uid': user.uid,
            'email': email
        }), 201

    except auth.EmailAlreadyExistsError:
        print("Erro: Email já está em uso", flush=True)
        return jsonify({'message': 'Este email já está registrado'}), 409
    except ValueError as e:
        print(f"Erro de validação: {str(e)}", flush=True)
        return jsonify({'message': 'Dados inválidos', 'details': str(e)}), 400
    except Exception as e:
        print(f"Erro inesperado no registro: {str(e)}", flush=True)
        return jsonify({'message': 'Erro interno no servidor', 'details': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    id_token = data.get('idToken')  # Recebe o token do frontend

    try:
        # Verifica o token do Firebase
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        return jsonify({'message': 'Usuário autenticado com sucesso!', 'uid': uid}), 200
    except Exception as e:
        return jsonify({'message': 'Erro ao autenticar usuário.', 'details': str(e)}), 401

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
