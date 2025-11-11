#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para limpar/resetar o banco de dados
Deleta todos os dados e recria as tabelas com um usuário admin padrão
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, Usuario
from werkzeug.security import generate_password_hash

def resetar_banco():
    """Deleta e recria o banco de dados"""
    
    with app.app_context():
        print("\n" + "="*60)
        print("🔄 RESETANDO BANCO DE DADOS")
        print("="*60 + "\n")
        
        # Caminho do arquivo do banco
        db_path = os.path.join(app.instance_path, 'student_system.db')
        
        # 1. Deletar arquivo do banco se existir
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"✅ Banco de dados deletado: {db_path}")
            except Exception as e:
                print(f"❌ Erro ao deletar banco: {str(e)}")
                return False
        else:
            print(f"ℹ️  Banco não encontrado em: {db_path}")
        
        # 2. Criar tabelas novamente
        try:
            db.create_all()
            print("✅ Tabelas recriadas com sucesso")
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {str(e)}")
            return False
        
        # 3. Criar usuário admin
        try:
            admin = Usuario(
                nome='Administrador',
                login='admin',
                senha_hash=generate_password_hash('admin123'),
                tipo_usuario='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário admin criado")
            print("   Login: admin")
            print("   Senha: admin123")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar admin: {str(e)}")
            return False
        
        # 4. Confirmação final
        print("\n" + "="*60)
        print("✅ BANCO DE DADOS RESETADO COM SUCESSO!")
        print("="*60)
        print("\n📝 Próximos passos:")
        print("   1. Acesse a aplicação")
        print("   2. Login com: admin / admin123")
        print("   3. Crie uma nova escola/evento\n")
        
        return True

if __name__ == '__main__':
    # Pedir confirmação
    print("\n⚠️  ATENÇÃO: Esta operação apagará TODOS os dados do banco!")
    resposta = input("Deseja continuar? (sim/não): ").strip().lower()
    
    if resposta in ['sim', 's', 'yes', 'y']:
        sucesso = resetar_banco()
        sys.exit(0 if sucesso else 1)
    else:
        print("❌ Operação cancelada")
        sys.exit(0)
