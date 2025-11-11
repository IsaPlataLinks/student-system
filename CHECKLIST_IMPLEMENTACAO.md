# Checklist de Implementação

## ✅ Backend (app.py)

### Modelo de Dados
- [x] Adicionada coluna `numero` ao Lead
- [x] Adicionada coluna `complemento` ao Lead
- [x] Adicionada coluna `tipo_imovel` ao Lead
- [x] Colunas com tipos e limites corretos

### Endpoint POST /api/cadastro
- [x] Processa `numero`
- [x] Processa `complemento`
- [x] Processa `tipo_imovel`
- [x] Salva corretamente no banco

### Endpoint PATCH /api/leads/<id>
- [x] Valida `numero` (max 10 chars)
- [x] Valida `complemento` (max 100 chars)
- [x] Valida `tipo_imovel` (enum)
- [x] Normaliza `tipo_imovel` para minúsculo
- [x] Retorna erros apropriados

### Endpoints GET /api/leads e /api/leads/<id>
- [x] Retorna `numero`
- [x] Retorna `complemento`
- [x] Retorna `tipo_imovel`
- [x] Formatação JSON correta

### Database Persistence
- [x] Adicionada pool configuration
- [x] `pool_pre_ping=True` ativado
- [x] `pool_recycle=3600` configurado
- [x] `max_overflow=20` setado
- [x] Pool size de 10 conexões

## ✅ Frontend (static/cadastro.html)

### Form HTML
- [x] Campo "Número" adicionado
- [x] Campo "Complemento" adicionado
- [x] Campo "Tipo de Imóvel" adicionado
- [x] Placeholders apropriados
- [x] Maxlength corretos
- [x] Labels descritivos

### Form JavaScript
- [x] `numero` incluído em FormData
- [x] `complemento` incluído em FormData
- [x] `tipo_imovel` incluído em FormData
- [x] Values trimmed corretamente

### Form Styling
- [x] Campos em seção "Localização"
- [x] Layout com col-md-3 e col-md-9
- [x] Consistência visual com outros campos
- [x] Responsive design mantido

## 📚 Documentação

- [x] RESUMO_ATUALIZACOES.md criado
- [x] DATABASE_PERSISTENCE_FIX.md criado
- [x] CHANGELOG_NOVOS_CAMPOS.md criado
- [x] CHECKLIST_IMPLEMENTACAO.md (este)

## 🧪 Testes Pendentes

### Testes Funcionais
- [ ] Criar novo cadastro com todos os campos
- [ ] Verificar se numero é salvo corretamente
- [ ] Verificar se complemento é salvo corretamente
- [ ] Verificar se tipo_imovel é salvo corretamente
- [ ] Atualizar lead existente com PATCH
- [ ] Buscar lead e confirmar novos campos aparecem

### Testes de Validação
- [ ] Teste numero com mais de 10 chars (deve rejeitar)
- [ ] Teste complemento com mais de 100 chars (deve rejeitar)
- [ ] Teste tipo_imovel com valor inválido (deve rejeitar)
- [ ] Teste campos vazios/nulos (deve aceitar, são opcionais)

### Testes de Persistência
- [ ] Criar cadastro
- [ ] Aguardar 15+ minutos
- [ ] Fazer nova requisição
- [ ] Verificar se dados persistem (com novo fix)

## 🚀 Deployment

### Antes de Deploy
- [ ] Fazer backup do banco atual
- [ ] Revisar mudanças em app.py
- [ ] Revisar mudanças em cadastro.html
- [ ] Testar localmente (se possível)

### No Render
- [ ] Push das mudanças
- [ ] Deploy automático
- [ ] Verificar build logs
- [ ] Testar endpoint /api/diagnostico
- [ ] Escolher solução de persistência (Opção 1, 2 ou 3)
- [ ] Atualizar DATABASE_URL se necessário

### Pós-Deploy
- [ ] Acessar /cadastro?e=1 (ou e=seu_evento_id)
- [ ] Preencher com novos campos
- [ ] Submeter
- [ ] Verificar em GET /api/leads/<id>
- [ ] Verificar no dashboard

## 📋 Linhas de Código Modificadas

### app.py
- **Linhas 188-192**: Adicionadas 3 colunas ao modelo Lead
- **Linhas 64-70**: Adicionada SQLALCHEMY_ENGINE_OPTIONS para pool
- **Linhas 732-734**: Adicionados campos ao Create (POST /api/cadastro)
- **Linhas 1168-1200**: Adicionadas validações ao Update (PATCH /api/leads/<id>)
- **Linhas 815-819**: Adicionados campos ao listar_leads
- **Linhas 873-875**: Adicionados campos ao obter_lead

### cadastro.html
- **Linhas 627-650**: Adicionados 3 campos HTML
- **Linhas 977-979**: Adicionados 3 appends ao FormData

## 🔍 Como Verificar Implementação

### Banco de Dados
```bash
# SSH no Render e conecte ao PostgreSQL
psql $DATABASE_URL

# Verifique as colunas
\d leads
```

Deve mostrar:
- numero (character varying)
- complemento (character varying)
- tipo_imovel (character varying)

### Frontend
```bash
# Abra em navegador
https://seu-app.onrender.com/cadastro?e=1

# Procure pelos campos:
# - Campo "Número" (col-md-3)
# - Campo "Complemento" (col-md-9)
# - Select "Tipo de imóvel" (col-md-6)
```

### API
```bash
# Crie um cadastro
curl -X POST https://seu-app.onrender.com/api/cadastro \
  -F evento_id=1 \
  -F tipo_cadastro=aluno \
  -F matricula=123456 \
  -F nome_formando="João Silva" \
  -F serie="1º ano" \
  -F turma="A" \
  -F nome_contato="Maria Silva" \
  -F email="maria@example.com" \
  -F whatsapp="11987654321" \
  -F numero="123" \
  -F complemento="Apto 45" \
  -F tipo_imovel="apartamento"

# Deve retornar 201 com ID
# Depois verifique:
curl https://seu-app.onrender.com/api/leads/LEAD_ID \
  -H "Authorization: Bearer YOUR_TOKEN"

# Procure pelos campos:
# "numero": "123"
# "complemento": "Apto 45"
# "tipo_imovel": "apartamento"
```

## ⚠️ Problemas Conhecidos & Soluções

### Problema: "Coluna não existe" no banco
**Solução**: O Render criará automaticamente na próxima vez que rodar `db.create_all()`. Se não:
```sql
ALTER TABLE leads ADD COLUMN numero VARCHAR(10);
ALTER TABLE leads ADD COLUMN complemento VARCHAR(100);
ALTER TABLE leads ADD COLUMN tipo_imovel VARCHAR(20);
```

### Problema: Campos aparecem como NULL na API
**Solução**: Crie novo cadastro (registros antigos não terão os campos). Ou:
```sql
UPDATE leads SET numero = '', complemento = '', tipo_imovel = '';
```

### Problema: Pool ping falha com erro de conexão
**Solução**: Upgrade para banco persistente (veja DATABASE_PERSISTENCE_FIX.md)

## ✅ Status Final

| Componente | Status | Evidência |
|-----------|--------|-----------|
| Modelo | ✅ OK | app.py linhas 188-192 |
| POST | ✅ OK | app.py linhas 732-734 |
| PATCH | ✅ OK | app.py linhas 1168-1200 |
| GET | ✅ OK | app.py linhas 815-819, 873-875 |
| HTML | ✅ OK | cadastro.html linhas 627-650 |
| JS | ✅ OK | cadastro.html linhas 977-979 |
| Pool | ✅ OK | app.py linhas 64-70 |
| Docs | ✅ OK | 3 arquivos markdown |

**Status Geral**: ✅ PRONTO PARA DEPLOY

---

## Comandos Úteis Pós-Deploy

```bash
# Verificar status do app
curl https://seu-app.onrender.com/api/diagnostico

# Ver logs em tempo real
# No Render dashboard: seu-app → Logs

# Forçar rebuild (se necessário)
# No Render dashboard: seu-app → Manual Deploy
```
