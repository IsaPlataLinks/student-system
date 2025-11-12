from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from PIL import Image, ImageOps
import qrcode
from io import BytesIO
import os
import re
from sqlalchemy import extract, or_
from sqlalchemy.exc import IntegrityError
import cloudinary
import cloudinary.uploader
import cloudinary.api


# ==================== HELPERS/JWT ====================

def current_user_id() -> int | None:
    """Converte o sub do JWT para int com segurança"""
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None

def eh_administrador(usuario):
    """Verifica se um usuário é admin ou dono"""
    return usuario.tipo_usuario in ['admin', 'dono']

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

# 3.5) PROTEÇÃO: impede produção com SQLite efêmero
ENV = os.getenv('FLASK_ENV', 'development')
if ENV == 'production' and not os.getenv('DATABASE_URL'):
    print('\n❌ ERRO CRÍTICO: Produção detectada sem DATABASE_URL!')
    print('   SQLite em container é efêmero (dados desaparecem a cada deploy).')
    print('   Configure DATABASE_URL antes de rodar em produção.')
    import sys
    sys.exit(1)

# 4) Normaliza prefixo do Postgres para SQLAlchemy
if uri.startswith('postgres://'):
    uri = uri.replace('postgres://', 'postgresql+psycopg2://', 1)

# (opcional – só se seu Postgres exigir SSL e a string não trouxer):
# if uri.startswith('postgresql') and 'sslmode=' not in uri:
#     uri += '?sslmode=require'

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,  # Recicla conexões a cada 1 hora
    'pool_pre_ping': True,  # Verifica se conexão está viva antes de usar
    'max_overflow': 20,
}
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'r3-formaturas-secret-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)

# Configurar Cloudinary
cloudinary_url = os.getenv('CLOUDINARY_URL')
if cloudinary_url:
    cloudinary.config(url=cloudinary_url)
    print("[OK] Cloudinary configurado com sucesso")
else:
    print("[AVISO] CLOUDINARY_URL não configurado - uploads podem falhar em produção")

# Pasta de uploads local (apenas para desenvolvimento)
upload_path = 'static/uploads'
app.config['UPLOAD_FOLDER'] = upload_path
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024  # 15MB

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Criar pasta se não existir (apenas para desenvolvimento)
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    print(f"[OK] Pasta de uploads local criada/verificada: {app.config['UPLOAD_FOLDER']}")
except Exception as e:
    print(f"[AVISO] Falha ao criar pasta de uploads local: {str(e)}")


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
    data_evento = db.Column(db.Date, nullable=False)  # OBRIGATÓRIA
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
    
    @property
    def dias_desde_evento(self):
        """Calcula dias desde a data do evento"""
        if not self.data_evento:
            return None
        from datetime import datetime, timezone
        hoje = datetime.now().date()
        return (hoje - self.data_evento).days
    
    @property
    def status_automatico(self):
        """
        Calcula status automaticamente:
        - Se data_evento não está definida: 'pendente'
        - Se passou 7 dias da data: 'finalizado'
        - Se passou menos de 7 dias: 'ativo'
        """
        if not self.data_evento:
            return 'pendente'
        
        dias = self.dias_desde_evento
        if dias is None:
            return 'pendente'
        
        # Se passou 7 dias, está finalizado
        if dias >= 7:
            return 'finalizado'
        
        # Se ainda não chegou a data ou passou menos de 7 dias, está ativo
        if dias >= 0:
            return 'ativo'
        
        # Se ainda não chegou a data do evento
        return 'agendado'
    
    def atualizar_status_automatico(self):
        """Atualiza o status baseado na data do evento"""
        novo_status = self.status_automatico
        if self.status != novo_status:
            self.status = novo_status
            db.session.commit()
            return True
        return False
    
    @property
    def qr_code_valido(self):
        """QR code é válido apenas se status for 'ativo' ou 'agendado'"""
        return self.status_automatico in ['ativo', 'agendado']

class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=False)

    serie = db.Column(db.String(15))
    letra_turma = db.Column(db.String(4))
    ano_formatura = db.Column(db.Integer)

    matricula = db.Column(db.String(20), nullable=False)
    nome_formando = db.Column(db.String(100), nullable=False)
    foto = db.Column(db.String(255))
    link_galeria = db.Column(db.String(500))
    descricao_galeria = db.Column(db.Text)

    nome_contato = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    whatsapp = db.Column(db.String(20), nullable=False)
    tipo_cadastro = db.Column(db.String(20))

    cep = db.Column(db.String(10))
    endereco = db.Column(db.String(300))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(100))
    tipo_imovel = db.Column(db.String(20))

    status_lead = db.Column(db.String(20), default='novo')
    observacoes = db.Column(db.Text)
    data_contato = db.Column(db.DateTime)
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('matricula', 'evento_id', name='unique_matricula_evento'),
    )

class GaleriaFoto(db.Model):
    __tablename__ = 'galeria_fotos'
    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)  # opcional
    nome_arquivo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    evento = db.relationship('Evento', backref='galeria_fotos')
    lead = db.relationship('Lead', backref='fotos_galeria')

# ==================== VALIDAÇÕES ====================

def validar_nome(nome: str) -> bool:
    return bool(nome and len(nome) >= 3 and re.match(r"^[a-zA-ZÀ-ÿ\s']+$", nome))

def validar_email(email: str) -> bool:
    return bool(email and re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email))

def validar_whatsapp(whatsapp: str) -> bool:
    # Aceita apenas dígitos (10 ou 11 dígitos) OU formato (11) 98765-4321
    if not whatsapp:
        return False
    # Remove tudo que não é dígito
    digitos = re.sub(r'\D', '', whatsapp)
    # Valida: 10 ou 11 dígitos
    return len(digitos) in [10, 11]

def validar_cep(cep: str) -> bool:
    return bool((not cep) or re.match(r'^\d{5}-\d{3}$', cep))

def validar_serie(serie: str) -> bool:
    series_validas = ['1º ano', '2º ano', '3º ano', '4º ano', '5º ano', '6º ano', '7º ano', '8º ano', '9º ano', '1º ano EM', '2º ano EM', '3º ano EM']
    return serie in series_validas

def validar_letra_turma(letra: str) -> bool:
    return bool(letra and len(letra) <= 4 and letra.isalnum())

def validar_matricula(matricula: str) -> bool:
    if not matricula:
        return False
    matricula = matricula.strip().replace(' ', '')
    # Aceita 1 a 10 dígitos numéricos
    return matricula.isdigit() and 1 <= len(matricula) <= 10

def corrigir_orientacao_exif(img):
    """Corrige a orientação da imagem baseado em dados EXIF"""
    try:
        from PIL import ExifTags
        # Tenta ler EXIF
        exif_data = img._getexif()
        if not exif_data:
            return img
        
        # Procura a tag de orientação
        orientation_tag = None
        for tag, name in ExifTags.TAGS.items():
            if name == 'Orientation':
                orientation_tag = tag
                break
        
        if not orientation_tag:
            return img
        
        orientation = exif_data.get(orientation_tag, 1)
        
        # Aplica rotação conforme orientação EXIF
        if orientation == 2:
            img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        elif orientation == 3:
            img = img.rotate(180, expand=True)
        elif orientation == 4:
            img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        elif orientation == 5:
            img = img.rotate(90, expand=True)
            img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        elif orientation == 6:
            img = img.rotate(-90, expand=True)
        elif orientation == 7:
            img = img.rotate(-90, expand=True)
            img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        elif orientation == 8:
            img = img.rotate(90, expand=True)
    
    except Exception as e:
        print(f"[AVISO] Erro ao corrigir EXIF: {str(e)}")
    
    return img

def processar_foto(file):
     """
     Processa foto do lead (com crop e resize para 300x400)
     Salva LOCALMENTE no Render E NO Cloudinary (ambos obrigatórios)
     Retorna URL HTTPS completa do Cloudinary
     """
     if not file:
         return None

     filename = secure_filename(file.filename or 'foto.jpg')
     timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
     nome_arquivo = f"{timestamp}_{filename}"

     print(f"[DEBUG] Processando foto do lead: {file.filename}")
     
     # Caminho local de salvamento
     local_path = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
     os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
     
     try:
         file.save(local_path)
         print(f"[OK] Arquivo salvo localmente: {local_path}")
     except Exception as e:
         print(f"[ERRO] Falha ao salvar arquivo local: {str(e)}")
         raise

     # Abre com PIL para redimensionamento e correção de orientação
     cloudinary_url = None
     try:
         with Image.open(local_path) as img:
             # Corrige orientação EXIF
             img = corrigir_orientacao_exif(img)
             
             if img.mode != 'RGB':
                 img = img.convert('RGB')
             
             width, height = img.size
             target_width, target_height = 300, 400
             aspect_ratio = target_width / target_height  # 0.75 (3x4)
             
             # Calcula crop inteligente mantendo aspect ratio
             current_ratio = width / height
             
             if current_ratio > aspect_ratio:
                 # Imagem muito larga - croppa os lados
                 new_width = int(height * aspect_ratio)
                 left = (width - new_width) // 2
                 img = img.crop((left, 0, left + new_width, height))
             else:
                 # Imagem muito alta - croppa o topo e parte inferior
                 new_height = int(width / aspect_ratio)
                 # Prioriza a parte superior (rosto geralmente está acima do centro)
                 top = int(height * 0.15)  # começa 15% do topo
                 img = img.crop((0, top, width, top + new_height))
             
             # Redimensiona para o tamanho final (300x400)
             img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
             img.save(local_path, 'JPEG', quality=85, optimize=True)
         
         print(f"[OK] Foto processada e salva localmente: {local_path}")
         
         # ✅ Upload para Cloudinary (obrigatório)
         if os.getenv('CLOUDINARY_URL'):
             try:
                 response = cloudinary.uploader.upload(
                     local_path,
                     folder='fotos-alunos',
                     resource_type='image',
                     use_filename=True,
                     unique_filename=False,
                     overwrite=True
                 )
                 # Retorna a URL HTTPS completa da foto
                 cloudinary_url = response.get('secure_url')
                 if not cloudinary_url:
                     cloudinary_url = response.get('url', '').replace('http://', 'https://')
                 
                 print(f"[✅ OK] Foto salva LOCALMENTE e no Cloudinary: {cloudinary_url}")
                 return cloudinary_url
             except Exception as e:
                 print(f"[⚠️ AVISO] Falha ao fazer upload para Cloudinary: {str(e)}")
                 print(f"[✅ OK] Foto permanece salva localmente: {local_path}")
                 # Retorna URL local como fallback
                 return f'/uploads/{nome_arquivo}'
         else:
             print(f"[⚠️ AVISO] CLOUDINARY_URL não configurado, foto salva APENAS localmente")
             return f'/uploads/{nome_arquivo}'
     
     except Exception as e:
         print(f"[ERRO] Erro ao processar imagem: {str(e)}")
         # Se sobrou arquivo local, manter para fallback
         if os.path.exists(local_path):
             print(f"[✅] Arquivo local preservado para fallback: {local_path}")
             return f'/uploads/{nome_arquivo}'
         raise

def processar_foto_galeria(file):
     """
     Processa foto para galeria (sem redimensionar, apenas otimiza)
     Salva LOCALMENTE no Render E NO Cloudinary (ambos obrigatórios)
     Retorna URL HTTPS completa do Cloudinary
     """
     if not file:
         return None

     filename = secure_filename(file.filename or 'foto.jpg')
     timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
     nome_arquivo = f"{timestamp}_{filename}"

     print(f"[DEBUG] Processando foto para galeria: {file.filename}")
     
     # Caminho local de salvamento
     local_path = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
     os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
     
     try:
         file.save(local_path)
         print(f"[OK] Arquivo salvo localmente: {local_path}")
     except Exception as e:
         print(f"[ERRO] Falha ao salvar arquivo local: {str(e)}")
         raise

     # Otimizar apenas qualidade (sem redimensionar)
     cloudinary_url = None
     try:
         with Image.open(local_path) as img:
             if img.mode != 'RGB':
                 img = img.convert('RGB')
             img.save(local_path, 'JPEG', quality=90, optimize=True)
         
         print(f"[OK] Foto de galeria otimizada e salva localmente: {local_path}")
         
         # ✅ Upload para Cloudinary (obrigatório)
         if os.getenv('CLOUDINARY_URL'):
             try:
                 response = cloudinary.uploader.upload(
                     local_path,
                     folder='fotos-galeria',
                     resource_type='image',
                     use_filename=True,
                     unique_filename=False,
                     overwrite=True
                 )
                 
                 cloudinary_url = response.get('secure_url')
                 if not cloudinary_url:
                     cloudinary_url = response.get('url', '').replace('http://', 'https://')
                 
                 print(f"[✅ OK] Foto salva LOCALMENTE e no Cloudinary: {cloudinary_url}")
                 return cloudinary_url
             except Exception as e:
                 print(f"[⚠️ AVISO] Falha ao fazer upload para Cloudinary: {str(e)}")
                 print(f"[✅ OK] Foto permanece salva localmente: {local_path}")
                 # Retorna URL local como fallback
                 return f'/uploads/{nome_arquivo}'
         else:
             print(f"[⚠️ AVISO] CLOUDINARY_URL não configurado, foto salva APENAS localmente")
             return f'/uploads/{nome_arquivo}'
     
     except Exception as e:
         print(f"[ERRO] Erro ao processar foto galeria: {str(e)}")
         # Se sobrou arquivo local, manter para fallback
         if os.path.exists(local_path):
             print(f"[✅] Arquivo local preservado para fallback: {local_path}")
             return f'/uploads/{nome_arquivo}'
         raise

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

# ==================== CLEANUP ====================

@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    """
    Reset TOTAL do banco de dados - deleta todas as tabelas e reseta sequências
    Requer header de autenticação: X-Cleanup-Token
    """
    token = request.headers.get('X-Cleanup-Token', '')
    cleanup_token = os.getenv('CLEANUP_TOKEN', 'cleanup-2024-secret')
    
    if token != cleanup_token:
        print(f"[ERRO] Tentativa de cleanup com token inválido: {token}")
        return jsonify({'erro': 'Token inválido'}), 401
    
    try:
        print("\n[CLEANUP] Iniciando RESET TOTAL do banco de dados...")
        from sqlalchemy import text
        
        # 1. Contar antes de deletar
        galeria_count = GaleriaFoto.query.count()
        leads_count = Lead.query.count()
        eventos_count = Evento.query.count()
        escolas_count = Escola.query.count()
        usuarios_count = Usuario.query.count()
        
        # 2. Deletar todos os dados das tabelas (ordem importa: FK dependencies)
        GaleriaFoto.query.delete()
        db.session.commit()
        print(f"[OK] {galeria_count} fotos de galeria deletadas")
        
        Lead.query.delete()
        db.session.commit()
        print(f"[OK] {leads_count} leads deletados")
        
        Evento.query.delete()
        db.session.commit()
        print(f"[OK] {eventos_count} eventos deletados")
        
        Escola.query.delete()
        db.session.commit()
        print(f"[OK] {escolas_count} escolas deletadas")
        
        # Deletar todos EXCETO admin
        Usuario.query.filter(Usuario.login != 'admin').delete()
        db.session.commit()
        print(f"[OK] {usuarios_count - 1} usuários deletados (admin preservado)")
        
        # 3. RESETAR AUTO-INCREMENT (para SQLite e PostgreSQL)
        try:
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            if 'sqlite' in db_url:
                # SQLite: resetar sequences
                db.session.execute(text("DELETE FROM sqlite_sequence WHERE name='galeria_fotos'"))
                db.session.execute(text("DELETE FROM sqlite_sequence WHERE name='leads'"))
                db.session.execute(text("DELETE FROM sqlite_sequence WHERE name='eventos'"))
                db.session.execute(text("DELETE FROM sqlite_sequence WHERE name='escolas'"))
                db.session.execute(text("DELETE FROM sqlite_sequence WHERE name='usuarios'"))
            elif 'postgresql' in db_url:
                # PostgreSQL: resetar sequences
                db.session.execute(text("ALTER SEQUENCE galeria_fotos_id_seq RESTART WITH 1"))
                db.session.execute(text("ALTER SEQUENCE leads_id_seq RESTART WITH 1"))
                db.session.execute(text("ALTER SEQUENCE eventos_id_seq RESTART WITH 1"))
                db.session.execute(text("ALTER SEQUENCE escolas_id_seq RESTART WITH 1"))
                db.session.execute(text("ALTER SEQUENCE usuarios_id_seq RESTART WITH 1"))
            db.session.commit()
            print("[OK] Auto-increment resetado")
        except Exception as seq_err:
            print(f"[AVISO] Erro ao resetar auto-increment: {str(seq_err)}")
        
        # 4. Limpar Cloudinary
        cloudinary_deleted = 0
        if os.getenv('CLOUDINARY_URL'):
            try:
                resultado = cloudinary.api.resources(
                    type='upload',
                    prefix='fotos-alunos/',
                    max_results=500
                )
                fotos = resultado.get('resources', [])
                for foto in fotos:
                    cloudinary.api.delete_resources([foto['public_id']])
                    cloudinary_deleted += 1
                print(f"[OK] {cloudinary_deleted} fotos do Cloudinary deletadas")
            except Exception as e:
                print(f"[AVISO] Erro ao limpar Cloudinary: {str(e)}")
        
        print("[OK] RESET TOTAL concluído com sucesso!\n")
        
        return jsonify({
            'mensagem': 'Banco de dados resetado com sucesso!',
            'escolas_deletadas': escolas_count,
            'eventos_deletados': eventos_count,
            'leads_deletados': leads_count,
            'galeria_deletada': galeria_count,
            'usuarios_deletados': usuarios_count - 1,
            'cloudinary_deletado': cloudinary_deleted
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERRO] Falha no reset: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'erro': 'Erro ao resetar',
            'detalhes': str(e)
        }), 500

# ==================== RESET DB ====================

@app.route('/api/reset-db', methods=['POST'])
def reset_database():
    """
    Reseta o banco de dados (deleta todos os dados e recria as tabelas)
    Requer header de autenticação: X-Reset-Token
    """
    token = request.headers.get('X-Reset-Token', '')
    reset_token = os.getenv('RESET_TOKEN', 'reset-2024-secret')
    
    if token != reset_token:
        print(f"[ERRO] Tentativa de reset com token inválido: {token}")
        return jsonify({'erro': 'Token inválido'}), 401
    
    try:
        print("\n[RESET] Iniciando reset do banco de dados...")
        
        # Deletar todos os dados
        db.drop_all()
        print("[OK] Todas as tabelas deletadas")
        
        # Recriar tabelas
        db.create_all()
        print("[OK] Tabelas recriadas")
        
        # Criar admin padrão
        admin = Usuario(
            nome='Administrador',
            login='admin',
            senha_hash=generate_password_hash('admin123'),
            tipo_usuario='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("[OK] Usuário admin criado")
        
        print("[OK] Reset concluído com sucesso!\n")
        
        return jsonify({
            'mensagem': 'Banco de dados resetado com sucesso!',
            'usuario_admin': 'admin',
            'senha_admin': 'admin123'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERRO] Falha no reset: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'erro': 'Erro ao resetar banco de dados',
            'detalhes': str(e)
        }), 500

# ==================== DIAGNÓSTICO ====================

@app.route('/api/diagnostico', methods=['GET'])
def diagnostico():
    """Endpoint de diagnóstico para verificar estado do sistema"""
    from datetime import datetime, date
    from sqlalchemy import inspect
    
    print(f"\n[DIAGNOSTICO] Requisição recebida em {datetime.now()}")
    
    try:
        hoje = date.today()
        
        # Verificar se as colunas faltantes existem
        inspector = inspect(db.engine)
        colunas_leads = [col['name'] for col in inspector.get_columns('leads')]
        colunas_esperadas = ['numero', 'complemento', 'tipo_imovel', 'ano_formatura']
        colunas_faltantes = [col for col in colunas_esperadas if col not in colunas_leads]
        
        # Contar dados
        total_usuarios = Usuario.query.count()
        total_escolas = Escola.query.count()
        total_eventos = Evento.query.count()
        total_leads = Lead.query.count()
        
        # Eventos por status
        eventos_data = []
        for evt in Evento.query.all():
            evt.atualizar_status_automatico()
            eventos_data.append({
                'id': evt.id,
                'escola': evt.escola.nome if evt.escola else 'N/A',
                'data': evt.data_evento.isoformat() if evt.data_evento else None,
                'status_auto': evt.status_automatico,
                'total_leads': len(evt.leads)
            })
        
        # Leads recentes
        leads_recentes = []
        for lead in Lead.query.order_by(Lead.criado_em.desc()).limit(5).all():
            foto_existe = False
            if lead.foto:
                foto_path = os.path.join(app.config['UPLOAD_FOLDER'], lead.foto)
                foto_existe = os.path.exists(foto_path)
            
            leads_recentes.append({
                'id': lead.id,
                'nome': lead.nome_formando,
                'email': lead.email,
                'criado_em': lead.criado_em.isoformat() if lead.criado_em else None,
                'foto': lead.foto,
                'foto_existe': foto_existe
            })
        
        resultado = {
            'timestamp': datetime.now().isoformat(),
            'hoje': hoje.isoformat(),
            'database': {
                'uri': str(app.config['SQLALCHEMY_DATABASE_URI'])[:50] + '...',
                'colunas_leads_esperadas': colunas_esperadas,
                'colunas_leads_existentes': colunas_leads,
                'colunas_faltantes': colunas_faltantes,
                'status': '❌ ERRO: Colunas faltando!' if colunas_faltantes else '✅ OK: Todas as colunas presentes'
            },
            'totais': {
                'usuarios': total_usuarios,
                'escolas': total_escolas,
                'eventos': total_eventos,
                'leads': total_leads
            },
            'eventos': eventos_data,
            'leads_recentes': leads_recentes,
            'pasta_uploads': app.config['UPLOAD_FOLDER'],
            'pasta_exists': os.path.exists(app.config['UPLOAD_FOLDER'])
        }
        
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            arquivos = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f != '.gitkeep']
            resultado['arquivos_upload'] = len(arquivos)
            resultado['arquivos'] = arquivos[:10]  # Primeiros 10
        
        print(f"[OK] Diagnóstico concluído: {total_leads} leads, {total_eventos} eventos")
        return jsonify(resultado), 200
        
    except Exception as e:
        print(f"[ERRO] Diagnóstico falhou: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': 'Erro ao executar diagnóstico', 'detalhes': str(e)}), 500

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
    if user.tipo_usuario not in ['admin', 'dono']:
        return jsonify({'erro': 'Apenas administradores e donos podem criar eventos'}), 403

    data = request.get_json(silent=True) or {}

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
        db.session.flush()  # Garante que a escola tem ID antes de usar no Evento

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
        print(f"[DEBUG] Antes de commit - Evento: id={evento.id}, escola_id={evento.escola_id}, data={evento.data_evento}")
        db.session.add(evento)
        db.session.commit()
        print(f"[OK] Evento criado com sucesso! ID: {evento.id}, Escola: {evento.escola.nome if evento.escola else 'None'}")
        
        # Debug: verificar se foi salvo
        evento_test = Evento.query.get(evento.id)
        print(f"[DEBUG] Verificacao pos-commit: evento {evento.id} existe? {evento_test is not None}")
    except IntegrityError as ie:
        db.session.rollback()
        print(f"[ERRO] IntegrityError ao criar evento: {str(ie)}")
        return jsonify({'erro': 'Já existe um evento para esta escola nesta data'}), 409
    except Exception as e:
        db.session.rollback()
        print(f"[ERRO] Erro ao criar evento: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': 'Erro ao criar evento', 'detalhes': str(e)}), 500

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
        # Debug: contar eventos brutos
        total_raw = db.session.query(Evento).count()
        print(f"[DEBUG] Total de eventos no BD (raw count): {total_raw}")
        
        # Buscar eventos com escolas carregadas usando JOIN
        eventos = (db.session.query(Evento)
                   .outerjoin(Escola)
                   .order_by(Evento.criado_em.desc())
                   .all())
        
        print(f"[OK] Eventos encontrados: {len(eventos)}")
        for ev in eventos:
            print(f"  - ID: {ev.id}, Escola: {ev.escola.nome if ev.escola else 'None'}, Data: {ev.data_evento}")

        payload = []
        for e in eventos:
            try:
                # Atualizar status automaticamente
                if hasattr(e, 'atualizar_status_automatico'):
                    e.atualizar_status_automatico()
                
                dias_restantes = 0
                if e.dias_desde_evento is not None and 0 <= e.dias_desde_evento < 7:
                    dias_restantes = 7 - e.dias_desde_evento
                
                # Trata escola nula ou erro ao acessá-la
                escola_nome = None
                try:
                    if e.escola:
                        escola_nome = e.escola.nome
                except Exception as escola_err:
                    print(f"Aviso: erro ao acessar escola do evento {e.id}: {str(escola_err)}")
                
                payload.append({
                    'id': e.id,
                    'escola': escola_nome,
                    'tipo_formatura': e.tipo_formatura,
                    'data_evento': e.data_evento.isoformat() if e.data_evento else None,
                    'local_evento': e.local_evento,
                    'status': e.status_automatico,
                    'status_original': e.status,
                    'total_leads': len(e.leads) if hasattr(e, 'leads') else 0,
                    'galeria_count': len(e.galeria_fotos) if hasattr(e, 'galeria_fotos') else 0,
                    'dias_restantes': dias_restantes,
                    'qr_valido': e.qr_code_valido,
                    'qr_url': f"{request.host_url}cadastro?e={e.id}"
                })
            except Exception as event_err:
                print(f"Aviso: erro ao processar evento {getattr(e, 'id', '?')}: {str(event_err)}")
                continue
        
        return jsonify(payload), 200
    except Exception as e:
        print(f"[ERRO] Erro em listar_eventos: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': 'Erro ao listar eventos', 'detalhes': str(e)}), 500

@app.route('/api/eventos/<int:evento_id>', methods=['DELETE'])
@jwt_required()
def deletar_evento(evento_id):
    """
    Deleta um evento e todos seus dados associados (leads, fotos, galeria)
    Apenas admin ou dono pode deletar
    """
    usuario_id = current_user_id()
    if usuario_id is None:
        return jsonify({'erro': 'Token inválido'}), 401
    
    usuario = Usuario.query.get(usuario_id)
    if not usuario or not eh_administrador(usuario):
        return jsonify({'erro': 'Apenas administradores podem deletar eventos'}), 403
    
    evento = Evento.query.get_or_404(evento_id)
    
    try:
        # Guardar informações ANTES de deletar
        nome_escola = evento.escola.nome if evento.escola else 'N/A'
        total_leads = len(evento.leads)
        total_fotos = len(evento.galeria_fotos)
        
        # Deletar arquivos de foto dos leads (apenas locais)
        for lead in evento.leads:
            if lead.foto:
                # Se não for do Cloudinary, deletar arquivo local
                if not lead.foto.startswith('fotos-alunos/'):
                    foto_path = os.path.join(app.config['UPLOAD_FOLDER'], lead.foto)
                    if os.path.exists(foto_path):
                        try:
                            os.remove(foto_path)
                            print(f"✅ Foto do lead {lead.id} deletada")
                        except Exception as e:
                            print(f"⚠️  Erro ao deletar foto: {str(e)}")
                else:
                    print(f"[INFO] Foto do lead {lead.id} é do Cloudinary: {lead.foto}")
        
        # Deletar arquivos da galeria
        for foto_galeria in evento.galeria_fotos:
            foto_path = os.path.join(app.config['UPLOAD_FOLDER'], foto_galeria.nome_arquivo)
            if os.path.exists(foto_path):
                try:
                    os.remove(foto_path)
                    print(f"✅ Foto da galeria {foto_galeria.id} deletada")
                except Exception as e:
                    print(f"⚠️  Erro ao deletar foto da galeria: {str(e)}")
        
        # Deletar leads (cascata)
        for lead in evento.leads:
            db.session.delete(lead)
        
        # Deletar galeria (cascata)
        for foto_galeria in evento.galeria_fotos:
            db.session.delete(foto_galeria)
        
        # Deletar evento
        db.session.delete(evento)
        db.session.commit()
        
        print(f"✅ Evento {evento_id} deletado com sucesso por admin {usuario_id}")
        
        return jsonify({
            'mensagem': f'Evento {evento_id} deletado com sucesso!',
            'escola': nome_escola,
            'leads_deletados': total_leads,
            'fotos_deletadas': total_fotos
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao deletar evento {evento_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'erro': 'Erro ao deletar evento',
            'detalhes': str(e)
        }), 500

@app.route('/api/eventos/<int:evento_id>', methods=['GET'])
def buscar_evento(evento_id):
    try:
        print(f"[DEBUG] Buscando evento {evento_id}")
        # Buscar evento sem joinedload para evitar erro se escola for None
        evento = Evento.query.filter_by(id=evento_id).first()
        
        if not evento:
            print(f"[ERRO] Evento {evento_id} não encontrado")
            return jsonify({'erro': 'Evento não encontrado'}), 404
        
        # Atualizar status automaticamente
        if hasattr(evento, 'atualizar_status_automatico'):
            evento.atualizar_status_automatico()
        
        print(f"[OK] Evento {evento_id} encontrado. Status automático: {evento.status_automatico}")
        
        # REMOVIDO: Filtro de status que impedia acesso a eventos finalizados
        # Agora permite visualizar evento mesmo se status for 'finalizado'
        
        dias_restantes = 0
        if evento.dias_desde_evento is not None and 0 <= evento.dias_desde_evento < 7:
            dias_restantes = 7 - evento.dias_desde_evento
        
        # Trata escola nula ou erro ao acessá-la
        escola_info = {
            'id': None,
            'nome': None,
            'cidade': None,
            'estado': None
        }
        try:
            if evento.escola:
                escola_info = {
                    'id': evento.escola.id,
                    'nome': evento.escola.nome,
                    'cidade': evento.escola.cidade,
                    'estado': evento.escola.estado
                }
        except Exception as escola_err:
            print(f"Aviso: erro ao acessar escola do evento {evento.id}: {str(escola_err)}")
        
        return jsonify({
            'id': evento.id,
            'escola': escola_info,
            'data_evento': evento.data_evento.isoformat() if evento.data_evento else None,
            'local_evento': evento.local_evento,
            'endereco_evento': evento.endereco_evento,
            'tipo_formatura': evento.tipo_formatura,
            'status': evento.status_automatico,
            'dias_restantes': dias_restantes,
            'qr_valido': evento.qr_code_valido
        }), 200
    except Exception as e:
        print(f"❌ Erro em buscar_evento: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': 'Erro ao buscar evento', 'detalhes': str(e)}), 500


# ==================== QR CODE PÚBLICO ====================
@app.route('/api/eventos/<int:evento_id>/qrcode', methods=['GET'])
def gerar_qrcode(evento_id):
    print(f"[DEBUG] Gerando QR code para evento {evento_id}")
    evento = Evento.query.get_or_404(evento_id)
    
    # Atualizar status automaticamente
    evento.atualizar_status_automatico()
    
    # LOG: Verificar status do QR
    print(f"[OK] QR code valido? {evento.qr_code_valido} | Status: {evento.status_automatico}")
    
    # REMOVIDO: Filtro que impedia gerar QR code para eventos finalizados
    # Agora gera QR code mesmo se evento estiver finalizado

    base_url = request.host_url.rstrip('/')     # evita //cadastro
    qr_url = f"{base_url}/cadastro?e={evento.id}"

    print(f"[DEBUG] QR URL: {qr_url}")

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
    print(f"[OK] QR code gerado com sucesso para evento {evento_id}")
    return send_file(buffer, mimetype='image/png', download_name=f'qrcode-evento-{evento_id}.png')


# ==================== CADASTRO PÚBLICO ====================

@app.route('/api/cadastro', methods=['POST'])
def cadastrar_lead():
    try:
        data = request.form
        evento_id = data.get('evento_id')
        if not evento_id:
            print(f"[ERRO] Evento não identificado no cadastro")
            print(f"[DEBUG] Form data keys: {list(data.keys())}")
            print(f"[DEBUG] Form data: {dict(data)}")
            return jsonify({'erro': 'Evento não identificado'}), 400

        evento = Evento.query.get(evento_id)
        if not evento:
            print(f"[ERRO] Evento {evento_id} não encontrado no cadastro")
            return jsonify({'erro': 'Evento não encontrado'}), 404
        
        # Atualizar status automaticamente
        evento.atualizar_status_automatico()
        print(f"[OK] Cadastro iniciado para evento {evento_id}. Status: {evento.status_automatico}")
        
        # REMOVIDO: Filtro que impedia cadastro em eventos finalizados
        # Agora permite cadastro mesmo se evento estiver finalizado

        matricula = (data.get('matricula') or '').strip().upper()
        nome_formando = data.get('nome_formando')
        nome_contato = data.get('nome_contato')
        email = data.get('email')
        whatsapp = data.get('whatsapp')
        tipo_cadastro = data.get('tipo_cadastro')
        serie = data.get('serie')
        turma = (data.get('turma') or '').strip().upper()

        print(f"[DEBUG] Dados recebidos: matricula={matricula}, nome={nome_formando}, email={email}")

        if not all([matricula, nome_formando, nome_contato, email, whatsapp, serie, turma]):
            print(f"[ERRO] Campos obrigatórios faltando")
            return jsonify({'erro': 'Preencha todos os campos obrigatórios'}), 400
        if not validar_matricula(matricula):
            print(f"[ERRO] Matrícula inválida: {matricula}")
            return jsonify({'erro': 'Matrícula inválida! Use apenas números (máximo 10 dígitos)'}), 400

        if Lead.query.filter_by(matricula=matricula, evento_id=evento_id).first():
            print(f"[ERRO] Matrícula {matricula} já existe no evento {evento_id}")
            return jsonify({'erro': f'Matrícula {matricula} já cadastrada neste evento!'}), 400
        if not validar_nome(nome_formando):
            print(f"[ERRO] Nome do formando inválido: {nome_formando}")
            return jsonify({'erro': 'Nome do formando inválido! Use apenas letras'}), 400
        if not validar_nome(nome_contato):
            print(f"[ERRO] Nome do contato inválido: {nome_contato}")
            return jsonify({'erro': 'Seu nome inválido! Use apenas letras'}), 400
        if not validar_email(email):
            print(f"[ERRO] E-mail inválido: {email}")
            return jsonify({'erro': 'E-mail inválido'}), 400
        if not validar_whatsapp(whatsapp):
            print(f"[ERRO] WhatsApp inválido: {whatsapp}")
            return jsonify({'erro': 'WhatsApp inválido! Formato: (11) 98765-4321'}), 400

        foto_filename = None
        if 'foto' in request.files and request.files['foto'].filename:
            try:
                foto_filename = processar_foto(request.files['foto'])
                print(f"[OK] Foto processada: {foto_filename}")
            except Exception as foto_err:
                print(f"[AVISO] Erro ao processar foto: {str(foto_err)}")

        lead = Lead(
            evento_id=evento_id,
            matricula=matricula,
            nome_formando=nome_formando,
            nome_contato=nome_contato,
            email=email,
            whatsapp=whatsapp,
            tipo_cadastro=tipo_cadastro,
            serie=serie,
            letra_turma=turma,
            cep=data.get('cep'),
            endereco=data.get('endereco'),
            numero=data.get('numero'),
            complemento=data.get('complemento'),
            tipo_imovel=data.get('tipo_imovel'),
            foto=foto_filename,
            status_lead='novo'
        )
        print(f"[DEBUG] Lead criado em memória: evento_id={lead.evento_id}, matricula={lead.matricula}, nome={lead.nome_formando}, vendedor_id={lead.vendedor_id}")
        db.session.add(lead)
        db.session.commit()

        # Verificar se foi realmente salvo
        lead_test = Lead.query.get(lead.id)
        evento_test = Evento.query.get(evento_id)
        print(f"[OK] Lead {lead.id} cadastrado com sucesso!")
        print(f"     - Evento: {evento_id} -> Total de leads agora: {len(evento_test.leads) if evento_test else 'erro'}")
        print(f"     - Matrícula: {matricula}, Nome: {nome_formando}")
        print(f"     - Foto: {foto_filename}")
        return jsonify({
            'mensagem': 'Cadastro realizado com sucesso!', 
            'id': lead.id, 
            'matricula': matricula,
            'success': True
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERRO no cadastro: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'erro': 'Erro ao processar cadastro',
            'detalhes': str(e)
        }), 500

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

        # Verificar permissão (admin/dono vê tudo, vendedor só seus leads ou sem dono)
        if not eh_administrador(vendedor):
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
                'foto': f'/uploads/{lead.foto}' if lead.foto else None,
                'cep': lead.cep,
                'endereco': lead.endereco,
                'numero': lead.numero,
                'complemento': lead.complemento,
                'tipo_imovel': lead.tipo_imovel,
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

@app.route('/api/leads/<int:lead_id>', methods=['GET'])
@jwt_required()
def obter_lead(lead_id):
    try:
        vendedor_id = current_user_id()
        if vendedor_id is None:
            return jsonify({'erro': 'Token inválido'}), 401
        
        vendedor = Usuario.query.get(vendedor_id)
        if not vendedor:
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        lead = (Lead.query
                .options(joinedload(Lead.evento).joinedload(Evento.escola))
                .filter_by(id=lead_id)
                .first())
        
        if not lead:
            return jsonify({'erro': 'Lead não encontrado'}), 404

        # Verificar permissão (admin/dono vê tudo, vendedor só seus leads ou sem dono)
        if not eh_administrador(vendedor):
            if lead.vendedor_id and lead.vendedor_id != vendedor_id:
                return jsonify({'erro': 'Sem permissão para visualizar este lead'}), 403

        ev = lead.evento
        escola_obj = ev.escola if ev else None
        
        # Processar URL da foto (Cloudinary ou local)
        foto_url = None
        if lead.foto:
            # Se é uma URL completa HTTPS do Cloudinary, usar diretamente
            if lead.foto.startswith('https://res.cloudinary.com/'):
                foto_url = lead.foto
            # Se começa com 'fotos-alunos/', é um public_id do Cloudinary (formato antigo)
            elif lead.foto.startswith('fotos-alunos/'):
                foto_url = cloudinary.CloudinaryResource(lead.foto).build_url()
            else:
                # É um arquivo local
                foto_path = os.path.join(app.config['UPLOAD_FOLDER'], lead.foto)
                if os.path.exists(foto_path):
                    foto_url = f'/uploads/{lead.foto}'
        
        return jsonify({
            'id': lead.id,
            'matricula': lead.matricula,
            'nome_formando': lead.nome_formando,
            'serie': lead.serie,
            'letra_turma': lead.letra_turma,
            'nome_contato': lead.nome_contato,
            'email': lead.email,
            'whatsapp': lead.whatsapp,
            'tipo_cadastro': lead.tipo_cadastro,
            'cep': lead.cep,
            'endereco': lead.endereco,
            'numero': lead.numero,
            'complemento': lead.complemento,
            'tipo_imovel': lead.tipo_imovel,
            'foto': foto_url,
            'link_galeria': lead.link_galeria,
            'descricao_galeria': lead.descricao_galeria,
            'status_lead': lead.status_lead,
            'observacoes': lead.observacoes,
            'evento': {
                'id': ev.id if ev else None,
                'escola': escola_obj.nome if escola_obj else None,
                'cidade': escola_obj.cidade if escola_obj else None,
                'estado': escola_obj.estado if escola_obj else None,
                'tipo_formatura': ev.tipo_formatura if ev else None,
                'data_evento': ev.data_evento.isoformat() if (ev and ev.data_evento) else None,
                'local_evento': ev.local_evento if ev else None
            },
            'criado_em': lead.criado_em.isoformat(),
            'atualizado_em': lead.atualizado_em.isoformat() if lead.atualizado_em else None
        }), 200
    except Exception as e:
        print(f"❌ Erro em obter_lead: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': 'Erro ao buscar lead', 'detalhes': str(e)}), 500

@app.route('/api/leads/<int:lead_id>/foto', methods=['PATCH'])
@jwt_required()
def atualizar_foto_lead(lead_id):
    vendedor_id = current_user_id()
    if vendedor_id is None:
        return jsonify({'erro': 'Token inválido'}), 401

    lead = Lead.query.get_or_404(lead_id)

    if 'foto' not in request.files:
        return jsonify({'erro': 'Nenhuma foto enviada'}), 400

    foto_file = request.files['foto']
    if foto_file.filename == '':
        return jsonify({'erro': 'Arquivo vazio'}), 400

    # Se o lead já tem uma foto, deletar a antiga (apenas se for local)
    if lead.foto:
        # Se começa com 'fotos-alunos/', é do Cloudinary - não deletar
        if not lead.foto.startswith('fotos-alunos/'):
            caminho_antigo = os.path.join(app.config['UPLOAD_FOLDER'], lead.foto)
            if os.path.exists(caminho_antigo):
                try:
                    os.remove(caminho_antigo)
                except Exception as e:
                    print(f"Aviso: não foi possível deletar foto antiga: {str(e)}")
        else:
            # Se é Cloudinary, apenas log
            print(f"[INFO] Foto anterior era Cloudinary: {lead.foto}")

    # Processar e salvar a nova foto
    nome_foto = processar_foto(foto_file)
    lead.foto = nome_foto
    
    try:
        db.session.commit()
        return jsonify({
            'mensagem': 'Foto atualizada com sucesso!',
            'foto': nome_foto
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao atualizar foto: {str(e)}")
        return jsonify({'erro': 'Erro ao atualizar foto'}), 500

@app.route('/api/leads/<int:lead_id>/galeria-link', methods=['PATCH'])
@jwt_required()
def adicionar_galeria_link(lead_id):
    """
    Adiciona/atualiza link de galeria de fotos em nuvem
    
    Payload:
    {
        "link_galeria": "https://photos.google.com/share/...",
        "descricao_galeria": "Fotos da criança - 130 imagens"
    }
    """
    vendedor_id = current_user_id()
    if vendedor_id is None:
        return jsonify({'erro': 'Token inválido'}), 401

    lead = Lead.query.get_or_404(lead_id)
    data = request.get_json() or {}
    
    link = (data.get('link_galeria') or '').strip()
    descricao = (data.get('descricao_galeria') or '').strip()
    
    # Validação básica de URL
    if not link:
        return jsonify({'erro': 'Link da galeria é obrigatório'}), 400
    
    if not link.startswith(('http://', 'https://')):
        return jsonify({'erro': 'Link deve começar com http:// ou https://'}), 400
    
    if len(link) > 500:
        return jsonify({'erro': 'Link muito longo (máximo 500 caracteres)'}), 400
    
    if descricao and len(descricao) > 500:
        return jsonify({'erro': 'Descrição muito longa (máximo 500 caracteres)'}), 400
    
    try:
        lead.link_galeria = link
        lead.descricao_galeria = descricao if descricao else None
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Galeria de fotos vinculada com sucesso!',
            'link_galeria': link,
            'descricao_galeria': descricao
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao adicionar galeria link: {str(e)}")
        return jsonify({'erro': 'Erro ao vincular galeria'}), 500


@app.route('/api/leads/<int:lead_id>/galeria-link', methods=['DELETE'])
@jwt_required()
def remover_galeria_link(lead_id):
    """Remove o link de galeria de um lead"""
    vendedor_id = current_user_id()
    if vendedor_id is None:
        return jsonify({'erro': 'Token inválido'}), 401

    lead = Lead.query.get_or_404(lead_id)
    
    try:
        lead.link_galeria = None
        lead.descricao_galeria = None
        db.session.commit()
        
        return jsonify({'mensagem': 'Galeria removida com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao remover galeria link: {str(e)}")
        return jsonify({'erro': 'Erro ao remover galeria'}), 500

@app.route('/api/eventos/<int:evento_id>/galeria', methods=['POST'])
@jwt_required()
def upload_galeria_foto(evento_id):
    """
    Upload de fotos para galeria do evento
    ✅ Salva diretamente no Cloudinary (padronizado)
    """
    vendedor_id = current_user_id()
    if vendedor_id is None:
        return jsonify({'erro': 'Token inválido'}), 401
    
    evento = Evento.query.get_or_404(evento_id)
    
    if 'fotos' not in request.files:
        return jsonify({'erro': 'Nenhuma foto enviada'}), 400
    
    arquivos = request.files.getlist('fotos')
    if not arquivos:
        return jsonify({'erro': 'Nenhuma foto selecionada'}), 400
    
    fotos_salvas = []
    lead_id = request.form.get('lead_id')
    descricao = request.form.get('descricao', '')
    
    for arquivo in arquivos:
        if arquivo.filename == '':
            continue
        
        # Validar tipo
        tipos_permitidos = {'jpg', 'jpeg', 'png'}
        ext = arquivo.filename.rsplit('.', 1)[1].lower() if '.' in arquivo.filename else ''
        if ext not in tipos_permitidos:
            print(f"[AVISO] Tipo de arquivo não permitido: {ext}")
            continue
        
        try:
            # ✅ Usar processar_foto_galeria() - salva em Cloudinary
            foto_url = processar_foto_galeria(arquivo)
            
            # Registrar no banco com URL Cloudinary
            galeria = GaleriaFoto(
                evento_id=evento_id,
                lead_id=int(lead_id) if lead_id else None,
                nome_arquivo=foto_url,  # ← URL HTTPS Cloudinary
                descricao=descricao
            )
            db.session.add(galeria)
            fotos_salvas.append(foto_url)
            print(f"[OK] Foto galeria adicionada ao banco: {foto_url}")
        except Exception as e:
            print(f"[ERRO] Erro ao processar foto galeria: {str(e)}")
            continue
    
    try:
        db.session.commit()
        return jsonify({
            'mensagem': f'{len(fotos_salvas)} foto(s) salva(s) com sucesso!',
            'fotos': fotos_salvas
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao salvar galeria: {str(e)}")
        return jsonify({'erro': 'Erro ao salvar fotos'}), 500

@app.route('/api/eventos/<int:evento_id>/galeria', methods=['GET'])
@jwt_required()
def listar_galeria(evento_id):
    """
    Lista fotos da galeria do evento
    ✅ Retorna URLs Cloudinary (padronizado)
    """
    fotos = GaleriaFoto.query.filter_by(evento_id=evento_id).order_by(GaleriaFoto.criado_em.desc()).all()
    
    resultado = []
    for foto in fotos:
        # nome_arquivo agora é URL Cloudinary (https://res.cloudinary.com/...)
        foto_url = foto.nome_arquivo
        
        # Fallback para fotos antigas salvas localmente (antes da padronização)
        if not foto_url.startswith('https://'):
            foto_url = f'/uploads/{foto.nome_arquivo}'
            print(f"[AVISO] Foto galeria {foto.id} ainda é local: {foto.nome_arquivo}")
        
        resultado.append({
            'id': foto.id,
            'url': foto_url,
            'nome_arquivo': foto.nome_arquivo,
            'descricao': foto.descricao,
            'lead_id': foto.lead_id,
            'criado_em': foto.criado_em.isoformat()
        })
    
    return jsonify(resultado), 200

@app.route('/api/galeria/<int:foto_id>', methods=['DELETE'])
@jwt_required()
def deletar_galeria_foto(foto_id):
    foto = GaleriaFoto.query.get_or_404(foto_id)
    
    # Deletar arquivo
    caminho = os.path.join(app.config['UPLOAD_FOLDER'], foto.nome_arquivo)
    if os.path.exists(caminho):
        try:
            os.remove(caminho)
        except Exception as e:
            print(f"Aviso: não foi possível deletar arquivo: {str(e)}")
    
    # Deletar registro
    try:
        db.session.delete(foto)
        db.session.commit()
        return jsonify({'mensagem': 'Foto deletada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao deletar foto: {str(e)}")
        return jsonify({'erro': 'Erro ao deletar foto'}), 500

@app.route('/api/leads/<int:lead_id>', methods=['PATCH'])
@jwt_required()
def atualizar_lead(lead_id):
    vendedor_id = current_user_id()
    if vendedor_id is None:
        return jsonify({'erro': 'Token inválido'}), 401

    lead = Lead.query.get_or_404(lead_id)
    data = request.get_json() or {}

    # Campos de contato do responsável
    if 'nome_contato' in data:
        nome = (data['nome_contato'] or '').strip()
        if nome and not validar_nome(nome):
            return jsonify({'erro': 'Nome do responsável inválido! Use apenas letras'}), 400
        lead.nome_contato = nome
    
    if 'email' in data:
        email = (data['email'] or '').strip()
        if email and not validar_email(email):
            return jsonify({'erro': 'E-mail inválido'}), 400
        lead.email = email
    
    if 'whatsapp' in data:
        whatsapp = (data['whatsapp'] or '').strip()
        if whatsapp and not validar_whatsapp(whatsapp):
            return jsonify({'erro': 'WhatsApp inválido! Formato: (11) 98765-4321'}), 400
        lead.whatsapp = whatsapp

    # Dados do formando
    if 'nome_formando' in data:
        nome = (data['nome_formando'] or '').strip()
        if nome and not validar_nome(nome):
            return jsonify({'erro': 'Nome do formando inválido! Use apenas letras'}), 400
        lead.nome_formando = nome
    
    if 'matricula' in data:
        matricula = (data['matricula'] or '').strip().upper()
        if matricula and not validar_matricula(matricula):
            return jsonify({'erro': 'Matrícula inválida! Use apenas números (máximo 10 dígitos)'}), 400
        # Verifica se a nova matrícula já existe para outro lead no mesmo evento
        existente = Lead.query.filter(
            Lead.matricula == matricula,
            Lead.evento_id == lead.evento_id,
            Lead.id != lead_id
        ).first()
        if existente:
            return jsonify({'erro': f'Matrícula {matricula} já cadastrada neste evento!'}), 400
        lead.matricula = matricula
    
    if 'serie' in data:
        serie = (data['serie'] or '').strip()
        if serie and not validar_serie(serie):
            return jsonify({'erro': 'Série inválida!'}), 400
        lead.serie = serie
    
    if 'letra_turma' in data:
        turma = (data['letra_turma'] or '').strip().upper()
        if turma and not validar_letra_turma(turma):
            return jsonify({'erro': 'Turma inválida! Use apenas letras e números'}), 400
        lead.letra_turma = turma
    
    # Endereço e imóvel
    if 'cep' in data:
        cep = (data['cep'] or '').strip()
        if cep and not validar_cep(cep):
            return jsonify({'erro': 'CEP inválido! Use formato: 01310-100'}), 400
        lead.cep = cep
    
    if 'endereco' in data:
        endereco = (data['endereco'] or '').strip()
        if len(endereco) > 300:
            return jsonify({'erro': 'Endereço não pode ter mais que 300 caracteres'}), 400
        lead.endereco = endereco
    
    if 'numero' in data:
        numero = (data['numero'] or '').strip()
        if len(numero) > 10:
            return jsonify({'erro': 'Número não pode ter mais que 10 caracteres'}), 400
        lead.numero = numero
    
    if 'complemento' in data:
        complemento = (data['complemento'] or '').strip()
        if len(complemento) > 100:
            return jsonify({'erro': 'Complemento não pode ter mais que 100 caracteres'}), 400
        lead.complemento = complemento
    
    if 'tipo_imovel' in data:
        tipo_imovel = (data['tipo_imovel'] or '').strip()
        tipos_validos = ['casa', 'apartamento', 'outro']
        if tipo_imovel and tipo_imovel.lower() not in tipos_validos:
            return jsonify({'erro': f'Tipo de imóvel inválido! Opções: {", ".join(tipos_validos)}'}), 400
        lead.tipo_imovel = tipo_imovel.lower() if tipo_imovel else None

    # Status e observações
    if 'status_lead' in data:
        status = (data['status_lead'] or '').strip().lower()
        status_validos = ['novo', 'contatado', 'interessado', 'convertido', 'perdido']
        if status and status not in status_validos:
            return jsonify({'erro': f'Status inválido! Opções: {", ".join(status_validos)}'}), 400
        lead.status_lead = status
    
    if 'observacoes' in data:
        obs = (data['observacoes'] or '').strip()
        if len(obs) > 2000:
            return jsonify({'erro': 'Observações não podem ter mais que 2000 caracteres'}), 400
        lead.observacoes = obs
    
    if data.get('marcar_contato'):
        lead.data_contato = datetime.utcnow()
    if not lead.vendedor_id:
        lead.vendedor_id = vendedor_id

    try:
        db.session.commit()
        return jsonify({'mensagem': 'Lead atualizado com sucesso!'}), 200
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'erro': 'Erro ao atualizar: matrícula duplicada ou conflito de dados'}), 409
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao atualizar lead: {str(e)}")
        return jsonify({'erro': 'Erro ao atualizar lead'}), 500


@app.route('/api/leads/<int:lead_id>', methods=['DELETE'])
@jwt_required()
def deletar_lead(lead_id):
    """
    Deleta um lead (apenas admin)
    
    Args:
        lead_id: ID do lead a ser deletado
    
    Returns:
        200: Lead deletado com sucesso
        401: Não autenticado
        403: Sem permissão (apenas admin)
        404: Lead não encontrado
        500: Erro ao deletar
    """
    usuario_id = current_user_id()
    if usuario_id is None:
        return jsonify({'erro': 'Token inválido'}), 401
    
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    # Apenas admin/dono pode deletar leads
    if not eh_administrador(usuario):
        return jsonify({'erro': 'Apenas administradores podem deletar leads'}), 403
    
    lead = Lead.query.get(lead_id)
    if not lead:
        return jsonify({'erro': 'Lead não encontrado'}), 404
    
    try:
        # Deletar foto se existir (apenas se for local)
        if lead.foto:
            # Se não for do Cloudinary, deletar arquivo local
            if not lead.foto.startswith('fotos-alunos/'):
                foto_path = os.path.join(app.config['UPLOAD_FOLDER'], lead.foto)
                if os.path.exists(foto_path):
                    os.remove(foto_path)
                    print(f"✅ Foto deletada: {foto_path}")
            else:
                print(f"[INFO] Foto é do Cloudinary, não deletando arquivo local: {lead.foto}")
        
        # Deletar lead
        db.session.delete(lead)
        db.session.commit()
        
        print(f"✅ Lead {lead_id} deletado por admin {usuario_id}")
        return jsonify({'mensagem': 'Lead deletado com sucesso!'}), 200
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao deletar lead: {str(e)}")
        return jsonify({'erro': 'Erro ao deletar lead'}), 500


@app.route('/api/estatisticas', methods=['GET'])
@jwt_required()
def estatisticas():
    vendedor_id = current_user_id()
    if vendedor_id is None:
        return jsonify({'erro': 'Token inválido'}), 401

    vendedor = Usuario.query.get(vendedor_id)
    if not vendedor:
        return jsonify({'erro': 'Usuário não encontrado'}), 404

    leads_query = Lead.query if eh_administrador(vendedor) else Lead.query.filter_by(vendedor_id=vendedor_id)
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

# ==================== GALERIA (CONTAGEM CORRETA) ====================

@app.route('/api/dashboard/fotos-count', methods=['GET'])
@jwt_required()
def contar_fotos_enviadas():
    """
    Conta o total de fotos enviadas da galeria (não confundir com fotos de perfil dos leads)
    """
    try:
        # Contar fotos da galeria
        total_fotos = GaleriaFoto.query.count()
        
        # Contar leads com foto de perfil
        total_leads_com_foto = Lead.query.filter(Lead.foto != None).filter(Lead.foto != '').count()
        
        return jsonify({
            'fotos_galeria': total_fotos,
            'leads_com_foto': total_leads_com_foto,
            'total_fotos': total_fotos + total_leads_com_foto
        }), 200
    except Exception as e:
        print(f"[ERRO] Erro ao contar fotos: {str(e)}")
        return jsonify({'erro': 'Erro ao contar fotos'}), 500

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

@app.route('/uploads/<filename>')
def servir_upload(filename):
    """Serve arquivos do UPLOAD_FOLDER (pode ser local ou volume persistente)"""
    upload_folder = app.config['UPLOAD_FOLDER']
    print(f"[DEBUG] Servindo arquivo: {filename}")
    print(f"[DEBUG] Upload folder: {upload_folder}")
    print(f"[DEBUG] Arquivo existe: {os.path.exists(os.path.join(upload_folder, filename))}")
    return send_from_directory(upload_folder, filename)

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
            print(f"[ERRO] Token inválido ao listar alunos")
            return jsonify({'erro': 'Token inválido'}), 401

        vendedor = Usuario.query.get(vendedor_id)
        if not vendedor:
            print(f"[ERRO] Vendedor {vendedor_id} não encontrado")
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        # Buscar leads simples (sem eager loading que pode quebrar)
        q = Lead.query
        leads = q.all() if eh_administrador(vendedor) else q.filter(
            (Lead.vendedor_id == vendedor_id) | (Lead.vendedor_id == None)
        ).all()

        print(f"[DEBUG] Vendedor {vendedor_id} é admin: {eh_administrador(vendedor)}")
        print(f"[DEBUG] Total de leads encontrados: {len(leads)}")

        alunos = []
        for idx, lead in enumerate(leads):
            try:
                ev = lead.evento
                escola_nome = None
                ano_evento = None
                foto_url = None
                
                if ev:
                    if ev.data_evento:
                        ano_evento = ev.data_evento.year
                    try:
                        if ev.escola:
                            escola_nome = ev.escola.nome
                    except Exception as escola_err:
                        print(f"[AVISO] Erro ao acessar escola do evento {getattr(ev, 'id', '?')}: {str(escola_err)}")
                
                # Gerar URL da foto (Cloudinary ou local)
                if lead.foto:
                    # Se é uma URL completa HTTPS do Cloudinary, usar diretamente
                    if lead.foto.startswith('https://res.cloudinary.com/'):
                        foto_url = lead.foto
                        print(f"[OK] Foto Cloudinary URL completa encontrada para lead {lead.id}: {foto_url}")
                    # Se começa com 'fotos-alunos/', é um public_id do Cloudinary (formato antigo)
                    elif lead.foto.startswith('fotos-alunos/'):
                        foto_url = cloudinary.CloudinaryResource(lead.foto).build_url()
                        print(f"[OK] Foto Cloudinary public_id encontrada para lead {lead.id}: {foto_url}")
                    else:
                        # É um arquivo local
                        foto_path = os.path.join(app.config['UPLOAD_FOLDER'], lead.foto)
                        if os.path.exists(foto_path):
                            foto_url = f'/uploads/{lead.foto}'
                            print(f"[OK] Foto local encontrada para lead {lead.id}: {lead.foto}")
                        else:
                            print(f"[AVISO] Arquivo de foto não encontrado: {foto_path}")
                            # Não retorna URL se arquivo não existe para evitar erro 404

                aluno_data = {
                    'id': lead.id,
                    'nome': lead.nome_formando,
                    'escola': escola_nome,
                    'turma': (f"{lead.serie or ''} {lead.letra_turma or ''}").strip() or 'Não informada',
                    'ano_formatura': lead.ano_formatura or ano_evento,
                    'email': lead.email,
                    'whatsapp': lead.whatsapp,
                    'responsavel': lead.nome_contato if lead.tipo_cadastro == 'responsavel' else None,
                    'foto': foto_url,
                    'criado_em': lead.criado_em.isoformat() if lead.criado_em else None
                }
                
                alunos.append(aluno_data)
                print(f"[OK] Lead {lead.id} ({lead.nome_formando}) adicionado ao resultado")
                
            except Exception as lead_err:
                print(f"[ERRO] Erro ao processar lead {getattr(lead, 'id', '?')}: {str(lead_err)}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"[OK] Total de alunos retornados: {len(alunos)}")
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
        print("[OK] Usuario admin criado: login='admin', senha='admin123'")

# --- Auto-init também quando o app é importado (Render/Gunicorn) ---
def adicionar_colunas_faltantes():
    """Adiciona colunas que faltam na tabela leads (migração automática)"""
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(db.engine)
        colunas = [col['name'] for col in inspector.get_columns('leads')]
        
        print(f"[DEBUG] Colunas existentes em 'leads': {colunas}")
        
        # Lista de colunas a verificar
        colunas_necessarias = {
            'numero': 'VARCHAR(10)',
            'complemento': 'VARCHAR(100)',
            'tipo_imovel': 'VARCHAR(20)',
            'ano_formatura': 'INTEGER'
        }
        
        for coluna, tipo_sql in colunas_necessarias.items():
            if coluna not in colunas:
                print(f"[MIGRAÇÃO] Adicionando coluna '{coluna}' do tipo {tipo_sql}...")
                try:
                    db.session.execute(text(f'ALTER TABLE leads ADD COLUMN {coluna} {tipo_sql}'))
                    db.session.commit()
                    print(f"[OK] Coluna '{coluna}' adicionada com sucesso")
                except Exception as col_err:
                    print(f"[ERRO] Falha ao adicionar coluna '{coluna}': {str(col_err)}")
                    db.session.rollback()
            else:
                print(f"[OK] Coluna '{coluna}' já existe")
                
    except Exception as e:
        print(f"[AVISO] Erro geral ao verificar/adicionar colunas: {str(e)}")
        import traceback
        traceback.print_exc()

def verificar_e_criar_tabelas():
    """Cria todas as tabelas e adiciona colunas faltantes"""
    try:
        db.create_all()
        print("[OK] Todas as tabelas verificadas/criadas")
    except Exception as e:
        print(f"[ERRO] Erro ao criar tabelas: {str(e)}")
        import traceback
        traceback.print_exc()

with app.app_context():
    verificar_e_criar_tabelas()
    criar_usuario_admin()
    adicionar_colunas_faltantes()
    print("[OK] DB inicializado (auto-init)")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        criar_usuario_admin()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
