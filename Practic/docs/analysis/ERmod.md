# ER-модель и описание сущностей

## Разделение ответственности: Read-only vs Mutable
Согласно брифу (R-004, R-015, R-028), приложение потребляет данные из существующего бэкенда,
но не создаёт и не редактирует их. Поэтому сущности делятся на две категории:

📖 Read-only (только чтение). 
Сущности: TrainingFormat, Instructor, TrainingSlot. 
Кто управляет: Существующий бэкенд скалодрома

✏️ Mutable (создаёт/меняет приложение)
Сущности: Client, Booking, Review, Notification
Кто управляет: Наше клиентское приложение

## Описание моделей сущностей

### TrainingFormat (Формат тренировки)
id: UUID (PK)
name: String ("boltering", "rope_climbing")
description: String
max_group_size: Integer (8 или 16)
duration_minutes: Integer (90)
difficulty_level: Enum (beginner, advanced)

Источник: внешний API бэкенда. Приложение не создаёт и не редактирует.

### Instructor (Инструктор)
id: UUID (PK)
name: String
specialization: Enum (beginner, advanced, both)
average_rating: Decimal (1.0-5.0, вычисляется на бэкенде)
is_active: Boolean

Источник: внешний API бэкенда. Рейтинг пересчитывается бэкендом после каждой новой оценки.


### TrainingSlot (Слот тренировки)
id: UUID (PK)
format_id: UUID (FK → TrainingFormat)
instructor_id: UUID (FK → Instructor)
start_time: DateTime
end_time: DateTime
max_participants: Integer
current_participants: Integer
equipment_rental_price: Decimal
status: Enum (active, cancelled_by_climbing_gym, full)
cancellation_reason: String (nullable)

Источник: внешний API бэкенда. Статус cancelled_by_climbing_gym устанавливается бэкендом при 
профилактике. Приложение только отображает и проверяет доступность.


### Client (Клиент)
id: UUID (PK)
phone: String (unique, с SMS-верификацией)
name: String
email: String
is_loyal: Boolean (вычисляется: посещений >= 10)
created_at: DateTime
updated_at: DateTime

Создаётся при регистрации. is_loyal пересчитывается при завершении брони.

### Booking (Бронирование)
id: UUID (PK)
client_id: UUID (FK → Client)
slot_id: UUID (FK → TrainingSlot)
needs_equipment_rental: Boolean
status: Enum (confirmed, cancelled_by_client, cancelled_by_climbing_gym, completed)
created_at: DateTime
cancelled_at: DateTime (nullable)
attended: Boolean (default: false)
payment_status: Enum (pending, paid_on_site)

Создаётся при записи клиента. Статус меняется при отмене или после тренировки.
cancelled_by_climbing_gym проставляется при синхронизации с бэкендом.

### Review (Оценка)
id: UUID (PK)
booking_id: UUID (FK → Booking, unique constraint)
client_id: UUID (FK → Client)
instructor_id: UUID (FK → Instructor)
rating: Integer (1-5)
comment: String (nullable, max 500)
created_at: DateTime
deadline: DateTime (slot.end_time + 24 часа)

Создаётся один раз на бронь. Валидация: только если booking.attended = true и current_time < deadline.

### Notification (Уведомление)
id: UUID (PK)
client_id: UUID (FK → Client)
booking_id: UUID (FK → Booking, nullable)
type: Enum (reminder_2h, cancellation, booking_confirmation)
message: String
sent_at: DateTime
channel: Enum (email)
status: Enum (pending, sent, failed)

Создаётся при бронировании, отмене или по расписанию (напоминание за 2 часа).

## Sequence-диаграммы

### Сценарий 1: Бронирование тренировки
смотреть в С1.png

### Сценарий 2: Отмена бронирования клиентом
смотреть в С2.png

### Сценарий 3: Оценка инструктора после тренировки
смотреть в С3.png

### Сценарий 4: Отмена тренировки скалодромом (синхронизация)
смотреть в С4.png


## Ключевые инварианты данных
Уникальность оценки: Review.booking_id — UNIQUE. Одна оценка на одну бронь.
Ссылочная целостность: Booking.slot_id → TrainingSlot.id (FK). Нельзя создать бронь на несуществующий слот.
Статусный автомат Booking: confirmed → cancelled_by_client | cancelled_by_climbing_gym | completed. Обратных переходов нет.
Дедлайн оценки: Review.created_at ≤ TrainingSlot.end_time + 24h. Проверяется на уровне приложения и бэкенда.
Лояльность: Client.is_loyal = TRUE, если COUNT(Booking WHERE status=completed AND client_id=X) >= 10. Пересчитывается триггером или фоновой задачей.


