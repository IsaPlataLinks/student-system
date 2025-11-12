# 🔍 AUDITORIA COMPLETA: TODOS OS FLUXOS DE UPLOAD DE FOTOS

## ⚠️ RESULTADO: FLUXOS DESPADRONIZADOS!

---

## 📊 RESUMO EXECUTIVO

| Fluxo | Endpoint | Método | Destino | Status |
|-------|----------|--------|---------|--------|
| 1️⃣ Cadastro Lead | `POST /api/cadastro` | processar_foto() | **Cloudinary** | ✅ |
| 2️⃣ Atualizar Foto | `PATCH /api/leads/<id>/foto` | processar_foto() | **Cloudinary** | ✅ |
| 3️⃣ Upload Galeria | `POST /api/eventos/<id>/galeria` | direto | **ARQUIVO LOCAL** | ❌ |

---

## 🔴 FLUXO 1: CADASTRO DE NOVO LEAD (COM FOTO)

**Endpoint:** `POST /api/cadastro`
**Função:** `def cadastrar_lead()` (linhas 1031-1138)
**Route:** `@app.route('/api/cadastro', methods=['POST'])`

### Fluxo:
```
request.files['foto']
    ↓
1088: if 'foto' in request.files and request.files['foto'].filename:
    ↓
1090: foto_filename = processar_foto(request.files['foto'])
    ↓
[processar_foto() linhas 318-409]:
  1. Salva temporariamente localmente
  2. PIL: crop + resize (300x400)
  3. ✅ cloudinary.uploader.upload() [linha 376]
  4. Remove arquivo local
  5. Retorna URL HTTPS
    ↓
1110: foto=foto_filename (URL Cloudinary)
    ↓
1115: db.session.commit()
```

### Status:
- ✅ Upload para Cloudinary: **SIM**
- ✅ Arquivo local removido: **SIM**
- ✅ Banco armazena: **URL HTTPS Cloudinary**

---

## 🟡 FLUXO 2: ATUALIZAR FOTO DO LEAD (DASHBOARD)

**Endpoint:** `PATCH /api/leads/<int:lead_id>/foto`
**Função:** `def atualizar_foto_lead()` (linhas 1295-1336)
**Route:** `@app.route('/api/leads/<int:lead_id>/foto', methods=['PATCH'])`

### Fluxo:
```
request.files['foto']
    ↓
1302-1307: Validação básica
    ↓
1310-1321: Delete foto antiga
  - Se for local: deleta disco
  - Se for Cloudinary: apenas loga (❌ NÃO DELETA)
    ↓
1324: nome_foto = processar_foto(foto_file)
    ↓
[processar_foto() - mesmo do Fluxo 1]
  1. Salva temporariamente
  2. PIL: crop + resize (300x400)
  3. ✅ cloudinary.uploader.upload() [linha 376]
  4. Remove arquivo local
  5. Retorna URL HTTPS
    ↓
1325: lead.foto = nome_foto (URL Cloudinary)
    ↓
1328: db.session.commit()
```

### Status:
- ✅ Upload para Cloudinary: **SIM**
- ✅ Arquivo local removido: **SIM**
- ✅ Banco armazena: **URL HTTPS Cloudinary**
- ⚠️ Limpeza Cloudinary antigo: **NÃO**

---

## 🔴 FLUXO 3: UPLOAD DE GALERIA (EVENTO)

**Endpoint:** `POST /api/eventos/<int:evento_id>/galeria`
**Função:** `def upload_galeria_foto()` (linhas 1412-1476)
**Route:** `@app.route('/api/eventos/<int:evento_id>/galeria', methods=['POST'])`

### ⚠️ PROBLEMA CRÍTICO:

```
request.files.getlist('fotos')
    ↓
1422: arquivos = request.files.getlist('fotos')
    ↓
1430: for arquivo in arquivos:
    ↓
1441-1444: SALVA ARQUIVO LOCALMENTE
  filename = secure_filename(arquivo.filename or 'foto.jpg')
  timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
  nome_arquivo = f"galeria_{evento_id}_{timestamp}_{filename}"
  caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
    ↓
1446: arquivo.save(caminho)  ❌ AQUI FICA LOCAL!
    ↓
1450-1453: Otimiza JPEG
    ↓
1458-1462: Salva no banco
  GaleriaFoto(
    evento_id=evento_id,
    lead_id=int(lead_id) if lead_id else None,
    nome_arquivo=nome_arquivo,  ❌ É CAMINHO LOCAL!
    descricao=descricao
  )
```

### Status:
- ❌ Upload para Cloudinary: **NÃO**
- ❌ Arquivo local: **SIM - PERMANECE NO DISCO**
- ❌ Banco armazena: **Caminho local (galeria_2025_.._.jpg)**
- 🚨 **DESPADRONIZADO**

### Retorno em GET /api/eventos/<id>/galeria (linhas 1478-1494):
```python
resultado.append({
    'id': foto.id,
    'url': f'/uploads/{foto.nome_arquivo}',  ← Referencia local!
    ...
})
```

---

## 📊 TABELA COMPARATIVA

```
╔════════════════════╦══════════════════╦═════════════════╦═══════════════════════╗
║ FLUXO              ║ UPLOAD DESTINO   ║ ARQUIVO LOCAL   ║ BANCO DE DADOS        ║
╠════════════════════╬══════════════════╬═════════════════╬═══════════════════════╣
║ Cadastro Lead      ║ Cloudinary ✅    ║ Deletado ✅     ║ URL HTTPS Cloudinary  ║
║ Atualizar Foto     ║ Cloudinary ✅    ║ Deletado ✅     ║ URL HTTPS Cloudinary  ║
║ Upload Galeria     ║ LOCAL ❌         ║ Mantido ❌      ║ Caminho local ❌      ║
╚════════════════════╩══════════════════╩═════════════════╩═══════════════════════╝
```

---

## 🚨 PROBLEMAS IDENTIFICADOS

### 1. **Fluxo de Galeria Despadronizado**
- Não usa Cloudinary
- Salva em arquivo local
- Depende de disco do servidor
- Em produção (Render): vai perder fotos em cada deploy
- ❌ **CRÍTICO**

### 2. **Inconsistência no Banco de Dados**
```
Lead.foto         → URL HTTPS (https://res.cloudinary.com/...)
GaleriaFoto.nome_arquivo → Caminho local (galeria_2025_..._foto.jpg)
```

### 3. **Endpoints Retornam Formatos Diferentes**
```
/api/leads/<id>                 → foto_url (processado)
/api/alunos                     → foto (processado)
/api/eventos/<id>/galeria       → /uploads/{nome} (local)
```

### 4. **Falta de Limpeza Cloudinary**
- Ao atualizar foto, imagem antiga não é deletada
- Acumula lixo no Cloudinary

---

## 💼 IMPACTO EM PRODUÇÃO (Render)

### Deploy no Render (Container Efêmero):
```
✅ Cadastro + Foto     → Foto vai para Cloudinary → Persiste após deploy
✅ Atualizar Foto      → Foto vai para Cloudinary → Persiste após deploy
❌ Galeria             → Foto salva LOCAL → PERDE TUDO após deploy
```

**Resultado:** Fotos de galeria desaparecem após cada deploy no Render!

---

## ✅ SOLUÇÃO: PADRONIZAR TODOS OS FLUXOS

### Opção A: TODOS para Cloudinary (RECOMENDADO)

#### Modificar `upload_galeria_foto()`:

```python
@app.route('/api/eventos/<int:evento_id>/galeria', methods=['POST'])
@jwt_required()
def upload_galeria_foto(evento_id):
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
            continue
        
        # ✅ USAR processar_foto_galeria() - NOVO
        try:
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
        except Exception as e:
            print(f"❌ Erro ao processar foto galeria: {str(e)}")
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
```

#### Nova função: `processar_foto_galeria()`

```python
def processar_foto_galeria(file):
    """
    Processa foto para galeria (sem redimensionar, apenas otimiza)
    Salva direto no Cloudinary
    Retorna URL HTTPS
    """
    if not file:
        return None

    filename = secure_filename(file.filename or 'foto.jpg')
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    nome_arquivo = f"{timestamp}_{filename}"

    print(f"[DEBUG] Processando foto galeria: {file.filename}")
    
    # Salva temporariamente
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    try:
        file.save(temp_path)
        print(f"[OK] Arquivo salvo temporariamente: {temp_path}")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar arquivo: {str(e)}")
        raise

    # Otimizar apenas qualidade (sem redimensionar)
    try:
        with Image.open(temp_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(temp_path, 'JPEG', quality=90, optimize=True)
        
        # ✅ Upload obrigatório para Cloudinary
        if not os.getenv('CLOUDINARY_URL'):
            raise Exception("[ERRO] CLOUDINARY_URL não configurado.")
        
        response = cloudinary.uploader.upload(
            temp_path,
            folder='fotos-galeria',  # Pasta diferente
            resource_type='image',
            use_filename=True,
            unique_filename=False,
            overwrite=True
        )
        
        cloudinary_url = response.get('secure_url')
        if not cloudinary_url:
            cloudinary_url = response.get('url', '').replace('http://', 'https://')
        
        print(f"[OK] Foto galeria enviada para Cloudinary: {cloudinary_url}")
        
        # Remove arquivo local
        try:
            os.remove(temp_path)
        except:
            pass
        
        return cloudinary_url
    
    except Exception as e:
        print(f"[ERRO] Erro ao processar foto galeria: {str(e)}")
        try:
            os.remove(temp_path)
        except:
            pass
        raise
```

#### Atualizar GET /api/eventos/<id>/galeria:

```python
@app.route('/api/eventos/<int:evento_id>/galeria', methods=['GET'])
@jwt_required()
def listar_galeria(evento_id):
    fotos = GaleriaFoto.query.filter_by(evento_id=evento_id).order_by(GaleriaFoto.criado_em.desc()).all()
    
    resultado = []
    for foto in fotos:
        resultado.append({
            'id': foto.id,
            'url': foto.nome_arquivo,  # ← Já é URL Cloudinary!
            'nome_arquivo': foto.nome_arquivo,
            'descricao': foto.descricao,
            'lead_id': foto.lead_id,
            'criado_em': foto.criado_em.isoformat()
        })
    
    return jsonify(resultado), 200
```

---

## 📋 CHECKLIST PÓS-IMPLEMENTAÇÃO

Após padronizar todos os fluxos:

- [ ] Fluxo 1 (Cadastro) → Cloudinary ✅
- [ ] Fluxo 2 (Atualizar Foto) → Cloudinary ✅
- [ ] Fluxo 3 (Galeria) → Cloudinary ✅
- [ ] Todos retornam URL HTTPS
- [ ] Nenhum arquivo persiste local
- [ ] Testes em produção (Render)
- [ ] Implementar limpeza Cloudinary antigo
- [ ] Documentar mudança no README

---

## 🎯 CONCLUSÃO

**Status Atual:** ❌ DESPADRONIZADO
- 2/3 fluxos usam Cloudinary
- 1/3 fluxo usa arquivo local

**Status Necessário:** ✅ PADRONIZADO
- Todos os fluxos usam Cloudinary
- Consistência entre Lead e GaleriaFoto
- Segurança em produção (Render)
