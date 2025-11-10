#!/usr/bin/env python3
"""
Script de diagnóstico para verificar problemas no banco de dados
Apenas LEITURA - nenhuma alteração será feita
"""
from app import db, Evento, Escola, Lead

print("\n" + "=" * 70)
print("DIAGNÓSTICO DO BANCO DE DADOS - RELATÓRIO DE EVENTOS")
print("=" * 70)

# 1. Verificar eventos
print("\n📊 EVENTOS:")
print("-" * 70)

todos_eventos = db.session.query(Evento).order_by(Evento.criado_em.desc()).all()
print(f"Total de eventos: {len(todos_eventos)}")

if todos_eventos:
    print("\nDetalhes:")
    for ev in todos_eventos:
        escola_nome = ev.escola.nome if ev.escola else None
        total_leads = len(ev.leads) if hasattr(ev, 'leads') else 0
        status = "✅" if ev.escola else "⚠️ "
        
        print(f"\n{status} Evento #{ev.id}")
        print(f"   Data: {ev.data_evento}")
        print(f"   Tipo: {ev.tipo_formatura}")
        print(f"   Local: {ev.local_evento}")
        print(f"   Escola ID: {ev.escola_id}")
        print(f"   Escola Nome: {escola_nome}")
        print(f"   Status: {ev.status}")
        print(f"   Leads: {total_leads}")

# 2. Contar leads
print("\n\n📋 LEADS:")
print("-" * 70)
total_leads = db.session.query(Lead).count()
print(f"Total de leads: {total_leads}")

# 3. Verificar escolas
print("\n\n🏫 ESCOLAS:")
print("-" * 70)
todas_escolas = db.session.query(Escola).all()
print(f"Total de escolas: {len(todas_escolas)}")

if todas_escolas:
    print("\nDetalhes:")
    for esc in todas_escolas:
        eventos_ligados = len(esc.eventos) if hasattr(esc, 'eventos') else 0
        print(f"  • {esc.nome} (ID: {esc.id})")
        print(f"    Cidade: {esc.cidade}, Estado: {esc.estado}")
        print(f"    Eventos: {eventos_ligados}")

# 4. Verificar inconsistências
print("\n\n🔍 VERIFICAÇÃO DE INCONSISTÊNCIAS:")
print("-" * 70)

eventos_sem_escola = db.session.query(Evento).filter(Evento.escola_id == None).all()
if eventos_sem_escola:
    print(f"⚠️  {len(eventos_sem_escola)} evento(s) SEM ESCOLA VINCULADA:")
    for ev in eventos_sem_escola:
        print(f"   - Evento #{ev.id} (Data: {ev.data_evento}, Tipo: {ev.tipo_formatura})")
else:
    print("✅ Todos os eventos têm escola vinculada!")

# Verificar escolas órfãs
escolas_sem_eventos = [esc for esc in todas_escolas if len(esc.eventos) == 0]
if escolas_sem_eventos:
    print(f"\n⚠️  {len(escolas_sem_eventos)} escola(s) SEM EVENTOS:")
    for esc in escolas_sem_eventos:
        print(f"   - {esc.nome} (ID: {esc.id})")
else:
    print("\n✅ Todas as escolas têm pelo menos um evento!")

print("\n" + "=" * 70)
print("FIM DO DIAGNÓSTICO")
print("=" * 70 + "\n")
