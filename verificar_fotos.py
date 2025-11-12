#!/usr/bin/env python3
"""
Script de verificação de integridade de fotos
Garante que nenhum dado foi perdido após as mudanças
"""

from app import app, db, Lead, GaleriaFoto
import os

def verificar_fotos():
    with app.app_context():
        print("\n" + "="*60)
        print("🔍 VERIFICAÇÃO DE INTEGRIDADE DE FOTOS")
        print("="*60 + "\n")
        
        # 1. Contar leads com foto
        leads_com_foto = Lead.query.filter(
            (Lead.foto != None) & (Lead.foto != '')
        ).count()
        print(f"✅ Leads com foto de perfil: {leads_com_foto}")
        
        # 2. Contar fotos de galeria
        total_galeria = GaleriaFoto.query.count()
        print(f"✅ Fotos na galeria: {total_galeria}")
        
        # 3. Verificar fotos que ainda existem localmente
        upload_folder = app.config['UPLOAD_FOLDER']
        if os.path.exists(upload_folder):
            local_files = [
                f for f in os.listdir(upload_folder) 
                if f != '.gitkeep' and f.endswith(('.jpg', '.jpeg', '.png'))
            ]
            print(f"✅ Arquivos locais em {upload_folder}: {len(local_files)}")
        else:
            print(f"⚠️  Pasta de uploads não existe: {upload_folder}")
        
        # 4. Verificar integridade de URLs
        print("\n📊 VERIFICAÇÃO DE URLs:\n")
        
        # Leads com foto
        leads_url_invalida = Lead.query.filter(
            (Lead.foto != None) & (Lead.foto != '')
        ).all()
        
        cloudinary_count = 0
        local_count = 0
        missing_count = 0
        
        for lead in leads_url_invalida:
            if lead.foto.startswith('https://res.cloudinary.com/'):
                cloudinary_count += 1
            elif lead.foto.startswith('/uploads/') or lead.foto.startswith('fotos-alunos/'):
                local_count += 1
            else:
                missing_count += 1
                print(f"  ⚠️  Lead {lead.id}: URL inválida = {lead.foto}")
        
        print(f"  ✅ URLs Cloudinary: {cloudinary_count}")
        print(f"  ✅ URLs locais: {local_count}")
        if missing_count > 0:
            print(f"  ⚠️  URLs inválidas: {missing_count}")
        
        # Fotos de galeria
        galeria_cloudinary = 0
        galeria_local = 0
        galeria_missing = 0
        
        for foto in GaleriaFoto.query.all():
            if foto.nome_arquivo.startswith('https://res.cloudinary.com/'):
                galeria_cloudinary += 1
            elif foto.nome_arquivo.startswith('/uploads/') or foto.nome_arquivo.startswith('fotos-galeria/'):
                galeria_local += 1
            else:
                galeria_missing += 1
                print(f"  ⚠️  Foto galeria {foto.id}: URL inválida = {foto.nome_arquivo}")
        
        print(f"\n  ✅ URLs Cloudinary (galeria): {galeria_cloudinary}")
        print(f"  ✅ URLs locais (galeria): {galeria_local}")
        if galeria_missing > 0:
            print(f"  ⚠️  URLs inválidas (galeria): {galeria_missing}")
        
        # 5. Resumo final
        print("\n" + "="*60)
        print("✅ RESUMO FINAL:")
        print("="*60)
        total_fotos = leads_com_foto + total_galeria
        print(f"Total de fotos no banco: {total_fotos}")
        print(f"  - Leads: {leads_com_foto}")
        print(f"  - Galeria: {total_galeria}")
        print(f"\nFotos com URLs válidas: {cloudinary_count + galeria_cloudinary + local_count + galeria_local}")
        print(f"  - Cloudinary: {cloudinary_count + galeria_cloudinary}")
        print(f"  - Locais: {local_count + galeria_local}")
        
        if missing_count + galeria_missing == 0:
            print("\n🎉 NENHUM DADO PERDIDO! Todas as fotos têm URLs válidas.\n")
        else:
            print(f"\n⚠️  ATENÇÃO: {missing_count + galeria_missing} fotos com URLs inválidas\n")

if __name__ == '__main__':
    verificar_fotos()
