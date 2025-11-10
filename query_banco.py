#!/usr/bin/env python3
"""Query banco para verificar leads"""
import sqlite3
import os

db_path = 'instance/student_system.db'

if not os.path.exists(db_path):
    print(f"❌ Banco não encontrado em {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 80)
print("VERIFICAÇÃO DO BANCO DE DADOS")
print("=" * 80)

# Total de leads
cursor.execute("SELECT COUNT(*) as total FROM leads")
result = cursor.fetchone()
print(f"\n✓ Total de Leads: {result['total']}")

if result['total'] > 0:
    # Últimos 5 leads
    print("\n📋 Últimos 5 Leads cadastrados:")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            l.id, 
            l.nome_formando, 
            l.evento_id, 
            e.escola_id,
            s.nome as escola_nome,
            l.criado_em
        FROM leads l
        LEFT JOIN eventos e ON l.evento_id = e.id
        LEFT JOIN escolas s ON e.escola_id = s.id
        ORDER BY l.criado_em DESC
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"\n  ID: {row['id']}")
        print(f"  Nome: {row['nome_formando']}")
        print(f"  Evento ID: {row['evento_id']}")
        print(f"  Escola: {row['escola_nome'] or '❌ SEM ESCOLA'}")
        print(f"  Criado em: {row['criado_em']}")
else:
    print("❌ Nenhum lead encontrado no banco!")

# Verificar eventos
print("\n" + "=" * 80)
cursor.execute("SELECT COUNT(*) as total FROM eventos")
result = cursor.fetchone()
print(f"\n✓ Total de Eventos: {result['total']}")

if result['total'] > 0:
    cursor.execute("""
        SELECT 
            e.id, 
            s.nome as escola, 
            e.data_evento,
            COUNT(l.id) as total_leads
        FROM eventos e
        LEFT JOIN escolas s ON e.escola_id = s.id
        LEFT JOIN leads l ON e.id = l.evento_id
        GROUP BY e.id
    """)
    
    print("\nEventos e seus leads:")
    for row in cursor.fetchall():
        print(f"  Evento #{row['id']}: {row['escola']} - {row['data_evento']} ({row['total_leads']} leads)")

# Verificar escolas
print("\n" + "=" * 80)
cursor.execute("SELECT COUNT(*) as total FROM escolas")
result = cursor.fetchone()
print(f"\n✓ Total de Escolas: {result['total']}")

print("\n" + "=" * 80)
conn.close()
