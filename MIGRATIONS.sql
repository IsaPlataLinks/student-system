-- MIGRATIONS: Adicionar novos campos ao banco de dados
-- Suporta PostgreSQL e SQLite

-- ==================== PostgreSQL ====================

-- Se você estiver usando PostgreSQL (recomendado em produção)
-- Execute os comandos abaixo:

ALTER TABLE leads ADD COLUMN numero VARCHAR(10);
ALTER TABLE leads ADD COLUMN complemento VARCHAR(100);
ALTER TABLE leads ADD COLUMN tipo_imovel VARCHAR(20);

-- Verificar que as colunas foram criadas:
\d leads

-- ==================== SQLite ====================

-- Se você estiver usando SQLite (desenvolvimento apenas):

ALTER TABLE leads ADD COLUMN numero VARCHAR(10);
ALTER TABLE leads ADD COLUMN complemento VARCHAR(100);
ALTER TABLE leads ADD COLUMN tipo_imovel VARCHAR(20);

-- Verificar que as colunas foram criadas:
PRAGMA table_info(leads);

-- ==================== Backup (Recomendado Antes) ====================

-- PostgreSQL - Backup completo
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

-- SQLite - Backup completo (local)
cp instance/student_system.db instance/student_system.backup_$(date +%Y%m%d_%H%M%S).db

-- ==================== Restaurar de Backup (Se Necessário) ====================

-- PostgreSQL - Restaurar
psql $DATABASE_URL < backup_20251111_103000.sql

-- SQLite - Restaurar (local)
cp instance/student_system.backup_20251111_103000.db instance/student_system.db

-- ==================== Verificação Pós-Migração ====================

-- PostgreSQL - Verificar dados
SELECT COUNT(*) FROM leads;
SELECT id, numero, complemento, tipo_imovel FROM leads LIMIT 5;

-- SQLite - Verificar dados
SELECT COUNT(*) FROM leads;
SELECT id, numero, complemento, tipo_imovel FROM leads LIMIT 5;

-- ==================== Como Executar ====================

-- No Render (PostgreSQL):
-- 1. Conecte via SSH em seu serviço
-- 2. psql $DATABASE_URL < MIGRATIONS.sql

-- Localmente (SQLite):
-- 1. sqlite3 instance/student_system.db
-- 2. Copie os comandos SQLite acima

-- Via Python (Automático - RECOMENDADO):
-- 1. Simplesmente execute o app.py
-- 2. SQLAlchemy rodará `db.create_all()` automaticamente
-- 3. As colunas serão criadas se não existirem

-- ==================== Exemplo: Executar via Python ====================

/*
from app import app, db

with app.app_context():
    db.create_all()
    print("✅ Tabelas e colunas criadas/verificadas")
*/

-- ==================== Verificar Exatamente Quais Colunas Existem ====================

-- PostgreSQL:
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'leads' 
-- ORDER BY ordinal_position;

-- SQLite:
-- PRAGMA table_info(leads);

-- ==================== Se Tudo der Errado: Rollback ====================

-- PostgreSQL - Remover as colunas (CUIDADO: Apaga dados!)
ALTER TABLE leads DROP COLUMN numero;
ALTER TABLE leads DROP COLUMN complemento;
ALTER TABLE leads DROP COLUMN tipo_imovel;

-- SQLite - Remover as colunas
-- Nota: SQLite não tem DROP COLUMN nativo
-- Solução: Criar tabela nova sem as colunas e migrar dados
-- (Veja DATABASE_PERSISTENCE_FIX.md para instruções completas)

-- ==================== Status Esperado Pós-Migração ====================

-- Colunas adicionadas:
-- - numero (VARCHAR/TEXT, nullable)
-- - complemento (VARCHAR/TEXT, nullable)
-- - tipo_imovel (VARCHAR/TEXT, nullable)

-- Dados antigos:
-- - numero, complemento, tipo_imovel estarão NULL para registros antigos
-- - Isso é esperado e OK

-- Novos dados:
-- - Serão preenchidos automaticamente pelo formulário/API
