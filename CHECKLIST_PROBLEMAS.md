# CHECKLIST DE PROBLEMAS - VERIFICAÇÃO MINUCIOSA

## PROBLEMA 1: EXCEL ALUNOS - Faltam campos (CEP, ENDEREÇO, NUMERO, COMPLEMENTO, TIPO)
**Localização:** `static/js/dashboard.js` - função `exportarExcel()` (linhas 311-350)

**Status:** ✗ INCOMPLETO
- Está exportando: ID Evento, Matrícula, Nome, Série, Turma, Ano, Escola, Email, WhatsApp, Responsável, CEP, Endereço, Número, Complemento
- Faltam: TIPO_IMOVEL (tipo de imóvel: casa, apartamento, outro)
- Header está correto, mas falta adicionar `a.tipo_imovel || ''` na array de dados

**Correção Necessária:** Adicionar `a.tipo_imovel` aos dados da exportação

---

## PROBLEMA 2: EXCEL ALUNOS - Matrícula aparece como N/A
**Localização:** `static/js/dashboard.js` - função `exportarExcel()` (linha 323)

**Status:** ✗ BUG CRÍTICO
- O array `rows` tem: `a.matricula || ''` (correto)
- Mas a função `listar_alunos()` do backend (linha 885) retorna `'matricula': lead.matricula`
- Problema: O Backend está retornando os dados corretos, mas o Excel pode estar recebendo dados vazios
- Verificar se os alunos estão realmente com matricula no BD

**Correção:** Verificar se o campo `matricula` está sendo populado corretamente no formulário

---

## PROBLEMA 3: EXCEL ALUNOS - Falta EVENTO_ID na tabela de alunos
**Localização:** `static/js/dashboard.js` - função `listar_alunos()` (linha 884) e `exportarExcel()` (linha 322)

**Status:** ✓ JÁ CORRIGIDO
- O backend retorna `evento_id` (linha 884 em app.py)
- O Excel exporta `evento_id` na primeira coluna (linha 322)
- Status: OK

---

## PROBLEMA 4: EXCEL EVENTOS - Cidade e Estado em branco
**Localização:** `static/js/eventos.js` - função `exportarEventosExcel()` (linha 197)

**Status:** ✗ PROBLEMA NO BACKEND
- O export JavaScript tem: `e.cidade || ''` e `e.estado || ''` (correto)
- O problema: Backend em `listar_eventos()` (linha 914-915) retorna `cidade` e `estado` da ESCOLA
- Se evento não tem escola vinculada, esses campos vêm como NULL
- Backend: linhas 902-909 tentam acessar `e.escola.cidade` e `e.escola.estado`

**Verificação Necessária:**
1. Todos os eventos estão com escola vinculada?
2. Todas as escolas têm cidade e estado preenchidos?

---

## PROBLEMA 5: XSS - Caracteres (';">) aparecem no link_galeria
**Localização:** `static/js/dashboard.js` - função `renderizarDetalhesLead()` (linha 598)

**Status:** ✗ ERRO DE ESCAPING
- Linha 598: `<a href="${escapeHtml(lead.link_galeria)}" ...`
- ERRADO: `escapeHtml()` é para conteúdo HTML, não para atributos
- O link_galeria é uma URL, não deve ser escapado com HTML entities
- Ao escapar a URL, caracteres como `?`, `&`, `=` viram entidades HTML, quebrando a URL

**Correção Necessária:**
- Remover `escapeHtml()` do atributo `href`
- Usar apenas `link_galeria` direto ou `encodeURI()` se necessário
- Para segurança XSS em atributos, confiar na validação de URL no backend

---

## PROBLEMA 6: FOTOS - Barra preta nos cards
**Localização:** `static/dashboard.html` (linhas 412-430) e `static/js/dashboard.js` (linhas 425-429)

**Status:** ✗ PROBLEMA DE ASPECT RATIO
- CSS: `.foto-container` tem `width: 90px; height: 120px;` (proporção 3:4 correta)
- CSS: `img` tem `object-fit: cover; object-position: center;`
- Problema provável: As fotos salvas no backend têm proporção errada ou o crop está falhando
- Backend: `processar_foto()` (linhas 318-412) faz crop inteligente e resize para 300x400

**Verificação Necessária:**
1. Checar se as fotos estão sendo salvas com proporção 300x400
2. Checar o EXIF das fotos origem
3. Barra preta pode ser parte da imagem original (não foi cropada corretamente)

---

## PROBLEMA 7: TIPO_IMOVEL faltando no Excel
**Localização:** `static/js/dashboard.js` - função `exportarExcel()` (linhas 321-336)

**Status:** ✗ INCOMPLETO
- Backend retorna `tipo_imovel` (linha 899 em app.py: não está na exportação)
- Excel não tem coluna para tipo de imóvel
- Header tem 14 campos, mas precisa adicionar 1 mais

**Correção Necessária:**
1. Adicionar `a.tipo_imovel || ''` na array `rows`
2. Adicionar `'Tipo Imóvel'` no array `headers`

---

## RESUMO DAS CORREÇÕES NECESSÁRIAS

### Frontend (static/js/dashboard.js)
1. ✗ Linha 335: Adicionar `a.tipo_imovel || ''` nos rows
2. ✗ Linha 338: Adicionar `'Tipo Imóvel'` no header (13º coluna)
3. ✗ Linha 598: Remover `escapeHtml()` do atributo `href`

### Frontend (static/js/eventos.js)
- ✓ OK - Backend já retorna cidade/estado corretamente

### Backend (app.py)
- ✓ OK - Já retorna todos os dados necessários

---

## PRÓXIMOS PASSOS
1. Corrigir XSS no link_galeria (CRÍTICO)
2. Adicionar tipo_imovel ao Excel
3. Verificar qual é o problema com matricula N/A
4. Investigar fotos com barra preta (pode ser problema com imagens originais)
5. Confirmar que eventos têm escolas com cidade/estado preenchidos
