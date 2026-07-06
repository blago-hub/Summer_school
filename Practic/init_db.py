from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost/climbing_gym"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Создаём таблицы
    with open('schema.sql', 'r', encoding='utf-8') as f:
        schema = f.read()
        conn.execute(text(schema))

    # Проверяем, есть ли слоты
    result = conn.execute(text("SELECT COUNT(*) FROM slots"))
    count = result.scalar()

    if count == 0:
        # Добавляем начальные данные
        conn.execute(text("""
            INSERT INTO slots (format_name, instructor, start_time, max_participants, current_participants) 
            VALUES 
            ('Болдеринг (новички)', 'Алексей Петров', '15.07.26 18:00', 8, 0),
            ('Трассы с верёвкой (опытные)', 'Мария Иванова', '16.07.26 14:00', 16, 0),
            ('Болдеринг (новички)', 'Дмитрий Сидоров', '17.07.26 10:00', 8, 0)
        """))

    conn.commit()
    print("✅ База данных инициализирована!")