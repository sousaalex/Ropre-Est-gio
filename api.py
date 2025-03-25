from flask import Flask, request, jsonify, send_from_directory, send_file, g
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
import re  # Importar o módulo de expressões regulares
import os
import json
import qrcode
import firebase_admin
from firebase_admin import credentials, firestore
import base64
from io import BytesIO
import tempfile


app = Flask(__name__)
CORS(app)



# Configuração do Firebase
if os.getenv('VERCEL_ENV'):
    # Em produção (Vercel)
    firebase_credentials = json.loads(os.getenv('FIREBASE_CREDENTIALS'))
    cred = credentials.Certificate(firebase_credentials)
else:
    # Em desenvolvimento local
    cred = credentials.Certificate("firebase_credentials.json")

firebase_admin.initialize_app(cred)
db = firestore.client()






# Rota para o index.html
@app.route('/')
def home():
    try:
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
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Erro ao gerar QR Code: {e}")
        raise

@app.route('/trabalhadores', methods=['GET'])
def get_trabalhadores():
    try:
        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM trabalhadores')
        trabalhadores = [dict(row) for row in cursor.fetchall()]
        return jsonify(trabalhadores), 200
    except Exception as e:
        return jsonify({'message': 'Erro ao listar trabalhadores.', 'details': str(e)}), 500

@app.route('/trabalhadores', methods=['POST'])
def add_trabalhador():
    try:
        data = request.get_json()
        nome = data.get('nome')
        is_chefe = data.get('chefe', False)
        
        if not nome:
            return jsonify({'message': 'Nome do trabalhador é obrigatório'}), 400

        # Gerar QR Code em Base64
        conteudo_qr = f"ID: {nome}\nChefe: {is_chefe}"
        qr_code_base64 = gerar_qr_code_base64(conteudo_qr)

        # Adicionar trabalhador ao Firestore
        trabalhador_ref = db.collection('trabalhadores').add({
            'nome': nome,
            'chefe': is_chefe,
            'qr_code': qr_code_base64
        })

        trabalhador_id = trabalhador_ref[1].id

        return jsonify({
            'message': 'Trabalhador adicionado com sucesso!',
            'id': trabalhador_id,
            'qr_code_trabalhador': qr_code_trabalhador,
            'qr_code_chefe': qr_code_chefe
        }), 201

    except Exception as e:
        return jsonify({'message': 'Erro ao adicionar trabalhador.', 'details': str(e)}), 500



@app.route('/cartao/<string:trabalhador_id>', methods=['GET'])
def gerar_cartao_pdf(trabalhador_id):
    try:
        cursor = get_db().cursor()
        cursor.execute('DELETE FROM trabalhadores WHERE id = ?', (id,))
        get_db().commit()
        
        if cursor.rowcount == 0:
            return jsonify({'message': 'Trabalhador não encontrado'}), 404
            
        return jsonify({'message': 'Trabalhador removido com sucesso!'}), 200
    except Exception as e:
        return jsonify({'message': 'Erro ao remover trabalhador.', 'details': str(e)}), 500

@app.route('/cartao/<string:trabalhador_id>/<string:tipo_cartao>', methods=['GET'])
def gerar_cartao_pdf(trabalhador_id, tipo_cartao):
    try:
        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM trabalhadores WHERE id = ?', (trabalhador_id,))
        trabalhador = cursor.fetchone()
        
        if not trabalhador:
            return jsonify({'message': 'Trabalhador não encontrado.'}), 404

        trabalhador = trabalhador_ref.to_dict()

        # Gerar QR Code a partir do Base64
        qr_code_base64 = trabalhador['qr_code']
        qr_code_data = base64.b64decode(qr_code_base64)
        qr_code_img = Image.open(BytesIO(qr_code_data))

        # Caminho temporário para salvar o PDF
        temp_dir = tempfile.gettempdir()
        pdf_path = f"{temp_dir}/cartao_{trabalhador_id}_{tipo_cartao}.pdf"
        largura, altura = 7 * cm, 10 * cm
        
        pdf = canvas.Canvas(pdf_path, pagesize=(largura, altura))

        # Adicionar QR Code ao cartão
        qr_code_img = qr_code_img.resize((100, 100))  # Redimensionar o QR Code
        qr_code_buffer = BytesIO()
        qr_code_img.save(qr_code_buffer, format="PNG")
        pdf.drawImage(ImageReader(qr_code_buffer), (largura - 100) / 2, altura - 120, width=100, height=100)

        # Adicionar informações do trabalhador logo abaixo do QR Code
        pdf.setFont("Helvetica", 12)  # Usar a fonte Helvetica (similar à Arial)

        # Definir a posição inicial para o texto (abaixo do QR Code)
        y_info_start = altura - 140  # Começar logo abaixo do QR Code
        line_spacing = 15  # Espaçamento entre as linhas de texto

        # Textos com informações do trabalhador
        nome_texto = f"Nome: {trabalhador['nome']}"
        chefe_texto = f"Chefe: {'Sim' if trabalhador.get('chefe', False) else 'Não'}"

        # Calcular larguras para centralização
        nome_width = pdf.stringWidth(nome_texto, "Helvetica", 12)
        chefe_width = pdf.stringWidth(chefe_texto, "Helvetica", 12)

        # Desenhar textos centralizados
        pdf.drawString((largura - nome_width) / 2, y_info_start, nome_texto)
        pdf.drawString((largura - chefe_width) / 2, y_info_start - 2 * line_spacing, chefe_texto)

        # Finalizar o PDF
        pdf.save()

        # Retornar o PDF como arquivo para download
        return send_from_directory(temp_dir, f"cartao_{trabalhador_id}.pdf", as_attachment=True)
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
        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM paletes')
        paletes = [dict(row) for row in cursor.fetchall()]
        return jsonify(paletes), 200
    except Exception as e:
        return jsonify({'message': 'Erro ao listar paletes.', 'details': str(e)}), 500

@app.route('/paletes', methods=['POST'])
def add_palete():
    try:
        data = request.get_json()

        # Validação dos campos obrigatórios
        required_fields = ['data_entrega', 'op', 'referencia', 'nome_produto',
                           'medida', 'cor_botao', 'cor_ribete',
                           'leva_embalagem', 'quantidade', 'data_hora', 'numero_lote']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            return jsonify({'message': f'Campos obrigatórios ausentes: {", ".join(missing_fields)}'}), 400

        # Gerar QR Code em Base64
        conteudo_qr = (
            f"Data de Entrega: {data['data_entrega']}\n"
            f"OP: {data['op']}\n"
            f"Referência: {data['referencia']}\n"
            f"Nome do Produto: {data['nome_produto']}\n"
        )
        qr_code_base64 = gerar_qr_code_base64(conteudo_qr)

        # Adicionar a palete ao Firestore
        palete_data = {**data, 'qr_code': qr_code_base64}
        db.collection('paletes').add(palete_data)

        return jsonify({
            'message': 'Palete adicionada com sucesso!',
            'qr_code': qr_code_base64
        }), 201

    except Exception as e:
        return jsonify({'message': 'Erro ao adicionar palete.', 'details': str(e)}), 500


# Rota para gerar o PDF da palete
# Rota para gerar o PDF da palete
@app.route('/paletes/<string:palete_id>/pdf', methods=['GET'])
def gerar_pdf_palete(palete_id):
    try:
        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM paletes WHERE id = ?', (palete_id,))
        palete = cursor.fetchone()
        
        if not palete:
            return jsonify({'message': 'Palete não encontrada.'}), 404
            
        qr_code_data = base64.b64decode(palete['qr_code'])
        qr_code_img = Image.open(BytesIO(qr_code_data))
        
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, f"palete_{palete_id}.pdf")
        largura, altura = A4
        
        pdf = canvas.Canvas(pdf_path, pagesize=A4)
        pdf.setFillColor(colors.lightblue)
        pdf.rect(0, 0, largura, altura, fill=True, stroke=False)
        
        qr_code_size = 250
        qr_code_img = qr_code_img.resize((qr_code_size, qr_code_size))
        qr_code_buffer = BytesIO()
        qr_code_img.save(qr_code_buffer, format="PNG")
        pdf.drawImage(ImageReader(qr_code_buffer), (largura - qr_code_size)/2, altura - 300, qr_code_size, qr_code_size)
        
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica", 12)
        y = altura - 320
        line_height = 14
        
        campos = [
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
        
        for campo in campos:
            pdf.drawString(50, y, campo)
            y -= line_height
        
        pdf.save()
        return send_from_directory(temp_dir, f"palete_{palete_id}.pdf", as_attachment=True)
    except Exception as e:
        return jsonify({'message': 'Erro ao gerar PDF.', 'details': str(e)}), 500

@app.route('/tarefas', methods=['GET'])
def get_tarefas():
    try:
        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM tarefas')
        tarefas = [dict(row) for row in cursor.fetchall()]
        return jsonify(tarefas), 200
    except Exception as e:
        return jsonify({'message': 'Erro ao listar tarefas.', 'details': str(e)}), 500

@app.route('/tarefas', methods=['POST'])
def add_tarefa():
    try:
        data = request.get_json()
        nome_tarefa = data.get('nome_tarefa')
        secao = data.get('secao')
        
        if not nome_tarefa or not secao:
            return jsonify({'message': 'Nome da tarefa e secção são obrigatórios.'}), 400

        # Gerar QR Code para a tarefa
        qr_code_data = f"Tarefa: {nome_tarefa}\nSecção: {secao}"
        qr_code_base64 = gerar_qr_code_base64(qr_code_data)

        # Salvar a tarefa no Firestore
        tarefa_data = {
            'nome': nome_tarefa, 
           'secao':secao,
           'qr_code': qr_code_base64
        }
        tarefa_ref = db.collection('tarefas').add(tarefa_data)

        return jsonify({
            'message': 'Tarefa adicionada com sucesso!',
            'tarefa_id': tarefa_ref[1].id,
            'qr_code': qr_code_base64
        }), 201

    except Exception as e:
        return jsonify({'message': 'Erro ao adicionar tarefa.', 'details': str(e)}), 500


# Rota para gerar o PDF da tarefa
@app.route('/tarefas/<string:tarefa_id>/pdf', methods=['GET'])
def gerar_pdf_tarefa(tarefa_id):
    try:
        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM tarefas WHERE id = ?', (tarefa_id,))
        tarefa = cursor.fetchone()
        
        if not tarefa:
            return jsonify({'message': 'Tarefa não encontrada.'}), 404
            
        qr_code_data = base64.b64decode(tarefa['qr_code'])
        qr_code_img = Image.open(BytesIO(qr_code_data))
        
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, f"tarefa_{tarefa_id}.pdf")
        largura, altura = (14*cm, 21*cm)
        
        pdf = canvas.Canvas(pdf_path, pagesize=(largura, altura))
        pdf.setFillColor(colors.lightgreen)
        pdf.rect(0, 0, largura, altura, fill=True, stroke=False)
        
        qr_code_size = 150
        qr_code_img = qr_code_img.resize((qr_code_size, qr_code_size))
        qr_code_buffer = BytesIO()
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
            f"Seção: {tarefa.get('secao', 'Não especificada')}",
        ]

        # Adicionar as informações ao PDF
        for info in informacoes:
            pdf.drawString(30, y_info_start, info)  # Alinhar o texto à esquerda
            y_info_start -= line_spacing

        # Finalizar e salvar o PDF
        pdf.save()
        return send_from_directory(temp_dir, f"tarefa_{tarefa_id}.pdf", as_attachment=True)
    except Exception as e:
        return jsonify({'message': 'Erro ao gerar PDF.', 'details': str(e)}), 500

@app.route('/registro_trabalho', methods=['GET'])
def get_registro_trabalho():
    try:
        registros_ref = db.collection('registros_trabalho').stream()
        registros = {}

        for dia_doc in registros_ref:
            dia_data = dia_doc.to_dict().get('data', 'Desconhecido')
            dia_id = dia_doc.id

            # Inicializar a estrutura para o dia
            if dia_data not in registros:
                registros[dia_data] = {
                    "data": dia_data,
                    "paletes_trabalhadas": {}
                }

            # Obter as paletes trabalhadas no dia
            paletes_ref = db.collection('registros_trabalho').document(dia_id).collection('paletes_trabalhadas').stream()

            for palete_doc in paletes_ref:
                palete_id = palete_doc.id
                palete_data = palete_doc.to_dict()

                # Inicializar a estrutura para a palete
                if palete_id not in registros[dia_data]["paletes_trabalhadas"]:
                    registros[dia_data]["paletes_trabalhadas"][palete_id] = {
                        "secoes": {}  # Adicionando a estrutura de secões
                    }

                # Obter as seções dentro da palete
                secoes_ref = db.collection('registros_trabalho').document(dia_id).collection('paletes_trabalhadas').document(palete_id).collection('secoes').stream()

                for secao_doc in secoes_ref:
                    secao_nome = secao_doc.id
                    secao_data = secao_doc.to_dict()

                    # Inicializar a estrutura para a seção
                    if secao_nome not in registros[dia_data]["paletes_trabalhadas"][palete_id]["secoes"]:
                        registros[dia_data]["paletes_trabalhadas"][palete_id]["secoes"][secao_nome] = {
                            "tarefas": {}
                        }

                    # Obter as tarefas dentro da seção
                    tarefas_ref = db.collection('registros_trabalho').document(dia_id).collection('paletes_trabalhadas').document(palete_id).collection('secoes').document(secao_nome).collection('tarefas').stream()

                    for tarefa_doc in tarefas_ref:
                        tarefa_id = tarefa_doc.id
                        tarefa_data = tarefa_doc.to_dict()

                        # Adicionar a tarefa à seção
                        registros[dia_data]["paletes_trabalhadas"][palete_id]["secoes"][secao_nome]["tarefas"][tarefa_id] = {
                            "nome": tarefa_data.get('nome', 'Nome Desconhecido'),
                            "trabalhador_id": tarefa_data.get('trabalhador_id', 'ID Desconhecido'),
                            "hora_inicio": tarefa_data.get('hora_inicio', 'Não informado'),
                            "hora_fim": tarefa_data.get('hora_fim', 'Em andamento')
                        }

        # Retornar os registros como uma lista
        registros_list = list(registros.values())
        return jsonify(registros_list), 200

    except Exception as e:
        print(f"Erro ao listar registros de trabalho: {e}")
        return jsonify({'message': 'Erro ao listar registros de trabalho.', 'details': str(e)}), 500

        return jsonify({'message': 'Erro ao listar registros de trabalho.', 'details': str(e)}), 500



# Função para formatar a data sem o "+00:00"
def formatar_horario():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Rota para registrar trabalho com tarefa, trabalhador e palete
@app.route('/registro_trabalho', methods=['POST'])
def registrar_trabalho():
    try:
        data = request.get_json()

        # Leitura dos QR Codes
        tarefa_qr = data.get('tarefa_qr')
        trabalhador_qr = data.get('trabalhador_qr')
        palete_qr = data.get('palete_qr')

        if not tarefa_qr or not trabalhador_qr or not palete_qr:
            return jsonify({'message': 'QR Codes de tarefa, trabalhador e palete são obrigatórios.'}), 400

        # Extrair IDs dos QR Codes
        tarefa_id = tarefa_qr.split(';')[0].replace('ID:', '').strip()
        trabalhador_id = trabalhador_qr.split(';')[0].replace('ID:', '').strip()
        palete_id = palete_qr.split(';')[0].replace('ID:', '').strip()
        secao = palete_qr.split(';')[1].replace('Secao:', '').strip()  # Capturar a seção corretamente

        # Validar tarefa no Firestore
        tarefa_ref = db.collection('tarefas').document(tarefa_id).get()
        if not tarefa_ref.exists:
            return jsonify({'message': f'Tarefa com ID {tarefa_id} não encontrada.'}), 404
        tarefa = tarefa_ref.to_dict()
        
        # Validar trabalhador no Firestore
        trabalhador_ref = db.collection('trabalhadores').document(trabalhador_id).get()
        if not trabalhador_ref.exists:
            return jsonify({'message': f'Trabalhador com ID {trabalhador_id} não encontrado.'}), 404

        # Data do registro
        data_atual = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        # Referência do dia no Firestore
        dia_ref = db.collection('registros_trabalho').document(data_atual)

        # Verificar se o documento do dia existe, senão criar
        dia_doc = dia_ref.get()
        if not dia_doc.exists:
            dia_ref.set({'data': data_atual})

        # Referência da palete dentro do dia
        palete_ref = dia_ref.collection('paletes_trabalhadas').document(palete_id)

        # Verificar se o documento da palete existe, senão criar
        palete_doc = palete_ref.get()
        if not palete_doc.exists:
            palete_ref.set({'secao': secao})  # Agora a seção é um campo dentro da palete

        # **CORREÇÃO IMPORTANTE**
        # Garantir que cada secção tenha suas próprias tarefas dentro da palete
        secao_ref = palete_ref.collection('secoes').document(secao)

        # Verificar se a seção existe dentro da palete
        secao_doc = secao_ref.get()
        if not secao_doc.exists:
            secao_ref.set({'nome': secao})

        # Referência da tarefa dentro da seção da palete
        tarefa_ref = secao_ref.collection('tarefas').document(tarefa_id)

        # Verificar se a tarefa já foi iniciada (para marcar o fim)
        tarefa_doc = tarefa_ref.get()
        if tarefa_doc.exists:
            tarefa_ref.update({'hora_fim': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')})
            return jsonify({
                'message': 'Tarefa finalizada com sucesso!',
                'tarefa_id': tarefa_id,
                'trabalhador_id': trabalhador_id,
                'palete_id': palete_id,
                'secao': secao
            }), 200

        # Se a tarefa ainda não existe, registrar o início
        registro_tarefa = {
            'nome': tarefa['nome'],
            'trabalhador_id': trabalhador_id,
            'hora_inicio': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'hora_fim': None  # Hora de fim será atualizada posteriormente
        }
        tarefa_ref.set(registro_tarefa)

        return jsonify({
            'message': 'Usuário registrado com sucesso!',
            'uid': user_id,
            'email': email
        }), 201
    except Exception as e:
        print(f"Erro ao registrar trabalho: {e}")
        return jsonify({'message': 'Erro ao registrar trabalho.', 'details': str(e)}), 500





if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)