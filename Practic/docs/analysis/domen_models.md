# Доменная модель

## Основные сущности и их атрибуты

### 1. Client (Клиент)
- id: UUID
- phone: String (уникальный, с SMS-верификацией)
- name: String
- email: String
- is_loyal: Boolean (посетил 10+ тренировок)
- created_at: DateTime
- updated_at: DateTime

### 2. Instructor (Инструктор)
- id: UUID
- name: String
- specialization: Enum (beginner, advanced, both)
- average_rating: Decimal (1.0-5.0)
- is_active: Boolean

### 3. TrainingFormat (Формат тренировки)
- id: UUID
- name: String (boltering, rope_climbing)
- description: String
- max_group_size: Integer (8 для новичков, 16 для опытных)
- duration_minutes: Integer (90)
- difficulty_level: Enum (beginner, advanced

### 4. TrainingSlot (Слот тренировки)
- id: UUID
- format_id: UUID (FK → TrainingFormat)
- instructor_id: UUID (FK → Instructor)
- start_time: DateTime
- end_time: DateTime
- max_participants: Integer
- current_participants: Integer
- equipment_rental_price: Decimal
- status: Enum (active, cancelled_by_climbing_gym, full)
- cancellation_reason: String (nullable)

### 5. Booking (Бронирование)
- id: UUID
- client_id: UUID (FK → Client)
- slot_id: UUID (FK → TrainingSlot)
- needs_equipment_rental: Boolean
- status: Enum (confirmed, cancelled_by_client, cancelled_by_climbing_gym, completed)
- created_at: DateTime
- cancelled_at: DateTime (nullable)
- attended: Boolean (по умолчанию false, становится true после тренировки)
- payment_status: Enum (pending, paid_on_site)

### 6. Review (Оценка)
- id: UUID
- booking_id: UUID (FK → Booking, unique - одна оценка на бронь)
- client_id: UUID (FK → Client)
- instructor_id: UUID (FK → Instructor)
- rating: Integer (1-5)
- comment: String (nullable, max 500 символов)
- created_at: DateTime
- deadline: DateTime (booking.end_time + 24 часа)

### 7. Notification (Уведомление)
- id: UUID
- client_id: UUID (FK → Client)
- type: Enum (reminder_2h, cancellation, booking_confirmation)
- message: String
- sent_at: DateTime
- channel: Enum (email, push)

## Связи между сущностями
Client 1───M Booking
Booking M───1 TrainingSlot
TrainingSlot M───1 Instructor
TrainingSlot M───1 TrainingFormat
Booking 1───0..1 Review
Review M───1 Instructor
Client 1───M Review
Client 1───M Notification

## Бизнес-правила (инварианты домена)
BR-001: Ограничение группы
Если TrainingFormat.difficulty_level = beginner, то max_participants ≤ 8
Если TrainingFormat.difficulty_level = advanced, то max_participants ≤ 16
BR-002: Доступность слота
Слот доступен для бронирования, если current_participants < max_participants И status = active
BR-003: Отмена клиентом
Клиент может отменить бронь без штрафа, если booking.created_at < slot.start_time - 2 часа
BR-004: Оценка после тренировки
Оценка возможна только если booking.attended = true И current_time < booking.end_time + 24 часа
Одна оценка на одно бронирование (уникальность booking_id в Review)
BR-005: Статус лояльности
Клиент становится is_loyal = true, если количество броней со статусом completed ≥ 10
BR-006: Отмена скалодромом
При отмене слота скалодромом все связанные брони получают статус cancelled_by_climbing_gym
Повторное бронирование отменённого слота запрещено

## Состояния сущностей

### Booking Status Flow
confirmed → cancelled_by_client (если отменил клиент)
confirmed → cancelled_by_climbing_gym (если отменил скалодром)
confirmed → completed (после тренировки)
completed → reviewed (после оценки)

## TrainingSlot Status Flow
