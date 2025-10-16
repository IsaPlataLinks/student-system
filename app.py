# ==================== ROTAS DO DASHBOARD (PROTEGIDAS) ====================

@app.route('/api/alunos', methods=['GET'])
@jwt_required()
def listar_alunos():
    """Lista alunos com filtros"""
    escola_id = request.args.get('escola_id')
    turma = request.args.get('turma')
    ano = request.args.get('ano')
    
    query = Aluno.query
    
    if escola_id:
        query = query.filter_by(escola_id=escola_id)
    if turma:
        query = query.filter_by(turma=turma)
    if ano:
        query = query.filter_by(ano_formatura=ano)
    
    alunos = query.all()
    
    resultado = []
    for aluno in alunos:
        resultado.append({
            'id': aluno.id,
            'nome': aluno.nome,
            'turma': aluno.turma,
            'ano_formatura': aluno.ano_formatura,
            'email': aluno.email,
            'whatsapp': aluno.whatsapp,
            'endereco': aluno.endereco,
            'cep': aluno.cep,
            'foto': f'/static/uploads/{aluno.foto}' if aluno.foto else None,
            'escola': aluno.escola.nome if aluno.escola else None,
            'escola_id': aluno.escola_id,
            'responsavel': aluno.responsavel.nome if aluno.responsavel else None,
            'email_responsavel': aluno.responsavel.email if aluno.responsavel else None,
            'whatsapp_responsavel': aluno.responsavel.whatsapp if aluno.responsavel else None
        })
    
    return jsonify(resultado), 200

@app.route('/api/alunos/<int:aluno_id>', methods=['GET'])
@jwt_required()
def obter_aluno(aluno_id):
    """Obter dados de um aluno específico"""
    aluno = Aluno.query.get_or_404(aluno_id)
    
    return jsonify({
        'id': aluno.id,
        'nome': aluno.nome,
        'turma': aluno.turma,
        'ano_formatura': aluno.ano_formatura,
        'email': aluno.email,
        'whatsapp': aluno.whatsapp,
        'endereco': aluno.endereco,
        'cep': aluno.cep,
        'foto': f'/static/uploads/{aluno.foto}' if aluno.foto else None,
        'escola': aluno.escola.nome if aluno.escola else None,
        'escola_id': aluno.escola_id,
        'responsavel': aluno.responsavel.nome if aluno.responsavel else None
    }), 200

@app.route('/api/alunos/<int:aluno_id>', methods=['PUT'])
@jwt_required()
def editar_aluno(aluno_id):
    """Editar dados de um aluno"""
    try:
        aluno = Aluno.query.get_or_404(aluno_id)
        data = request.form
        
        # Atualizar campos
        if data.get('nome'):
            aluno.nome = data.get('nome')
        if data.get('turma'):
            aluno.turma = data.get('turma')
        if data.get('ano_formatura'):
            aluno.ano_formatura = int(data.get('ano_formatura'))
        if data.get('email'):
            aluno.email = data.get('email')
        if data.get('whatsapp'):
            aluno.whatsapp = data.get('whatsapp')
        if data.get('endereco'):
            aluno.endereco = data.get('endereco')
        if data.get('cep'):
            aluno.cep = data.get('cep')
        
        # Processar nova foto se enviada
        foto = request.files.get('foto')
        if foto:
            foto_filename = processar_foto(foto)
            if foto_filename:
                aluno.foto = foto_filename
        
        db.session.commit()
        
        return jsonify({'mensagem': 'Aluno atualizado com sucesso!'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/alunos/<int:aluno_id>', methods=['DELETE'])
@jwt_required()
def deletar_aluno(aluno_id):
    """Deletar um aluno"""
    try:
        aluno = Aluno.query.get_or_404(aluno_id)
        
        # Deletar foto se existir
        if aluno.foto:
            caminho_foto = os.path.join(app.config['UPLOAD_FOLDER'], aluno.foto)
            if os.path.exists(caminho_foto):
                os.remove(caminho_foto)
        
        db.session.delete(aluno)
        db.session.commit()
        
        return jsonify({'mensagem': 'Aluno deletado com sucesso!'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/alunos/<int:aluno_id>', methods=['PUT'])
@jwt_required()
def editar_aluno(aluno_id):
    """Editar dados de um aluno"""
    try:
        aluno = Aluno.query.get_or_404(aluno_id)
        data = request.form
        
        # Validações
        if data.get('email') and not validar_email(data.get('email')):
            return jsonify({'erro': 'E-mail inválido'}), 400
        
        if data.get('whatsapp') and not validar_whatsapp(data.get('whatsapp')):
            return jsonify({'erro': 'WhatsApp inválido'}), 400
        
        # Atualizar campos
        if data.get('nome'):
            aluno.nome = data.get('nome')
        if data.get('turma'):
            aluno.turma = data.get('turma')
        if data.get('ano_formatura'):
            aluno.ano_formatura = int(data.get('ano_formatura'))
        if data.get('email'):
            aluno.email = data.get('email')
        if data.get('whatsapp'):
            aluno.whatsapp = data.get('whatsapp')
        if data.get('endereco'):
            aluno.endereco = data.get('endereco')
        if data.get('cep'):
            aluno.cep = data.get('cep')
        
        # Processar nova foto se enviada
        foto = request.files.get('foto')
        if foto:
            # Deletar foto antiga
            if aluno.foto:
                caminho_antigo = os.path.join(app.config['UPLOAD_FOLDER'], aluno.foto)
                if os.path.exists(caminho_antigo):
                    os.remove(caminho_antigo)
            
            foto_filename = processar_foto(foto)
            if foto_filename:
                aluno.foto = foto_filename
        
        db.session.commit()
        
        return jsonify({'mensagem': 'Aluno atualizado com sucesso!'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/alunos/<int:aluno_id>', methods=['DELETE'])
@jwt_required()
def deletar_aluno(aluno_id):
    """Deletar um aluno"""
    try:
        aluno = Aluno.query.get_or_404(aluno_id)
        
        # Deletar foto se existir
        if aluno.foto:
            caminho_foto = os.path.join(app.config['UPLOAD_FOLDER'], aluno.foto)
            if os.path.exists(caminho_foto):
                os.remove(caminho_foto)
        
        db.session.delete(aluno)
        db.session.commit()
        
        return jsonify({'mensagem': 'Aluno deletado com sucesso!'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/escolas', methods=['GET'])
@jwt_required()
def listar_escolas():
    """Lista todas as escolas com contagem de alunos"""
    escolas = Escola.query.all()
    resultado = []
    for escola in escolas:
        resultado.append({
            'id': escola.id,
            'nome': escola.nome,
            'total_alunos': len(escola.alunos)
        })
    return jsonify(resultado), 200

@app.route('/api/estatisticas', methods=['GET'])
@jwt_required()
def obter_estatisticas():
    """Estatísticas para gráficos do dashboard"""
    
    # Alunos por escola
    escolas = db.session.query(
        Escola.nome, 
        db.func.count(Aluno.id)
    ).join(Aluno).group_by(Escola.nome).all()
    
    # Alunos por ano
    anos = db.session.query(
        Aluno.ano_formatura,
        db.func.count(Aluno.id)
    ).group_by(Aluno.ano_formatura).order_by(Aluno.ano_formatura).all()
    
    # Alunos por turma
    turmas = db.session.query(
        Aluno.turma,
        db.func.count(Aluno.id)
    ).group_by(Aluno.turma).all()
    
    return jsonify({
        'por_escola': [{'nome': e[0], 'total': e[1]} for e in escolas],
        'por_ano': [{'ano': a[0], 'total': a[1]} for a in anos],
        'por_turma': [{'turma': t[0], 'total': t[1]} for t in turmas],
        'total_alunos': Aluno.query.count(),
        'total_escolas': Escola.query.count(),
        'com_fotos': Aluno.query.filter(Aluno.foto.isnot(None)).count(),
        'com_responsavel': Aluno.query.filter(Aluno.responsavel_id.isnot(None)).count()
    }), 200

@from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
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
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/student_system')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'sua-chave-secreta-aqui-mude-em-producao')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

# Inicialização
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Criar pasta de uploads
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==================== MODELS ====================

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo_usuario = db.Column(db.String(20), default='vendedor')  # admin ou vendedor
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class Escola(db.Model):
    __tablename__ = 'escolas'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    endereco = db.Column(db.String(300))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
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

# ==================== FUNÇÕES AUXILIARES ====================

def validar_email(email):
    """Valida formato de e-mail"""
    if not email:
        return True  # Email opcional
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email) is not None

def validar_whatsapp(whatsapp):
    """Valida formato de WhatsApp (XX) XXXXX-XXXX"""
    if not whatsapp:
        return True  # WhatsApp opcional
    padrao = r'^\(\d{2}\)\s?\d{5}-\d{4}$'
    return re.match(padrao, whatsapp) is not None

def validar_cep(cep):
    """Valida formato de CEP XXXXX-XXX"""
    if not cep:
        return True  # CEP opcional
    padrao = r'^\d{5}-\d{3}$'
    return re.match(padrao, cep) is not None

def processar_foto(file):
    """Redimensiona foto para proporção 3x4 e salva"""
    if not file:
        return None
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    nome_arquivo = f"{timestamp}_{filename}"
    caminho_temp = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
    
    # Salvar temporariamente
    file.save(caminho_temp)
    
    # Processar imagem
    img = Image.open(caminho_temp)
    
    # Redimensionar para proporção 3x4 (300x400 pixels)
    img.thumbnail((300, 400), Image.Resampling.LANCZOS)
    
    # Criar imagem com fundo branco 3x4
    nova_img = Image.new('RGB', (300, 400), (255, 255, 255))
    
    # Centralizar imagem redimensionada
    offset_x = (300 - img.width) // 2
    offset_y = (400 - img.height) // 2
    nova_img.paste(img, (offset_x, offset_y))
    
    # Salvar otimizada
    nova_img.save(caminho_temp, 'JPEG', quality=85, optimize=True)
    
    return nome_arquivo

# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.route('/api/login', methods=['POST'])
def login():
    """Login do dono do sistema"""
    data = request.get_json()
    
    usuario = Usuario.query.filter_by(login=data.get('login')).first()
    
    if usuario and check_password_hash(usuario.senha_hash, data.get('senha')):
        token = create_access_token(identity=usuario.id)
        return jsonify({
            'token': token,
            'nome': usuario.nome,
            'tipo_usuario': usuario.tipo_usuario
        }), 200
    
    return jsonify({'erro': 'Login ou senha inválidos'}), 401

# ==================== ROTAS DE CADASTRO (PÚBLICO) ====================

@app.route('/api/cadastro/aluno', methods=['POST'])
def cadastrar_aluno():
    """Cadastro direto do aluno"""
    try:
        # Dados do formulário
        data = request.form
        foto = request.files.get('foto')
        
        # Validações
        if not validar_email(data.get('email')):
            return jsonify({'erro': 'E-mail inválido'}), 400
        
        if not validar_whatsapp(data.get('whatsapp')):
            return jsonify({'erro': 'WhatsApp inválido. Use: (XX) XXXXX-XXXX'}), 400
        
        if not validar_cep(data.get('cep')):
            return jsonify({'erro': 'CEP inválido. Use: XXXXX-XXX'}), 400
        
        # ⭐ NOVO: Verificar duplicidade por email (se fornecido)
        if data.get('email'):
            aluno_existente = Aluno.query.filter_by(email=data.get('email')).first()
            if aluno_existente:
                return jsonify({
                    'erro': f'Já existe um aluno cadastrado com este e-mail: {aluno_existente.nome}',
                    'sugestao': 'Verifique se você já se cadastrou ou use outro e-mail.'
                }), 409
        
        # ⭐ NOVO: Verificar duplicidade por WhatsApp (se fornecido)
        if data.get('whatsapp'):
            aluno_existente = Aluno.query.filter_by(whatsapp=data.get('whatsapp')).first()
            if aluno_existente:
                return jsonify({
                    'erro': f'Já existe um aluno cadastrado com este WhatsApp: {aluno_existente.nome}',
                    'sugestao': 'Verifique se você já se cadastrou ou use outro número.'
                }), 409
        
        # ⭐ NOVO: Verificar duplicidade por Nome + Turma + Ano (provavelmente é a mesma pessoa)
        aluno_similar = Aluno.query.filter_by(
            nome=data.get('nome'),
            turma=data.get('turma'),
            ano_formatura=int(data.get('ano_formatura'))
        ).first()
        
        if aluno_similar:
            return jsonify({
                'erro': f'Já existe um aluno com o mesmo nome, turma e ano cadastrado!',
                'sugestao': 'Você pode ter se cadastrado anteriormente. Entre em contato se precisar atualizar seus dados.'
            }), 409
        
        # Processar escola
        nome_escola = data.get('escola')
        escola = Escola.query.filter_by(nome=nome_escola).first()
        if not escola:
            escola = Escola(nome=nome_escola)
            db.session.add(escola)
            db.session.flush()
        
        # Processar foto
        foto_filename = processar_foto(foto) if foto else None
        
        # Criar aluno
        aluno = Aluno(
            nome=data.get('nome'),
            turma=data.get('turma'),
            ano_formatura=int(data.get('ano_formatura')),
            email=data.get('email'),
            whatsapp=data.get('whatsapp'),
            endereco=data.get('endereco'),
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
    """Cadastro pelo responsável"""
    try:
        data = request.form
        foto = request.files.get('foto')
        
        # Validações
        if not validar_email(data.get('email_responsavel')):
            return jsonify({'erro': 'E-mail do responsável inválido'}), 400
        
        if not validar_whatsapp(data.get('whatsapp_responsavel')):
            return jsonify({'erro': 'WhatsApp inválido. Use: (XX) XXXXX-XXXX'}), 400
        
        if not validar_cep(data.get('cep_responsavel')):
            return jsonify({'erro': 'CEP inválido. Use: XXXXX-XXX'}), 400
        
        # ⭐ NOVO: Verificar se responsável já existe (por email ou WhatsApp)
        responsavel_existente = None
        
        if data.get('email_responsavel'):
            responsavel_existente = Responsavel.query.filter_by(
                email=data.get('email_responsavel')
            ).first()
        
        if not responsavel_existente and data.get('whatsapp_responsavel'):
            responsavel_existente = Responsavel.query.filter_by(
                whatsapp=data.get('whatsapp_responsavel')
            ).first()
        
        # Se responsável existe, reutilizar (um responsável pode ter vários alunos!)
        if responsavel_existente:
            responsavel = responsavel_existente
        else:
            # Criar novo responsável
            responsavel = Responsavel(
                nome=data.get('nome_responsavel'),
                email=data.get('email_responsavel'),
                whatsapp=data.get('whatsapp_responsavel'),
                endereco=data.get('endereco_responsavel'),
                cep=data.get('cep_responsavel')
            )
            db.session.add(responsavel)
            db.session.flush()
        
        # ⭐ NOVO: Verificar se este aluno JÁ foi cadastrado por este responsável
        aluno_existente = Aluno.query.filter_by(
            nome=data.get('nome_aluno'),
            turma=data.get('turma'),
            ano_formatura=int(data.get('ano_formatura')),
            responsavel_id=responsavel.id
        ).first()
        
        if aluno_existente:
            return jsonify({
                'erro': f'Você já cadastrou este aluno anteriormente!',
                'aluno': aluno_existente.nome,
                'sugestao': 'Entre em contato se precisar atualizar os dados.'
            }), 409
        
        # Processar escola
        nome_escola = data.get('escola')
        escola = Escola.query.filter_by(nome=nome_escola).first()
        if not escola:
            escola = Escola(nome=nome_escola)
            db.session.add(escola)
            db.session.flush()
        
        # Processar foto
        foto_filename = processar_foto(foto) if foto else None
        
        # Criar aluno
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

# ==================== ROTAS DO DASHBOARD (PROTEGIDAS) ====================

@app.route('/api/alunos', methods=['GET'])
@jwt_required()
def listar_alunos():
    """Lista alunos com filtros"""
    escola_id = request.args.get('escola_id')
    turma = request.args.get('turma')
    ano = request.args.get('ano')
    
    query = Aluno.query
    
    if escola_id:
        query = query.filter_by(escola_id=escola_id)
    if turma:
        query = query.filter_by(turma=turma)
    if ano:
        query = query.filter_by(ano_formatura=ano)
    
    alunos = query.all()
    
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
    """Lista todas as escolas"""
    escolas = Escola.query.all()
    resultado = [{'id': e.id, 'nome': e.nome} for e in escolas]
    return jsonify(resultado), 200

# ==================== ROTAS ESTÁTICAS ====================

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

# ==================== INICIALIZAÇÃO ====================

def criar_usuario_admin():
    """Cria usuário admin padrão se não existir"""
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