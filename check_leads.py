#!/usr/bin/env python3
from app import app, db, Lead, Evento, Escola, Usuario

with app.app_context():
    print("\n" + "="*80)
    print("VERIFICAÇÃO DO BANCO")
    print("="*80)
    
    # Total de leads
    total = Lead.query.count()
    print(f"\n✓ Total de Leads: {total}")
    
    if total == 0:
        print("\n❌ PROBLEMA: Nenhum lead encontrado!")
    else:
        print(f"\n📋 Últimos 5 Leads:")
        leads = Lead.query.order_by(Lead.criado_em.desc()).limit(5).all()
        
        for lead in leads:
            print(f"\n  ID: {lead.id}")
            print(f"  Nome: {lead.nome_formando}")
            print(f"  Email: {lead.email}")
            print(f"  Evento ID: {lead.evento_id}")
            
            if lead.evento:
                print(f"  ✓ Evento encontrado: {lead.evento.id}")
                if lead.evento.escola:
                    print(f"  ✓ Escola: {lead.evento.escola.nome}")
                else:
                    print(f"  ❌ Evento SEM escola associada!")
            else:
                print(f"  ❌ Evento {lead.evento_id} não encontrado!")
            
            print(f"  Vendedor ID: {lead.vendedor_id}")
            print(f"  Criado em: {lead.criado_em}")
    
    # Total de eventos
    total_eventos = Evento.query.count()
    print(f"\n\n✓ Total de Eventos: {total_eventos}")
    
    if total_eventos > 0:
        print("\nEventos cadastrados:")
        for evento in Evento.query.all():
            leads_count = Lead.query.filter_by(evento_id=evento.id).count()
            escola_nome = evento.escola.nome if evento.escola else "❌ SEM ESCOLA"
            print(f"  • Evento #{evento.id}: {escola_nome} ({leads_count} leads)")
    
    # Total de escolas
    total_escolas = Escola.query.count()
    print(f"\n\n✓ Total de Escolas: {total_escolas}")
    
    # Total de usuários
    total_users = Usuario.query.count()
    print(f"\n✓ Total de Usuários: {total_users}")
    
    print("\n" + "="*80 + "\n")
