#!/usr/bin/env python
"""Script para adicionar colunas faltantes ao banco de dados"""

import os
from sqlalchemy import text
from app import app, db

def add_missing_columns():
    """Adiciona colunas que faltam na tabela leads"""
    with app.app_context():
        try:
            # Tenta adicionar a coluna 'numero' se não existir
            db.session.execute(text("""
                ALTER TABLE leads 
                ADD COLUMN IF NOT EXISTS numero VARCHAR(10)
            """))
            print("✅ Coluna 'numero' adicionada/verificada")
            
            # Tenta adicionar a coluna 'ano_formatura' se não existir
            db.session.execute(text("""
                ALTER TABLE leads 
                ADD COLUMN IF NOT EXISTS ano_formatura INTEGER
            """))
            print("✅ Coluna 'ano_formatura' adicionada/verificada")
            
            db.session.commit()
            print("✅ Migração concluída com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro na migração: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_missing_columns()
