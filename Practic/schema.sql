-- Таблица слотов
CREATE TABLE IF NOT EXISTS slots (
    id SERIAL PRIMARY KEY,
    format_name VARCHAR NOT NULL,
    instructor VARCHAR NOT NULL,
    start_time VARCHAR NOT NULL,
    max_participants INTEGER DEFAULT 8,
    current_participants INTEGER DEFAULT 0,
    is_cancelled BOOLEAN DEFAULT FALSE,
    cancellation_reason TEXT
);

-- Таблица клиентов
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    phone VARCHAR UNIQUE NOT NULL,
    name VARCHAR,
    email VARCHAR,
    slot_id INTEGER REFERENCES slots(id),
    is_loyal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);