#!/usr/bin/env python3
"""
Script de migração para adicionar campos de galeria em nuvem
Execute com: python migrate_cloud_photos.py
"""

import os
import sys
from app import app, db

def migrate():
    with app.app_context():
        try:
            # Inspecionar banco de dados
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('leads')]
            
            print("📊 Verificando estrutura do banco de dados...")
            print(f"Colunas atuais na tabela 'leads': {columns}")
            print()
            
            # Verificar e adicionar coluna link_galeria
            if 'link_galeria' not in columns:
                print("➕ Adicionando coluna 'link_galeria'...")
                try:
                    db.session.execute('ALTER TABLE leads ADD COLUMN link_galeria VARCHAR(500)')
                    db.session.commit()
                    print("   ✅ Coluna 'link_galeria' adicionada com sucesso!")
                except Exception as e:
                    print(f"   ⚠️  Aviso: {str(e)}")
                    db.session.rollback()
            else:
                print("✓ Coluna 'link_galeria' já existe")
            
            print()
            
            # Verificar e adicionar coluna descricao_galeria
            if 'descricao_galeria' not in columns:
                print("➕ Adicionando coluna 'descricao_galeria'...")
                try:
                    db.session.execute('ALTER TABLE leads ADD COLUMN descricao_galeria TEXT')
                    db.session.commit()
                    print("   ✅ Coluna 'descricao_galeria' adicionada com sucesso!")
                except Exception as e:
                    print(f"   ⚠️  Aviso: {str(e)}")
                    db.session.rollback()
            else:
                print("✓ Coluna 'descricao_galeria' já existe")
            
            print()
            print("=" * 60)
            print("✅ Migração concluída com sucesso!")
            print("=" * 60)
            print()
            print("📝 Resumo:")
            print("   - Campo 'link_galeria' (VARCHAR 500): Link de galeria em nuvem")
            print("   - Campo 'descricao_galeria' (TEXT): Descrição opcional da galeria")
            print()
            print("🚀 Sistema pronto para usar a funcionalidade de galas em nuvem!")
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    migrate()
