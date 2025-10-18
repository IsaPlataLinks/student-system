from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
from PIL import Image
import re

# Configuração do Flask
app = Flask(__name__, static_folder='static')
CORS(app)

# Configurações
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///student_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'sua-chave-secreta-aqui'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# Inicialização
db = SQLAlchemy(app)
jwt = JWTManager(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# MODELS
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo_usuario = db.Column(db.String(20), default='vendedor')
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class Escola(db.Model):
    __tablename__ = 'escolas'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    alunos = db.relationship('Aluno', backref='escola', lazy=True)

class Responsavel(db.Model):
    __tablename__ = 'responsaveis'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    whatsapp = db.Column(db.String(20))
    endereco = db.Column(db.String(300))
    cep = db.Column(db.String(10))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    alunos = db.relationship('Aluno', backref='responsavel', lazy=True)

class Aluno(db.Model):
    __tablename__ = 'alunos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    turma = db.Column(db.String(50), nullable=False)
    ano_formatura = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100))
    whatsapp = db.Column(db.String(20))
    endereco = db.Column(db.String(300))
    cep = db.Column(db.String(10))
    foto = db.Column(db.String(255))
    escola_id = db.Column(db.Integer, db.ForeignKey('escolas.id'))
    responsavel_id = db.Column(db.Integer, db.ForeignKey('responsaveis.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

# VALIDAÇÕES
def validar_nome(nome):
    if not nome:
        return False
    return re.match(r"^[a-zA-ZÀ-ÿ\s']+$", nome) is not None

def validar_ano_formatura(ano):
    try:
        ano_int = int(ano)
        return len(str(ano)) == 4 and 2020 <= ano_int <= 2035
    except:
        return False

def validar_turma(turma):
    if not turma or len(turma) > 30:
        return False
    return re.match(r'^[a-zA-Z0-9º\s-]+$', turma) is not None

def validar_email(email):
    if not email:
        return False
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

def validar_whatsapp(whatsapp):
    if not whatsapp:
        return False
    return re.match(r'^\(\d{2}\)\s?\d{5}-\d{4}$', whatsapp) is not None

def validar_cep(cep):
    if not cep:
        return True
    return re.match(r'^\d{5}-\d{3}$', cep) is not None

def processar_foto(file):
    if not file:
        return None
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    nome_arquivo = f"{timestamp}_{filename}"
    caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
    file.save(caminho)
    img = Image.open(caminho)
    img.thumbnail((300, 400), Image.Resampling.LANCZOS)
    nova_img = Image.new('RGB', (300, 400), (255, 255, 255))
    nova_img.paste(img, ((300-img.width)//2, (400-img.height)//2))
    nova_img.save(caminho, 'JPEG', quality=85, optimize=True)
    return nome_arquivo

# ROTAS
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    usuario = Usuario.query.filter_by(login=data.get('login')).first()
    if usuario and check_password_hash(usuario.senha_hash, data.get('senha')):
        token = create_access_token(identity=usuario.id)
        return jsonify({'token': token, 'nome': usuario.nome, 'tipo_usuario': usuario.tipo_usuario}), 200
    return jsonify({'erro': 'Login ou senha inválidos'}), 401

@app.route('/api/cadastro/aluno', methods=['POST'])
def cadastrar_aluno():
    try:
        data = request.form
        foto = request.files.get('foto')
        
        if not validar_nome(data.get('nome')):
            return jsonify({'erro': 'Nome inválido! Use apenas letras.'}), 400
        if not validar_ano_formatura(data.get('ano_formatura')):
            return jsonify({'erro': 'Ano inválido! Use 4 dígitos.'}), 400
        if not validar_turma(data.get('turma')):
            return jsonify({'erro': 'Turma inválida! Máximo 30 caracteres.'}), 400
        if not validar_email(data.get('email')):
            return jsonify({'erro': 'E-mail inválido ou não preenchido!'}), 400
        if not validar_whatsapp(data.get('whatsapp')):
            return jsonify({'erro': 'WhatsApp inválido ou não preenchido!'}), 400
        if not validar_cep(data.get('cep')):
            return jsonify({'erro': 'CEP inválido!'}), 400
        
        nome_escola = data.get('escola')
        escola = Escola.query.filter_by(nome=nome_escola).first()
        if not escola:
            escola = Escola(nome=nome_escola)
            db.session.add(escola)
            db.session.flush()
        
        foto_filename = processar_foto(foto) if foto else None
        
        endereco_completo = None
        if data.get('logradouro'):
            partes = [data.get('logradouro'), data.get('numero'), data.get('complemento'), 
                     data.get('bairro'), data.get('cidade'), data.get('estado')]
            endereco_completo = ', '.join([p for p in partes if p])
        
        aluno = Aluno(
            nome=data.get('nome'),
            turma=data.get('turma'),
            ano_formatura=int(data.get('ano_formatura')),
            email=data.get('email'),
            whatsapp=data.get('whatsapp'),
            endereco=endereco_completo or data.get('endereco'),
            cep=data.get('cep'),
            foto=foto_filename,
            escola_id=escola.id
        )
        
        db.session.add(aluno)
        db.session.commit()
        return jsonify({'mensagem': 'Aluno cadastrado com sucesso!', 'id': aluno.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/cadastro/responsavel', methods=['POST'])
def cadastrar_responsavel():
    try:
        data = request.form
        foto = request.files.get('foto')
        
        if not validar_nome(data.get('nome_responsavel')):
            return jsonify({'erro': 'Nome do responsável inválido!'}), 400
        if not validar_nome(data.get('nome_aluno')):
            return jsonify({'erro': 'Nome do aluno inválido!'}), 400
        if not validar_ano_formatura(data.get('ano_formatura')):
            return jsonify({'erro': 'Ano inválido!'}), 400
        if not validar_turma(data.get('turma')):
            return jsonify({'erro': 'Turma inválida!'}), 400
        
        responsavel = Responsavel(
            nome=data.get('nome_responsavel'),
            email=data.get('email_responsavel'),
            whatsapp=data.get('whatsapp_responsavel'),
            endereco=data.get('endereco_responsavel'),
            cep=data.get('cep_responsavel')
        )
        db.session.add(responsavel)
        db.session.flush()
        
        nome_escola = data.get('escola')
        escola = Escola.query.filter_by(nome=nome_escola).first()
        if not escola:
            escola = Escola(nome=nome_escola)
            db.session.add(escola)
            db.session.flush()
        
        foto_filename = processar_foto(foto) if foto else None
        
        aluno = Aluno(
            nome=data.get('nome_aluno'),
            turma=data.get('turma'),
            ano_formatura=int(data.get('ano_formatura')),
            foto=foto_filename,
            escola_id=escola.id,
            responsavel_id=responsavel.id
        )
        
        db.session.add(aluno)
        db.session.commit()
        return jsonify({'mensagem': 'Aluno cadastrado com sucesso!', 'id': aluno.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/alunos', methods=['GET'])
@jwt_required()
def listar_alunos():
    alunos = Aluno.query.all()
    resultado = []
    for aluno in alunos:
        resultado.append({
            'id': aluno.id,
            'nome': aluno.nome,
            'turma': aluno.turma,
            'ano_formatura': aluno.ano_formatura,
            'email': aluno.email,
            'whatsapp': aluno.whatsapp,
            'foto': f'/static/uploads/{aluno.foto}' if aluno.foto else None,
            'escola': aluno.escola.nome if aluno.escola else None,
            'responsavel': aluno.responsavel.nome if aluno.responsavel else None
        })
    return jsonify(resultado), 200

@app.route('/api/escolas', methods=['GET'])
@jwt_required()
def listar_escolas():
    escolas = Escola.query.all()
    return jsonify([{'id': e.id, 'nome': e.nome} for e in escolas]), 200

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

def criar_usuario_admin():
    if not Usuario.query.filter_by(login='admin').first():
        admin = Usuario(
            nome='Administrador',
            login='admin',
            senha_hash=generate_password_hash('admin123'),
            tipo_usuario='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuário admin criado: login='admin', senha='admin123'")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        criar_usuario_admin()
    app.run(debug=True, host='0.0.0.0', port=5000)