#!/usr/bin/env python3
"""Debug script para verificar leads no banco"""

from app import app, db, Lead, Evento, Escola

with app.app_context():
    print("=" * 60)
    print("DEBUG: Verificando Leads no Banco")
    print("=" * 60)
    
    total_leads = Lead.query.count()
    print(f"\n✓ Total de Leads: {total_leads}")
    
    if total_leads == 0:
        print("⚠️  Nenhum lead encontrado!")
    else:
        print("\nÚltimos 5 Leads:")
        leads = Lead.query.order_by(Lead.criado_em.desc()).limit(5).all()
        
        for lead in leads:
            print(f"\n  ID: {lead.id}")
            print(f"  Nome: {lead.nome_formando}")
            print(f"  Evento ID: {lead.evento_id}")
            
            if lead.evento:
                print(f"  Evento Data: {lead.evento.data_evento}")
                if lead.evento.escola:
                    print(f"  Escola: {lead.evento.escola.nome}")
                else:
                    print(f"  ⚠️  Evento {lead.evento.id} SEM escola!")
            else:
                print(f"  ⚠️  Evento {lead.evento_id} não encontrado!")
            
            print(f"  Criado em: {lead.criado_em}")
    
    print("\n" + "=" * 60)
    print("Total de Eventos:", Evento.query.count())
    print("Total de Escolas:", Escola.query.count())
    print("=" * 60)
