#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the API directly"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app, db, Lead, Evento, Escola, Usuario

# Criar contexto da app
with app.app_context():
    print("\n" + "="*80)
    print("DEBUG: VERIFICACAO DO BANCO DE DADOS")
    print("="*80)
    
    try:
        # Contar leads
        lead_count = db.session.query(Lead).count()
        print(f"\nTotal de Leads: {lead_count}")
        
        if lead_count > 0:
            print("\nDetalhes dos Leads:")
            leads = db.session.query(Lead).order_by(Lead.criado_em.desc()).limit(10).all()
            
            for i, lead in enumerate(leads, 1):
                print(f"\n  [{i}] ID {lead.id}: {lead.nome_formando}")
                print(f"      Email: {lead.email}")
                print(f"      Evento ID: {lead.evento_id}")
                print(f"      Vendedor ID: {lead.vendedor_id}")
                
                # Verificar evento
                evento = db.session.query(Evento).filter_by(id=lead.evento_id).first()
                if evento:
                    print(f"      > Evento: {evento.id}")
                    if evento.escola:
                        print(f"      > Escola: {evento.escola.nome}")
                    else:
                        print(f"      >> Evento sem escola!")
                else:
                    print(f"      >> Evento nao encontrado!")
        else:
            print("\nAVISO: Nenhum lead encontrado!")
        
        # Eventos
        evento_count = db.session.query(Evento).count()
        print(f"\nTotal de Eventos: {evento_count}")
        
        # Escolas
        escola_count = db.session.query(Escola).count()
        print(f"Total de Escolas: {escola_count}")
        
        # Usuários
        user_count = db.session.query(Usuario).count()
        print(f"Total de Usuarios: {user_count}")
        
    except Exception as e:
        print(f"\nERRO ao consultar: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80 + "\n")
