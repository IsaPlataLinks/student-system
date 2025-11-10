#!/usr/bin/env python
"""Debug script para verificar eventos no banco de dados"""

import os
import sys
from app import app, db, Evento, Escola, Usuario

with app.app_context():
    print("=" * 60)
    print("VERIFICAÇÃO DO BANCO DE DADOS")
    print("=" * 60)
    
    # Usuários
    usuarios = Usuario.query.all()
    print(f"\n[USUARIOS] ({len(usuarios)}):")
    for u in usuarios:
        print(f"  - ID {u.id}: {u.nome} (tipo: {u.tipo_usuario}, login: {u.login})")
    
    # Escolas
    escolas = Escola.query.all()
    print(f"\n[ESCOLAS] ({len(escolas)}):")
    for e in escolas:
        print(f"  - ID {e.id}: {e.nome} ({e.cidade}, {e.estado})")
    
    # Eventos
    eventos = Evento.query.order_by(Evento.criado_em.desc()).all()
    print(f"\n[EVENTOS] ({len(eventos)}):")
    for ev in eventos:
        escola_nome = ev.escola.nome if ev.escola else "SEM ESCOLA"
        print(f"  - ID {ev.id}: {escola_nome} | Data: {ev.data_evento} | Status: {ev.status}")
        print(f"    Criado em: {ev.criado_em} | Vendedor ID: {ev.vendedor_id}")
    
    print("\n" + "=" * 60)
    if not eventos:
        print("❌ NENHUM EVENTO NO BANCO!")
    else:
        print(f"✅ {len(eventos)} evento(s) encontrado(s)")
    print("=" * 60)
