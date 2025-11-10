from app import app, db, Lead, Evento, Escola

with app.app_context():
    output = []
    output.append("\n" + "="*80)
    output.append("VERIFICAÇÃO DO BANCO")
    output.append("="*80)
    
    total = Lead.query.count()
    output.append(f"\n✓ Total de Leads: {total}")
    
    if total == 0:
        output.append("\n❌ PROBLEMA: Nenhum lead encontrado!")
    else:
        output.append(f"\n📋 Últimos 5 Leads:")
        leads = Lead.query.order_by(Lead.criado_em.desc()).limit(5).all()
        
        for lead in leads:
            output.append(f"\n  ID: {lead.id}")
            output.append(f"  Nome: {lead.nome_formando}")
            output.append(f"  Evento ID: {lead.evento_id}")
            
            if lead.evento:
                output.append(f"  ✓ Evento encontrado: {lead.evento.id}")
                if lead.evento.escola:
                    output.append(f"  ✓ Escola: {lead.evento.escola.nome}")
                else:
                    output.append(f"  ❌ Evento SEM escola!")
            else:
                output.append(f"  ❌ Evento não encontrado!")
    
    total_eventos = Evento.query.count()
    output.append(f"\n\n✓ Total de Eventos: {total_eventos}")
    
    total_escolas = Escola.query.count()
    output.append(f"\n✓ Total de Escolas: {total_escolas}")
    
    output.append("\n" + "="*80)
    
    result = "\n".join(output)
    print(result)
    
    # Também salva em arquivo
    with open("banco_check.txt", "w", encoding="utf-8") as f:
        f.write(result)
