from app import app, db, Escola, Evento
from datetime import date

with app.app_context():
    escola = Escola.query.filter_by(nome="Escola Teste").first()

    evento = Evento(
        escola_id=escola.id,
        ano_formatura=2025,
        serie="9º ano",
        letra_turma="A",
        data_evento=date(2025, 12, 10),
        local_evento="Auditório Central",
        tipo_formatura="Fundamental",
        status="ativo"
    )
    db.session.add(evento)
    db.session.commit()

    print("✅ Evento criado com ID:", evento.id)
