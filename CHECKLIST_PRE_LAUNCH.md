# ✅ Checklist de Pré-Launch - Student System

**Data de Verificação:** 10/11/2025  
**Projeto:** Student System (R3 Formaturas)  
**Tipo:** Sistema Web de Cadastro de Formandos

---

## 📊 Resumo Executivo

| Categoria | Status | Crítico |
|-----------|--------|---------|
| 🏢 Negócio & Conteúdo | ⚠️ Parcial | - |
| 🌐 Domínio, DNS e E-mail | ⚠️ Pendente | ⛔ SIM |
| ⚡ Desempenho (Web Vitals) | 🔄 Não testado | - |
| ♿ Acessibilidade | 🟡 Básica | - |
| 🔍 SEO & Descoberta | 🟡 Básica | - |
| 🔐 Segurança | 🔴 CRÍTICO | ⛔ SIM |
| 💾 Dados & Persistência | ✅ Bom | - |
| 📋 LGPD | 🔴 CRÍTICO | ⛔ SIM |
| 📡 Observabilidade & Suporte | 🟡 Parcial | - |
| 🏗️ Infra & Deploy | ✅ Bom | - |
| 📚 Treinamento & Entrega | 🟡 Incompleto | - |
| 📄 Documentos de Handover | 🔴 CRÍTICO | ⛔ SIM |

---

## 1️⃣ Negócio & Conteúdo

- [ ] **Objetivo e métricas** - Não está claro
  - Sugerir: Combinar metas com o cliente (leads/mês, taxa de conversão, tempo médio de cadastro)

- [ ] **Fluxos essenciais testados**
  - ✅ Cadastro de formando: OK
  - ✅ Upload de foto com QR Code: OK
  - ⚠️ Notificação ao cliente/CRM: **Não implementado** - Falta integração de e-mail
  - ⚠️ Confirmação ao responsável: **Sem envio de e-mail**

- [ ] **Conteúdo final revisado**
  - ✅ Layout e branding: Bem feito (R3 Formaturas)
  - ⚠️ Falta: Política de Privacidade/Termos em página visível
  - ⚠️ Falta: Telefone de contato/suporte

---

## 2️⃣ Domínio, DNS e E-mail

- [ ] **Domínio apontado + SSL/TLS**
  - Status: **PENDENTE** ⛔ CRÍTICO
  - Deploy: Render.com (render.yaml configurado)
  - Ação: Certificado SSL é automático no Render
  - **TODO:** Apontar domínio customizado para Render

- [ ] **SPF/DKIM/DMARC**
  - Status: **NÃO CONFIGURADO** ⛔ CRÍTICO
  - Impacto: E-mails do site podem cair em SPAM
  - **TODO:** Implementar envio de e-mail (SMTP) + configurar registros DNS

- [ ] **Páginas 404/500 + redirecionamentos 301**
  - ✅ Error handlers implementados (app.py: linhas 291-310)
  - ✅ Retorna JSON estruturado

---

## 3️⃣ Desempenho (Web Vitals)

- [ ] **LCP, CLS, TBT/INP**
  - Status: **NÃO TESTADO** 🔄
  - Ação: Testar com Lighthouse/PageSpeed Insights após deploy
  - Verificar: Mobile (3G) e Desktop

- [ ] **Imagens otimizadas**
  - ✅ Processamento de fotos: Redimensionamento 300x400px, qualidade 85% (app.py: linhas 249-289)
  - ✅ Lazy-loading possível no frontend (verificar JavaScript)
  - ⚠️ Logo externa (i.ibb.co) - usar versão local para melhor performance

- [ ] **Cache e CDN**
  - ⚠️ Cache não configurado explicitamente em Flask
  - Sugerir: Adicionar headers de cache para assets estáticos

---

## 4️⃣ Acessibilidade (WCAG 2.1 AA)

- [ ] **Contraste, navegação por teclado, labels, alt-text**
  - ✅ Contraste geral OK (ouro + branco/preto)
  - ⚠️ Alt-text não presente em imagens (logo)
  - ⚠️ Labels de formulário: Verificar em cadastro.html

- [ ] **Foco visível, "pular para conteúdo", mensagens de erro**
  - ✅ Bootstrap 5 fornece estilos de foco
  - ⚠️ "Pular para conteúdo" não implementado
  - ✅ Mensagens de erro em JSON (API)

- [ ] **Teste com leitor de tela**
  - Status: **NÃO TESTADO**

---

## 5️⃣ SEO & Descoberta

- [ ] **Title/Description únicos, Open Graph**
  - ⚠️ Title genérico em algumas páginas (verificar dashboard.html, eventos.html)
  - ❌ Meta description não presente
  - ❌ Open Graph/Twitter Cards não implementados
  - **TODO:** Adicionar em todas as páginas HTML

- [ ] **Sitemap e robots.txt**
  - ❌ `sitemap.xml` não existe
  - ❌ `robots.txt` não existe
  - **TODO:** Criar antes do deploy em produção

- [ ] **Dados estruturados (Schema.org)**
  - ❌ Não implementados
  - Sugerir: LocalBusiness para a escola/evento

---

## 6️⃣ Segurança (OWASP Top 10) ⛔ CRÍTICO

### ✅ Implementado

- ✅ JWT para autenticação (Flask-JWT-Extended)
- ✅ Hashing de senhas (werkzeug.security)
- ✅ CORS habilitado (controlled)
- ✅ Validação server-side de formulários
- ✅ Proteção contra SQLite efêmero em produção (app.py: linhas 46-53)

### 🔴 CRÍTICO - Não implementado

1. **Cabeçalhos de segurança** ❌
   ```
   ❌ Content-Security-Policy (CSP)
   ❌ Strict-Transport-Security (HSTS)
   ❌ X-Content-Type-Options
   ❌ X-Frame-Options
   ❌ Referrer-Policy
   ```
   **Ação:** Adicionar middleware de segurança em app.py
   ```python
   @app.after_request
   def set_security_headers(response):
       response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
       response.headers['X-Content-Type-Options'] = 'nosniff'
       response.headers['X-Frame-Options'] = 'SAMEORIGIN'
       response.headers['X-XSS-Protection'] = '1; mode=block'
       response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; img-src 'self' https:; font-src 'self' cdnjs.cloudflare.com"
       return response
   ```

2. **2FA para admin** ❌
   - Login atual: usuário/senha apenas
   - **TODO:** Implementar 2FA (totp/email)

3. **Rate-limiting** ❌
   - Sem proteção contra brute-force
   - **TODO:** Implementar com Flask-Limiter

4. **Anti-CSRF** ⚠️
   - CORS está aberto (wildcard?)
   - **TODO:** Validar CORS config

5. **Anti-spam** ❌
   - Sem reCAPTCHA no cadastro
   - **TODO:** Adicionar reCAPTCHA ou hCaptcha no formulário

6. **Validação de entrada** ✅ Parcial
   - Validações existem (nome, email, WhatsApp, CEP)
   - ⚠️ Verificar injeção SQL em queries dinâmicas

7. **Senhas padrão** 🔴 CRÍTICO
   - Admin padrão: `login='admin'`, `senha='admin123'`
   - **AÇÃO IMEDIATA:** Alterar em produção

8. **JWT_SECRET_KEY** ⚠️ CRÍTICO
   - Padrão: `'r3-formaturas-secret-2024'` em app.py linha 65
   - **AÇÃO IMEDIATA:** Usar variável de ambiente (render.yaml tem `scope: secret`)

9. **Dependências desatualizadas** 🟡
   - Flask 3.1.0 (OK)
   - psycopg2-binary 2.9.9 (OK)
   - Pillow 10.4.0 (OK)
   - **TODO:** Verificar CVEs com `pip check`

---

## 7️⃣ Dados & Persistência

- ✅ **Banco de dados persistente**
  - Produção: PostgreSQL via `DATABASE_URL`
  - Desenvolvimento: SQLite em `instance/`
  - ✅ Proteção contra SQLite efêmero (app.py: linhas 46-53)

- ⚠️ **Backup automático**
  - Status: NÃO CONFIGURADO
  - Render oferece backup automático (verificar)
  - **TODO:** Documentar procedimento de backup/restauração

- [ ] **Exportação de dados**
  - ❌ Nenhum endpoint de exportação CSV/JSON
  - **TODO:** Implementar `/api/leads/export` (CSV/JSON)

- [ ] **Logs de auditoria**
  - ⚠️ Logs básicos em console (print statements)
  - ❌ Sem persistência de logs
  - **TODO:** Implementar logging estruturado (ex: database, arquivo)

---

## 8️⃣ LGPD (Lei Geral de Proteção de Dados) ⛔ CRÍTICO

- [ ] **Política de Privacidade**
  - ❌ NÃO EXISTE em produção
  - **AÇÃO IMEDIATA:** Adicionar página com política

- [ ] **Termos de Serviço**
  - ❌ NÃO EXISTE em produção
  - **AÇÃO IMEDIATA:** Adicionar página com termos

- [ ] **Consentimento/Cookies**
  - ❌ Nenhuma banner de cookies
  - ⚠️ Google Analytics/tracking não configurado (verificar render.yaml)
  - **TODO:** Adicionar banner de consentimento

- [ ] **Minimização e retenção de dados**
  - ⚠️ Falta política clara de retenção
  - Sugerir: Dados de leads excluídos após 90 dias de inatividade

- [ ] **Direitos do titular**
  - ❌ Nenhum endpoint para: acesso, retificação, eliminação de dados
  - **TODO:** Implementar:
    - GET /api/meus-dados (exportação)
    - DELETE /api/meus-dados (esquecimento)

- [ ] **Contratos com terceiros**
  - ⚠️ Não revisados
  - Verificar: Render (hosting), CDN (jsdelivr, cloudflare, ibb.co), Google Fonts

---

## 9️⃣ Observabilidade & Suporte

- ⚠️ **Monitoramento de uptime**
  - Status: Não implementado
  - Sugerir: UptimeRobot (free), Render Health Checks

- ⚠️ **Monitoramento de erros**
  - ⚠️ Logs em console apenas
  - Sugerir: Sentry (free tier), LogRocket
  - **TODO:** Implementar

- ⚠️ **Analytics**
  - ❌ Não configurado
  - Sugerir: Google Analytics 4, Plausible, Fathom (LGPD-friendly)

- [ ] **Alertas**
  - ❌ Sem alertas para quedas
  - Sugerir: Render Health Checks + e-mail

- [ ] **Runbook**
  - ❌ Não existe
  - **TODO:** Documentar como reiniciar, acessar logs, etc.

---

## 🔟 Infra & Deploy

- ✅ **CI/CD**
  - Render com `render.yaml`: buildCommand e startCommand OK
  - Deploy automático via git push

- ✅ **Rollback**
  - Render oferece rollback de deployments

- ✅ **Variáveis de ambiente**
  - `DATABASE_URL`, `UPLOAD_PATH`, `JWT_SECRET_KEY` configuradas
  - ⚠️ Falta documentação

- ✅ **Ambientes separados**
  - Desenvolvimento (SQLite local)
  - Produção (PostgreSQL)

- [ ] **Infra como código**
  - ✅ render.yaml está bem estruturado
  - Disco persistente (10GB) para uploads

- [ ] **Custos estimados**
  - Render: ~USD 10-50/mês (Web + PostgreSQL + Disk)
  - **TODO:** Documentar com cliente

---

## 1️⃣1️⃣ Treinamento & Entrega

- [ ] **Acesso do cliente**
  - ⚠️ Admin padrão existe (`admin/admin123`)
  - **TODO:** Criar usuário específico do cliente
  - **TODO:** Entregar credenciais via cofre seguro (ex: 1Password, LastPass)

- [ ] **Mini-guia de 1 página**
  - ❌ Não existe
  - **TODO:** Criar com print screens:
    1. Como fazer login
    2. Como ver leads cadastrados
    3. Como baixar foto/galeria
    4. Como gerar QR Code

- [ ] **Videozinho/capturas**
  - ❌ Não existe
  - Sugerir: Loom (grátis), OBS Studio
  - Mostrar os 3 fluxos: cadastro → admin → download

---

## 1️⃣2️⃣ Documentos de Handover (CRÍTICO)

### 📐 Arquitetura

```
student-system/
├── app.py                    # Backend Flask (1000 linhas)
├── requirements.txt          # Dependencies (Python)
├── render.yaml              # Configuração de deploy
├── static/                  # Frontend (HTML/CSS/JS)
│   ├── index.html           # Página inicial
│   ├── cadastro.html        # Formulário público
│   ├── dashboard.html       # Dashboard admin
│   ├── eventos.html         # Gerenciamento de eventos
│   ├── login.html           # Login
│   ├── js/                  # JavaScript (API calls, validação)
│   └── css/                 # Estilos (Bootstrap 5)
├── instance/                # SQLite (dev) ou PostgreSQL (prod)
└── static/uploads/          # Fotos dos formandos
```

**Stack:**
- Backend: Flask 3.1.0 + SQLAlchemy
- Frontend: HTML5 + Bootstrap 5 + Vanilla JS
- DB: SQLite (dev) / PostgreSQL (prod)
- Deploy: Render.com
- Auth: JWT (Flask-JWT-Extended)

### 📋 Variáveis de Ambiente

| Variável | Escopo | Descrição | Exemplo |
|----------|--------|-----------|---------|
| `DATABASE_URL` | build/runtime | URL do PostgreSQL | `postgresql://user:pass@host/db` |
| `UPLOAD_PATH` | runtime | Diretório de uploads | `/mnt/data/uploads` |
| `JWT_SECRET_KEY` | secret | Chave para assinar JWT | (gerada automaticamente) |
| `FLASK_ENV` | runtime | environment | `production` ou `development` |

### 📞 Fornecedores e Contatos

| Fornecedor | Serviço | Status | Contato |
|-----------|---------|--------|---------|
| Render.com | Hosting + DB + Disk | ✅ Ativo | [render.com/support](https://render.com/support) |
| Domínio | DNS | ⏳ Pendente | Registrar em Namecheap/GoDaddy |
| PostgreSQL | Banco (Render) | ✅ Pronto | Gerenciado pelo Render |
| SMTP | E-mail | ❌ Não configurado | SendGrid/Resend/Mailgun |

### 🔧 Plano de Manutenção

**Janela de updates:** Toda segunda-feira, 22h-23h (horário de Brasília)

**Checklist de atualização:**
1. Backup do banco de dados
2. Deploy em staging (se existir)
3. Executar testes
4. Rollback se necessário
5. Commit no git com mensagem clara

**Responsabilidades:**
- **Deploy:** Desenvolvedor (você)
- **Testes:** Cliente (validar funcionalidade)
- **Suporte crítico:** Respostas em até 24h

### 📊 SLA Leve

- **Suporte normal:** Resposta em 1 dia útil
- **Correções críticas (sem funcionamento):** Resposta em até 24h
- **Bugs menores/melhorias:** Próximo sprint

---

## 🎯 Ações Críticas Imediatas (Antes de Go-Live)

| Prioridade | Tarefa | Estimativa |
|-----------|--------|------------|
| 🔴 CRÍTICO | Implementar cabeçalhos de segurança | 30 min |
| 🔴 CRÍTICO | Alterar JWT_SECRET_KEY para variável de ambiente | 15 min |
| 🔴 CRÍTICO | Alterar senha admin padrão | 10 min |
| 🔴 CRÍTICO | Criar Política de Privacidade e Termos | 2h |
| 🔴 CRÍTICO | Configurar SMTP para envio de e-mails | 1h |
| 🟠 ALTO | Adicionar reCAPTCHA no cadastro | 1h |
| 🟠 ALTO | Implementar rate-limiting | 30 min |
| 🟠 ALTO | Criar sitemap.xml e robots.txt | 30 min |
| 🟡 MÉDIO | Implementar 2FA para admin | 3h |
| 🟡 MÉDIO | Adicionar monitoramento com Sentry | 1h |
| 🟡 MÉDIO | Criar documentação de handover | 2h |
| 🟡 MÉDIO | Criar mini-guia de usuário | 1h |

**Total estimado:** ~13.5 horas de trabalho

---

## 📋 Checklist de Validação Rápida

Copie e marque conforme for completando:

```
[ ] Domínio + SSL auto-renew
[ ] DNS + SPF/DKIM/DMARC
[ ] Formulários enviam e chegam no destino (e caem no CRM/planilha)
[ ] Web Vitals ok nas páginas críticas
[ ] Acessibilidade básica (teclado, contraste, labels)
[ ] SEO (title/desc, OG, sitemap, robots)
[ ] Segurança (2FA admin, CSP, HSTS, anti-spam)
[ ] Banco persistente + backup + restauração testada
[ ] Política de Privacidade/Termos + consentimento (LGPD)
[ ] Monitoramento/alertas + erros capturados
[ ] CI/CD com rollback + docs de env
[ ] Acessos entregues + guia de uso + plano de suporte
```

---

## 📝 Próximos Passos

1. **Semana 1:** Implementar itens críticos (segurança, LGPD)
2. **Semana 2:** Configurar infra (SMTP, monitoramento)
3. **Semana 3:** Documentação e treinamento
4. **Semana 4:** Testes finais e go-live

---

**Gerado em:** 10/11/2025  
**Verificado por:** Amp (Sourcegraph)
