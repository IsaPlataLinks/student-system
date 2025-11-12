#!/usr/bin/env python3
"""
Script de limpeza de banco de dados e Cloudinary
Remove todos os leads e fotos para limpar ambiente
"""

import os
import sys
from app import app, db, Lead, GaleriaFoto
import cloudinary
import cloudinary.api

def cleanup_database():
    """Limpa os dados do banco de dados PostgreSQL"""
    print("\n🗑️  Iniciando limpeza do banco de dados...")
    
    try:
        with app.app_context():
            # Contar antes de deletar
            total_leads = Lead.query.count()
            total_fotos = GaleriaFoto.query.count()
            
            print(f"  📊 Encontrados: {total_leads} leads e {total_fotos} fotos")
            
            # Deletar galeria primeiro (por causa da relação)
            if total_fotos > 0:
                GaleriaFoto.query.delete()
                db.session.commit()
                print(f"  ✅ {total_fotos} fotos de galeria deletadas")
            
            # Deletar leads
            if total_leads > 0:
                Lead.query.delete()
                db.session.commit()
                print(f"  ✅ {total_leads} leads deletados")
            
            print("✅ Banco de dados limpo com sucesso!\n")
            return True
    
    except Exception as e:
        print(f"❌ Erro ao limpar banco de dados: {str(e)}\n")
        return False

def cleanup_cloudinary():
    """Limpa todas as fotos do Cloudinary"""
    print("☁️  Iniciando limpeza do Cloudinary...")
    
    try:
        # Verificar se Cloudinary está configurado
        if not os.getenv('CLOUDINARY_URL'):
            print("⚠️  CLOUDINARY_URL não configurado - pulando limpeza")
            return True
        
        # Listar todos os recursos na pasta 'fotos-alunos'
        resultado = cloudinary.api.resources(
            type='upload',
            prefix='fotos-alunos/',
            max_results=500
        )
        
        fotos = resultado.get('resources', [])
        total = len(fotos)
        
        if total == 0:
            print("  📊 Nenhuma foto encontrada no Cloudinary")
            print("✅ Cloudinary já estava vazio!\n")
            return True
        
        print(f"  📊 Encontradas: {total} fotos")
        
        # Deletar cada foto
        deletadas = 0
        erros = 0
        
        for foto in fotos:
            try:
                cloudinary.api.delete_resources([foto['public_id']])
                deletadas += 1
                print(f"  ✅ Deletada: {foto['public_id']}")
            except Exception as e:
                erros += 1
                print(f"  ❌ Erro ao deletar {foto['public_id']}: {str(e)}")
        
        print(f"\n✅ Cloudinary limpo! ({deletadas} deletadas, {erros} erros)\n")
        return erros == 0
    
    except Exception as e:
        print(f"❌ Erro ao limpar Cloudinary: {str(e)}\n")
        return False

def main():
    """Executa limpeza completa"""
    print("\n" + "="*60)
    print("🧹 SCRIPT DE LIMPEZA - BANCO DE DADOS E CLOUDINARY")
    print("="*60)
    
    confirmacao = input("\n⚠️  AVISO: Esta ação é IRREVERSÍVEL!\nTodos os leads e fotos serão deletados.\nDeseja continuar? (s/n): ").lower().strip()
    
    if confirmacao != 's':
        print("\n❌ Limpeza cancelada!\n")
        return False
    
    # Executar limpeza
    db_ok = cleanup_database()
    cloud_ok = cleanup_cloudinary()
    
    if db_ok and cloud_ok:
        print("="*60)
        print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
        print("="*60 + "\n")
        return True
    else:
        print("="*60)
        print("⚠️  Limpeza concluída com erros")
        print("="*60 + "\n")
        return False

if __name__ == '__main__':
    try:
        sucesso = main()
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {str(e)}\n")
        sys.exit(1)
