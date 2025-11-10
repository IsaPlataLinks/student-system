#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para DELETAR TODOS os eventos, leads e escolas do banco de dados
CUIDADO: Esta acao eh irreversivel!
"""
from app import app, db, Evento, Lead, Escola, GaleriaFoto

with app.app_context():
    print("\n" + "=" * 70)
    print("LIMPEZA COMPLETA DO BANCO DE DADOS")
    print("=" * 70)

    # Contar antes
    print("\nDADOS ANTES DA LIMPEZA:")
    print("-" * 70)
    print("  * Escolas: {}".format(Escola.query.count()))
    print("  * Eventos: {}".format(Evento.query.count()))
    print("  * Leads/Cadastros: {}".format(Lead.query.count()))
    print("  * Fotos de Galeria: {}".format(GaleriaFoto.query.count()))

    print("\nDELETANDO...")
    print("-" * 70)

    # Deletar na ordem correta (por causa das foreign keys)
    try:
        # 1. Deletar fotos de galeria (relacionadas a leads e eventos)
        fotos = GaleriaFoto.query.all()
        if fotos:
            for foto in fotos:
                db.session.delete(foto)
            db.session.commit()
            print("[OK] {} foto(s) de galeria deletada(s)".format(len(fotos)))
        
        # 2. Deletar leads (relacionados a eventos)
        leads = Lead.query.all()
        if leads:
            for lead in leads:
                db.session.delete(lead)
            db.session.commit()
            print("[OK] {} lead(s)/cadastro(s) deletado(s)".format(len(leads)))
        
        # 3. Deletar eventos (relacionados a escolas)
        eventos = Evento.query.all()
        if eventos:
            for evento in eventos:
                db.session.delete(evento)
            db.session.commit()
            print("[OK] {} evento(s) deletado(s)".format(len(eventos)))
        
        # 4. Deletar escolas
        escolas = Escola.query.all()
        if escolas:
            for escola in escolas:
                db.session.delete(escola)
            db.session.commit()
            print("[OK] {} escola(s) deletada(s)".format(len(escolas)))
        
        print("\n" + "=" * 70)
        print("DADOS APOS A LIMPEZA:")
        print("-" * 70)
        print("  * Escolas: {}".format(Escola.query.count()))
        print("  * Eventos: {}".format(Evento.query.count()))
        print("  * Leads/Cadastros: {}".format(Lead.query.count()))
        print("  * Fotos de Galeria: {}".format(GaleriaFoto.query.count()))
        
        print("\n[OK] BANCO DE DADOS LIMPO COM SUCESSO!")
        print("=" * 70 + "\n")

    except Exception as e:
        print("\n[ERRO] ao limpar: {}".format(str(e)))
        db.session.rollback()
        print("=" * 70 + "\n")
