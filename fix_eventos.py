#!/usr/bin/env python3
"""
Script para corrigir eventos sem escola vinculada
"""
from app import db, Evento, Escola

print("=" * 60)
print("CORRIGINDO EVENTOS SEM ESCOLA VINCULADA")
print("=" * 60)

# Listar eventos sem escola
eventos_sem_escola = db.session.query(Evento).filter(Evento.escola_id == None).all()

if not eventos_sem_escola:
    print("✅ Todos os eventos têm escola vinculada!")
else:
    print(f"\n⚠️  Encontrados {len(eventos_sem_escola)} eventos sem escola:")
    
    for idx, ev in enumerate(eventos_sem_escola, 1):
        print(f"\n{idx}. Evento #{ev.id}")
        print(f"   Data: {ev.data_evento}")
        print(f"   Tipo: {ev.tipo_formatura}")
        print(f"   Local: {ev.local_evento}")
        print(f"   \n   Opções:")
        print(f"   a) Deletar este evento")
        print(f"   b) Criar/vincular a uma escola")
        print(f"   c) Vincular a escola existente")
    
    print("\n" + "-" * 60)
    print("AÇÃO: Deletando eventos órfãos (sem escola)...")
    print("-" * 60)
    
    for ev in eventos_sem_escola:
        db.session.delete(ev)
        print(f"✓ Evento #{ev.id} deletado")
    
    db.session.commit()
    print("\n✅ Limpeza concluída!\n")

# Mostrar status final
print("=" * 60)
print("STATUS FINAL DOS EVENTOS")
print("=" * 60)

todos = db.session.query(Evento).order_by(Evento.criado_em.desc()).all()
print(f"\nTotal de eventos: {len(todos)}\n")

if todos:
    for ev in todos:
        escola_nome = ev.escola.nome if ev.escola else "❌ SEM ESCOLA"
        status = "✅" if ev.escola else "❌"
        print(f"{status} #{ev.id:3d} | {ev.data_evento} | {ev.tipo_formatura:12s} | {escola_nome}")
else:
    print("Nenhum evento encontrado.")
