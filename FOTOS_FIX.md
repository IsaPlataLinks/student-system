# ✅ Fix: Contagem de Fotos e Salvamento em Render + Cloudinary

## Problema Original
- ❌ "Fotos Enviadas" mostrava **0** no dashboard mesmo com alunos cadastrados
- ❌ Fotos eram contadas errado (contavam apenas leads com foto de perfil)
- ❌ Fotos de galeria não eram contabilizadas
- ❌ Não havia garantia que fotos fossem salvas em ambos os lugares (Render + Cloudinary)

## Solução Implementada

### 1️⃣ Novo Endpoint para Contagem Correta
**Arquivo:** `app.py`

```python
@app.route('/api/dashboard/fotos-count', methods=['GET'])
@jwt_required()
def contar_fotos_enviadas():
    """Conta fotos da galeria + fotos de leads"""
    total_fotos = GaleriaFoto.query.count()
    total_leads_com_foto = Lead.query.filter(Lead.foto != None).count()
    return jsonify({
        'fotos_galeria': total_fotos,
        'leads_com_foto': total_leads_com_foto,
        'total_fotos': total_fotos + total_leads_com_foto
    })
```

### 2️⃣ Dashboard Usa Contagem Correta
**Arquivo:** `static/js/dashboard.js`

Antes:
```javascript
// ❌ ERRADO - contava apenas leads com foto
const comFotos = todosAlunos.filter((a) => a.foto).length;
document.getElementById('totalFotos').textContent = comFotos;
```

Depois:
```javascript
// ✅ CORRETO - busca do endpoint
async function carregarContagemFotos() {
    const response = await fetch(`${API_URL}/dashboard/fotos-count`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    const data = await response.json();
    document.getElementById('totalFotos').textContent = data.total_fotos;
}
```

### 3️⃣ Salvamento em AMBOS os Lugares

#### `processar_foto()` - Foto de Perfil do Lead
**Antes:** ❌ Salvava **APENAS** no Cloudinary (ou falha = sem fallback)

**Depois:** ✅ Salva em **AMBOS**
```python
def processar_foto(file):
    # 1. Salva LOCALMENTE no Render
    file.save(local_path)
    print(f"[OK] Arquivo salvo localmente: {local_path}")
    
    # 2. Processa (crop 300x400)
    img = img.resize((300, 400), Image.Resampling.LANCZOS)
    img.save(local_path, 'JPEG', quality=85)
    
    # 3. Tenta Cloudinary (se disponível)
    if os.getenv('CLOUDINARY_URL'):
        response = cloudinary.uploader.upload(local_path, folder='fotos-alunos')
        cloudinary_url = response.get('secure_url')
        print(f"[✅ OK] Foto salva LOCALMENTE e no Cloudinary")
        return cloudinary_url
    else:
        # Fallback: retorna URL local se Cloudinary não tiver
        return f'/uploads/{nome_arquivo}'
```

#### `processar_foto_galeria()` - Foto de Galeria
**Antes:** ❌ Salvava **APENAS** no Cloudinary (ou erro fatal)

**Depois:** ✅ Salva em **AMBOS**
```python
def processar_foto_galeria(file):
    # 1. Salva LOCALMENTE no Render
    file.save(local_path)
    
    # 2. Otimiza qualidade
    img.save(local_path, 'JPEG', quality=90, optimize=True)
    
    # 3. Tenta Cloudinary (se disponível)
    if os.getenv('CLOUDINARY_URL'):
        response = cloudinary.uploader.upload(local_path, folder='fotos-galeria')
        cloudinary_url = response.get('secure_url')
        return cloudinary_url
    else:
        # Fallback: URL local
        return f'/uploads/{nome_arquivo}'
```

## Garantias Agora

✅ **Fotos SEMPRE salvam localmente** no Render (`/static/uploads/`)
✅ **Fotos TENTAM salvar** no Cloudinary (se `CLOUDINARY_URL` estiver configurada)
✅ **Sem CLOUDINARY_URL?** Fotos funcionam localmente via `/uploads/` endpoint
✅ **Cloudinary falhar?** Mantém arquivo local como fallback
✅ **Contagem correta** inclui galeria + fotos de leads
✅ **Dashboard atualizado** mostra número real de fotos enviadas

## Arquivos Modificados
- `app.py`
  - ✅ Novo endpoint `/api/dashboard/fotos-count`
  - ✅ `processar_foto()` - salva local + Cloudinary
  - ✅ `processar_foto_galeria()` - salva local + Cloudinary
  
- `static/js/dashboard.js`
  - ✅ Nova função `carregarContagemFotos()`
  - ✅ `atualizarEstatisticas()` usa contagem correta

## Para Testar

1. **Dashboard:**
   - Acesse `/dashboard`
   - Veja "Fotos Enviadas" mostrar número > 0

2. **Upload de Foto de Lead:**
   - Clique em um aluno → "Upload Foto"
   - Verifique pasta `static/uploads/` (arquivo local)
   - Se Cloudinary configurado: verifique URL em Cloudinary

3. **Logs:**
   ```
   [✅ OK] Foto salva LOCALMENTE e no Cloudinary: https://res.cloudinary.com/...
   ```

## Notas Importantes

- `CLOUDINARY_URL` agora é **OPCIONAL** (mas recomendado para produção)
- Sem Cloudinary: fotos servem via endpoint `/uploads/<filename>`
- Com Cloudinary: prioriza URL do Cloudinary, mantém local como backup
- Banco de dados armazena URL (Cloudinary ou local)

---

**Commit:** `8fe61f8` - Fix: contagem de fotos e salvamento duplo
