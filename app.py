from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from PIL import Image
import qrcode
from io import BytesIO
import os
import re

# ==================== CONFIGURAÇÃO ====================

app = Flask(__name__, static_folder='static')
CORS(app)

# Configurações
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///student_system.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'r3-formaturas-secret-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

# Inicialização
db = SQLAlchemy(app)
jwt = JWTManager(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==================== MODELS ====================

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
    nome = db.Column(db.String(200), nullable=False, unique=True)
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    eventos = db.relationship('Evento', backref='escola', lazy=True)

class Evento(db.Model):
    __tablename__ = 'eventos'
    id = db.Column(db.Integer, primary_key=True)
    escola_id = db.Column(db.Integer, db.ForeignKey('escolas.id'), nullable=False)
    data_evento = db.Column(db.Date)
    local_evento = db.Column(db.String(200))
    endereco_evento = db.Column(db.String(255))
    tipo_formatura = db.Column(db.String(50))
    status = db.Column(db.String(20), default='ativo')
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    leads = db.relationship('Lead', backref='evento', lazy=True)
    
    @property
    def qr_url(self):
        return f"/cadastro?e={self.id}"

class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=False)
    serie = db.Column(db.String(15))
    letra_turma = db.Column(db.String(2))
    ano_formatura = db.Column(db.Integer)
    matricula = db.Column(db.String(20), nullable=False)
    nome_formando = db.Column(db.String(100), nullable=False)
    foto = db.Column(db.String(255))
    nome_contato = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    whatsapp = db.Column(db.String(20), nullable=False)
    tipo_cadastro = db.Column(db.String(20))
    cep = db.Column(db.String(10))
    endereco = db.Column(db.String(300))
    status_lead = db.Column(db.String(20), default='novo')
    observacoes = db.Column(db.Text)
    data_contato = db.Column(db.DateTime)
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint('matricula', 'evento_id', name='unique_matricula_evento'),
    )

# ==================== VALIDAÇÕES ====================

def validar_nome(nome):
    if not nome or len(nome) < 3:
        return False
    return re.match(r"^[a-zA-ZÀ-ÿ\s']+$", nome) is not None

def validar_email(email):
    if not email:
        return False
    return re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email) is not None

def validar_whatsapp(whatsapp):
    if not whatsapp:
        return False
    return re.match(r'^\(\d{2}\)\s?\d{5}-\d{4}$', whatsapp) is not None

def validar_cep(cep):
    if not cep:
        return True
    return re.match(r'^\d{5}-\d{3}$', cep) is not None

def validar_serie(serie):
    series_validas = ['6º ano','7º ano','8º ano','9º ano','1º ano EM','2º ano EM','3º ano EM']
    return serie in series_validas

def validar_letra_turma(letra):
    if not letra or len(letra) > 2:
        return False
    return letra.isalnum()

def validar_matricula(matricula):
    if not matricula or len(matricula) < 3:
        return False
    matricula = matricula.strip().replace(' ', '')
    return matricula.isalnum()

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
    offset = ((300 - img.width) // 2, (400 - img.height) // 2)
    nova_img.paste(img, offset)
    nova_img.save(caminho, 'JPEG', quality=85, optimize=True)
    return nome_arquivo

# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    usuario = Usuario.query.filter_by(login=data.get('login')).first()
    if usuario and check_password_hash(usuario.senha_hash, data.get('senha')):
        token = create_access_token(identity=usuario.id)
        return jsonify({'token': token,'nome': usuario.nome,'tipo_usuario': usuario.tipo_usuario}), 200
    return jsonify({'erro': 'Login ou senha inválidos'}), 401

# ==================== ROTAS DE EVENTOS ====================

@app.route('/api/eventos', methods=['POST'])
@jwt_required()
def criar_evento():
    vendedor_id = get_jwt_identity()
    vendedor = Usuario.query.get(vendedor_id)
    if vendedor.tipo_usuario != 'admin':
        return jsonify({'erro': 'Apenas administradores podem criar eventos'}), 403

    data = request.get_json()

    escola_nome = (data.get('escola') or '').strip()
    if not escola_nome:
        return jsonify({'erro': 'Informe o nome da escola'}), 400

    escola = Escola.query.filter_by(nome=escola_nome).first()
    if not escola:
        escola = Escola(
            nome=escola_nome,
            cidade=data.get('cidade'),
            estado=(data.get('estado') or '').upper()[:2]
        )
        db.session.add(escola)
        db.session.flush()

    data_evento = None
    if data.get('data_evento'):
        try:
            data_evento = datetime.fromisoformat(data['data_evento']).date()
        except ValueError:
            return jsonify({'erro': 'Data do evento inválida (use YYYY-MM-DD)'}), 400

    evento = Evento(
        escola_id=escola.id,
        data_evento=data_evento,
        local_evento=data.get('local_evento'),
        endereco_evento=data.get('endereco_evento'),
        tipo_formatura=data.get('tipo_formatura'),
        status='ativo',
        vendedor_id=vendedor_id
    )

    db.session.add(evento)
    db.session.commit()

    base_url = request.host_url
    qr_url = f"{base_url}cadastro?e={evento.id}"

    return jsonify({'mensagem': 'Evento criado com sucesso!','evento_id': evento.id,'qr_url': qr_url}), 201

@app.route('/api/eventos/<int:evento_id>', methods=['GET'])
def buscar_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    if evento.status != 'ativo':
        return jsonify({'erro': 'Este evento não está mais disponível'}), 400
    return jsonify({
        'id': evento.id,
        'escola': {'id': evento.escola.id,'nome': evento.escola.nome,'cidade': evento.escola.cidade,'estado': evento.escola.estado},
        'data_evento': evento.data_evento.isoformat() if evento.data_evento else None,
        'local_evento': evento.local_evento,
        'endereco_evento': evento.endereco_evento,
        'tipo_formatura': evento.tipo_formatura
    }), 200

@app.route('/api/eventos', methods=['GET'])
@jwt_required()
def listar_eventos():
    eventos = Evento.query.order_by(Evento.criado_em.desc()).all()
    resultado = []
    for evento in eventos:
        resultado.append({
            'id': evento.id,
            'escola': evento.escola.nome,
            'data_evento': evento.data_evento.isoformat() if evento.data_evento else None,
            'local_evento': evento.local_evento,
            'status': evento.status,
            'total_leads': len(evento.leads),
            'qr_url': f"{request.host_url}cadastro?e={evento.id}",
            'tipo_formatura': evento.tipo_formatura
        })
    return jsonify(resultado), 200

@app.route('/api/eventos/<int:evento_id>/qrcode', methods=['GET'])
@jwt_required()
def gerar_qrcode(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    base_url = request.host_url
    qr_url = f"{base_url}cadastro?e={evento.id}"
    qr = qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=10,border=4)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png', download_name=f'qrcode-evento-{evento_id}.png')

# ==================== ROTAS DE CADASTRO ====================

@app.route('/api/cadastro', methods=['POST'])
def cadastrar_lead():
    try:
        data = request.form
        evento_id = data.get('evento_id')
        if not evento_id:
            return jsonify({'erro': 'Evento não identificado'}), 400
        evento = Evento.query.get(evento_id)
        if not evento or evento.status != 'ativo':
            return jsonify({'erro': 'Evento não disponível'}), 400

        matricula = data.get('matricula', '').strip().upper()
        nome_formando = data.get('nome_formando')
        nome_contato = data.get('nome_contato')
        email = data.get('email')
        whatsapp = data.get('whatsapp')
        tipo_cadastro = data.get('tipo_cadastro')

        if not all([matricula, nome_formando, nome_contato, email, whatsapp]):
            return jsonify({'erro': 'Preencha todos os campos obrigatórios'}), 400
        if not validar_matricula(matricula):
            return jsonify({'erro': 'Matrícula inválida! Digite pelo menos 3 caracteres'}), 400

        lead_existente = Lead.query.filter_by(matricula=matricula, evento_id=evento_id).first()
        if lead_existente:
            return jsonify({'erro': f'Matrícula {matricula} já cadastrada neste evento!'}), 400

        if not validar_nome(nome_formando):
            return jsonify({'erro': 'Nome do formando inválido! Use apenas letras'}), 400
        if not validar_nome(nome_contato):
            return jsonify({'erro': 'Seu nome inválido! Use apenas letras'}), 400
        if not validar_email(email):
            return jsonify({'erro': 'E-mail inválido'}), 400
        if not validar_whatsapp(whatsapp):
            return jsonify({'erro': 'WhatsApp inválido! Formato: (11) 98765-4321'}), 400

        foto_filename = None
        if 'foto' in request.files and request.files['foto'].filename:
            foto_filename = processar_foto(request.files['foto'])

        lead = Lead(
            evento_id=evento_id,
            matricula=matricula,
            nome_formando=nome_formando,
            nome_contato=nome_contato,
            email=email,
            whatsapp=whatsapp,
            tipo_cadastro=tipo_cadastro,
            cep=data.get('cep'),
            endereco=data.get('endereco'),
            foto=foto_filename,
            status_lead='novo'
        )
        db.session.add(lead)
        db.session.commit()

        return jsonify({'mensagem': 'Cadastro realizado com sucesso!','id': lead.id,'matricula': matricula}), 201
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERRO: {str(e)}")
        return jsonify({'erro': 'Erro ao processar cadastro'}), 500

# ==================== ROTAS DE LEADS ====================

@app.route('/api/leads', methods=['GET'])
@jwt_required()
def listar_leads():
    vendedor_id = get_jwt_identity()
    vendedor = Usuario.query.get(vendedor_id)
    evento_id = request.args.get('evento_id')
    status = request.args.get('status')
    busca = request.args.get('busca', '')
    query = Lead.query

    if vendedor.tipo_usuario != 'admin':
        query = query.filter((Lead.vendedor_id == vendedor_id) | (Lead.vendedor_id == None))
    if evento_id:
        query = query.filter_by(evento_id=evento_id)
    if status:
        query = query.filter_by(status_lead=status)
    if busca:
        query = query.filter(
            (Lead.nome_formando.ilike(f'%{busca}%')) |
            (Lead.nome_contato.ilike(f'%{busca}%')) |
            (Lead.email.ilike(f'%{busca}%')) |
            (Lead.matricula.ilike(f'%{busca}%'))
        )

    leads = query.order_by(Lead.criado_em.desc()).all()
    resultado = []
    for lead in leads:
        ano_evento = lead.evento.data_evento.year if lead.evento and lead.evento.data_evento else None
        resultado.append({
            'id': lead.id,
            'matricula': lead.matricula,
            'nome_formando': lead.nome_formando,
            'nome_contato': lead.nome_contato,
            'email': lead.email,
            'whatsapp': lead.whatsapp,
            'tipo_cadastro': lead.tipo_cadastro,
            'status_lead': lead.status_lead,
            'observacoes': lead.observacoes,
            'foto': f'/static/uploads/{lead.foto}' if lead.foto else None,
            'evento': {
                'id': lead.evento.id,
                'escola': lead.evento.escola.nome,
                'tipo_formatura': lead.evento.tipo_formatura,
                'data_evento': lead.evento.data_evento.isoformat() if lead.evento.data_evento else None
            },
            'criado_em': lead.criado_em.isoformat()
        })
    return jsonify(resultado), 200

@app.route('/api/leads/<int:lead_id>', methods=['PATCH'])
@jwt_required()
def atualizar_lead(lead_id):
    vendedor_id = get_jwt_identity()
    lead = Lead.query.get_or_404(lead_id)
    data = request.get_json()
    if 'status_lead' in data:
        lead.status_lead = data['status_lead']
    if 'observacoes' in data:
        lead.observacoes = data['observacoes']
    if data.get('marcar_contato'):
        lead.data_contato = datetime.utcnow()
    if not lead.vendedor_id:
        lead.vendedor_id = vendedor_id
    db.session.commit()
    return jsonify({'mensagem': 'Lead atualizado!'}), 200

@app.route('/api/estatisticas', methods=['GET'])
@jwt_required()
def estatisticas():
    vendedor_id = get_jwt_identity()
    vendedor = Usuario.query.get(vendedor_id)
    leads_query = Lead.query if vendedor.tipo_usuario == 'admin' else Lead.query.filter_by(vendedor_id=vendedor_id)
    novos = leads_query.filter_by(status_lead='novo').count()
    contatados = leads_query.filter_by(status_lead='contatado').count()
    interessados = leads_query.filter_by(status_lead='interessado').count()
    convertidos = leads_query.filter_by(status_lead='convertido').count()
    perdidos = leads_query.filter_by(status_lead='perdido').count()
    total = leads_query.count()
    taxa_conversao = (convertidos / total * 100) if total > 0 else 0
    return jsonify({'total': total,'novos': novos,'contatados': contatados,'interessados': interessados,'convertidos': convertidos,'perdidos': perdidos,'taxa_conversao': round(taxa_conversao, 2)}), 200

@app.route('/api/eventos/<int:evento_id>/qrcode/download', methods=['GET'])
@jwt_required()
def baixar_qrcode(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    base_url = request.host_url
    qr_url = f"{base_url}cadastro?e={evento.id}"
    qr = qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_H,box_size=12,border=4)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return send_file(buffer,mimetype='image/png',as_attachment=True,download_name=f'evento_{evento.id}_qrcode.png')

# ==================== ROTAS ESTÁTICAS ====================

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

# ==================== ROTA DE ALUNOS (LEADS) ====================

@app.route('/api/alunos', methods=['GET'])
@jwt_required()
def listar_alunos_dashboard():
    vendedor_id = get_jwt_identity()
    vendedor = Usuario.query.get(vendedor_id)
    leads = Lead.query.all() if vendedor.tipo_usuario == 'admin' else Lead.query.filter((Lead.vendedor_id == vendedor_id) | (Lead.vendedor_id == None)).all()
    resultado = []
    for lead in leads:
        ano_evento = lead.evento.data_evento.year if lead.evento and lead.evento.data_evento else None
        resultado.append({
            'id': lead.id,
            'nome': lead.nome_formando,
            'escola': lead.evento.escola.nome,
            'turma': f"{lead.serie or ''} {lead.letra_turma or ''}".strip() or 'Não informada',
            'ano_formatura': lead.ano_formatura or ano_evento,
            'email': lead.email,
            'whatsapp': lead.whatsapp,
            'responsavel': lead.nome_contato if lead.tipo_cadastro == 'responsavel' else None,
            'foto': f'/static/uploads/{lead.foto}' if lead.foto else None
        })
    return jsonify(resultado), 200

# ==================== INICIALIZAÇÃO ====================

def criar_usuario_admin():
    if not Usuario.query.filter_by(login='admin').first():
        admin = Usuario(nome='Administrador',login='admin',senha_hash=generate_password_hash('admin123'),tipo_usuario='admin')
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuário admin criado: login='admin', senha='admin123'")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        criar_usuario_admin()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
