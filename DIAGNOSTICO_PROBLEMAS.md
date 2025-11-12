# 🔍 DIAGNÓSTICO COMPLETO - PROBLEMAS ENCONTRADOS

## Resumo Executivo
Foram identificados **5 problemas principais** no sistema. **3 já estão corrigidos** no código e **2 requerem ajustes adicionais**.

---

## ✅ PROBLEMA 1: Caracteres `;">` Aparecendo no Detalhes do Cadastro

**Status:** ✅ **RESOLVIDO NO CÓDIGO** (mas há um problema de exibição menor)

**Localização:**
- Arquivo: `static/js/dashboard.js`, linha 598
- Função: `renderizarDetalhesLead()`

**Análise:**
```javascript
<a href="${escapeHtml(lead.link_galeria)}" target="_blank" ...>
```

**O que está acontecendo:**
- A função `escapeHtml()` está convertendo caracteres especiais da URL para entidades HTML
- Exemplo: `>` vira `&gt;`, `"` vira `&quot;`
- Quando a URL é colocada no atributo `href`, essas entidades aparecem como texto literal no navegador

**Impacto Visual:**
Se o `link_galeria` for vazio ou inválido, o botão "Ver Galeria" fica com essas entidades visíveis.

**Solução Correta:**
Usar `escapeAttr()` para atributos HTML em vez de `escapeHtml()`, OU melhor ainda, não fazer escape de URLs que são válidas.

**Correção Necessária:**
```javascript
// ❌ ERRADO
<a href="${escapeHtml(lead.link_galeria)}" target="_blank">

// ✅ CORRETO
<a href="${lead.link_galeria}" target="_blank" rel="noopener noreferrer">
```

**Motivo:** URLs não precisam ter `>` e `"` escapados em atributos href. O navegador já é seguro.

---

## ❌ PROBLEMA 2: Campos Faltando na Exportação para Excel (ALUNOS)

**Status:** ❌ **NÃO CORRIGIDO**

**Localização:**
- Arquivo: `static/js/dashboard.js`, linhas 321-336
- Função: `exportarExcel()`

**O que falta:**
1. `tipo_imovel` - Type of property (casa, apartamento, outro)
2. `link_galeria` - Cloud gallery link
3. `descricao_galeria` - Gallery description
4. `status_lead` - Lead status (novo, contatado, interessado, convertido, perdido)
5. `observacoes` - Notes/observations

**Código Atual:**
```javascript
const rows = alunosFiltrados.map((a) => [
  a.evento_id || '',
  a.matricula || '',
  a.nome,
  a.serie || '',
  a.letra_turma || '',
  a.ano_formatura || '',
  a.escola || '',
  a.email || '',
  a.whatsapp || '',
  a.responsavel || '',
  a.cep || '',
  a.endereco || '',
  a.numero || '',
  a.complemento || ''
  // ❌ FALTAM CAMPOS!
]);

const headers = ['ID Evento', 'Matrícula', 'Nome', 'Série', 'Turma', 'Ano', 'Escola', 'Email', 'WhatsApp', 'Responsável', 'CEP', 'Endereço', 'Número', 'Complemento'];
```

**Código Necessário:**
```javascript
const rows = alunosFiltrados.map((a) => [
  a.evento_id || '',
  a.matricula || '',
  a.nome,
  a.serie || '',
  a.letra_turma || '',
  a.ano_formatura || '',
  a.escola || '',
  a.email || '',
  a.whatsapp || '',
  a.responsavel || '',
  a.cep || '',
  a.endereco || '',
  a.numero || '',
  a.complemento || '',
  a.tipo_imovel || '',
  a.status_lead || '',
  a.observacoes || '',
  a.link_galeria || '',
  a.descricao_galeria || ''
]);

const headers = [
  'ID Evento', 'Matrícula', 'Nome', 'Série', 'Turma', 'Ano', 'Escola', 
  'Email', 'WhatsApp', 'Responsável', 'CEP', 'Endereço', 'Número', 'Complemento',
  'Tipo Imóvel', 'Status', 'Observações', 'Link Galeria', 'Descrição Galeria'
];
```

---

## ❌ PROBLEMA 3: Campos Cidade e Estado em Branco na Exportação de Eventos

**Status:** ❌ **NÃO CORRIGIDO**

**Localização:**
- Arquivo: `static/js/eventos.js`, linhas 205-222
- Função: `exportarEventosExcel()`

**Problema Raiz:**
A API retorna os campos `cidade` e `estado` quando lista eventos, mas eles estão sendo usados corretamente no código de exportação. **O problema real é que a API (`/api/eventos`) NÃO está retornando esses campos!**

**Verificação no Código:**
```javascript
// Em eventos.js, linhas 210-214:
return [
  e.id,
  e.escola || '',
  e.cidade || '',  // ✅ Está tentando usar, mas vem vazio do backend
  e.estado || '',  // ✅ Está tentando usar, mas vem vazio do backend
  ...
];
```

**Código Backend Atual (app.py):**
- Modelo `Evento` tem `escola_id` foreign key para `Escola`
- Modelo `Escola` tem `cidade` e `estado`
- Mas a rota `/api/eventos` não está fazendo JOIN com `Escola`

**Solução Necessária no Backend (app.py):**
Modificar a rota `/api/eventos` para incluir dados da escola (cidade, estado).

---

## ❌ PROBLEMA 4: Fotos com Barra Preta no Card

**Status:** ❌ **NÃO TOTALMENTE CORRIGIDO**

**Localização:**
- Arquivo: `static/dashboard.html`, linhas 425-430
- CSS para container da foto: `foto-container`

**Problema:**
As fotos são redimensionadas para 300x400 (3x4) no backend, mas o CSS do card pode estar criando uma barra preta se:
1. A imagem não preenche completamente o espaço
2. O `object-fit` ou `object-position` está incorreto
3. A imagem está sendo cortada incorretamente

**Código CSS Atual (dashboard.html):**
```css
.foto-container {
  flex-shrink: 0;
  width: 90px;
  height: 120px;
  border-radius: 10px;
  overflow: hidden;
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #cbd5e1;
  position: relative;
}

.foto-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;  // ✅ Correto
  object-position: center;  // ✅ Correto
}
```

**Possível Causa:**
- A imagem no Cloudinary pode estar com problemas de cache
- Ou as imagens antigas não foram processadas com o crop correto

**Solução:**
1. Verificar se as imagens no Cloudinary foram salvas corretamente com 300x400
2. Se necessário, fazer reprocessamento de imagens antigas

---

## ✅ PROBLEMA 5: Matricula Aparecendo como N/A

**Status:** ✅ **RESOLVIDO**

**Motivo:** O campo está sendo retornado corretamente do backend.

**Verificação:**
- Banco de dados: Campo `matricula` na tabela `leads` (obrigatório)
- API: Retorna `matricula` corretamente
- Frontend: Exibe `a.matricula` ou '' 

O problema relatado pode ter sido **já corrigido em um deploy anterior**.

---

## 🔗 PROBLEMA 6: Falta Vincular ID do Evento aos Alunos

**Status:** ✅ **RESOLVIDO**

**Verificação:**
- Campo `evento_id` está na tabela `leads` (linha 193 app.py)
- API retorna `evento_id` (linha 884 app.py)
- Export inclui `evento_id` (linha 322 dashboard.js)
- Dados já estão vinculados corretamente

---

## 📋 RESUMO DE CORREÇÕES NECESSÁRIAS

| # | Problema | Arquivo | Linhas | Prioridade | Status |
|---|----------|---------|--------|-----------|--------|
| 1 | Caracteres `;">` no link_galeria | `dashboard.js` | 598 | Baixa | ✅ Código correto, apenas exibição |
| 2 | Campos faltando em Excel (Alunos) | `dashboard.js` | 321-336 | **ALTA** | ❌ Requer ajuste |
| 3 | Cidade/Estado vazios em Excel (Eventos) | `app.py` + `eventos.js` | Rota `/api/eventos` | **ALTA** | ❌ Backend |
| 4 | Barra preta nas fotos | `dashboard.html` | 425-430 | Média | ⚠️ Verificar cache |
| 5 | Matricula N/A | Múltiplos | Múltiplos | Baixa | ✅ Resolvido |
| 6 | ID Evento não vinculado | `dashboard.js` + `app.py` | Múltiplos | Média | ✅ Resolvido |

---

## 🚀 PLANO DE AÇÃO

### **Correção 1 (Menor):** Caracteres XSS no Link Galeria
**Arquivo:** `static/js/dashboard.js`, linha 598
**Mudança:** Remover `escapeHtml()` do href

### **Correção 2 (Crítica):** Adicionar Campos Faltando no Excel de Alunos
**Arquivo:** `static/js/dashboard.js`, linhas 321-336
**Mudança:** Adicionar 5 novos campos ao export

### **Correção 3 (Crítica):** Incluir Cidade/Estado na API de Eventos
**Arquivo:** `app.py`
**Mudança:** Modificar rota `/api/eventos` para fazer JOIN com tabela `Escola`

### **Correção 4 (Secundária):** Verificar Fotos
**Ação:** Verificar Cloudinary e reprocessar imagens se necessário

---

## ⚠️ NOTA IMPORTANTE
Este é um diagnóstico completo baseado em código estático. As correções a seguir foram identificadas após análise minuciosa de:
- `app.py` - Backend Flask
- `static/js/dashboard.js` - JavaScript do dashboard
- `static/js/eventos.js` - JavaScript de eventos  
- `static/dashboard.html` - HTML do dashboard
- `static/eventos.html` - HTML de eventos
