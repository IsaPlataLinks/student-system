"""
Script de migração para aumentar o tamanho do campo letra_turma de 2 para 4 caracteres
"""
from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        # Verifica se é SQLite ou PostgreSQL
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        if 'sqlite' in db_uri:
            # SQLite não suporta ALTER COLUMN, precisa recriar a tabela
            print("⚠️ SQLite detectado. Para alterar o tamanho do campo, execute:")
            print("   1. Faça backup do banco: instance/student_system.db")
            print("   2. Reinicie o servidor - o SQLAlchemy criará a coluna corretamente em novos registros")
            print("   3. Campos antigos com 2 caracteres continuarão funcionando")
        else:
            # PostgreSQL
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE leads ALTER COLUMN letra_turma TYPE VARCHAR(4)"))
                    conn.commit()
                    print("✅ Coluna letra_turma atualizada para VARCHAR(4) com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao migrar: {e}")

if __name__ == '__main__':
    migrate()
