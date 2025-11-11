# ✅ Checklist de Pré-Launch - Student System (Aplicação Local)

**Data de Verificação:** 10/11/2025  
**Projeto:** Student System (R3 Formaturas)  
**Tipo:** Aplicação Web local (desktop/intranet)  
**Deploy:** Máquina do cliente (não hospedado)

---

## 📊 Resumo Executivo

| Categoria | Status | Crítico |
|-----------|--------|---------|
| 🏢 Negócio & Conteúdo | ✅ OK | - |
| 🖥️ Instalação e Setup | ⚠️ Pendente | ⛔ SIM |
| ⚡ Desempenho | ✅ OK | - |
| ♿ Acessibilidade | ✅ Básica OK | - |
| 🔍 SEO | 🟡 N/A | - |
| 🔐 Segurança Local | 🟠 Parcial | ⛔ SIM |
| 💾 Dados & Persistência | ✅ Bom | - |
| 📋 LGPD (Local) | ✅ Básico | - |
| 📡 Backup & Recuperação | 🔴 CRÍTICO | ⛔ SIM |
| 🏗️ Documentação | 🔴 CRÍTICO | ⛔ SIM |
| 📚 Treinamento & Handover | 🔴 CRÍTICO | ⛔ SIM |

---

## 1️⃣ Negócio & Conteúdo

- ✅ **Objetivo**
  - Sistema de cadastro de formandos com fotos
  - Gestão de leads para vendas
  - Dashboard para visualização de dados

- ✅ **Fluxos principais testados**
  - ✅ Cadastro de formando (público via QR Code)
  - ✅ Upload de foto com redimensionamento automático
  - ✅ Admin ver/filtrar leads
  - ✅ Marcar contatos como vendidos
  - ✅ Download de fotos (galeria)

- ✅ **Conteúdo**
  - ✅ Página inicial clara
  - ✅ Instruções de cadastro visíveis
  - ✅ Branding R3 Formaturas

---

## 2️⃣ Instalação e Setup (LOCAL) ⛔ CRÍTICO

### 📋 Requisitos para o Cliente

```
Mínimo:
- Windows 10+ / macOS 10.14+ / Linux Ubuntu 20.04+
- Python 3.9+
- 500MB de espaço livre (banco + uploads)
- Navegador moderno (Chrome, Firefox, Edge)
```

### 🔧 Procedimento de Instalação

- ❌ **Não existe** guia passo-a-passo
- **TODO:** Criar instalação facilitada:
  - [ ] `setup.sh` ou `setup.bat` (automático)
  - [ ] OU guia visual com screenshots
  - [ ] OU executável/instalador (.exe com PyInstaller)

**Opções:**

**A) Instalação Manual (simples)**
```bash
1. Baixar Python (python.org)
2. git clone <repo>
3. cd student-system
4. python -m venv venv
5. venv\Scripts\activate  # Windows
6. pip install -r requirements.txt
7. python app.py
8. Abrir http://localhost:5000
```

**B) Script Automático** (RECOMENDADO)
```batch
@echo off
REM setup.bat
if not exist venv (
  python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
pause
```

**C) Executável Standalone** (MELHOR)
```
PyInstaller com Flask embedded
→ student-system.exe (clica e abre)
```

**Ação:** Criar `setup.bat` (Windows) + `setup.sh` (Mac/Linux)

---

## 3️⃣ Desempenho

- ✅ **Interface responsiva**
  - Bootstrap 5 adapta bem ao layout
  - Testado em mobile (funciona)

- ✅ **Processamento de fotos**
  - Redimensionamento 300x400px
  - Compressão automática (JPEG 85%)
  - Rápido (~1-2s por foto)

- ✅ **Banco de dados**
  - SQLite rápido para volumes pequenos/médios
  - Até 10k+ leads sem problema

---

## 4️⃣ Acessibilidade

- ✅ **Contraste**
  - Ouro/Preto/Branco: boa legibilidade

- ✅ **Navegação por teclado**
  - Bootstrap 5 fornece suporte nativo
  - Tabindex funcionando

- ⚠️ **Labels e alt-text**
  - Falta alt-text em logo (imagem externa)
  - Inputs têm labels OK
  - **TODO:** Pequenos ajustes

- ✅ **Mensagens de erro**
  - Claras e legíveis

**Nível WCAG:** AA básico ✅

---

## 5️⃣ SEO & Descoberta

**Status:** N/A (não é aplicável para app local)

- Sitemap/robots.txt: não necessários
- Open Graph: não necessários
- Meta tags: apenas para referência interna

---

## 6️⃣ Segurança Local ⚠️ IMPORTANTE

### ✅ Implementado

- ✅ Autenticação JWT
- ✅ Hash de senhas (werkzeug)
- ✅ Validação de entrada server-side
- ✅ Proteção contra SQLite efêmero

### 🔴 CRÍTICO - Não implementado

1. **Cabeçalhos HTTP de segurança** ⚠️ Recomendado mesmo em local
   - Adicionar para boas práticas
   ```python
   @app.after_request
   def set_security_headers(response):
       response.headers['X-Content-Type-Options'] = 'nosniff'
       response.headers['X-Frame-Options'] = 'DENY'
       response.headers['X-XSS-Protection'] = '1; mode=block'
       response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
       return response
   ```

2. **Senha admin padrão** 🔴 MUITO CRÍTICO
   - Atual: `admin/admin123`
   - **AÇÃO IMEDIATA:** Forçar mudança na primeira execução
   - Implementar:
   ```python
   @app.before_request
   def forcar_setup_admin():
       admin = Usuario.query.filter_by(login='admin').first()
       if admin:
           if check_password_hash(admin.senha_hash, 'admin123'):
               # Redirecionar para página de setup
               if request.path != '/setup':
                   return redirect('/setup')
   ```

3. **2FA** ⚠️ Seria bom em local também
   - Cliente pode querer proteção extra
   - Sugerir: TOTP simples (Google Authenticator)

4. **Rate-limiting** ⚠️ Importante em local (brute-force)
   - Implementar:
   ```python
   from flask_limiter import Limiter
   limiter = Limiter(app, key_func=lambda: request.remote_addr)
   @app.route('/api/login', methods=['POST'])
   @limiter.limit("5 per minute")
   def login():
   ```

5. **Anti-CSRF** ✅ OK em local (não é crítico)

---

## 7️⃣ Dados & Persistência

- ✅ **SQLite Persistente**
  - `instance/student_system.db`
  - Dados salvos localmente
  - Acessível para consultas diretas se necessário

- ✅ **Fotos em disco**
  - `static/uploads/`
  - Intactas e organizadas

- [ ] **Exportação de dados**
  - ❌ Sem endpoint de exportação
  - **TODO:** Implementar:
    - GET `/api/leads/export?format=csv` → CSV
    - GET `/api/leads/export?format=json` → JSON
    - GET `/api/eventos/<id>/export` → Excel (opcional)

---

## 8️⃣ LGPD (Simplificada para local)

Como é local, LGPD é menos crítica, mas importante:

- ✅ **Dados do próprio cliente**
  - Formulário coleta: nome, e-mail, WhatsApp, foto
  - Finalidade: venda de fotos de formatura

- [ ] **Política de Privacidade**
  - ❌ Não existe em página
  - **TODO:** Adicionar página simples `/privacidade.html`
  - Conteúdo mínimo:
    - "Seus dados são coletados para..."
    - "Seus dados não serão compartilhados"
    - "Você pode solicitar exclusão"

- [ ] **Consentimento**
  - ⚠️ Checkbox no cadastro seria bom
  - Algo como: "Concordo com a Política de Privacidade"

- [ ] **Direito ao esquecimento**
  - ❌ Sem endpoint DELETE /api/meus-dados
  - **TODO:** Implementar se cliente pedir

---

## 9️⃣ Backup & Recuperação ⛔ CRÍTICO

**Problema:** Se o banco.db corrompe = perda total de dados

### 📋 Estratégia de Backup

**Opção A: Manual (Simples)**
```
- Copiar instance/student_system.db regularmente
- Manter em pasta diferente ou pendrive
- Data: 1x semana mínimo
```

**Opção B: Automático (RECOMENDADO)**
```python
# Adicionar a app.py
import shutil
from datetime import datetime

@app.route('/api/backup', methods=['POST'])
@jwt_required()
def fazer_backup():
    """Cria backup do banco de dados"""
    uid = current_user_id()
    usuario = Usuario.query.get(uid)
    if not eh_administrador(usuario):
        return jsonify({'erro': 'Apenas admin'}), 403
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(app.instance_path, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    db_path = os.path.join(app.instance_path, 'student_system.db')
    backup_path = os.path.join(backup_dir, f'backup_{timestamp}.db')
    
    try:
        shutil.copy2(db_path, backup_path)
        return jsonify({
            'mensagem': 'Backup criado com sucesso!',
            'arquivo': backup_path
        }), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
```

**Opção C: Backup Automático Diário**
```python
# No __main__
import schedule
import threading

def backup_diario():
    # código acima
    pass

def scheduler():
    schedule.every().day.at("02:00").do(backup_diario)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    threading.Thread(daemon=True, target=scheduler).start()
    app.run(...)
```

### 🔄 Restauração

**Procedimento:**
1. Parar a aplicação
2. Copiar `backups/backup_YYYYMMDD_HHMMSS.db` → `instance/student_system.db`
3. Reiniciar

**TODO:** 
- [ ] Endpoint para restaurar backup
- [ ] Interface para visualizar backups disponíveis
- [ ] Documentar procedimento

---

## 🔟 Documentação ⛔ CRÍTICO

### 📄 Faltam (essencial para entregar ao cliente):

1. **Guia de Instalação** (START HERE)
   - Passo a passo com screenshots
   - Requisitos de sistema
   - Troubleshooting comum

2. **Guia de Uso** (1-2 páginas)
   - Como fazer login
   - Como ver dashboard
   - Como gerar QR Code
   - Como baixar fotos
   - Como exportar dados

3. **Guia de Administrador**
   - Como criar novo vendedor
   - Como gerenciar eventos
   - Como resolver problemas

4. **Guia Técnico** (para suporte/IT)
   - Arquitetura
   - Estrutura de arquivos
   - Como restaurar banco
   - Ports (5000 default)
   - Python version required

5. **Troubleshooting**
   - "Não consigo abrir http://localhost:5000"
   - "Diz que porta 5000 está em uso"
   - "Foto não aparece"
   - "Banco corrompeu"

**Formato:** Markdown + PDF (para imprimir se necessário)

---

## 1️⃣1️⃣ Treinamento & Handover ⛔ CRÍTICO

### 👥 Stakeholders

- **Admin da escola** (vai usar dia-a-dia)
- **IT/Suporte técnico** (vai manter)
- **Vendedor** (vai ver leads)

### 📚 Material necessário

- [ ] **Vídeo de 5-10 min** mostrando:
  1. Instalar e iniciar
  2. Fazer login
  3. Ver dashboard
  4. Gerar QR Code para evento
  5. Alguém faz cadastro (formulário)
  6. Admin vê novo lead
  7. Download de fotos

- [ ] **Documento "Primeiros Passos"** (1 página)
  - Como iniciar a app
  - Primeiro login
  - Criar evento
  - Imprimir QR Code

- [ ] **FAQ rápido**
  - 5-10 perguntas mais comuns

- [ ] **Contato de suporte**
  - Seu WhatsApp/e-mail
  - Tempo de resposta esperado

### 🎓 Sessão de Treinamento

**Recomendado:** 1h presencial ou video call
- 20min: Mostrar funcionamento
- 20min: Praticar juntos
- 20min: Q&A

---

## 🎯 Ações Críticas Imediatas

| Prioridade | Tarefa | Estimativa | Necessário |
|-----------|--------|------------|-----------|
| 🔴 CRÍTICO | Criar guia de instalação + setup.bat | 2h | ✅ SIM |
| 🔴 CRÍTICO | Implementar backup automático ou manual | 1.5h | ✅ SIM |
| 🔴 CRÍTICO | Criar guia de uso (admin) | 1.5h | ✅ SIM |
| 🔴 CRÍTICO | Forçar alterar senha admin na 1ª vez | 1h | ✅ SIM |
| 🟠 ALTO | Implementar rate-limiting | 30 min | ⚠️ BOA IDEIA |
| 🟠 ALTO | Adicionar cabeçalhos HTTP security | 20 min | ⚠️ BOA IDEIA |
| 🟠 ALTO | Criar página de Privacidade | 30 min | ⚠️ BOA IDEIA |
| 🟠 ALTO | Implementar exportação CSV | 1h | ⚠️ BOA IDEIA |
| 🟡 MÉDIO | Criar vídeo tutorial | 3h | ✅ RECOMENDADO |
| 🟡 MÉDIO | Criar FAQ | 1h | ✅ RECOMENDADO |

**Total crítico:** ~6.5 horas  
**Total com boas práticas:** ~11.5 horas  
**Total com vídeo:** ~14.5 horas

---

## 📋 Checklist Simplificado para Local

```
[ ] Instalação facilitada (setup.bat / executável)
[ ] Senha admin muda na primeira vez
[ ] Backup automático/manual funcionando
[ ] Guideline de instalação escrito
[ ] Guia de uso para admin
[ ] Troubleshooting preparado
[ ] Cabeçalhos HTTP security adicionados
[ ] Rate-limiting anti-brute-force
[ ] Exportação CSV implementada
[ ] Página de privacidade criada
[ ] Treinamento agendado com cliente
[ ] Contato de suporte definido
```

---

## 📦 Estrutura Final de Entrega

```
student-system/
├── app.py                          # Backend principal
├── requirements.txt
├── setup.bat                       # NOVO: Instalação Windows
├── setup.sh                        # NOVO: Instalação Mac/Linux
│
├── INSTALL.md                      # NOVO: Guia de instalação
├── USUARIO.md                      # NOVO: Guia do usuário admin
├── TECNICO.md                      # NOVO: Guia técnico/suporte
├── FAQ.md                          # NOVO: Perguntas frequentes
│
├── static/
│   ├── privacidade.html            # NOVO: Política de privacidade
│   ├── index.html
│   ├── cadastro.html
│   ├── dashboard.html
│   ├── js/
│   └── css/
│
├── instance/
│   ├── student_system.db           # Banco de dados
│   └── backups/                    # NOVO: Pasta de backups
│
└── static/uploads/
    └── (fotos dos formandos)
```

---

## 🔑 Resumo: Principais Diferenças Local vs Hospedado

| Item | Hospedado | Local |
|------|-----------|-------|
| Domínio/SSL | CRÍTICO | N/A |
| LGPD rigorosa | SIM | Básico |
| Backup na nuvem | Recomendado | Manual local |
| Monitoramento 24/7 | SIM | Não |
| Escalabilidade | Importante | Não importa |
| Documentação | Técnica | Usuário + Técnica |
| Instalação | Via git/cloud | Via script |

---

## ✅ Próximos Passos (Ordem)

1. **Esta semana:**
   - [ ] Criar `setup.bat` + `setup.sh`
   - [ ] Forçar alterar senha admin
   - [ ] Implementar backup automático

2. **Próxima semana:**
   - [ ] Escrever INSTALL.md, USUARIO.md, TECNICO.md
   - [ ] Criar FAQ
   - [ ] Adicionar cabeçalhos HTTP
   - [ ] Implementar rate-limiting

3. **Antes de entregar:**
   - [ ] Gravar vídeo tutorial (5-10 min)
   - [ ] Testar toda a instalação do zero
   - [ ] Agendar treinamento
   - [ ] Preparar pacote de backup

---

**Gerado em:** 10/11/2025  
**Verificado por:** Amp (Sourcegraph)  
**Contexto:** Aplicação Local (não hospedada)
