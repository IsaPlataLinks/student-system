# 🚀 Setup do Student System no Render

## Pré-requisitos
- Conta no Render.com
- Repositório GitHub conectado

## 1️⃣ Criar Banco de Dados PostgreSQL

1. No dashboard do Render, clique em **New +**
2. Selecione **PostgreSQL**
3. Configure:
   - **Name**: `student-system-db`
   - **Region**: Escolha a mais próxima
   - **PostgreSQL Version**: 15
   - **Free tier** (ou pago conforme necessário)
4. Copie a **Internal Database URL** gerada

## 2️⃣ Criar Disk (Volume Persistente)

1. No dashboard, clique em **New +**
2. Selecione **Disk**
3. Configure:
   - **Name**: `student-system-uploads`
   - **Size**: 10GB (ou mais se precisar)
   - **Mount Path**: `/mnt/data/uploads`

## 3️⃣ Criar Web Service

1. No dashboard, clique em **New +**
2. Selecione **Web Service**
3. Conecte seu repositório GitHub (`student-system`)
4. Configure:

   | Campo | Valor |
   |-------|-------|
   | **Name** | student-system |
   | **Environment** | Python 3 |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn app:app` |
   | **Plan** | Free (ou pago) |

5. Clique em **Advanced**
6. Em **Disks**, clique em **Add Disk**:
   - **Disk**: `student-system-uploads`
   - **Mount Path**: `/mnt/data/uploads`

7. Em **Environment Variables**, adicione:

   ```
   DATABASE_URL = <Cole a URL do PostgreSQL aqui>
   UPLOAD_PATH = /mnt/data/uploads
   JWT_SECRET_KEY = <Cole uma chave secreta forte aqui>
   ```

8. Clique em **Create Web Service**

## 4️⃣ Verificar Deploy

Após o deploy ser concluído:

```bash
# Teste a API de login
curl -X POST https://<seu-app>.onrender.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"login":"admin","senha":"admin123"}'
```

Resposta esperada:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "nome": "Administrador",
  "tipo_usuario": "admin"
}
```

## 5️⃣ Testar Upload de Fotos

1. Acesse `/dashboard`
2. Login: `admin` / `admin123`
3. Crie um evento
4. Abra um lead e tente fazer upload de foto
5. Verifique se a foto aparece e persiste após reinicios

## 📝 Variáveis de Ambiente

| Variável | Valor | Onde |
|----------|-------|------|
| `DATABASE_URL` | URL do PostgreSQL | Render env vars |
| `UPLOAD_PATH` | `/mnt/data/uploads` | Render env vars |
| `JWT_SECRET_KEY` | String aleatória forte | Render secrets |

## 🔧 Troubleshooting

### Fotos não carregam após reiniciar?
- Verifique se o Disk está montado em `/mnt/data/uploads`
- Verifique se `UPLOAD_PATH` está correto no environment

### PostgreSQL não conecta?
- Copie a URL corretamente (Internal Database URL)
- Certifique-se de que o serviço PostgreSQL está ativo
- Verifique firewall/allow-list do Render

### Erro ao enviar foto?
- Verifique permissões da pasta `/mnt/data/uploads`
- Veja os logs: `Logs` tab no Render dashboard

## 📊 Estrutura Final no Render

```
render.com
├── Web Service: student-system (app.py rodhando)
├── PostgreSQL: student-system-db (banco de dados)
└── Disk: student-system-uploads montado em /mnt/data/uploads
```

## ✅ Após Setup

- Fotos são salvas em `/mnt/data/uploads` (persistente)
- Banco de dados está em PostgreSQL (persistente)
- App reinicia sem perder dados
