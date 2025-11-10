#!/usr/bin/env python3
"""
Script de diagnóstico para verificar dados de eventos e leads
Uso: python debug_dados.py
"""

import os
import sys
from datetime import datetime, timedelta

# Adicionar o diretório do app ao path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, Evento, Lead, Escola, Usuario

def debug_dados():
    with app.app_context():
        print("\n" + "="*80)
        print("DIAGNÓSTICO DO SISTEMA DE FORMANDOS")
        print("="*80 + "\n")
        
        # ===== USUÁRIOS =====
        print("[1] USUÁRIOS")
        print("-" * 80)
        usuarios = Usuario.query.all()
        print(f"Total de usuários: {len(usuarios)}")
        for user in usuarios:
            print(f"  - ID: {user.id}, Nome: {user.nome}, Login: {user.login}, Tipo: {user.tipo_usuario}")
        print()
        
        # ===== ESCOLAS =====
        print("[2] ESCOLAS")
        print("-" * 80)
        escolas = Escola.query.all()
        print(f"Total de escolas: {len(escolas)}")
        for escola in escolas:
            print(f"  - ID: {escola.id}, Nome: {escola.nome}, Cidade: {escola.cidade}, Estado: {escola.estado}")
        print()
        
        # ===== EVENTOS =====
        print("[3] EVENTOS")
        print("-" * 80)
        eventos = Evento.query.all()
        print(f"Total de eventos: {len(eventos)}\n")
        
        hoje = datetime.now().date()
        for evento in eventos:
            status_auto = evento.status_automatico
            dias_desde = evento.dias_desde_evento
            
            print(f"  Evento ID: {evento.id}")
            print(f"    Escola: {evento.escola.nome if evento.escola else 'N/A'}")
            print(f"    Data: {evento.data_evento}")
            print(f"    Status no BD: {evento.status}")
            print(f"    Status automático: {status_auto}")
            print(f"    Dias desde evento: {dias_desde}")
            print(f"    Hoje: {hoje}")
            print(f"    QR válido? {evento.qr_code_valido}")
            print(f"    Total de leads: {len(evento.leads)}")
            print()
        print()
        
        # ===== LEADS =====
        print("[4] LEADS (TODOS)")
        print("-" * 80)
        leads = Lead.query.all()
        print(f"Total de leads: {len(leads)}\n")
        
        for lead in leads:
            evento = lead.evento
            evento_info = f"ID: {evento.id}, Escola: {evento.escola.nome if evento.escola else 'N/A'}" if evento else "N/A"
            
            print(f"  Lead ID: {lead.id}")
            print(f"    Nome: {lead.nome_formando}")
            print(f"    Matrícula: {lead.matricula}")
            print(f"    E-mail: {lead.email}")
            print(f"    Evento: {evento_info}")
            print(f"    Criado em: {lead.criado_em}")
            print(f"    Foto: {lead.foto if lead.foto else 'Nenhuma'}")
            
            # Verificar se arquivo de foto existe
            if lead.foto:
                foto_path = os.path.join(app.config['UPLOAD_FOLDER'], lead.foto)
                existe = os.path.exists(foto_path)
                print(f"    Arquivo existe? {existe} ({foto_path})")
            
            print()
        print()
        
        # ===== RESUMO DE FOTOS =====
        print("[5] DIAGNÓSTICO DE FOTOS")
        print("-" * 80)
        upload_folder = app.config['UPLOAD_FOLDER']
        print(f"Pasta de uploads: {upload_folder}")
        print(f"Existe? {os.path.exists(upload_folder)}")
        
        if os.path.exists(upload_folder):
            arquivos = os.listdir(upload_folder)
            print(f"Total de arquivos: {len(arquivos)}\n")
            for arquivo in arquivos:
                if arquivo != '.gitkeep':
                    caminho = os.path.join(upload_folder, arquivo)
                    tamanho = os.path.getsize(caminho)
                    print(f"  - {arquivo} ({tamanho} bytes)")
                    
                    # Verificar se tem lead associado
                    lead = Lead.query.filter_by(foto=arquivo).first()
                    if lead:
                        print(f"    ✓ Associado ao lead {lead.id} ({lead.nome_formando})")
                    else:
                        print(f"    ⚠ NÃO associado a nenhum lead")
        print()
        
        # ===== ESTATÍSTICAS POR EVENTO =====
        print("[6] ESTATÍSTICAS POR EVENTO")
        print("-" * 80)
        for evento in eventos:
            leads_count = len(evento.leads)
            leads_com_foto = len([l for l in evento.leads if l.foto])
            print(f"Evento {evento.id} ({evento.escola.nome if evento.escola else 'N/A'}):")
            print(f"  - Total de leads: {leads_count}")
            print(f"  - Leads com foto: {leads_com_foto}")
            print(f"  - Status: {evento.status_automatico}")
        print()
        
        print("="*80)
        print("DIAGNÓSTICO CONCLUÍDO")
        print("="*80 + "\n")

if __name__ == '__main__':
    debug_dados()
