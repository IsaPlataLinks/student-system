from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from PIL import Image
import qrcode
from io import BytesIO
import os
import re
from sqlalchemy import extract, or_
from sqlalchemy.exc import IntegrityError


# ==================== HELPERS/JWT ====================

def current_user_id() -> int | None:
    """Converte o sub do JWT para int com segurança"""
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None

# ==================== CONFIG ====================

app = Flask(__name__, static_folder='static')
CORS(app)

# 1) Garante que a pasta 'instance' existe ANTES de montar a URI
os.makedirs(app.instance_path, exist_ok=True)

# 2) Define o SQLite default usando caminho absoluto dentro de instance/
default_sqlite_path = os.path.join(app.instance_path, 'student_system.db')
default_uri = f"sqlite:///{default_sqlite_path}"

# 3) Usa DATABASE_URL se existir (Render/Heroku), senão cai no SQLite
uri = os.getenv('DATABASE_URL', default_uri)

# 4) Normaliza prefixo do Postgres para SQLAlchemy
if uri.startswith('postgres://'):
    uri = uri.replace('postgres://', 'postgresql+psycopg2://', 1)

# (opcional – só se seu Postgres exigir SSL e a string não trouxer):
# if uri.startswith('postgresql') and 'sslmode=' not in uri:
#     uri += '?sslmode=require'

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'r3-formaturas-secret-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

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
    data_evento = db.Column(db.Date, nullable=False)  # agora OBRIGATÓRIA
    local_evento = db.Column(db.String(200))
    endereco_evento = db.Column(db.String(255))
    tipo_formatura = db.Column(db.String(50))
    status = db.Column(db.String(20), default='ativo')
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    leads = db.relationship('Lead', backref='evento', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('escola_id', 'data_evento', name='unique_evento_escola_data'),
    )

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

def validar_nome(nome: str) -> bool:
    return bool(nome and len(nome) >= 3 and re.match(r"^[a-zA-ZÀ-ÿ\s']+$", nome))

def validar_email(email: str) -> bool:
    return bool(email and re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email))

def validar_whatsapp(whatsapp: str) -> bool:
    return bool(whatsapp and re.match(r'^\(\d{2}\)\s?\d{5}-\d{4}$', whatsapp))

def validar_cep(cep: str) -> bool:
    return bool((not cep) or re.match(r'^\d{5}-\d{3}$', cep))

def validar_serie(serie: str) -> bool:
    series_validas = ['6º ano', '7º ano', '8º ano', '9º ano', '1º ano EM', '2º ano EM', '3º ano EM']
    return serie in series_validas

def validar_letra_turma(letra: str) -> bool:
    return bool(letra and len(letra) <= 2 and letra.isalnum())

def validar_matricula(matricula: str) -> bool:
    if not matricula or len(matricula) < 3:
        return False
    matricula = matricula.strip().replace(' ', '')
    return matricula.isalnum()

def processar_foto(file):
    if not file:
        return None

    filename = secure_filename(file.filename or 'foto.jpg')
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    nome_arquivo = f"{timestamp}_{filename}"
    caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)

    # salva original
    file.save(caminho)

    # abre, normaliza e salva como JPEG 300x400 com fundo branco
    with Image.open(caminho) as img:
        if img.mode != 'RGB':           # evita erro ao salvar/pastar JPEG
            img = img.convert('RGB')
        img.thumbnail((300, 400), Image.Resampling.LANCZOS)

        nova_img = Image.new('RGB', (300, 400), (255, 255, 255))
        offset = ((300 - img.width) // 2, (400 - img.height) // 2)
        nova_img.paste(img, offset)
        nova_img.save(caminho, 'JPEG', quality=85, optimize=True)

    return nome_arquivo

# ==================== ERROR HANDLERS ====================

from werkzeug.exceptions import HTTPException

@app.errorhandler(Exception)
def handle_error(e):
    # Mantém status codes corretos (404, 401, 400, etc.) e retorna JSON
    if isinstance(e, HTTPException):
        return jsonify({'erro': e.description}), e.code
    # Log do stacktrace:
    import traceback; traceback.print_exc()
    return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'erro': 'Recurso não encontrado'}), 404

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({'erro': 'Não autorizado'}), 401

# ==================== AUTENTICAÇÃO ====================

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    usuario = Usuario.query.filter_by(login=data.get('login')).first()
    if usuario and check_password_hash(usuario.senha_hash, data.get('senha')):
        token = create_access_token(identity=str(usuario.id))
        return jsonify({'token': token, 'nome': usuario.nome, 'tipo_usuario': usuario.tipo_usuario}), 200
    return jsonify({'erro': 'Login ou senha inválidos'}), 401

# Helper para aceitar "YYYY-MM-DD" (e opcionalmente "DD/MM/YYYY")
def _parse_data_evento(valor):
    if not valor:
        return None
    s = str(valor).strip()
    try:
        return datetime.fromisoformat(s).date()
    except ValueError:
        try:
            return datetime.strptime(s, "%d/%m/%Y").date()
        except ValueError:
            return None

# ==================== EVENTOS ====================

@app.route('/api/eventos', methods=['POST'])
@jwt_required()
def criar_evento():
    uid = current_user_id()
    if uid is None:
        return jsonify({'erro': 'Token inválido'}), 401

    user = Usuario.query.get(uid)
    if not user:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    if user.tipo_usuario != 'admin':
        return jsonify({'erro': 'Apenas administradores podem criar eventos'}), 403

    data = (request.get_json(silent=True) or {})

    escola_nome = (data.get('escola') or '').strip()
    if not escola_nome:
        return jsonify({'erro': 'Informe o nome da escola'}), 400

    # Busca ou cria a escola
    escola = Escola.query.filter_by(nome=escola_nome).first()
    if not escola:
        escola = Escola(
            nome=escola_nome,
            cidade=data.get('cidade'),
            estado=(data.get('estado') or '').upper()[:2]
        )
        db.session.add(escola)

    # -------- DAQUI PRA BAIXO PRECISA FICAR DENTRO DA FUNÇÃO --------
    # Data do evento (OBRIGATÓRIA)
    if not data.get('data_evento'):
        return jsonify({'erro': 'Data do evento é obrigatória (dd/mm/aaaa ou YYYY-MM-DD)'}), 400

    data_evento = _parse_data_evento(data['data_evento'])
    if not data_evento:
        return jsonify({'erro': 'Data do evento inválida (use dd/mm/aaaa ou YYYY-MM-DD)'}), 400
    if data_evento.year < datetime.utcnow().year:
        return jsonify({'erro': 'Ano da data do evento não pode ser anterior ao ano atual'}), 400

    evento = Evento(
        escola=escola,
        data_evento=data_evento,
        local_evento=data.get('local_evento'),
        endereco_evento=data.get('endereco_evento'),
        tipo_formatura=data.get('tipo_formatura'),
        status='ativo',
        vendedor_id=uid
    )

    try:
        db.session.add(evento)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'erro': 'Já existe um evento para esta escola nesta data'}), 409

    qr_url = f"{request.host_url}cadastro?e={evento.id}"
    return jsonify({
        'mensagem': 'Evento criado com sucesso!',
        'evento_id': evento.id,
        'qr_url': qr_url
    }), 201

@app.route('/api/eventos', methods=['GET'])
@jwt_required()
def listar_eventos():
    try:
        # ✅ joinedload evita N+1 e AttributeError
        eventos = (Evento.query
                   .options(joinedload(Evento.escola))
                   .order_by(Evento.criado_em.desc())
                   .all())

        payload = []
        for e in eventos:
            payload.append({
                'id': e.id,
                'escola': e.escola.nome if e.escola else None,
                'tipo_formatura': e.tipo_formatura,
                'data_evento': e.data_evento.isoformat() if e.data_evento else None,
                'local_evento': e.local_evento,
                'status': e.status,
                'total_leads': len(e.leads),
                'qr_url': f"{request.host_url}cadastro?e={e.id}"
            })
        return jsonify(payload), 200
    except Exception as e:
        print(f"❌ Erro em listar_eventos: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': 'Erro ao listar eventos', 'detalhes': str(e)}), 500

@app.route('/api/eventos/<int:evento_id>', methods=['GET'])
def buscar_evento(evento_id):
    try:
        # ✅ Adicionar joinedload para evitar AttributeError
        evento = (Evento.query
                  .options(joinedload(Evento.escola))
                  .filter_by(id=evento_id)
                  .first_or_404())
        
        if evento.status != 'ativo':
            return jsonify({'erro': 'Este evento não está mais disponível'}), 400
        
        return jsonify({
            'id': evento.id,
            'escola': {
                'id': evento.escola.id if evento.escola else None,
                'nome': evento.escola.nome if evento.escola else None,
                'cidade': evento.escola.cidade if evento.escola else None,
                'estado': evento.escola.estado if evento.escola else None
            },
            'data_evento': evento.data_evento.isoformat() if evento.data_evento else None,
            'local_evento': evento.local_evento,
            'endereco_evento': evento.endereco_evento,
            'tipo_formatura': evento.tipo_formatura
        }), 200
    except Exception as e:
        print(f"❌ Erro em buscar_evento: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': 'Erro ao buscar evento', 'detalhes': str(e)}), 500


# ==================== QR CODE PÚBLICO ====================
@app.route('/api/eventos/<int:evento_id>/qrcode', methods=['GET'])
def gerar_qrcode(evento_id):
    evento = Evento.query.get_or_404(evento_id)

    base_url = request.host_url.rstrip('/')     # evita //cadastro
    qr_url = f"{base_url}/cadastro?e={evento.id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png', download_name=f'qrcode-evento-{evento_id}.png')


# ==================== CADASTRO PÚBLICO ====================

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

        matricula = (data.get('matricula') or '').strip().upper()
        nome_formando = data.get('nome_formando')
        nome_contato = data.get('nome_contato')
        email = data.get('email')
        whatsapp = data.get('whatsapp')
        tipo_cadastro = data.get('tipo_cadastro')

        if not all([matricula, nome_formando, nome_contato, email, whatsapp]):
            return jsonify({'erro': 'Preencha todos os campos obrigatórios'}), 400
        if not validar_matricula(matricula):
            return jsonify({'erro': 'Matrícula inválida! Digite pelo menos 3 caracteres'}), 400

        if Lead.query.filter_by(matricula=matricula, evento_id=evento_id).first():
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

        return jsonify({'mensagem': 'Cadastro realizado com sucesso!', 'id': lead.id, 'matricula': matricula}), 201
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERRO: {str(e)}")
        return jsonify({'erro': 'Erro ao processar cadastro'}), 500

# ==================== LEADS/CRM ====================

@app.route('/api/leads', methods=['GET'])
@jwt_required()
def listar_leads():
    try:
        vendedor_id = current_user_id()
        if vendedor_id is None:
            return jsonify({'erro': 'Token inválido'}), 401
        vendedor = Usuario.query.get(vendedor_id)
        if not vendedor:
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        # Filtros
        evento_id = request.args.get('evento_id')
        status = request.args.get('status')
        busca = request.args.get('busca', '')

        q = (Lead.query
             .options(joinedload(Lead.evento).joinedload(Evento.escola))
             .order_by(Lead.criado_em.desc()))

        if vendedor.tipo_usuario != 'admin':
            q = q.filter((Lead.vendedor_id == vendedor_id) | (Lead.vendedor_id == None))
        if evento_id:
            q = q.filter(Lead.evento_id == evento_id)
        if status:
            q = q.filter(Lead.status_lead == status)
        if busca:
            like = f'%{busca}%'
            q = q.filter((Lead.nome_formando.ilike(like)) |
                         (Lead.nome_contato.ilike(like)) |
                         (Lead.email.ilike(like)) |
                         (Lead.matricula.ilike(like)))

        resultado = []
        for lead in q.all():
            ev = lead.evento
            escola = ev.escola.nome if (ev and ev.escola) else None
            data_iso = ev.data_evento.isoformat() if (ev and ev.data_evento) else None
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
                    'id': ev.id if ev else None,
                    'escola': escola,
                    'tipo_formatura': ev.tipo_formatura if ev else None,
                    'data_evento': data_iso
                },
                'criado_em': lead.criado_em.isoformat()
            })
        return jsonify(resultado), 200
    except Exception as e:
        print(f"❌ Erro em listar_leads: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': 'Erro ao listar leads', 'detalhes': str(e)}), 500


@app.route('/api/leads/<int:lead_id>', methods=['PATCH'])
@jwt_required()
def atualizar_lead(lead_id):
    vendedor_id = current_user_id()
    if vendedor_id is None:
        return jsonify({'erro': 'Token inválido'}), 401

    lead = Lead.query.get_or_404(lead_id)
    data = request.get_json() or {}

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
    vendedor_id = current_user_id()
    if vendedor_id is None:
        return jsonify({'erro': 'Token inválido'}), 401

    vendedor = Usuario.query.get(vendedor_id)
    if not vendedor:
        return jsonify({'erro': 'Usuário não encontrado'}), 404

    leads_query = Lead.query if vendedor.tipo_usuario == 'admin' else Lead.query.filter_by(vendedor_id=vendedor_id)
    total = leads_query.count()
    novos = leads_query.filter_by(status_lead='novo').count()
    contatados = leads_query.filter_by(status_lead='contatado').count()
    interessados = leads_query.filter_by(status_lead='interessado').count()
    convertidos = leads_query.filter_by(status_lead='convertido').count()
    perdidos = leads_query.filter_by(status_lead='perdido').count()
    taxa_conversao = (convertidos / total * 100) if total > 0 else 0.0

    return jsonify({
        'total': total,
        'novos': novos,
        'contatados': contatados,
        'interessados': interessados,
        'convertidos': convertidos,
        'perdidos': perdidos,
        'taxa_conversao': round(taxa_conversao, 2)
    }), 200

# ==================== QR DOWNLOAD ====================

@app.route('/api/eventos/<int:evento_id>/qrcode/download', methods=['GET'])
@jwt_required()
def baixar_qrcode(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    base_url = request.host_url
    qr_url = f"{base_url}cadastro?e={evento.id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png', as_attachment=True, download_name=f'evento_{evento.id}_qrcode.png')

# ==================== ESTÁTICOS ====================

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')
# ==================== PÁGINAS (URLs bonitas) ====================
@app.route('/cadastro')
def page_cadastro():
    return send_from_directory('static', 'cadastro.html')

@app.route('/dashboard')
def page_dashboard():
    return send_from_directory('static', 'dashboard.html')

@app.route('/eventos')
def page_eventos():
    return send_from_directory('static', 'eventos.html')

@app.route('/login')
def page_login():
    return send_from_directory('static', 'login.html')

@app.route('/sucesso')
def page_sucesso():
    return send_from_directory('static', 'sucesso.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

# ==================== ALUNOS (VIEW DO DASHBOARD) ====================

@app.route('/api/alunos', methods=['GET'])
@jwt_required()
def listar_alunos():
    try:
        vendedor_id = current_user_id()
        if vendedor_id is None:
            return jsonify({'erro': 'Token inválido'}), 401

        vendedor = Usuario.query.get(vendedor_id)
        if not vendedor:
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        # ✅ joinedload para evitar N+1
        q = Lead.query.options(joinedload(Lead.evento).joinedload(Evento.escola))
        leads = q.all() if vendedor.tipo_usuario == 'admin' else q.filter(
            (Lead.vendedor_id == vendedor_id) | (Lead.vendedor_id == None)
        ).all()

        alunos = []
        for lead in leads:
            ev = lead.evento
            escola_nome = ev.escola.nome if (ev and ev.escola) else None
            ano_evento = ev.data_evento.year if (ev and ev.data_evento) else None

            alunos.append({
                'id': lead.id,
                'nome': lead.nome_formando,
                'escola': escola_nome,
                'turma': (f"{lead.serie or ''} {lead.letra_turma or ''}").strip() or 'Não informada',
                'ano_formatura': lead.ano_formatura or ano_evento,
                'email': lead.email,
                'whatsapp': lead.whatsapp,
                'responsavel': lead.nome_contato if lead.tipo_cadastro == 'responsavel' else None,
                'foto': f'/static/uploads/{lead.foto}' if lead.foto else None
            })
        return jsonify(alunos), 200
    except Exception as e:
        print(f"❌ Erro em listar_alunos: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': 'Erro ao listar alunos', 'detalhes': str(e)}), 500

# ==================== INIT ====================

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

# --- Auto-init também quando o app é importado (Render/Gunicorn) ---
with app.app_context():
    db.create_all()
    criar_usuario_admin()
    print("✅ DB inicializado (auto-init)")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        criar_usuario_admin()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
