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
from pymongo import MongoClient
from bson.objectid import ObjectId  # Para manipular ObjectId do MongoDB




app = Flask(__name__)
CORS(app)

# Conexão com o MongoDB
MONGO_URI = os.getenv("MONGO_URI")  # Obtém o URI do MongoDB a partir de variáveis de ambiente
if MONGO_URI:
    client = MongoClient(MONGO_URI)
    db = client['gestao_fabrica']
    trabalhadores_collection = db['trabalhadores']
    paletes_collection = db['paletes']
    registros_trabalho_collection = db['registros_trabalho']
else:
    client = None
    print("Aviso: MongoDB não está configurado. As funcionalidades de banco de dados não estarão disponíveis.")

def gerar_qr_code(trabalhador_id):
    # Certifica-se de que o diretório para os QR Codes existe
    os.makedirs('static/qr_codes', exist_ok=True)
    conteudo = f"trabalhador_{trabalhador_id}"

    qr = qrcode.QRCode(
        version=1,  # Tamanho do QR Code (1 é o menor)
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,  # Tamanho da caixa
        border=4,  # Tamanho da borda
        
    )
    qr.add_data(conteudo)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Salva a imagem do QR Code
    img.save(f"static/qr_codes/qr_trabalhador_{trabalhador_id}.png")

@app.route('/qr_codes/<filename>', methods=['GET'])
def get_qr_code(filename):
    return send_from_directory('static/qr_codes', filename)


#criar cartão trabalhador
def criar_cartao(trabalhador_id, nome_trabalhador, secao, cor="white", pasta="trabalhadores"):
    os.makedirs(f'static/cartoes/{pasta}', exist_ok=True)

    # Caminho do QR Code gerado
    qr_code_path = f"static/qr_codes/qr_trabalhador_{trabalhador_id}.png"

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
    fonte = ImageFont.truetype("arial.ttf", size=24)

    # Centralizar o texto do nome
    texto_nome = f"Nome: {nome_trabalhador}"
    largura_texto_nome = draw.textbbox((0, 0), texto_nome, font=fonte)[2]  # Obter largura do texto
    pos_x_nome = (largura - largura_texto_nome) // 2
    draw.text((pos_x_nome, 320), texto_nome, fill="black", font=fonte)

    # Centralizar o texto da seção
    texto_secao = f"Seção: {secao}"
    largura_texto_secao = draw.textbbox((0, 0), texto_secao, font=fonte)[2]  # Obter largura do texto
    pos_x_secao = (largura - largura_texto_secao) // 2
    draw.text((pos_x_secao, 360), texto_secao, fill="black", font=fonte)

    # Salvar o cartão na pasta específica
    caminho_cartao = f"static/cartoes/{pasta}/cartao_{trabalhador_id}.png"
    cartao.save(caminho_cartao)

    return caminho_cartao



# Rota para o index.html
@app.route('/')
def index():
    # Especifica o diretório onde o index.html está localizado
    return send_from_directory('.', 'index.html')

@app.route('/favicon.ico')
def no_favicon():
    return '', 204


# Rota para outros arquivos estáticos (CSS, JS, etc.)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


@app.route('/cartoes/<pasta>/<filename>', methods=['GET'])
def get_cartao(pasta, filename):
    # Certifique-se de que a pasta seja 'trabalhadores' ou 'chefes'
    if pasta not in ['trabalhadores', 'chefes']:
        return jsonify({"message": "Pasta inválida"}), 400
    return send_from_directory(f'static/cartoes/{pasta}', filename)
















# Rota para listar trabalhadores
@app.route('/trabalhadores', methods=['GET'])
def get_trabalhadores():
    try:
        trabalhadores = list(trabalhadores_collection.find())
        output = []
        for trabalhador in trabalhadores:
            output.append({
                'id': str(trabalhador['_id']),
                'nome': trabalhador['nome'],
                'secao': trabalhador['secao'],
                'chefe': trabalhador.get('chefe', False)
            })
        return jsonify(output), 200
    except Exception as e:
        return jsonify({'message': 'Erro ao listar trabalhadores.', 'details': str(e)}), 500





@app.route('/trabalhadores', methods=['POST'])
def add_trabalhador():
    try:
        data = request.get_json()
        print(f"Dados recebidos: {data}")  # Log dos dados recebidos
        nome = data.get('nome')
        secao = data.get('secao')
        is_chefe = data.get('chefe', False)

        if not nome or not secao:
            return jsonify({'message': 'Nome e seção são obrigatórios.'}), 400

        # Criar trabalhador como documento para o MongoDB
        trabalhador = {
            'nome': nome,
            'secao': secao,
            'chefe': is_chefe,
            'senha_hash': None  # Inicialmente sem senha
        }

        # Inserir no MongoDB e obter o ID gerado
        result = trabalhadores_collection.insert_one(trabalhador)
        trabalhador_id = str(result.inserted_id)

        # Certifica-se de que os diretórios existem
        try:
            os.makedirs('static/qr_codes', exist_ok=True)
            os.makedirs('static/cartoes/trabalhadores', exist_ok=True)
            os.makedirs('static/cartoes/chefes', exist_ok=True)
        except Exception as e:
            print(f"Erro ao criar diretórios: {e}")
            return jsonify({'message': 'Erro ao criar diretórios.', 'details': str(e)}), 500

        # Gerar QR Code com informações detalhadas do trabalhador
        try:
            conteudo = (
                f"ID: {trabalhador_id}\n"
                f"Nome: {trabalhador['nome']}\n"
                f"Secção: {trabalhador['secao']}\n"
            )
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(conteudo)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            qr_code_path = f"static/qr_codes/qr_trabalhador_{trabalhador_id}.png"
            img.save(qr_code_path)
        except Exception as e:
            print(f"Erro ao gerar QR Code: {e}")
            return jsonify({'message': 'Erro ao gerar QR Code.', 'details': str(e)}), 500

        # Criar cartão do trabalhador
        try:
            criar_cartao(trabalhador_id, trabalhador['nome'], trabalhador['secao'])
            if is_chefe:
                criar_cartao(trabalhador_id, trabalhador['nome'], trabalhador['secao'], cor="red", pasta="chefes")
        except Exception as e:
            print(f"Erro ao criar cartão: {e}")
            return jsonify({'message': 'Erro ao criar cartão.', 'details': str(e)}), 500

        mensagem = 'Trabalhador e chefe de secção adicionados com sucesso!' if is_chefe else 'Trabalhador adicionado com sucesso!'
        return jsonify({'message': mensagem, 'id': trabalhador_id}), 201
    except Exception as e:
        print(f"Erro ao adicionar trabalhador: {e}")  # Log do erro
        return jsonify({'message': 'Erro ao adicionar trabalhador.', 'details': str(e)}), 500






    
    # Rota para remover trabalhador
@app.route('/trabalhadores/<string:id>', methods=['DELETE'])  # O ID é string no MongoDB
def delete_trabalhador(id):
    try:
        # Buscar o trabalhador no MongoDB pelo ID
        trabalhador = trabalhadores_collection.find_one({"_id": ObjectId(id)})
        if not trabalhador:
            return jsonify({'message': 'Trabalhador não encontrado'}), 404

        # Caminho do QR Code associado
        qr_code_path = os.path.join('static', 'qr_codes', f"qr_trabalhador_{id}.png")

        # Remove o arquivo de QR Code, se existir
        if os.path.exists(qr_code_path):
            os.remove(qr_code_path)
            print(f"QR Code removido: {qr_code_path}")
        else:
            print(f"QR Code não encontrado para exclusão: {qr_code_path}")

        # Caminho para o cartão associado ao trabalhador
        cartao_path = os.path.join('static', 'cartoes', 'trabalhadores', f"cartao_{id}.png")

        # Remove o arquivo do cartão do trabalhador, se existir
        if os.path.exists(cartao_path):
            os.remove(cartao_path)
            print(f"Cartão removido: {cartao_path}")
        else:
            print(f"Cartão não encontrado para exclusão: {cartao_path}")

        # Caminho para o cartão associado ao chefe
        cartao_chefe_path = os.path.join('static', 'cartoes', 'chefes', f"cartao_{id}.png")

        # Remove o arquivo do cartão do chefe, se existir
        if os.path.exists(cartao_chefe_path):
            os.remove(cartao_chefe_path)
            print(f"Cartão de chefe removido: {cartao_chefe_path}")
        else:
            print(f"Cartão de chefe não encontrado para exclusão: {cartao_chefe_path}")

        # Remove o trabalhador da base de dados MongoDB
        trabalhadores_collection.delete_one({"_id": ObjectId(id)})
        print(f"Trabalhador removido do banco de dados: {id}")

        return jsonify({'message': 'Trabalhador removido com sucesso!'}), 200
    except Exception as e:
        print(f"Erro ao remover trabalhador: {e}")
        return jsonify({'message': 'Erro ao remover trabalhador', 'details': str(e)}), 500


    




# Função para gerar QR code da palete
def gerar_qr_code_palete(palete):
    # Certifica-se de que o diretório de QR codes existe
    os.makedirs('static/qr_codes_paletes', exist_ok=True)

    # Conteúdo do QR Code com os dados da palete
    conteudo = (
        f"ID: {palete.id}\n"
        f"Data de Entrega: {palete.data_entrega}\n"
        f"OP: {palete.op}\n"
        f"Referência: {palete.referencia}\n"
        f"Nome do Produto: {palete.nome_produto}\n"
        f"Medida: {palete.medida}\n"
        f"Cor do Botão: {palete.cor_botao}\n"
        f"Cor do Ribete: {palete.cor_ribete}\n"
        f"Leva Embalagem: {'Sim' if palete.leva_embalagem else 'Não'}\n"
        f"Quantidade: {palete.quantidade}\n"
        f"Data e Hora: {palete.data_hora}\n"
        f"Número do Lote: {palete.numero_lote}"
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
    qr_code_path = f"static/qr_codes_paletes/qr_palete_{palete.id}.png"
    img.save(qr_code_path)

    return qr_code_path




       
       
# Rota para listar todas as paletes
@app.route('/paletes', methods=['GET'])
def get_paletes():
    try:
        # Buscar todas as paletes no MongoDB
        paletes = list(paletes_collection.find())

        if not paletes:
            return jsonify({'message': 'Nenhuma palete encontrada.'}), 404

        # Formatar os dados para envio
        output = [
            {
                'id': str(p['_id']),  # Converter ObjectId para string
                'data_entrega': p['data_entrega'],
                'op': p['op'],
                'referencia': p['referencia'],
                'nome_produto': p['nome_produto'],
                'medida': p['medida'],
                'cor_botao': p['cor_botao'],
                'cor_ribete': p['cor_ribete'],
                'leva_embalagem': p['leva_embalagem'],
                'quantidade': p['quantidade'],
                'data_hora': p['data_hora'],
                'numero_lote': p['numero_lote'],
                'qr_code_path': p.get('qr_code_path'),
            }
            for p in paletes
        ]

        print(f"GET /paletes - {len(paletes)} paletes encontradas")
        return jsonify(output), 200
    except Exception as e:
        print(f"Erro ao obter paletes: {e}")
        return jsonify({'message': 'Erro ao obter paletes.', 'details': str(e)}), 500




# Rota para adicionar palete com geração de QR code
@app.route('/paletes', methods=['POST'])
def add_palete():
    try:
        data = request.get_json()

        # Validar os campos obrigatórios
        required_fields = ['data_entrega', 'op', 'referencia', 'nome_produto',
                           'medida', 'cor_botao', 'cor_ribete',
                           'leva_embalagem', 'quantidade', 'data_hora', 'numero_lote']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            return jsonify({'message': f'Campos obrigatórios ausentes: {", ".join(missing_fields)}'}), 400

        # Adicionar a nova palete
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

        # Inserir a palete no MongoDB
        result = paletes_collection.insert_one(palete_data)
        palete_id = str(result.inserted_id)

        # Gerar QR Code com as informações da palete
        qr_code_path = gerar_qr_code_palete(palete_id, palete_data)
        paletes_collection.update_one({'_id': ObjectId(palete_id)}, {'$set': {'qr_code_path': qr_code_path}})

        return jsonify({'message': 'Palete adicionada com sucesso!', 'id': palete_id}), 201
    except Exception as e:
        print(f"Erro ao adicionar palete: {e}")
        return jsonify({'message': 'Erro ao adicionar palete.', 'details': str(e)}), 500




@app.route('/FolhaPalete/<filename>', methods=['GET'])
def get_pdf(filename):
    return send_from_directory('static/FolhaPalete', filename)




        
# Rota para remover palete
@app.route('/paletes/<string:palete_id>', methods=['DELETE'])
def delete_palete(palete_id):
    try:
        # Buscar a palete pelo ID no MongoDB
        palete = paletes_collection.find_one({"_id": palete_id})
        if not palete:
            return jsonify({'message': 'Palete não encontrada'}), 404

        # Caminho do arquivo de QR Code associado
        qr_code_path = os.path.join('static', 'qr_codes_paletes', f"qr_palete_{palete_id}.png")
        if os.path.exists(qr_code_path):
            os.remove(qr_code_path)
            print(f"QR Code removido: {qr_code_path}")
        else:
            print(f"QR Code não encontrado para exclusão: {qr_code_path}")

        # Caminho do arquivo de PDF associado
        pdf_path = os.path.join('static', 'FolhaPalete', f"folha_palete_{palete_id}.pdf")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"PDF removido: {pdf_path}")
        else:
            print(f"PDF não encontrado para exclusão: {pdf_path}")

        # Remover a palete da base de dados
        result = paletes_collection.delete_one({"_id": palete_id})
        if result.deleted_count == 0:
            return jsonify({'message': 'Erro ao remover palete do banco de dados'}), 500

        return jsonify({'message': 'Palete removida com sucesso!'}), 200
    except Exception as e:
        print(f"Erro ao remover palete: {e}")
        return jsonify({'message': 'Erro ao remover palete', 'details': str(e)}), 500



def gerar_folha_palete(palete_id, palete_data):
    try:
        # Pasta onde os QR codes estão armazenados
        qr_code_path = os.path.join('static', 'qr_codes_paletes', f"qr_palete_{palete_id}.png")

        # Verificar se o QR code existe
        if not os.path.exists(qr_code_path):
            raise FileNotFoundError(f"QR Code não encontrado para a palete {palete_id}")

        # Nome do arquivo PDF
        output_pdf_path = f"static/FolhaPalete/folha_palete_{palete_id}.pdf"

        # Criar diretório para os PDFs, se necessário
        os.makedirs("static/FolhaPalete", exist_ok=True)

        # Configuração do PDF
        pdf = canvas.Canvas(output_pdf_path, pagesize=A4)
        width, height = A4

        # Adicionar QR code
        qr_code_img = ImageReader(qr_code_path)
        pdf.drawImage(qr_code_img, x=173, y=height - 300, width=250, height=250)

        # Título
        pdf.setFont("Helvetica-Bold", 25)
        texto = "Folha de Palete"
        largura_texto = pdf.stringWidth(texto, "Helvetica-Bold", 25)
        x = (width - largura_texto) / 2
        pdf.drawString(x, height - 50, texto)

        # Informações da palete
        pdf.setFont("Helvetica", 12)
        y = height - 350
        line_height = 20

        dados = [
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

        for dado in dados:
            pdf.drawString(50, y, dado)
            y -= line_height

        # Seção de preenchimento manual
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Seções de destino inicial e próximas:")
        y -= line_height

        secoes = [
            "Corte e vinco",
            "Seção da cola",
            "Acabamento",
            "Confeção",
            "Acabamento",
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
        registros = list(registros_trabalho_collection.find())
        output = []
        for r in registros:
            output.append({
                'id': str(r['_id']),
                'trabalhador': {'id': r['trabalhador_id'], 'nome': r['trabalhador_nome']},
                'palete': {'id': r['palete_id'], 'nome_produto': r['palete_nome']},
                'horario_inicio': r['horario_inicio'],
                'horario_fim': r['horario_fim'] if 'horario_fim' in r else None
            })
        print(f"GET /registro_trabalho - {len(registros)} registros encontrados")
        return jsonify(output), 200
    except Exception as e:
        print(f"Erro ao listar registros de trabalho: {e}")
        return jsonify({'message': 'Erro ao listar registros de trabalho.', 'details': str(e)}), 500


# Rota para registrar início ou fim de trabalho
@app.route('/registro_trabalho', methods=['POST'])
def registro_trabalho():
    try:
        data = request.get_json()

        # Extração do ID do Trabalhador a partir do QR Code
        trabalhador_info = data.get('trabalhador_qr')  # Conteúdo do QR Code do Trabalhador
        if not trabalhador_info:
            return jsonify({'message': 'QR Code do trabalhador não fornecido.'}), 400

        # Extração do ID da Palete a partir do QR Code
        palete_info = data.get('palete_qr')  # Conteúdo do QR Code da Palete
        if not palete_info:
            return jsonify({'message': 'QR Code da palete não fornecido.'}), 400

        # Extrair ID do Trabalhador
        try:
            trabalhador_id = trabalhador_info.split(';')[0].replace('ID', '').strip()
        except (IndexError, ValueError):
            return jsonify({'message': 'QR Code do trabalhador inválido.'}), 400

        # Validar Trabalhador
        trabalhador = trabalhadores_collection.find_one({"_id": trabalhador_id})
        if not trabalhador:
            return jsonify({'message': f'Trabalhador com ID {trabalhador_id} não encontrado.'}), 404

        # Extrair ID da Palete
        try:
            palete_id = palete_info.split(';')[0].replace('ID', '').strip()
        except (IndexError, ValueError):
            return jsonify({'message': 'QR Code da palete inválido.'}), 400

        # Validar Palete
        palete = paletes_collection.find_one({"_id": palete_id})
        if not palete:
            return jsonify({'message': f'Palete com ID {palete_id} não encontrada.'}), 404

        # Verificar se já há um trabalho em andamento para o trabalhador
        registro_existente = registros_trabalho_collection.find_one({
            "trabalhador_id": trabalhador_id,
            "horario_fim": None
        })

        # Se houver um registro em andamento, finaliza o trabalho
        if registro_existente:
            registros_trabalho_collection.update_one(
                {"_id": registro_existente["_id"]},
                {"$set": {"horario_fim": datetime.now(timezone.utc).isoformat()}}
            )
            return jsonify({
                'registro_id': str(registro_existente['_id']),
                'trabalhador': trabalhador['nome'],
                'palete': palete['nome_produto'],
                'horario_inicio': registro_existente['horario_inicio'],
                'horario_fim': datetime.now(timezone.utc).isoformat(),
                'message': 'Trabalho finalizado com sucesso.'
            }), 200

        # Caso contrário, cria um novo registro para iniciar o trabalho
        novo_registro = {
            "trabalhador_id": trabalhador_id,
            "trabalhador_nome": trabalhador['nome'],
            "palete_id": palete_id,
            "palete_nome": palete['nome_produto'],
            "horario_inicio": datetime.now(timezone.utc).isoformat(),
            "horario_fim": None
        }
        resultado = registros_trabalho_collection.insert_one(novo_registro)

        return jsonify({
            'registro_id': str(resultado.inserted_id),
            'trabalhador': trabalhador['nome'],
            'palete': palete['nome_produto'],
            'horario_inicio': novo_registro['horario_inicio'],
            'horario_fim': None,
            'message': 'Trabalho iniciado com sucesso.'
        }), 201

    except Exception as e:
        print(f"Erro ao registrar trabalho: {e}")
        return jsonify({'message': 'Erro ao registrar trabalho.', 'details': str(e)}), 500




@app.route('/chefes/definir_senha', methods=['POST'])
def definir_senha_chefe():
    try:
        data = request.get_json()
        id_trabalhador = data.get('id')
        nova_senha = data.get('senha')

        if not nova_senha or len(nova_senha) < 6:
            return jsonify({'message': 'A senha deve ter pelo menos 6 caracteres.'}), 400

        # Busca o trabalhador na coleção
        trabalhador = trabalhadores_collection.find_one({"_id": id_trabalhador, "chefe": True})

        if not trabalhador:
            return jsonify({'message': 'Chefe não encontrado ou não autorizado.'}), 404

        if 'senha_hash' in trabalhador:
            return jsonify({'message': 'Senha já definida.'}), 400

        # Define a senha e atualiza no MongoDB
        senha_hash = generate_password_hash(nova_senha)
        trabalhadores_collection.update_one(
            {"_id": id_trabalhador},
            {"$set": {"senha_hash": senha_hash}}
        )

        return jsonify({'message': 'Senha definida com sucesso!'}), 200
    except Exception as e:
        print(f"Erro ao definir senha: {e}")
        return jsonify({'message': 'Erro ao definir senha.', 'details': str(e)}), 500


@app.route('/chefes/login', methods=['POST'])
def login_chefe():
    try:
        data = request.get_json()
        id_trabalhador = data.get('id')
        senha = data.get('senha')

        # Busca o trabalhador na coleção
        trabalhador = trabalhadores_collection.find_one({"_id": id_trabalhador, "chefe": True})

        if not trabalhador:
            return jsonify({'message': 'Chefe não encontrado ou não autorizado.'}), 404

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





@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    usuario = trabalhadores_collection.find_one({'email': data['email']})
    if usuario and check_password_hash(usuario['senha'], data['senha']):
        return jsonify({'tipo': usuario['tipo'], 'nome': usuario['nome']}), 200
    return jsonify({'message': 'Credenciais inválidas'}), 401





if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)