from flask import Flask, request, jsonify, send_from_directory
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



app = Flask(__name__)
CORS(app)

BASE_PATH = 'C:\\Users\\User\\Documents\\Documentos Fábrica ROPRE'

PATHS = {
    'PALETES': {
        'QRCODES': os.path.join(BASE_PATH, 'paletes', 'qrcodes'),
        'FOLHAS': os.path.join(BASE_PATH, 'paletes', 'folhas_palete'),
    },
    'TRABALHADORES': {
        'QRCODES': os.path.join(BASE_PATH, 'trabalhadores', 'qrcodes'),
        'CARTOES': {
            'CHEFES': os.path.join(BASE_PATH, 'trabalhadores', 'cartoes', 'chefes'),
            'TRABALHADORES': os.path.join(BASE_PATH, 'trabalhadores', 'cartoes', 'trabalhadores')
        }
    }
}



# Adicionar logo após a definição do PATHS
def criar_estrutura_pastas():
    """
    Cria toda a estrutura de pastas necessária caso não exista
    """
    try:
        # Criar pastas para paletes
        os.makedirs(PATHS['PALETES']['QRCODES'], exist_ok=True)
        os.makedirs(PATHS['PALETES']['FOLHAS'], exist_ok=True)
        
        # Criar pastas para trabalhadores
        os.makedirs(PATHS['TRABALHADORES']['QRCODES'], exist_ok=True)
        os.makedirs(PATHS['TRABALHADORES']['CARTOES']['CHEFES'], exist_ok=True)
        os.makedirs(PATHS['TRABALHADORES']['CARTOES']['TRABALHADORES'], exist_ok=True)
        
        print("Estrutura de pastas criada com sucesso!")
    except Exception as e:
        print(f"Erro ao criar estrutura de pastas: {e}")
        raise

criar_estrutura_pastas()  # Garantir que todas as pastas existam

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
    # Especifica o diretório onde o index.html está localizado
    return send_from_directory('.', 'index.html')

@app.route('/favicon.ico')
def no_favicon():
    return '', 204

@app.route('/favicon.png')
def no_favicon_png():
    return '', 204



def gerar_qr_code(conteudo, filename):
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
        img.save(filename)
        print(f"QR Code gerado em: {filename}")
    except Exception as e:
        print(f"Erro ao gerar QR Code: {e}")
        raise

@app.route('/qr_codes/<filename>', methods=['GET'])
def get_qr_code(filename):
    if 'trabalhador' in filename:
        return send_from_directory(PATHS['TRABALHADORES']['QRCODES'], filename)
    else:
        return send_from_directory(PATHS['PALETES']['QRCODES'], filename)


def criar_cartao(trabalhador_id, nome_trabalhador, secao, cor="white", tipo="trabalhador"):
    try:
        # Determinar o caminho correto baseado no tipo
        cartao_path = os.path.join(
            PATHS['TRABALHADORES']['CARTOES']['CHEFES' if tipo == "chefe" else 'TRABALHADORES'],
            f"cartao_{trabalhador_id}.png"
        )
        
        # Usar o novo caminho para QR codes
        qr_code_path = os.path.join(PATHS['TRABALHADORES']['QRCODES'], f"qr_trabalhador_{trabalhador_id}.png")

        # Verifica se o QR Code existe
        if not os.path.exists(qr_code_path):
            raise FileNotFoundError(f"QR Code não encontrado em: {qr_code_path}")

        # Criar diretórios se não existirem
        os.makedirs(os.path.dirname(cartao_path), exist_ok=True)

        # Abrir o QR Code
        qr_code_img = Image.open(qr_code_path)

        # Criar uma imagem para o cartão
        largura, altura = 400, 600
        cartao = Image.new('RGB', (largura, altura), cor)
        draw = ImageDraw.Draw(cartao)

        # Adicionar o QR Code ao cartão
        qr_code_tamanho = 200
        qr_code_img = qr_code_img.resize((qr_code_tamanho, qr_code_tamanho))
        cartao.paste(qr_code_img, (100, 100))

        # Configurar a fonte
        try:
            fonte = ImageFont.truetype("arial.ttf", size=24)
        except IOError:
            print("Fonte 'arial.ttf' não encontrada, usando fonte padrão.")
            fonte = ImageFont.load_default()

        # Centralizar o texto do nome
        texto_nome = f"Nome: {nome_trabalhador}"
        largura_texto_nome = draw.textbbox((0, 0), texto_nome, font=fonte)[2]
        pos_x_nome = (largura - largura_texto_nome) // 2
        draw.text((pos_x_nome, 320), texto_nome, fill="black", font=fonte)

        # Centralizar o texto da seção
        texto_secao = f"Seção: {secao}"
        largura_texto_secao = draw.textbbox((0, 0), texto_secao, font=fonte)[2]
        pos_x_secao = (largura - largura_texto_secao) // 2
        draw.text((pos_x_secao, 360), texto_secao, fill="black", font=fonte)

        # Salvar o cartão
        cartao.save(cartao_path)
        print(f"Cartão gerado em: {cartao_path}")
        return cartao_path
    except Exception as e:
        print(f"Erro ao criar cartão: {e}")
        return None







@app.route('/cartoes/<pasta>/<filename>', methods=['GET'])
def get_cartao(pasta, filename):
    if pasta == 'chefes':
        return send_from_directory(PATHS['TRABALHADORES']['CARTOES']['CHEFES'], filename)
    else:
        return send_from_directory(PATHS['TRABALHADORES']['CARTOES']['TRABALHADORES'], filename)






# Rota para listar trabalhadores
@app.route('/trabalhadores', methods=['GET'])
def get_trabalhadores():
    try:
        trabalhadores_ref = db.collection('trabalhadores').stream()
        output = [{'id': doc.id, **doc.to_dict()} for doc in trabalhadores_ref]
        return jsonify(output), 200
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

        # Adicionar trabalhador ao Firestore
        trabalhador_ref = db.collection('trabalhadores').add({
            'nome': nome,
            'secao': secao,
            'chefe': is_chefe
        })

        trabalhador_id = trabalhador_ref[1].id

        # Geração de QR Code
        qr_code_path = None
        try:
            conteudo_qr = f"ID: {trabalhador_id}\nNome: {nome}\nSeção: {secao}\nChefe: {is_chefe}"
            os.makedirs(PATHS['TRABALHADORES']['QRCODES'], exist_ok=True)
            qr_code_path = os.path.join(PATHS['TRABALHADORES']['QRCODES'], f"qr_trabalhador_{trabalhador_id}.png")
            gerar_qr_code(conteudo_qr, qr_code_path)
        except Exception as e:
            print(f"Erro ao gerar QR Code: {e}")

        # Criação dos cartões
        try:
            # Criar cartão normal
            criar_cartao(trabalhador_id, nome, secao, cor="white", tipo="trabalhador")
            
            # Se for chefe, criar cartão adicional
            if is_chefe:
                criar_cartao(trabalhador_id, nome, secao, cor="red", tipo="chefe")
        except Exception as e:
            print(f"Erro ao criar cartão: {e}")

        mensagem = 'Trabalhador e chefe de secção adicionados com sucesso!' if is_chefe else 'Trabalhador adicionado com sucesso!'
        
        return jsonify({
            'message': mensagem,
            'id': trabalhador_id,
            'qr_code_path': qr_code_path
        }), 201

    except Exception as e:
        print(f"Erro ao adicionar trabalhador: {e}")
        return jsonify({'message': 'Erro ao adicionar trabalhador.', 'details': str(e)}), 500








    
# Rota para remover trabalhador
@app.route('/trabalhadores/<string:id>', methods=['DELETE'])
def delete_trabalhador(id):
    try:
        # Buscar trabalhador no Firestore
        trabalhador_ref = db.collection('trabalhadores').document(id)
        trabalhador = trabalhador_ref.get()
        if not trabalhador.exists:
            return jsonify({'message': 'Trabalhador não encontrado'}), 404

        # Remover QR Code
        qr_code_path = os.path.join(PATHS['TRABALHADORES']['QRCODES'], f"qr_trabalhador_{id}.png")
        if os.path.exists(qr_code_path):
            os.remove(qr_code_path)

        # Remover cartão de trabalhador
        cartao_path = os.path.join(PATHS['TRABALHADORES']['CARTOES']['TRABALHADORES'], f"cartao_{id}.png")
        if os.path.exists(cartao_path):
            os.remove(cartao_path)

        # Remover cartão de chefe (se existir)
        cartao_chefe_path = os.path.join(PATHS['TRABALHADORES']['CARTOES']['CHEFES'], f"cartao_{id}.png")
        if os.path.exists(cartao_chefe_path):
            os.remove(cartao_chefe_path)

        # Remover trabalhador do Firestore
        trabalhador_ref.delete()

        return jsonify({'message': 'Trabalhador removido com sucesso!'}), 200
    except Exception as e:
        return jsonify({'message': 'Erro ao remover trabalhador.', 'details': str(e)}), 500





# Função para gerar QR code da palete
def gerar_qr_code_palete(palete_id, palete_data):

    # Conteúdo do QR Code com os dados da palete
    conteudo = (
        f"ID: {palete_id}\n"
        f"Data de Entrega: {palete_data['data_entrega']}\n"
        f"OP: {palete_data['op']}\n"
        f"Referência: {palete_data['referencia']}\n"
        f"Nome do Produto: {palete_data['nome_produto']}\n"
        f"Medida: {palete_data['medida']}\n"
        f"Cor do Botão: {palete_data['cor_botao']}\n"
        f"Cor do Ribete: {palete_data['cor_ribete']}\n"
        f"Leva Embalagem: {'Sim' if palete_data['leva_embalagem'] else 'Não'}\n"
        f"Quantidade: {palete_data['quantidade']}\n"
        f"Data e Hora: {palete_data['data_hora']}\n"
        f"Número do Lote: {palete_data['numero_lote']}"
    )

    # Gera o QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(conteudo)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Caminho para salvar o QR Code
    qr_code_path = os.path.join(PATHS['PALETES']['QRCODES'], f"qr_palete_{palete_id}.png")
    img.save(qr_code_path)

    return qr_code_path




       
       
# Rota para listar todas as paletes
@app.route('/paletes', methods=['GET'])
def get_paletes():
    try:
        # Recupera todas as paletes do Firestore
        paletes_ref = db.collection('paletes')
        paletes_docs = paletes_ref.stream()

        paletes = []
        for doc in paletes_docs:
            data = doc.to_dict()
            data['id'] = doc.id  # Inclui o ID do documento
            paletes.append(data)

        if not paletes:
            return jsonify({'message': 'Nenhuma palete encontrada.'}), 404

        print(f"GET /paletes - {len(paletes)} paletes encontradas")
        return jsonify(paletes), 200
    except Exception as e:
        print(f"Erro ao obter paletes: {e}")
        return jsonify({'message': 'Erro ao obter paletes.', 'details': str(e)}), 500



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

        # Adiciona a nova palete ao Firestore
        palete_data = {
            'data_entrega': data['data_entrega'],
            'op': data['op'],
            'referencia': data['referencia'],
            'nome_produto': data['nome_produto'],
            'medida': data['medida'],
            'cor_botao': data['cor_botao'],
            'cor_ribete': data['cor_ribete'],
            'leva_embalagem': data['leva_embalagem'],
            'quantidade': int(data['quantidade']),
            'data_hora': data['data_hora'],
            'numero_lote': data['numero_lote'],
        }

        # Insere a palete na Firestore
        doc_ref = db.collection('paletes').add(palete_data)
        palete_id = doc_ref[1].id

        # Gera QR Code
        qr_code_path = gerar_qr_code_palete(palete_id, palete_data)

        # Gera a folha da palete
        folha_path = gerar_folha_palete(palete_id, palete_data)
        if not folha_path:
            raise Exception("Erro ao gerar folha da palete")

        # Atualiza documento com os caminhos
        db.collection('paletes').document(palete_id).update({
            'qr_code_path': qr_code_path,
            'folha_path': folha_path
        })

        return jsonify({
            'message': 'Palete adicionada com sucesso!',
            'id': palete_id,
            'qr_code_path': qr_code_path,
            'folha_path': folha_path
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

        # Caminho do arquivo de QR Code associado
        qr_code_path = os.path.join(PATHS['PALETES']['QRCODES'], f"qr_palete_{palete_id}.png")
        if os.path.exists(qr_code_path):
            os.remove(qr_code_path)
            print(f"QR Code removido: {qr_code_path}")
        else:
            print(f"QR Code não encontrado para exclusão: {qr_code_path}")

        # Caminho do arquivo de PDF associado
        pdf_path = os.path.join(PATHS['PALETES']['FOLHAS'], f"folha_palete_{palete_id}.pdf")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"PDF removido: {pdf_path}")
        else:
            print(f"PDF não encontrado para exclusão: {pdf_path}")

        # Remover a palete da base de dados Firestore
        palete_ref.delete()
        print(f"Palete removida do Firestore: {palete_id}")

        return jsonify({'message': 'Palete removida com sucesso!'}), 200
    except Exception as e:
        print(f"Erro ao remover palete: {e}")
        return jsonify({'message': 'Erro ao remover palete', 'details': str(e)}), 500




def gerar_folha_palete(palete_id, palete_data):
    try:
        # Garantir que o diretório para PDFs exista
        os.makedirs(PATHS['PALETES']['FOLHAS'], exist_ok=True)

        # Caminho do QR Code
        qr_code_path = os.path.join(PATHS['PALETES']['QRCODES'], f"qr_palete_{palete_id}.png")
        if not os.path.exists(qr_code_path):
            raise FileNotFoundError(f"QR Code não encontrado em: {qr_code_path}")

        # Caminho para salvar o PDF
        output_pdf_path = os.path.join(PATHS['PALETES']['FOLHAS'], f"folha_palete_{palete_id}.pdf")

        # Criar o PDF
        pdf = canvas.Canvas(output_pdf_path, pagesize=A4)
        width, height = A4

        # Título
        pdf.setFont("Helvetica-Bold", 25)
        titulo = "Folha de Palete"
        titulo_width = pdf.stringWidth(titulo, "Helvetica-Bold", 25)
        pdf.drawString((width - titulo_width) / 2, height - 50, titulo)

        # Adicionar QR Code ao PDF
        pdf.drawImage(qr_code_path, x=173, y=height - 300, width=240, height=240)

        # Adicionar informações da palete
        pdf.setFont("Helvetica", 12)
        y = height - 350
        line_height = 20
        informacoes = [
            f"Data de Entrega: {palete_data['data_entrega']}",
            f"OP: {palete_data['op']}",
            f"Referência: {palete_data['referencia']}",
            f"Nome do Produto: {palete_data['nome_produto']}",
            f"Medida: {palete_data['medida']}",
            f"Cor do Botão: {palete_data['cor_botao']}",
            f"Cor do Ribete: {palete_data['cor_ribete']}",
            f"Leva Embalagem: {'Sim' if palete_data['leva_embalagem'] else 'Não'}",
            f"Quantidade: {palete_data['quantidade']}",
            f"Data e Hora: {palete_data['data_hora']}",
            f"Número do Lote: {palete_data['numero_lote']}",
        ]

        for info in informacoes:
            pdf.drawString(50, y, info)
            y -= line_height

        # Adicionar seções de destino
        y -= line_height
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Seções de destino inicial e próximas:")
        y -= line_height
        secoes = [
            "Corte e vinco",
            "Seção da cola",
            "Acabamento",
            "Confeção",
            "Acabamento"
        ]
        pdf.setFont("Helvetica", 12)
        for secao in secoes:
            pdf.drawString(70, y, f"(   ) {secao}")
            y -= line_height

        # Finalizar o PDF
        pdf.save()
        print(f"PDF gerado com sucesso: {output_pdf_path}")
        return output_pdf_path

    except Exception as e:
        print(f"Erro ao gerar folha da palete: {e}")
        return None






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