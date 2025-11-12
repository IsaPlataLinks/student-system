#!/usr/bin/env python3
"""
Script direto de limpeza - sem input do usuário
Usa variáveis de ambiente já configuradas
"""

import os
from app import app, db, Lead, GaleriaFoto, Evento
import cloudinary
import cloudinary.api

def cleanup():
    with app.app_context():
        print("\n🧹 LIMPEZA DIRETA DE DADOS\n")
        
        try:
            # 1. Deletar galeria (por causa da relação)
            galeria_count = GaleriaFoto.query.count()
            GaleriaFoto.query.delete()
            db.session.commit()
            print(f"✅ {galeria_count} fotos de galeria deletadas")
            
            # 2. Deletar leads
            leads_count = Lead.query.count()
            Lead.query.delete()
            db.session.commit()
            print(f"✅ {leads_count} leads deletados")
            
            # 3. Deletar eventos
            eventos_count = Evento.query.count()
            Evento.query.delete()
            db.session.commit()
            print(f"✅ {eventos_count} eventos deletados")
            
            # 3. Limpar Cloudinary
            cloudinary_count = 0
            if os.getenv('CLOUDINARY_URL'):
                try:
                    resultado = cloudinary.api.resources(
                        type='upload',
                        prefix='fotos-alunos/',
                        max_results=500
                    )
                    fotos = resultado.get('resources', [])
                    for foto in fotos:
                        cloudinary.api.delete_resources([foto['public_id']])
                        cloudinary_count += 1
                    print(f"✅ {cloudinary_count} fotos do Cloudinary deletadas")
                except Exception as e:
                    print(f"⚠️  Erro ao limpar Cloudinary: {str(e)}")
            else:
                print("⚠️  CLOUDINARY_URL não configurado")
            
            print("\n" + "="*50)
            print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
            print("="*50)
            print(f"\nResumo:")
            print(f"  • Eventos deletados: {eventos_count}")
            print(f"  • Leads deletados: {leads_count}")
            print(f"  • Fotos de galeria deletadas: {galeria_count}")
            print(f"  • Fotos Cloudinary deletadas: {cloudinary_count}")
            print()
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO: {str(e)}\n")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    cleanup()
