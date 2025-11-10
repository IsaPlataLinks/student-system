from app import db, Evento, Escola

# Verificar eventos sem escola
eventos_sem_escola = db.session.query(Evento).filter(Evento.escola_id == None).all()
print(f'Eventos sem escola vinculada: {len(eventos_sem_escola)}')

for ev in eventos_sem_escola:
    print(f'  - ID: {ev.id}, data: {ev.data_evento}, tipo: {ev.tipo_formatura}')

# Listar todos os eventos
print('\nTodos os eventos:')
todos = db.session.query(Evento).all()
for ev in todos:
    escola = ev.escola.nome if ev.escola else 'SEM ESCOLA'
    print(f'  - ID: {ev.id}, Escola: {escola}, Data: {ev.data_evento}')
