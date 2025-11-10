#!/usr/bin/env python3
"""Debug script para verificar leads no banco de dados"""

from app import app, db, Lead, Evento, Usuario, Escola

with app.app_context():
    print("=" * 60)
    print("VERIFICAÇÃO DE LEADS NO BANCO")
    print("=" * 60)
    
    # Total de leads
    total_leads = db.session.query(Lead).count()
    print(f"\n📊 Total de leads: {total_leads}")
    
    if total_leads == 0:
        print("⚠️  Nenhum lead encontrado no banco!")
    else:
        # Listar todos os leads com detalhes
        leads = db.session.query(Lead).all()
        for lead in leads:
            evento = Evento.query.get(lead.evento_id)
            escola = evento.escola.nome if evento and evento.escola else "SEM ESCOLA"
            print(f"\n  Lead ID: {lead.id}")
            print(f"    - Nome: {lead.nome_formando}")
            print(f"    - Evento: {evento.id if evento else 'INVÁLIDO'} ({escola})")
            print(f"    - Matrícula: {lead.matricula}")
            print(f"    - Email: {lead.email}")
            print(f"    - Vendedor ID: {lead.vendedor_id}")
            print(f"    - Status: {lead.status_lead}")
            print(f"    - Criado em: {lead.criado_em}")
    
    # Verificar eventos e seus leads
    print(f"\n\n{'='*60}")
    print("EVENTOS E CONTAGEM DE LEADS")
    print("=" * 60)
    
    eventos = db.session.query(Evento).all()
    for evt in eventos:
        total_evt_leads = len(evt.leads)
        escola = evt.escola.nome if evt.escola else "SEM ESCOLA"
        print(f"\n  Evento ID: {evt.id}")
        print(f"    - Escola: {escola}")
        print(f"    - Data: {evt.data_evento}")
        print(f"    - Total de leads: {total_evt_leads}")
        if total_evt_leads > 0:
            for lead in evt.leads:
                print(f"      └─ {lead.nome_formando} ({lead.matricula})")
