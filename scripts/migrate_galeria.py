#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migração para adicionar campos de galeria em nuvem
Execute com: python migrate_galeria.py
"""

import os
import sys
import sqlite3
import io
from app import app, db

# Fix encoding para Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def migrate_sqlite():
    """Migração para SQLite"""
    print("📊 Detectado: Banco SQLite")
    
    # Obter caminho do banco
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    db_path = os.path.join(instance_path, 'student_system.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        return False
    
    print(f"📁 Banco encontrado em: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar colunas existentes
        cursor.execute("PRAGMA table_info(leads)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"✓ Colunas atuais: {columns}")
        print()
        
        # Adicionar link_galeria
        if 'link_galeria' not in columns:
            print("➕ Adicionando coluna 'link_galeria'...")
            try:
                cursor.execute('ALTER TABLE leads ADD COLUMN link_galeria VARCHAR(500)')
                conn.commit()
                print("   ✅ Coluna 'link_galeria' adicionada com sucesso!")
            except Exception as e:
                print(f"   ⚠️  {str(e)}")
                conn.rollback()
        else:
            print("✓ Coluna 'link_galeria' já existe")
        
        print()
        
        # Adicionar descricao_galeria
        if 'descricao_galeria' not in columns:
            print("➕ Adicionando coluna 'descricao_galeria'...")
            try:
                cursor.execute('ALTER TABLE leads ADD COLUMN descricao_galeria TEXT')
                conn.commit()
                print("   ✅ Coluna 'descricao_galeria' adicionada com sucesso!")
            except Exception as e:
                print(f"   ⚠️  {str(e)}")
                conn.rollback()
        else:
            print("✓ Coluna 'descricao_galeria' já existe")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("🔄 MIGRAÇÃO: Adicionar Campos de Galeria em Nuvem")
    print("=" * 60)
    print()
    
    # Verificar tipo de banco
    database_url = os.environ.get('DATABASE_URL', '')
    
    if 'postgresql' in database_url or 'postgres' in database_url:
        print("📊 Detectado: Banco PostgreSQL")
        print("⚠️  Para PostgreSQL, execute:")
        print()
        print("   ALTER TABLE leads ADD COLUMN link_galeria VARCHAR(500);")
        print("   ALTER TABLE leads ADD COLUMN descricao_galeria TEXT;")
        print()
    else:
        # Default SQLite
        success = migrate_sqlite()
        
        if success:
            print()
            print("=" * 60)
            print("✅ Migração concluída com sucesso!")
            print("=" * 60)
            print()
            print("📝 Resumo:")
            print("   - Campo 'link_galeria' (VARCHAR 500)")
            print("   - Campo 'descricao_galeria' (TEXT)")
            print()
            print("🚀 Sistema pronto para usar galeria em nuvem!")
            return 0
        else:
            print()
            print("❌ Migração falhou!")
            return 1

if __name__ == '__main__':
    sys.exit(main())
