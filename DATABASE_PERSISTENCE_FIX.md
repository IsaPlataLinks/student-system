# Solução: Dados Desaparecendo do Banco de Dados

## Problema
Os dados desaparecem quando o servidor Render "dorme" (após 15 minutos de inatividade no plano free).

## Causas Possíveis

### 1. **Render Database Free Tier** (Causa Principal)
- O banco de dados PostgreSQL do Render é **efêmero** no plano free
- Vai para modo sleep após 15 minutos de inatividade
- **Solução**: Upgrade para plano pago ou usar um banco externo

### 2. **Container Docker Efêmero**
- Se estiver usando SQLite (não recomendado em produção)
- O arquivo `student_system.db` é deletado a cada deploy
- **Solução**: Usar PostgreSQL persistente

### 3. **Conexões Abertas Não Reciciadas**
- Conexões antigas podem ficar inválidas após o banco acordar
- **Solução**: ✅ Implementada em `app.py` com `pool_pre_ping` e `pool_recycle`

## Soluções Implementadas

### ✅ 1. Connection Pooling (Já Implementado)
```python
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,  # Recicla conexões a cada 1 hora
    'pool_pre_ping': True,  # Verifica se conexão está viva antes de usar
    'max_overflow': 20,
}
```

**O que faz:**
- `pool_pre_ping=True`: Antes de usar uma conexão do pool, envia um comando `SELECT 1` para verificar se ainda está viva
- `pool_recycle=3600`: Descarta conexões com mais de 1 hora, forçando novas conexões
- `pool_size=10`: Mantém até 10 conexões no pool

### ✅ 2. Banco de Dados Persistente
O arquivo `app.py` já garante:
- Usa `DATABASE_URL` (PostgreSQL no Render) se disponível
- Fallback para SQLite local (apenas desenvolvimento)
- Aviso crítico se tentar rodar produção sem `DATABASE_URL`

## Próximos Passos - OBRIGATÓRIOS

### ⚠️ Opção 1: Upgrade Render Database (Recomendado)
1. Acesse https://dashboard.render.com
2. Vá para seu banco de dados PostgreSQL
3. Clique em "Settings"
4. Faça upgrade para plano pago (mínimo: PostgreSQL Standard)
5. **Você receberá uma nova DATABASE_URL**
6. Atualize a variável de ambiente no seu serviço web

### ⚠️ Opção 2: Usar Banco Externo (ElephantSQL, Neon, Railway)
1. Crie uma conta em https://www.elephantsql.com ou https://neon.tech
2. Crie um banco de dados gratuito
3. Copie a string de conexão (DATABASE_URL)
4. Configure no Render:
   - Vá em seu serviço web
   - Environment
   - Substitua `DATABASE_URL` pela nova string

### ⚠️ Opção 3: Migrar para Plano Pago do Render
1. https://render.com/pricing
2. Escolha plano PostgreSQL Standard (mais econômico)
3. Isso elimina o comportamento de sleep

## Verificar se o Fix Funciona

Teste a persistência de dados:

```bash
# 1. Crie um novo cadastro
# 2. Espere o app adormecer (15+ min sem requisições)
# 3. Faça uma requisição nova
# 4. Verifique se os dados persistem

curl https://seu-app.onrender.com/api/diagnostico
```

Você deve ver os dados cadastrados anteriormente na resposta `leads_recentes`.

## Status Atual

| Item | Status | Ação |
|------|--------|------|
| Pool de Conexões | ✅ Implementado | Nenhuma |
| SQLite vs PostgreSQL | ✅ Correto | Usar PostgreSQL |
| DATABASE_URL | ⚠️ Verificar | Upgrade do banco Render |
| Validação | ✅ Implementado | Nenhuma |

## Debug: Como Verificar Qual BD está Sendo Usado

```python
# Execute no terminal Python do Render
python -c "from app import app; print(app.config['SQLALCHEMY_DATABASE_URI'])"
```

Se começar com `sqlite://`, então está usando SQLite (❌ ERRADO em produção)
Se começar com `postgresql://`, então está usando PostgreSQL (✅ CORRETO)

## Resumo da Solução

A raiz do problema é que **o Render Database Free Tier é efêmero e vai para sleep**. 

As 3 coisas que fizemos:
1. ✅ **Connection Pooling**: Garante que conexões mortas sejam detectadas
2. ✅ **Verifica DATABASE_URL**: Evita usar SQLite em produção
3. ⚠️ **Upgrade necessário**: Você precisa fazer upgrade do banco Render OR usar um banco externo gratuito (ElephantSQL, Neon, Railway)

**SEM o upgrade/troca do banco, os dados continuarão desaparecendo.**
