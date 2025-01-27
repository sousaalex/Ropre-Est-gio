from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
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
        secao = data.get('secao')
        is_chefe = data.get('chefe', False)

        if not nome or not secao:
            return jsonify({'message': 'Nome e seção são obrigatórios.'}), 400

        # Gerar QR Code em Base64
        conteudo_qr = f"ID: {nome}\nSeção: {secao}\nChefe: {is_chefe}"
        qr_code_base64 = gerar_qr_code_base64(conteudo_qr)

        # Adicionar trabalhador ao Firestore
        trabalhador_ref = db.collection('trabalhadores').add({
            'nome': nome,
            'secao': secao,
            'chefe': is_chefe,
            'qr_code': qr_code_base64
        })

        trabalhador_id = trabalhador_ref[1].id

        return jsonify({
            'message': 'Trabalhador adicionado com sucesso!',
            'id': trabalhador_id,
            'qr_code': qr_code_base64
        }), 201
    except Exception as e:
        print(f"Erro ao adicionar trabalhador: {e}")
        return jsonify({'message': 'Erro ao adicionar trabalhador.', 'details': str(e)}), 500







@app.route('/cartao/<string:trabalhador_id>', methods=['GET'])
def gerar_cartao(trabalhador_id):
    try:
        print(f"Gerando cartão para trabalhador ID: {trabalhador_id}")  # Log para debug
        # Buscar informações do trabalhador no Firestore
        trabalhador_ref = db.collection('trabalhadores').document(trabalhador_id).get()
        if not trabalhador_ref.exists:
            return jsonify({'message': 'Trabalhador não encontrado.'}), 404

        trabalhador = trabalhador_ref.to_dict()
        print(f"Trabalhador encontrado: {trabalhador}")  # Verificar os dados

        # Gerar QR Code a partir do Base64
        qr_code_base64 = trabalhador['qr_code']
        qr_code_data = base64.b64decode(qr_code_base64)
        qr_code_img = Image.open(BytesIO(qr_code_data))

        # Criar imagem do cartão
        largura, altura = 400, 600
        cartao = Image.new('RGB', (largura, altura), 'white')
        draw = ImageDraw.Draw(cartao)

        # Adicionar QR Code ao cartão
        qr_code_tamanho = 200
        qr_code_img = qr_code_img.resize((qr_code_tamanho, qr_code_tamanho))
        cartao.paste(qr_code_img, (100, 100))

        # Configuração da fonte
        font_path = os.path.join(os.path.dirname(__file__), 'static', 'fonts', 'arial.ttf')
        print(f"Font path: {font_path}")  # Verificar se o caminho está correto
        font_size = 24
        fonte = ImageFont.truetype(font_path, font_size)

        draw.text((50, 350), f"Nome: {trabalhador['nome']}", fill="black", font=fonte)
        draw.text((50, 400), f"Secção: {trabalhador['secao']}", fill="black", font=fonte)
        if trabalhador.get('chefe', False):
            draw.text((50, 450), "Chefe: Sim", fill="black", font=fonte)
        else:
            draw.text((50, 450), "Chefe: Não", fill="black", font=fonte)

        # Salvar o cartão no diretório temporário
        temp_dir = tempfile.gettempdir()
        cartao_path = os.path.join(temp_dir, f"cartao_{trabalhador_id}.png")
        print(f"Salvando cartão em: {cartao_path}")
        cartao.save(cartao_path, format="PNG")

        # Retornar o cartão como um arquivo
        return send_from_directory(temp_dir, f"cartao_{trabalhador_id}.png", as_attachment=True)
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
        print(f"Erro ao adicionar palete: {e}")
        return jsonify({'message': 'Erro ao adicionar palete.', 'details': str(e)}), 500











        
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









# Rota para listar todos os registros de trabalho
@app.route('/registro_trabalho', methods=['GET'])
def get_registro_trabalho():
    try:
        registros_ref = db.collection('registros_trabalho').stream()
        registros = []
        for r in registros_ref:
            registro = r.to_dict()
            registros.append({
                'id': r.id,
                'trabalhador': {'id': registro['trabalhador_id'], 'nome': registro['trabalhador_nome']},
                'palete': {'id': registro['palete_id'], 'nome_produto': registro['palete_nome']},
                'horario_inicio': registro['horario_inicio'],
                'horario_fim': registro.get('horario_fim')
            })

        print(f"GET /registro_trabalho - {len(registros)} registros encontrados")
        return jsonify(registros), 200
    except Exception as e:
        print(f"Erro ao listar registros de trabalho: {e}")
        return jsonify({'message': 'Erro ao listar registros de trabalho.', 'details': str(e)}), 500


# Rota para registrar início ou fim de trabalho
@app.route('/registro_trabalho', methods=['POST'])
def registro_trabalho():
    try:
        data = request.get_json()

        # Validação dos dados enviados
        trabalhador_qr = data.get('trabalhador_qr')  # QR Code do trabalhador
        palete_qr = data.get('palete_qr')  # QR Code da palete

        if not trabalhador_qr:
            return jsonify({'message': 'QR Code do trabalhador não fornecido.'}), 400
        if not palete_qr:
            return jsonify({'message': 'QR Code da palete não fornecido.'}), 400

        # Extrair IDs do QR Code
        try:
            trabalhador_id = trabalhador_qr.split(';')[0].replace('ID', '').strip()
            palete_id = palete_qr.split(';')[0].replace('ID', '').strip()
        except (IndexError, ValueError):
            return jsonify({'message': 'QR Code inválido.'}), 400

        # Validar trabalhador no Firestore
        trabalhador_ref = db.collection('trabalhadores').document(trabalhador_id).get()
        if not trabalhador_ref.exists:
            return jsonify({'message': f'Trabalhador com ID {trabalhador_id} não encontrado.'}), 404
        trabalhador = trabalhador_ref.to_dict()

        # Validar palete no Firestore
        palete_ref = db.collection('paletes').document(palete_id).get()
        if not palete_ref.exists:
            return jsonify({'message': f'Palete com ID {palete_id} não encontrada.'}), 404
        palete = palete_ref.to_dict()

        # Verificar se há um trabalho em andamento para o trabalhador
        registros_ref = db.collection('registros_trabalho').where('trabalhador_id', '==', trabalhador_id).where('horario_fim', '==', None).stream()
        registro_existente = next((r.to_dict() for r in registros_ref), None)

        if registro_existente:
            # Finalizar trabalho existente
            registro_id = registro_existente['id']
            db.collection('registros_trabalho').document(registro_id).update({
                'horario_fim': datetime.now(timezone.utc).isoformat()
            })

            return jsonify({
                'registro_id': registro_id,
                'trabalhador': trabalhador['nome'],
                'palete': palete['nome_produto'],
                'horario_inicio': registro_existente['horario_inicio'],
                'horario_fim': datetime.now(timezone.utc).isoformat(),
                'message': 'Trabalho finalizado com sucesso.'
            }), 200

        # Criar novo registro de trabalho
        novo_registro = {
            'trabalhador_id': trabalhador_id,
            'trabalhador_nome': trabalhador['nome'],
            'palete_id': palete_id,
            'palete_nome': palete['nome_produto'],
            'horario_inicio': datetime.now(timezone.utc).isoformat(),
            'horario_fim': None
        }
        registro_ref = db.collection('registros_trabalho').add(novo_registro)

        return jsonify({
            'registro_id': registro_ref[1].id,
            'trabalhador': trabalhador['nome'],
            'palete': palete['nome_produto'],
            'horario_inicio': novo_registro['horario_inicio'],
            'horario_fim': None,
            'message': 'Trabalho iniciado com sucesso.'
        }), 201

    except Exception as e:
        print(f"Erro ao registrar trabalho: {e}")
        return jsonify({'message': 'Erro ao registrar trabalho.', 'details': str(e)}), 500





# Rota para definir senha do chefe
@app.route('/chefes/definir_senha', methods=['POST'])
def definir_senha_chefe():
    try:
        data = request.get_json()
        id_trabalhador = data.get('id')
        nova_senha = data.get('senha')

        if not nova_senha or len(nova_senha) < 6:
            return jsonify({'message': 'A senha deve ter pelo menos 6 caracteres.'}), 400

        # Busca o trabalhador na coleção do Firestore
        trabalhador_ref = db.collection('trabalhadores').document(id_trabalhador).get()
        if not trabalhador_ref.exists:
            return jsonify({'message': 'Chefe não encontrado ou não autorizado.'}), 404

        trabalhador = trabalhador_ref.to_dict()

        if not trabalhador.get('chefe', False):
            return jsonify({'message': 'O trabalhador não é um chefe autorizado.'}), 403

        if 'senha_hash' in trabalhador:
            return jsonify({'message': 'Senha já definida.'}), 400

        # Define a senha e atualiza no Firestore
        senha_hash = generate_password_hash(nova_senha)
        db.collection('trabalhadores').document(id_trabalhador).update({
            'senha_hash': senha_hash
        })

        return jsonify({'message': 'Senha definida com sucesso!'}), 200
    except Exception as e:
        print(f"Erro ao definir senha: {e}")
        return jsonify({'message': 'Erro ao definir senha.', 'details': str(e)}), 500


# Rota para login do chefe
@app.route('/chefes/login', methods=['POST'])
def login_chefe():
    try:
        data = request.get_json()
        id_trabalhador = data.get('id')
        senha = data.get('senha')

        if not id_trabalhador or not senha:
            return jsonify({'message': 'ID e senha são obrigatórios.'}), 400

        # Busca o trabalhador na coleção do Firestore
        trabalhador_ref = db.collection('trabalhadores').document(id_trabalhador).get()
        if not trabalhador_ref.exists:
            return jsonify({'message': 'Chefe não encontrado ou não autorizado.'}), 404

        trabalhador = trabalhador_ref.to_dict()

        if not trabalhador.get('chefe', False):
            return jsonify({'message': 'O trabalhador não é um chefe autorizado.'}), 403

        if 'senha_hash' not in trabalhador:
            return jsonify({'message': 'Senha não definida. Por favor, defina uma senha.'}), 400

        # Verifica a senha
        if not check_password_hash(trabalhador['senha_hash'], senha):
            return jsonify({'message': 'Senha incorreta.'}), 401

        return jsonify({
            'message': 'Login bem-sucedido!',
            'nome': trabalhador['nome'],
            'secao': trabalhador['secao']
        }), 200
    except Exception as e:
        print(f"Erro ao autenticar chefe: {e}")
        return jsonify({'message': 'Erro ao autenticar chefe.', 'details': str(e)}), 500





if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)