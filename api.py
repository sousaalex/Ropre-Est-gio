from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image, ImageDraw, ImageFont
import re  # Importar o módulo de expressões regulares
import os
import json
import qrcode


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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





@app.route('/cartoes/<filename>', methods=['GET'])
def get_cartao(filename):
    return send_from_directory('static/cartoes', filename)


# Rota para o index.html
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# Rota para outros arquivos estáticos (CSS, JS, etc.)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# Configuração do banco de dados
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'database', 'novo_fabrica.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo Trabalhador
class Trabalhador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    secao = db.Column(db.String(100), nullable=False)
    chefe = db.Column(db.Boolean, default=False)  # Indica se é chefe
    senha_hash = db.Column(db.String(200), nullable=True)  # Senha protegida (hash)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


# Modelo Palete
class Palete(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_palete = db.Column(db.String(100), unique=True, nullable=False)
    produtos = db.Column(db.Text, nullable=False)  # JSON de produtos

# Modelo RegistroTrabalho
class RegistroTrabalho(db.Model):
    __tablename__ = 'registro_trabalho'
    id = db.Column(db.Integer, primary_key=True)
    trabalhador_id = db.Column(db.Integer, db.ForeignKey('trabalhador.id'), nullable=False)
    palete_id = db.Column(db.Integer, db.ForeignKey('palete.id'), nullable=False)
    horario_inicio = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    horario_fim = db.Column(db.DateTime, nullable=True)

    trabalhador = db.relationship('Trabalhador', backref=db.backref('registros', lazy=True))
    palete = db.relationship('Palete', backref=db.backref('registros', lazy=True))

# Criar tabelas automaticamente
with app.app_context():
    try:
        db.create_all()
        print(f"Banco de dados configurado em: {db_path}")
    except Exception as e:
        print(f"Erro ao configurar o banco de dados: {e}")


# Rota para listar trabalhadores
@app.route('/trabalhadores', methods=['GET'])
def get_trabalhadores():
    trabalhadores = Trabalhador.query.all()
    output = [
        {
            'id': t.id,
            'nome': t.nome,
            'secao': t.secao,  # Exibe a seção na listagem
        } 
        for t in trabalhadores
    ]
    return jsonify(output)



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

        # Criar trabalhador
        trabalhador = Trabalhador(nome=nome, secao=secao, chefe=is_chefe)
        db.session.add(trabalhador)
        db.session.flush()  # Gera o ID do trabalhador sem commit ainda

        # Gerar QR Code e cartão para trabalhador
        gerar_qr_code(trabalhador.id)
        criar_cartao(trabalhador.id, trabalhador.nome, trabalhador.secao)

        if is_chefe:
            # Criar cartão de chefe em uma pasta separada
            criar_cartao(trabalhador.id, trabalhador.nome, trabalhador.secao, cor="red", pasta="chefes")

        db.session.commit()

        mensagem = 'Trabalhador e chefe de secção adicionados com sucesso!' if is_chefe else 'Trabalhador adicionado com sucesso!'
        return jsonify({'message': mensagem, 'id': trabalhador.id}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao adicionar trabalhador: {e}")
        return jsonify({'message': 'Erro ao adicionar trabalhador.', 'details': str(e)}), 500



    
    # Rota para remover trabalhador
@app.route('/trabalhadores/<int:id>', methods=['DELETE'])
def delete_trabalhador(id):
    try:
        trabalhador = Trabalhador.query.get(id)
        if not trabalhador:
            return jsonify({'message': 'Trabalhador não encontrado'}), 404

        # Caminho do QR Code associado
        qr_code_path = os.path.join('static', 'qr_codes', f"qr_trabalhador_{trabalhador.id}.png")

        # Remove o arquivo de QR Code, se existir
        if os.path.exists(qr_code_path):
            os.remove(qr_code_path)
            print(f"QR Code removido: {qr_code_path}")
        else:
            print(f"QR Code não encontrado para exclusão: {qr_code_path}")





        #caminho para cartao associado
        cartao_path = os.path.join('static', 'cartoes', f"cartao_trabalhador_{trabalhador.id}.png")

        # Remove o arquivo de cartoes, se existir
        if os.path.exists(cartao_path):
            os.remove(cartao_path)
            print(f"Cartão removido: {cartao_path}")
        else:
            print(f"Cartão não encontrado para exclusão: {cartao_path}")



        

        # Remove o trabalhador da base de dados
        db.session.delete(trabalhador)
        db.session.commit()

        return jsonify({'message': 'Trabalhador removido com sucesso!'}), 200
    except Exception as e:
        print(f"Erro ao remover trabalhador: {e}")
        return jsonify({'message': 'Erro ao remover trabalhador', 'details': str(e)}), 500


    
# Rota para listar todos os registros de trabalho
@app.route('/registro_trabalho', methods=['GET'])
def get_registro_trabalho():
    registros = RegistroTrabalho.query.all()
    output = []
    for r in registros:
        output.append({
            'id': r.id,
            'trabalhador': {'id': r.trabalhador.id, 'nome': r.trabalhador.nome},
            'palete': {'id': r.palete.id, 'numero_palete': r.palete.numero_palete},
            'horario_inicio': r.horario_inicio.isoformat(),
            'horario_fim': r.horario_fim.isoformat() if r.horario_fim else None
        })
    print(f"GET /registro_trabalho - {len(registros)} registros encontrados")
    return jsonify(output)


# Rota para registrar início ou fim de trabalho
@app.route('/registro_trabalho', methods=['POST'])
def registro_trabalho():
    try:
        data = request.get_json()

        trabalhador = Trabalhador.query.filter_by(cartao_qr=data['cartao_qr']).first()
        if not trabalhador:
            return jsonify({'message': 'Trabalhador não encontrado'}), 404

        palete = Palete.query.filter_by(numero_palete=data['numero_palete']).first()
        if not palete:
            return jsonify({'message': 'Palete não encontrada'}), 404

        registro_existente = RegistroTrabalho.query.filter_by(
            trabalhador_id=trabalhador.id,
            palete_id=palete.id,
            horario_fim=None
        ).first()

        if registro_existente:
            registro_existente.horario_fim = datetime.now(timezone.utc)
            db.session.commit()
            return jsonify({
                'registro_id': registro_existente.id,
                'trabalhador': trabalhador.nome,
                'palete': palete.numero_palete,
                'horario_inicio': registro_existente.horario_inicio,
                'horario_fim': registro_existente.horario_fim,
                'message': 'Trabalho finalizado com sucesso.'
            }), 200
        else:
            novo_registro = RegistroTrabalho(
                trabalhador_id=trabalhador.id,
                palete_id=palete.id,
                horario_inicio=datetime.now(timezone.utc)
            )
            db.session.add(novo_registro)
            db.session.commit()
            return jsonify({
                'registro_id': novo_registro.id,
                'trabalhador': trabalhador.nome,
                'palete': palete.numero_palete,
                'horario_inicio': novo_registro.horario_inicio,
                'horario_fim': None,
                'message': 'Trabalho iniciado com sucesso.'
            }), 201
    except Exception as e:
        print(f"Erro ao registrar trabalho: {e}")
        return jsonify({'message': 'Erro ao registrar trabalho', 'details': str(e)}), 500

        # Rota para listar todas as paletes
@app.route('/paletes', methods=['GET'])
def get_paletes():
    paletes = Palete.query.all()
    output = []
    for p in paletes:
        produtos = json.loads(p.produtos) if p.produtos else []
        output.append({
            'id': p.id,
            'numero_palete': p.numero_palete,
            'produtos': produtos
        })
    print(f"GET /paletes - {len(paletes)} paletes encontradas")
    return jsonify(output)


# Rota para adicionar palete
@app.route('/paletes', methods=['POST'])
def add_palete():
    try:
        data = request.get_json()
        if 'numero_palete' not in data or 'produtos' not in data:
            return jsonify({'message': 'Campos obrigatórios ausentes'}), 400

        nova_palete = Palete(
            numero_palete=data['numero_palete'],
            produtos=json.dumps(data['produtos'])
        )
        db.session.add(nova_palete)
        db.session.commit()
        return jsonify({'message': 'Palete adicionada com sucesso!'}), 201
    except Exception as e:
        print(f"Erro ao adicionar palete: {e}")
        return jsonify({'message': 'Erro ao adicionar palete', 'details': str(e)}), 500
        
# Rota para remover palete
@app.route('/paletes/<int:id>', methods=['DELETE'])
def delete_palete(id):
    try:
        # Buscar a palete pelo ID
        palete = Palete.query.get(id)
        if not palete:
            return jsonify({'message': 'Palete não encontrada'}), 404

        # Remover a palete do banco de dados
        db.session.delete(palete)
        db.session.commit()

        return jsonify({'message': 'Palete removida com sucesso!'}), 200
    except Exception as e:
        print(f"Erro ao remover palete: {e}")
        return jsonify({'message': 'Erro ao remover palete', 'details': str(e)}), 500
    




@app.route('/chefes/definir_senha', methods=['POST'])
def definir_senha_chefe():
    try:
        data = request.get_json()
        id_trabalhador = data.get('id')
        nova_senha = data.get('senha')

        if not nova_senha or len(nova_senha) < 6:
            return jsonify({'message': 'A senha deve ter pelo menos 6 caracteres.'}), 400

        trabalhador = Trabalhador.query.get(id_trabalhador)
        if not trabalhador or not trabalhador.chefe:
            return jsonify({'message': 'Chefe não encontrado ou não autorizado.'}), 404

        if trabalhador.senha_hash is not None:
            return jsonify({'message': 'Senha já definida.'}), 400

        trabalhador.set_senha(nova_senha)
        db.session.commit()

        return jsonify({'message': 'Senha definida com sucesso!'}), 200
    except Exception as e:
        print(f"Erro ao definir senha: {e}")
        return jsonify({'message': 'Erro ao definir senha.', 'details': str(e)}), 500





#rota para autenticar chefe
@app.route('/chefes/login', methods=['POST'])
def login_chefe():
    try:
        data = request.get_json()
        id_trabalhador = data.get('id')
        senha = data.get('senha')

        trabalhador = Trabalhador.query.get(id_trabalhador)
        if not trabalhador or not trabalhador.chefe:
            return jsonify({'message': 'Chefe não encontrado ou não autorizado.'}), 404

        if trabalhador.senha_hash is None:
            return jsonify({'message': 'Senha não definida. Por favor, defina uma senha.'}), 400

        if not trabalhador.verificar_senha(senha):
            return jsonify({'message': 'Senha incorreta.'}), 401

        return jsonify({'message': 'Login bem-sucedido!', 'nome': trabalhador.nome, 'secao': trabalhador.secao}), 200
    except Exception as e:
        print(f"Erro ao autenticar chefe: {e}")
        return jsonify({'message': 'Erro ao autenticar chefe.', 'details': str(e)}), 500







if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)



