# Changelog: Novos Campos de Localização

## Resumo das Alterações

Foram adicionados 3 novos campos ao formulário de cadastro e banco de dados:

1. **Número** - Número do imóvel
2. **Complemento** - Complemento de endereço (apto, lote, etc)
3. **Tipo de Imóvel** - Classificação: Casa, Apartamento ou Outro

## Arquivos Modificados

### 1. **Backend: app.py**

#### Model (Lead)
Adicionadas 3 novas colunas à tabela `leads`:
```python
numero = db.Column(db.String(10))          # Max 10 chars
complemento = db.Column(db.String(100))     # Max 100 chars
tipo_imovel = db.Column(db.String(20))      # casa, apartamento, outro
```

#### Endpoint POST `/api/cadastro`
Agora processa os novos campos ao criar um lead:
```python
numero=data.get('numero'),
complemento=data.get('complemento'),
tipo_imovel=data.get('tipo_imovel'),
```

#### Endpoint PATCH `/api/leads/<lead_id>`
Agora permite atualizar os novos campos com validações:
- `numero`: Max 10 caracteres
- `complemento`: Max 100 caracteres
- `tipo_imovel`: Apenas ['casa', 'apartamento', 'outro']

#### Endpoints GET `/api/leads` e `/api/leads/<lead_id>`
Agora retornam os novos campos na resposta JSON:
```json
{
  "numero": "123",
  "complemento": "Apto 42",
  "tipo_imovel": "apartamento"
}
```

### 2. **Frontend: static/cadastro.html**

#### Form HTML
Adicionados 3 novos campos na seção "Localização":

```html
<!-- Número -->
<div class="col-md-3">
    <label class="form-label">Número</label>
    <input type="text" class="form-control" name="numero" id="numero" 
           maxlength="10" placeholder="Ex: 123 ou S/N" />
</div>

<!-- Complemento -->
<div class="col-md-9">
    <label class="form-label">Complemento</label>
    <input type="text" class="form-control" name="complemento" id="complemento" 
           maxlength="100" placeholder="Ex: Apto 42 ou Lote B" />
</div>

<!-- Tipo de Imóvel -->
<div class="col-md-6">
    <label class="form-label">Tipo de imóvel</label>
    <select class="form-select" name="tipo_imovel" id="tipoImovel">
        <option value="">Selecione</option>
        <option value="casa">Casa</option>
        <option value="apartamento">Apartamento</option>
        <option value="outro">Outro</option>
    </select>
</div>
```

#### Form Submission
Atualizado o código que envia o formulário para incluir os novos campos:
```javascript
data.append('numero', byId('numero').value.trim());
data.append('complemento', byId('complemento').value.trim());
data.append('tipo_imovel', byId('tipoImovel').value);
```

## Banco de Dados

### Migração Necessária

Se você está em produção, execute:

```sql
-- Para PostgreSQL
ALTER TABLE leads ADD COLUMN numero VARCHAR(10);
ALTER TABLE leads ADD COLUMN complemento VARCHAR(100);
ALTER TABLE leads ADD COLUMN tipo_imovel VARCHAR(20);

-- Para SQLite
ALTER TABLE leads ADD COLUMN numero VARCHAR(10);
ALTER TABLE leads ADD COLUMN complemento VARCHAR(100);
ALTER TABLE leads ADD COLUMN tipo_imovel VARCHAR(20);
```

**⚠️ Nota**: Se estiver usando Render com persistência automática, a tabela será criada automaticamente na próxima execução.

## Estrutura de Dados

### JSON Response Example
```json
{
  "id": 1,
  "matricula": "0000044081",
  "nome_formando": "João Silva",
  "cep": "01310-100",
  "endereco": "Avenida Paulista",
  "numero": "123",
  "complemento": "Apto 456",
  "tipo_imovel": "apartamento",
  "email": "joao@example.com",
  "whatsapp": "11987654321",
  "status_lead": "novo",
  "criado_em": "2025-11-11T10:30:00"
}
```

## Validações

Os campos foram validados tanto no frontend quanto no backend:

| Campo | Validação Frontend | Validação Backend |
|-------|-------------------|------------------|
| numero | maxlength=10 | Max 10 chars |
| complemento | maxlength=100 | Max 100 chars |
| tipo_imovel | select options | enum: ['casa', 'apartamento', 'outro'] |

## Testes Recomendados

1. **Criar novo cadastro com todos os campos**
   - Verificar se campos são salvos corretamente
   - Testar com diferentes tipos de imóvel

2. **Atualizar lead existente**
   - PATCH `/api/leads/1` com novos campos
   - Verificar persistência

3. **Buscar leads**
   - GET `/api/leads` deve retornar os novos campos
   - GET `/api/leads/1` deve retornar os novos campos

4. **Validação de entrada**
   - Tentar número > 10 chars (deve rejeitar)
   - Tentar complemento > 100 chars (deve rejeitar)
   - Tentar tipo_imovel inválido (deve rejeitar)

## Rollback (Se Necessário)

Se precisar reverter:

```sql
-- Para PostgreSQL/SQLite
ALTER TABLE leads DROP COLUMN numero;
ALTER TABLE leads DROP COLUMN complemento;
ALTER TABLE leads DROP COLUMN tipo_imovel;
```

## Notas Importantes

1. Todos os campos são **opcionais** (not null = false)
2. Os campos aparecem na seção "Localização" do formulário
3. Os valores são salvos com case normalization (`tipo_imovel` sempre minúsculo)
4. O tipo_imovel é opcional no formulário (select vazio é permitido)
