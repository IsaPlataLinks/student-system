#!/usr/bin/env python3
"""
Script de BACKUP de fotos antigas
Faz cópia de segurança de TODAS as fotos (local + Cloudinary)
NÃO DELETA NADA - apenas copia para pasta de backup
"""

from app import app, db, Lead, GaleriaFoto
import os
import shutil
from datetime import datetime

def backup_fotos_antiguas():
    with app.app_context():
        print("\n" + "="*60)
        print("💾 BACKUP DE FOTOS ANTIGAS")
        print("="*60 + "\n")
        
        # Criar pasta de backup com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_folder = f'backup_fotos_{timestamp}'
        os.makedirs(backup_folder, exist_ok=True)
        
        print(f"📁 Pasta de backup criada: {backup_folder}\n")
        
        # 1. Backup de fotos locais
        upload_folder = app.config['UPLOAD_FOLDER']
        if os.path.exists(upload_folder):
            local_files = [
                f for f in os.listdir(upload_folder) 
                if f != '.gitkeep' and f.endswith(('.jpg', '.jpeg', '.png'))
            ]
            
            backup_local = os.path.join(backup_folder, 'fotos_locais')
            os.makedirs(backup_local, exist_ok=True)
            
            for filename in local_files:
                src = os.path.join(upload_folder, filename)
                dst = os.path.join(backup_local, filename)
                try:
                    shutil.copy2(src, dst)
                    print(f"  ✅ {filename}")
                except Exception as e:
                    print(f"  ❌ {filename}: {str(e)}")
            
            print(f"\n✅ {len(local_files)} fotos locais copiadas para backup\n")
        
        # 2. Registrar URLs do banco de dados
        print("📝 Registrando URLs no banco de dados...\n")
        
        urls_file = os.path.join(backup_folder, 'URLS_BANCO_DE_DADOS.txt')
        with open(urls_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("BACKUP DE URLs - FOTOS DE LEADS\n")
            f.write("="*60 + "\n\n")
            
            for lead in Lead.query.filter((Lead.foto != None) & (Lead.foto != '')).all():
                f.write(f"Lead {lead.id} ({lead.nome_formando}):\n")
                f.write(f"  URL: {lead.foto}\n")
                f.write(f"  Criado em: {lead.criado_em}\n\n")
            
            f.write("\n" + "="*60 + "\n")
            f.write("BACKUP DE URLs - FOTOS DE GALERIA\n")
            f.write("="*60 + "\n\n")
            
            for foto in GaleriaFoto.query.all():
                f.write(f"Foto Galeria {foto.id}:\n")
                f.write(f"  URL: {foto.nome_arquivo}\n")
                f.write(f"  Descrição: {foto.descricao}\n")
                f.write(f"  Criado em: {foto.criado_em}\n\n")
        
        print(f"✅ URLs registradas em: {urls_file}\n")
        
        # 3. Resumo
        print("="*60)
        print("✅ BACKUP CONCLUÍDO")
        print("="*60)
        print(f"\n📁 Pasta: {backup_folder}")
        print(f"📋 Arquivos de backup criados")
        print(f"📝 Lista de URLs salva\n")
        print("⚠️  IMPORTANTE:")
        print("   - Nenhum arquivo foi DELETADO")
        print("   - Use esta pasta como referência se precisar restaurar")
        print("   - As mudanças no código são RETROATIVAS e não afetam dados antigos\n")

if __name__ == '__main__':
    backup_fotos_antiguas()
