from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

app = FastAPI()

# ========== БАЗА ДАННЫХ PostgreSQL ==========
DATABASE_URL = "postgresql://postgres:335599ps@localhost/climbing_gym"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Таблица клиентов
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=True)
    is_loyal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Таблица слотов
class Slot(Base):
    __tablename__ = "slots"
    id = Column(Integer, primary_key=True, index=True)
    format_name = Column(String, nullable=False)
    instructor = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    max_participants = Column(Integer, default=8)
    current_participants = Column(Integer, default=0)
    is_cancelled = Column(Boolean, default=False)
    cancellation_reason = Column(Text, nullable=True)


Base.metadata.create_all(bind=engine)


# ========== НАЧАЛЬНЫЕ ДАННЫЕ ==========
def create_initial_data():
    db = SessionLocal()
    existing_slots = db.query(Slot).count()
    if existing_slots == 0:
        initial_slots = [
            Slot(
                format_name="Болдеринг (новички)",
                instructor="Алексей Петров",
                start_time="15.07.26 18:00",
                max_participants=8,
                current_participants=0,
                is_cancelled=False
            ),
            Slot(
                format_name="Трассы с верёвкой (опытные)",
                instructor="Мария Иванова",
                start_time="16.07.26 14:00",
                max_participants=16,
                current_participants=0,
                is_cancelled=False
            ),
            Slot(
                format_name="Болдеринг (новички)",
                instructor="Дмитрий Сидоров",
                start_time="17.07.26 10:00",
                max_participants=8,
                current_participants=5,
                is_cancelled=False
            ),
        ]
        db.add_all(initial_slots)
        db.commit()
        print("✅ Начальные тренировки созданы!")
    db.close()


create_initial_data()

# ========== ДАННЫЕ ==========
current_user = None
current_user_is_admin = False


def reload_current_user():
    """Перезагрузить current_user из БД"""
    global current_user
    if current_user:
        db = SessionLocal()
        current_user = db.query(Client).filter(Client.id == current_user.id).first()
        db.close()


# ========== КЛИЕНТСКАЯ ЧАСТЬ ==========
@app.get("/")
async def root():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Вход - Скалодром</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen flex items-center justify-center p-4">
        <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md">
            <h1 class="text-3xl font-bold text-center mb-6">🧗 Скалодром Вертикаль</h1>
            <form action="/auth/sms/send" method="POST">
                <input type="tel" name="phone" placeholder="+79991234567" required
                       class="w-full px-4 py-3 border rounded-lg mb-4">
                <button type="submit" class="w-full bg-blue-600 text-white py-3 rounded-lg">
                    Получить код
                </button>
            </form>
            <div class="mt-4 pt-4 border-t">
                <a href="/admin" class="text-sm text-gray-500 hover:text-gray-700">Вход для администратора</a>
            </div>
        </div>
    </body>
    </html>
    """)


@app.post("/auth/sms/send")
async def send_sms(phone: str = Form(...)):
    print(f"[SMS] Код для {phone}: 1234")
    return RedirectResponse(url=f"/auth/verify?phone={phone}", status_code=303)


@app.get("/auth/verify")
async def verify_page(phone: str):
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Код - Скалодром</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen flex items-center justify-center p-4">
        <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md">
            <h1 class="text-2xl font-bold text-center mb-4">Введите код из SMS</h1>
            <p class="text-center text-gray-600 mb-4">Отправлен на {phone}</p>
            <form action="/auth/verify" method="POST">
                <input type="hidden" name="phone" value="{phone}">
                <input type="text" name="code" placeholder="1234" maxlength="4" required
                       class="w-full px-4 py-3 border rounded-lg mb-4 text-center text-2xl">
                <button type="submit" class="w-full bg-blue-600 text-white py-3 rounded-lg">
                    Войти
                </button>
            </form>
        </div>
    </body>
    </html>
    """)


@app.post("/auth/verify")
async def verify_submit(phone: str = Form(...), code: str = Form(...)):
    global current_user, current_user_is_admin
    if code == "1234":
        db = SessionLocal()
        client = db.query(Client).filter(Client.phone == phone).first()
        if not client:
            client = Client(phone=phone)
            db.add(client)
            db.commit()
            db.refresh(client)
        current_user = client
        current_user_is_admin = False
        db.close()
        return RedirectResponse(url="/slots", status_code=303)
    return HTMLResponse(content=f"<h1>Неверный код! Попробуйте 1234</h1><a href='/auth/verify?phone={phone}'>Назад</a>",
                        status_code=400)


@app.get("/profile")
async def profile():
    global current_user
    if not current_user:
        return RedirectResponse(url="/", status_code=303)

    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Профиль</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50">
        <header class="bg-white shadow p-4">
            <h1 class="text-xl font-bold">🧗 Скалодром Вертикаль</h1>
        </header>
        <main class="max-w-4xl mx-auto p-4">
            <h2 class="text-2xl font-bold mb-6">Мой профиль</h2>
            <div class="bg-white rounded-lg shadow p-6">
                <p class="text-gray-700"><strong>Телефон:</strong> {current_user.phone}</p>
                <p class="text-gray-700"><strong>Имя:</strong> {current_user.name or 'Не указано'}</p>
                <p class="text-gray-700"><strong>Email:</strong> {current_user.email or 'Не указан'}</p>
                <p class="text-gray-700"><strong>Статус:</strong> {'⭐ Постоянный клиент' if current_user.is_loyal else 'Обычный клиент'}</p>
            </div>
            <form action="/profile/update" method="POST" class="mt-6 bg-white rounded-lg shadow p-6">
                <h3 class="font-semibold mb-4">Редактировать профиль</h3>
                <input type="text" name="name" placeholder="Ваше имя" value="{current_user.name or ''}"
                       class="w-full px-4 py-2 border rounded-lg mb-3">
                <input type="email" name="email" placeholder="Email" value="{current_user.email or ''}"
                       class="w-full px-4 py-2 border rounded-lg mb-3">
                <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                    Сохранить
                </button>
            </form>
            <div class="mt-6">
                <a href="/slots" class="text-blue-600 hover:underline">← К расписанию</a>
                <br>
                <a href="/logout" class="text-red-600 hover:underline mt-2 inline-block">Выйти</a>
            </div>
        </main>
    </body>
    </html>
    """)


@app.post("/profile/update")
async def profile_update(name: str = Form(...), email: str = Form(...)):
    global current_user
    if not current_user:
        return RedirectResponse(url="/", status_code=303)

    db = SessionLocal()
    db.query(Client).filter(Client.id == current_user.id).update({
        "name": name,
        "email": email
    })
    db.commit()

    current_user = db.query(Client).filter(Client.id == current_user.id).first()
    db.close()

    return RedirectResponse(url="/profile", status_code=303)


@app.get("/slots")
async def slots():
    global current_user
    if not current_user:
        return RedirectResponse(url="/", status_code=303)

    db = SessionLocal()
    all_slots = db.query(Slot).all()
    db.close()

    slots_html = ""
    for slot in all_slots:
        available = slot.max_participants - slot.current_participants
        status_color = "text-green-600" if available > 0 and not slot.is_cancelled else "text-red-600"

        if slot.is_cancelled:
            button = '<button disabled class="mt-3 bg-red-300 text-red-700 px-4 py-2 rounded cursor-not-allowed">Отменено</button>'
        elif available > 0:
            button = f'''
            <form action="/book/{slot.id}" method="POST" class="inline">
                <button type="submit" class="mt-3 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                    Записаться
                </button>
            </form>
            '''
        else:
            button = '<button disabled class="mt-3 bg-gray-300 text-gray-500 px-4 py-2 rounded cursor-not-allowed">Мест нет</button>'

        slots_html += f"""
        <div class="bg-white rounded-lg shadow p-5 mb-4 {'opacity-60' if slot.is_cancelled else ''}">
            <h3 class="font-semibold text-lg">{slot.format_name}</h3>
            <p class="text-gray-600">🕐 {slot.start_time}</p>
            <p class="text-gray-600">👨‍🏫 {slot.instructor}</p>
            <p class="{status_color}">{'✅' if available > 0 and not slot.is_cancelled else '❌'} Свободно мест: {available} из {slot.max_participants}</p>
            {f'<p class="text-red-600 text-sm mt-2">️ {slot.cancellation_reason}</p>' if slot.is_cancelled and slot.cancellation_reason else ''}
            {button}
        </div>
        """

    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Расписание</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50">
        <header class="bg-white shadow p-4">
            <div class="max-w-4xl mx-auto flex justify-between items-center">
                <h1 class="text-xl font-bold">🧗 Скалодром Вертикаль</h1>
                <div>
                    <a href="/profile" class="text-blue-600 hover:underline mr-4">Профиль</a>
                    <a href="/my-bookings" class="text-blue-600 hover:underline mr-4">Мои брони</a>
                    <a href="/logout" class="text-red-600 hover:underline">Выйти</a>
                </div>
            </div>
        </header>
        <main class="max-w-4xl mx-auto p-4">
            <h2 class="text-2xl font-bold mb-6">Расписание тренировок</h2>
            {slots_html}
        </main>
    </body>
    </html>
    """)


@app.post("/book/{slot_id}")
async def book_slot(slot_id: int):
    global current_user
    if not current_user:
        return RedirectResponse(url="/", status_code=303)

    db = SessionLocal()
    slot = db.query(Slot).filter(Slot.id == slot_id).first()

    if not slot:
        db.close()
        return HTMLResponse(content="<h1>Слот не найден</h1><a href='/slots'>Назад</a>", status_code=404)

    if slot.is_cancelled:
        db.close()
        return HTMLResponse(content="<h1>Тренировка отменена!</h1><a href='/slots'>Назад</a>", status_code=400)

    if current_user.slot_id:
        existing_slot = db.query(Slot).filter(Slot.id == current_user.slot_id).first()
        db.close()
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>У вас уже есть запись</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100 min-h-screen flex items-center justify-center p-4">
            <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md text-center">
                <h1 class="text-2xl font-bold text-orange-600 mb-4">⚠️ У вас уже есть запись!</h1>
                <div class="bg-gray-50 p-4 rounded-lg mb-4 text-left">
                    <p class="font-semibold text-lg">{existing_slot.format_name}</p>
                    <p class="text-gray-600">🕐 {existing_slot.start_time}</p>
                    <p class="text-gray-600">👨‍🏫 {existing_slot.instructor}</p>
                </div>
                <p class="text-sm text-gray-600 mb-6">
                    Сначала отмените существующую запись, чтобы записаться на другую тренировку
                </p>
                <div class="space-y-3">
                    <a href="/my-bookings" class="block w-full bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition">
                        Перейти к моим броням
                    </a>
                    <a href="/slots" class="block w-full bg-gray-200 text-gray-700 px-4 py-3 rounded-lg hover:bg-gray-300 transition">
                        ← Назад к расписанию
                    </a>
                </div>
            </div>
        </body>
        </html>
        """, status_code=400)

    available = slot.max_participants - slot.current_participants
    if available <= 0:
        db.close()
        return HTMLResponse(content="<h1>Мест нет!</h1><a href='/slots'>Назад</a>", status_code=400)

    # Явно обновляем БД
    db.query(Client).filter(Client.id == current_user.id).update({
        "slot_id": slot.id
    })
    # Увеличиваем счётчик, но не больше max_participants
    if slot.current_participants < slot.max_participants:
        slot.current_participants += 1
    db.commit()
    db.close()

    # Обновляем current_user
    db = SessionLocal()
    current_user = db.query(Client).filter(Client.id == current_user.id).first()
    db.close()

    print(f"[Бронь] Запись создана")
    return RedirectResponse(url="/slots?booked=1", status_code=303)


@app.get("/my-bookings")
async def my_bookings():
    global current_user
    if not current_user:
        return RedirectResponse(url="/", status_code=303)

    if not current_user.slot_id:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Мои брони</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-50">
            <header class="bg-white shadow p-4">
                <h1 class="text-xl font-bold">🧗 Скалодром Вертикаль</h1>
            </header>
            <main class="max-w-4xl mx-auto p-4">
                <h1 class="text-2xl font-bold mb-4">У вас нет активных броней</h1>
                <a href='/slots' class="text-blue-600 hover:underline">Записаться на тренировку</a>
            </main>
        </body>
        </html>
        """)

    db = SessionLocal()
    slot = db.query(Slot).filter(Slot.id == current_user.slot_id).first()
    db.close()

    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Мои брони</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50">
        <header class="bg-white shadow p-4">
            <h1 class="text-xl font-bold">🧗 Скалодром Вертикаль</h1>
        </header>
        <main class="max-w-4xl mx-auto p-4">
            <h2 class="text-2xl font-bold mb-6">Моя запись</h2>
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="font-semibold text-lg">{slot.format_name}</h3>
                <p class="text-gray-600">🕐 {slot.start_time}</p>
                <p class="text-gray-600">👨‍🏫 {slot.instructor}</p>
                <p class="text-green-600 mt-3">✅ Статус: Подтверждено</p>
                {'<p class="text-red-600 mt-2">⚠️ Тренировка отменена скалодромом</p>' if slot.is_cancelled else ''}
                <form action="/cancel" method="POST" class="mt-4">
                    <button type="submit" class="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">
                        Отменить запись
                    </button>
                </form>
            </div>
            <a href="/slots" class="text-blue-600 hover:underline mt-4 inline-block">← Назад к расписанию</a>
        </main>
    </body>
    </html>
    """)


@app.post("/cancel")
async def cancel_booking():
    global current_user
    if not current_user or not current_user.slot_id:
        return RedirectResponse(url="/", status_code=303)

    db = SessionLocal()

    # Получаем слот
    slot = db.query(Slot).filter(Slot.id == current_user.slot_id).first()
    if slot and slot.current_participants > 0:
        slot.current_participants -= 1

    # Явно обновляем БД
    db.query(Client).filter(Client.id == current_user.id).update({
        "slot_id": None
    })
    db.commit()

    # Обновляем current_user
    current_user = db.query(Client).filter(Client.id == current_user.id).first()
    db.close()

    return RedirectResponse(url="/my-bookings", status_code=303)


# ========== АДМИНКА ==========
@app.get("/admin")
async def admin_login():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Вход для администратора</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen flex items-center justify-center p-4">
        <div class="bg-white rounded-lg shadow-lg p-8 w-full max-w-md">
            <h1 class="text-2xl font-bold text-center mb-6">🔐 Администратор</h1>
            <form action="/admin/login" method="POST">
                <input type="password" name="password" placeholder="Пароль" required
                       class="w-full px-4 py-3 border rounded-lg mb-4">
                <button type="submit" class="w-full bg-purple-600 text-white py-3 rounded-lg">
                    Войти
                </button>
            </form>
            <p class="text-xs text-gray-500 mt-4 text-center">Демо-пароль: admin123</p>
        </div>
    </body>
    </html>
    """)


@app.post("/admin/login")
async def admin_login_submit(password: str = Form(...)):
    global current_user_is_admin
    if password == "admin123":
        current_user_is_admin = True
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    return HTMLResponse(content="<h1>Неверный пароль!</h1><a href='/admin'>Назад</a>", status_code=401)


@app.get("/admin/dashboard")
async def admin_dashboard():
    global current_user_is_admin
    if not current_user_is_admin:
        return RedirectResponse(url="/admin", status_code=303)

    db = SessionLocal()
    slots = db.query(Slot).all()
    clients = db.query(Client).all()
    db.close()

    slots_rows = ""
    for slot in slots:
        status = "❌ Отменено" if slot.is_cancelled else "✅ Активно"
        slots_rows += f"""
        <tr class="border-b">
            <td class="p-3">{slot.id}</td>
            <td class="p-3">{slot.format_name}</td>
            <td class="p-3">{slot.instructor}</td>
            <td class="p-3">{slot.start_time}</td>
            <td class="p-3">{slot.current_participants}/{slot.max_participants}</td>
            <td class="p-3">{status}</td>
            <td class="p-3">
                <a href="/admin/slot/edit/{slot.id}" class="text-blue-600 hover:underline">Изменить</a>
            </td>
        </tr>
        """

    clients_rows = ""
    for client in clients:
        clients_rows += f"""
        <tr class="border-b">
            <td class="p-3">{client.id}</td>
            <td class="p-3">{client.phone}</td>
            <td class="p-3">{client.name or '-'}</td>
            <td class="p-3">{client.email or '-'}</td>
            <td class="p-3">{client.slot_id or '-'}</td>
        </tr>
        """

    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Панель администратора</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50">
        <header class="bg-purple-600 text-white p-4">
            <div class="max-w-6xl mx-auto flex justify-between items-center">
                <h1 class="text-xl font-bold">🔐 Админ-панель</h1>
                <a href="/admin/logout" class="text-white hover:underline">Выйти</a>
            </div>
        </header>
        <main class="max-w-6xl mx-auto p-4">
            <div class="mb-8">
                <h2 class="text-2xl font-bold mb-4"> Тренировки</h2>
                <a href="/admin/slot/create" class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 inline-block mb-4">
                    + Добавить тренировку
                </a>
                <table class="w-full bg-white rounded-lg shadow">
                    <thead class="bg-gray-100">
                        <tr>
                            <th class="p-3 text-left">ID</th>
                            <th class="p-3 text-left">Формат</th>
                            <th class="p-3 text-left">Инструктор</th>
                            <th class="p-3 text-left">Время</th>
                            <th class="p-3 text-left">Места</th>
                            <th class="p-3 text-left">Статус</th>
                            <th class="p-3 text-left">Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        {slots_rows}
                    </tbody>
                </table>
            </div>

            <div>
                <h2 class="text-2xl font-bold mb-4"> Зарегистрированные клиенты</h2>
                <table class="w-full bg-white rounded-lg shadow">
                    <thead class="bg-gray-100">
                        <tr>
                            <th class="p-3 text-left">ID</th>
                            <th class="p-3 text-left">Телефон</th>
                            <th class="p-3 text-left">Имя</th>
                            <th class="p-3 text-left">Email</th>
                            <th class="p-3 text-left">ID записи</th>
                        </tr>
                    </thead>
                    <tbody>
                        {clients_rows}
                    </tbody>
                </table>
            </div>
        </main>
    </body>
    </html>
    """)


@app.get("/admin/slot/create")
async def admin_slot_create():
    global current_user_is_admin
    if not current_user_is_admin:
        return RedirectResponse(url="/admin", status_code=303)

    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Добавить тренировку</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50">
        <header class="bg-purple-600 text-white p-4">
            <h1 class="text-xl font-bold"> Админ-панель</h1>
        </header>
        <main class="max-w-2xl mx-auto p-4">
            <h2 class="text-2xl font-bold mb-6">Добавить тренировку</h2>
            <form action="/admin/slot/create" method="POST" class="bg-white rounded-lg shadow p-6">
                <label class="block mb-2 font-semibold">Название формата</label>
                <input type="text" name="format_name" placeholder="Болдеринг (новички)" required
                       class="w-full px-4 py-2 border rounded-lg mb-4">

                <label class="block mb-2 font-semibold">Инструктор</label>
                <input type="text" name="instructor" placeholder="Алексей Петров" required
                       class="w-full px-4 py-2 border rounded-lg mb-4">

                <label class="block mb-2 font-semibold">Время начала (дд.мм.гг чч.мм)</label>
                <input type="text" name="start_time" placeholder="15.07.26 18:00" required
                       class="w-full px-4 py-2 border rounded-lg mb-4">

                <label class="block mb-2 font-semibold">Макс. участников</label>
                <input type="number" name="max_participants" value="8" min="1" max="20"
                       class="w-full px-4 py-2 border rounded-lg mb-4">

                <div class="flex gap-3">
                    <button type="submit" class="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700">
                        Создать
                    </button>
                    <a href="/admin/dashboard" class="bg-gray-300 text-gray-700 px-6 py-2 rounded hover:bg-gray-400">
                        Отмена
                    </a>
                </div>
            </form>
        </main>
    </body>
    </html>
    """)


@app.post("/admin/slot/create")
async def admin_slot_create_submit(
        format_name: str = Form(...),
        instructor: str = Form(...),
        start_time: str = Form(...),
        max_participants: int = Form(...)
):
    global current_user_is_admin
    if not current_user_is_admin:
        return RedirectResponse(url="/admin", status_code=303)

    db = SessionLocal()
    slot = Slot(
        format_name=format_name,
        instructor=instructor,
        start_time=start_time,
        max_participants=max_participants,
        current_participants=0,
        is_cancelled=False
    )
    db.add(slot)
    db.commit()
    db.close()

    return RedirectResponse(url="/admin/dashboard", status_code=303)


@app.get("/admin/slot/edit/{slot_id}")
async def admin_slot_edit(slot_id: int):
    global current_user_is_admin
    if not current_user_is_admin:
        return RedirectResponse(url="/admin", status_code=303)

    db = SessionLocal()
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    db.close()

    if not slot:
        return HTMLResponse(content="<h1>Не найдено</h1>", status_code=404)

    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Редактировать тренировку</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50">
        <header class="bg-purple-600 text-white p-4">
            <h1 class="text-xl font-bold">🔐 Админ-панель</h1>
        </header>
        <main class="max-w-2xl mx-auto p-4">
            <h2 class="text-2xl font-bold mb-6">Редактировать тренировку #{slot_id}</h2>
            <form action="/admin/slot/edit/{slot_id}" method="POST" class="bg-white rounded-lg shadow p-6">
                <label class="block mb-2 font-semibold">Название формата</label>
                <input type="text" name="format_name" value="{slot.format_name}" required
                       class="w-full px-4 py-2 border rounded-lg mb-4">

                <label class="block mb-2 font-semibold">Инструктор</label>
                <input type="text" name="instructor" value="{slot.instructor}" required
                       class="w-full px-4 py-2 border rounded-lg mb-4">

                <label class="block mb-2 font-semibold">Время начала</label>
                <input type="text" name="start_time" value="{slot.start_time}" required
                       class="w-full px-4 py-2 border rounded-lg mb-4">

                <label class="block mb-2 font-semibold">Макс. участников</label>
                <input type="number" name="max_participants" value="{slot.max_participants}" min="1" max="20"
                       class="w-full px-4 py-2 border rounded-lg mb-4">

                <label class="block mb-2 font-semibold">
                    <input type="checkbox" name="is_cancelled" {'checked' if slot.is_cancelled else ''}>
                    Отменено скалодромом
                </label>

                <label class="block mb-2 font-semibold">Причина отмены</label>
                <textarea name="cancellation_reason" rows="3" class="w-full px-4 py-2 border rounded-lg mb-4"
                          placeholder="Профилактика оборудования...">{slot.cancellation_reason or ''}</textarea>

                <div class="flex gap-3">
                    <button type="submit" class="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700">
                        Сохранить
                    </button>
                    <a href="/admin/dashboard" class="bg-gray-300 text-gray-700 px-6 py-2 rounded hover:bg-gray-400">
                        Отмена
                    </a>
                </div>
            </form>
        </main>
    </body>
    </html>
    """)


@app.post("/admin/slot/edit/{slot_id}")
async def admin_slot_edit_submit(
        slot_id: int,
        format_name: str = Form(...),
        instructor: str = Form(...),
        start_time: str = Form(...),
        max_participants: int = Form(...),
        is_cancelled: str = Form("off"),
        cancellation_reason: str = Form("")
):
    global current_user_is_admin
    if not current_user_is_admin:
        return RedirectResponse(url="/admin", status_code=303)

    db = SessionLocal()
    slot = db.query(Slot).filter(Slot.id == slot_id).first()

    if slot:
        slot.format_name = format_name
        slot.instructor = instructor
        slot.start_time = start_time
        slot.max_participants = max_participants
        slot.is_cancelled = (is_cancelled == "on")
        slot.cancellation_reason = cancellation_reason if is_cancelled == "on" else None
        db.commit()

    db.close()
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@app.get("/admin/logout")
async def admin_logout():
    global current_user_is_admin
    current_user_is_admin = False
    return RedirectResponse(url="/admin", status_code=303)


@app.get("/logout")
async def logout():
    global current_user
    current_user = None
    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)