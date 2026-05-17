import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from datetime import datetime, timedelta
from database import Database


TOKEN = "TOKEN_BOT"

bot = Bot(token=TOKEN)
dp = Dispatcher()

db = Database()
user_data = db.load_all_users()

def get_user_record(user_id: int) -> dict:
    now = datetime.now()
    today = now.date()
    record = user_data.setdefault(user_id, {
        'coins': 0,
        'last_farm': now - timedelta(hours=1),
        'infractions': 0,
        'last_violation': None,
        'muted_until': None,
        'first_seen': now,
        'total_messages': 0,
        'daily_messages': 0,
        'last_message_date': today,
        'nickname': None,
        'username': None,
        'full_name': None,
        'title': None,
        'bio': None,
        'custom_style': None,
        'favorite_emoji': None,
        'badges': [],
        'vip_member': False,
        'redeemed_codes': [],
        'married_to': None,
        'marriage_date': None,
    })

    if 'coins' not in record:
        record['coins'] = 0
    if 'last_farm' not in record:
        record['last_farm'] = now - timedelta(hours=1)
    if 'infractions' not in record:
        record['infractions'] = 0
    if 'last_violation' not in record:
        record['last_violation'] = None
    if 'muted_until' not in record:
        record['muted_until'] = None
    if 'first_seen' not in record:
        record['first_seen'] = now
    if 'total_messages' not in record:
        record['total_messages'] = 0
    if 'daily_messages' not in record:
        record['daily_messages'] = 0
    if 'last_message_date' not in record:
        record['last_message_date'] = today
    if 'nickname' not in record:
        record['nickname'] = None
    if 'username' not in record:
        record['username'] = None
    if 'full_name' not in record:
        record['full_name'] = None
    if 'title' not in record:
        record['title'] = None
    if 'bio' not in record:
        record['bio'] = None
    if 'custom_style' not in record:
        record['custom_style'] = None
    if 'favorite_emoji' not in record:
        record['favorite_emoji'] = None
    if 'badges' not in record:
        record['badges'] = []
    if 'vip_member' not in record:
        record['vip_member'] = False
    if 'redeemed_codes' not in record:
        record['redeemed_codes'] = []
    if 'married_to' not in record:
        record['married_to'] = None
    if 'marriage_date' not in record:
        record['marriage_date'] = None

    # Сброс daily_messages, если новый день
    if record['last_message_date'] != today:
        record['daily_messages'] = 0
        record['last_message_date'] = today

    return record

def find_user_id(identifier: str) -> int | None:
    """Найти ID пользователя по username, нику или ID"""
    identifier = identifier.strip()
    if not identifier:
        return None
    if identifier.startswith('@'):
        identifier = identifier[1:]

    if identifier.isdigit():
        user_id = int(identifier)
        if user_id in user_data:
            return user_id

    lowered = identifier.lower()
    for uid, record in user_data.items():
        nickname = record.get('nickname')
        username = record.get('username')
        full_name = record.get('full_name')
        if nickname and nickname.lower() == lowered:
            return uid
        if username and username.lower() == lowered:
            return uid
        if full_name and full_name.lower() == lowered:
            return uid
    return None

async def get_target_user(message: types.Message, args: list) -> tuple[int | None, str]:
    """
    Получить ID целевого пользователя из ответа на сообщение или аргумента
    Возвращает (user_id, display_name)
    """
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        display_name = message.reply_to_message.from_user.first_name
        return target_id, display_name
    
    if len(args) > 1:
        identifier = args[1]
        target_id = find_user_id(identifier)
        if target_id:
            record = get_user_record(target_id)
            display_name = record.get('nickname') or record.get('full_name') or f"ID{target_id}"
            return target_id, display_name
    
    return None, ""


BANNED_WORDS = [
    "сука", "блять", "нахуй", "долбаёб", "хуй", "пизда", "пиздец", "ебать", "ебаный",
    "еблан", "уебок", "мудак", "мразь", "суки", "сукаа", "шлюха", "шлюхи", "манда",
    "гондон", "сосать", "дрочить", "срать", "дерьмо", "бля", "блят", "хуета", "хуетос",
    "хуесос", "хуйн", "хуёва", "пидорас", "пидор", "пидорок", "заебал", "заебись",
    "охуеть", "охуенно", "блядь", "пиздеть", "пиздабол", "жопа", "залупа", "ебанутый"
]
STAFF_IDS = [1484732806,8540972267]
OWNER_ID = 1484732806

# Настройки рандомных сообщений
RANDOM_WORDS = ["Камень", "Кто здесь?", "Вайты сами себя не нафармят!", "Вижу всё.", "Хватит флудить!", "Я всё записываю..."]
RANDOM_MSG_CONFIG = {
    "enabled": True,
    "min_delay": 3600,  # Минимально 1 час
    "max_delay": 14400, # Максимально 4 часа
    "chat_id": -100123456789, # ID твоего чата (замени на свой!)
}


SHOP_ITEMS = {
    'mystery_box': {
        'name': '🎁 Секретный бокс',
        'price': 100,
        'description': 'Рандомный подарок: вайты или никнейм.',
        'cost_type': 'coins',
    },
    'super_joke': {
        'name': '😂 Супер-шутка',
        'price': 20,
        'description': 'Получить особую веселую шутку.',
        'cost_type': 'coins',
    },
    'nickname_change': {
        'name': '✍️ Смена ника',
        'price': 2000,
        'description': 'Позволяет установить новый ник прямо сейчас.',
        'cost_type': 'coins',
    },
    'vip_pass': {
        'name': '🌟 VIP-статус',
        'price': 500,
        'description': 'Требует 500 сообщений в чате и даёт VIP-статус.',
        'cost_type': 'messages',
    },
    'profile_frame': {
        'name': '🖼 Рамка профиля',
        'price': 33333,
        'description': 'Подарите себе стильную рамку и бейдж в профиле.',
        'cost_type': 'coins',
    },
}

PROFILE_STYLES = {
    'classic': 'Дефолтный',
    'neon': 'Неоновый',
    'shadow': 'Тёмный',
    'gold': 'Золотой',
    
}

PROMO_CODES = {
    'WELCOME50': {
        'type': 'coins',
        'value': 50,
        'description': 'Подарок для нового игрока.',
    },
    'LUCKY100': {
        'type': 'coins',
        'value': 100,
        'description': 'Счастливый разовый бонус.',
    },
    'VIPFREE': {
        'type': 'vip',
        'value': None,
        'description': 'Бесплатный VIP-статус.',
    },
}

promo_codes = db.load_promo_codes()
for code, info in PROMO_CODES.items():
    if code not in promo_codes:
        db.save_promo_code(code, info)
        promo_codes[code] = info

# --- ЭКОНОМИКА ---

@dp.message(F.text.lower() == "профиль")
async def profile_plain(message: types.Message):
    await profile_command(message)

@dp.message(F.text.lower() == "фарма")
async def farm_plain(message: types.Message):
    await farm_coins(message)

@dp.message(F.text.lower() == "баланс")
async def balance_plain(message: types.Message):
    await check_balance(message)

@dp.message(F.text.lower() == "магазин")
async def shop_plain(message: types.Message):
    await shop_command(message)

@dp.message(F.text.lower().startswith("передать"))
async def transfer_coins(message: types.Message):
    if not message.reply_to_message:
        return await message.reply("⚠️ Ответь на сообщение того, кому хочешь дать вайты.")
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        return await message.reply("⚠️ Напиши: передать [сумма]")
    amount = int(args[1])
    sender_id = message.from_user.id
    receiver_id = message.reply_to_message.from_user.id
    if sender_id == receiver_id: return await message.reply("🤔 Самому себе? Нельзя.")
    sender_record = get_user_record(sender_id)
    if sender_record['coins'] < amount: return await message.reply("❌ У тебя нет столько вайтов.")
    receiver_record = get_user_record(receiver_id)
    sender_record['coins'] -= amount
    receiver_record['coins'] += amount
    db.save_user(sender_id, sender_record)
    db.save_user(receiver_id, receiver_record)
    await message.answer(f"💸 {message.from_user.first_name} передал {amount} вайтов {message.reply_to_message.from_user.first_name}!")





@dp.message(Command("farm"))
async def farm_coins(message: types.Message):
    user_id = message.from_user.id
    now = datetime.now()
    
    record = get_user_record(user_id)
    last_farm = record['last_farm']
    if now - last_farm < timedelta(minutes=180):
        wait_time = (timedelta(minutes=180) - (now - last_farm)).seconds
        await message.reply(f"⏳ Твои работники устали! Подожди еще {wait_time} сек.")
        return

    earned = random.randint(10, 799)
    user_data[user_id]['coins'] += earned
    user_data[user_id]['last_farm'] = now
    
    await message.reply(f"⛏️ Ты успешно пофармил и заработал {earned} вайтов!\nТеперь твой баланс: {user_data[user_id]['coins']} вайтов")
    db.save_user(user_id, user_data[user_id])

@dp.message(Command("coins"))
async def check_balance(message: types.Message):
    record = get_user_record(message.from_user.id)
    await message.reply(f"💳 Твой баланс : {record['coins']} вайтов")

@dp.message(Command("joke"))
async def tell_joke(message: types.Message):
    jokes = [
        "Почему программист не плавает? Потому что он боится утечки памяти.",
        "Я спросил у лампы: 'Можешь исполнить три желания?' — она ответила 'Нет, я только зарядку держу'.",
        "Почему кофе не разговаривает? Потому что он слишком сильно заварен.",
        "— Ты кто? — Я бот. — Что умеешь? — Перезагружать каким-то образом сообщения.",
    ]
    await message.reply(random.choice(jokes))

@dp.message(Command("roll"))
async def roll_dice(message: types.Message):
    args = message.text.split()
    sides = 6
    if len(args) > 1:
        try:
            sides = max(2, int(args[1]))
        except ValueError:
            await message.reply("⚠️ Укажи число сторон, например /roll 10")
            return
    result = random.randint(1, sides)
    await message.reply(f"🎲 Бросок d{sides}: {result}")

@dp.message(Command("rps"))
async def rock_paper_scissors(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("⚠️ Укажи камень, ножницы или бумагу: /rps ножницы")
        return
    choice = args[1].lower()
    options = ["камень", "ножницы", "бумага"]
    if choice not in options:
        await message.reply("⚠️ Выбери: камень, ножницы или бумага.")
        return
    bot_choice = random.choice(options)
    if choice == bot_choice:
        result = "Ничья"
    elif (choice == "камень" and bot_choice == "ножницы") or \
         (choice == "ножницы" and bot_choice == "бумага") or \
         (choice == "бумага" and bot_choice == "камень"):
        result = "Ты выиграл!"
    else:
        result = "Я выиграл!"
    await message.reply(f"🧠 Я выбрал {bot_choice}. {result}")

@dp.message(Command("quote"))
async def random_quote(message: types.Message):
    quotes = [
        "Жизнь — это то, что с тобой происходит, когда ты строишь другие планы.",
        "Лучший способ предсказать будущее — создать его.",
        "Улыбка ничего не стоит, но даёт очень много.",
        "Ошибка — это просто возможность начать снова, но уже более мудро.",
    ]
    await message.reply(random.choice(quotes))

@dp.message(Command("chance"))
async def chance_command(message: types.Message):
    args = message.text.split(maxsplit=1)
    subject = args[1] if len(args) > 1 else "вещь"
    percent = random.randint(0, 100)
    await message.reply(f"🔮 Шанс для '{subject}': {percent}%")

@dp.message(Command("chatstats"))
async def chat_stats(message: types.Message):
    if message.chat.type not in ("group", "supergroup"):
        await message.reply("⚠️ Команда работает только в чате.")
        return

    stats = db.get_chat_stats(message.chat.id)
    if not stats:
        await message.reply("⚠️ В этом чате ещё нет статистики сообщений.")
        return

    text = "📊 Статистика сообщений в этом чате:\n"
    for item in stats[:10]:
        text += f"ID {item['user_id']}: всего {item['total_messages']}, сегодня {item['daily_messages']}\n"
    await message.reply(text)

# --- STAFF (АДМИН-КОМАНДЫ) ---

@dp.message(Command("staff"))
async def staff_panel(message: types.Message):
    if message.from_user.id not in STAFF_IDS:
        await message.answer("❌ Тебе нельзя. Ты не состоишь в персонале проекта.")
        return
    
    await message.answer(
        "🛠 **Staff Панель**\n\n"
        "/give_coins [ID] [кол-во] - Выдать валюту\n"
        "/stats - Статистика бота\n"
        "/users - Список известных пользователей\n"
        "/infractions [ID] - Информация о нарушителе\n"
        "/violators - Список нарушителей\n"
        "/warn [ID] [причина] - Выдать предупреждение\n"
        "/create_promo [код] [coins|vip] [значение] [описание] - Создать промокод\n"
        "/mute [ID] [минуты] - Замутить вручную\n"
        "/unmute [ID] - Размутить пользователя\n"
        "/chatstats - Статистика сообщений в этом чате\n"
        "/help - Помощь по командам\n"
        "/profile [ID] - Просмотр профиля",
        parse_mode="Markdown"
       

    )

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "👋 Привет! Я Whetium,я слежу за чатом,и развлекаю людей.\n"
        "Используй /help, чтобы увидеть доступные команды."
    )

@dp.message(Command("setbio"))
async def set_bio(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.reply("⚠️ Укажи своё описание: /setbio Твой текст")
        return
    record = get_user_record(message.from_user.id)
    record['bio'] = args[1].strip()[:120]
    db.save_user(message.from_user.id, record)
    await message.reply("✅ Описание профиля обновлено.")

@dp.message(Command("settitle"))
async def set_title(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.reply("⚠️ Укажи свой титул: /settitle Мой титул")
        return
    record = get_user_record(message.from_user.id)
    record['title'] = args[1].strip()[:32]
    db.save_user(message.from_user.id, record)
    await message.reply(f"✅ Твой титул установлен: {record['title']}")

@dp.message(Command("setstyle"))
async def set_style(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.reply("⚠️ Укажи стиль: /setstyle classic|neon|shadow|gold")
        return
    style = args[1].strip().lower()
    if style not in PROFILE_STYLES:
        await message.reply("⚠️ Доступные стили профиля: classic, neon, shadow, gold")
        return
    record = get_user_record(message.from_user.id)
    record['custom_style'] = PROFILE_STYLES[style]
    db.save_user(message.from_user.id, record)
    await message.reply(f"✅ Стиль профиля установлен: {record['custom_style']}")

@dp.message(Command("setemoji"))
async def set_emoji(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.reply("⚠️ Укажи эмодзи: /setemoji 😎")
        return
    record = get_user_record(message.from_user.id)
    record['favorite_emoji'] = args[1].strip()[:4]
    db.save_user(message.from_user.id, record)
    await message.reply(f"✅ Любимое эмодзи установлено: {record['favorite_emoji']}")

@dp.message(Command("about"))
async def about_command(message: types.Message):
    await message.answer(
        "📌 Я могу давать вайты, мутить за мат, хранить статистику и развлекать чат.\n"
        "Команды для развлечений: /joke, /roll, /rps, /quote, /chance."
        "Рп команды: /обнять /поцеловать /подарить /ударить /похвалить /пожалеть /насмешить /напугать /поздравить /пожелать /мотивировать"
    )

@dp.message(Command("setnick"))
async def set_nickname(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.reply("⚠️ Укажи ник: /setnick Ник")
        return
    nickname = args[1].strip()[:32]
    record = get_user_record(message.from_user.id)
    record['nickname'] = nickname
    db.save_user(message.from_user.id, record)
    await message.reply(f"✅ Твой ник установлен: {nickname}")

@dp.message(F.text.regexp(r'(?i)^setnick(?:@\w+)?\b'))
async def set_nickname_plain(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.reply("⚠️ Укажи ник: setnick Ник")
        return
    nickname = args[1].strip()[:32]
    record = get_user_record(message.from_user.id)
    record['nickname'] = nickname
    db.save_user(message.from_user.id, record)
    await message.reply(f"✅ Твой ник установлен: {nickname}")

@dp.message(Command("help"))
async def help_command(message: types.Message):
    print(f"Help command called by user {message.from_user.id}")
    is_staff = message.from_user.id in STAFF_IDS
    
    help_text = (
        "🤖 **Бот для модерации и развлечения**\n\n"
        "Этот бот помогает поддерживать порядок в чате, автоматически мутить за запрещённые слова, "
        "и предоставляет экономику с фармом валюты Вайты.\n\n"
        "📋 **Общие команды:**\n"
        "/start - Приветственное сообщение\n"
        "/about - О боте\n"
        "/farm - Ферма (каждые 5 минут)\n"
        "/coins - Проверить баланс\n"
        "/profile [ID|ник|username] - Просмотр профиля\n"
        "/setnick [ник] - Установить свой ник\n"
        "/settitle [текст] - Установить титул\n"
        "/setbio [текст] - Установить описание профиля\n"
        "/setstyle [classic|neon|shadow|gold] - Выбрать стиль профиля\n"
        "/setemoji [эмодзи] - Установить любимое эмодзи\n"
        "/shop - Открыть магазин\n"
        "/buy [товар] - Купить товар из магазина\n"
        "/promo - Узнать про промокоды\n"
        "/redeem [код] - Активировать промокод\n"
        "/joke - Случайная шутка\n"
        "/roll [число] - Бросить кубик\n"
        "/rps [камень|ножницы|бумага] - Игра в КНБ\n"
        "/quote - Случайная цитата\n"
        "/chance [дело] - Узнать шанс\n"
        "/chatstats - Статистика сообщений в этом чате\n"
        "/help - Эта справка\n"
        "/report [причина] - отправить репорт на нарушителя"
        "/marry - Пожениться\n" 
        "\nЕсли ты в группе, используй /help или /help@ВашBotUsername\n"
    )
    
    if is_staff:
        help_text += (
            "\n🛠 **Админ-команды:**\n"
            "/staff - Панель администратора\n"
            "/give_coins [ID] [кол-во] - Выдать валюту\n"
            "/stats - Статистика бота\n"
            "/infractions [ID] - Информация о нарушителе\n"
            "/violators - Список нарушителей\n"
            "/warn [ID] [причина] - Выдать предупреждение\n"
            "/mute [ID] [минуты] - Замутить вручную\n"
            "/unmute [ID] - Размучить пользователя\n"
        )
    
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("shop"))
async def shop_command(message: types.Message):
    text = "🛍 **Магазин  вещей**\n\n"
    for key, item in SHOP_ITEMS.items():
        if item['cost_type'] == 'coins':
            cost = f"{item['price']} вайтов"
        else:
            cost = f"{item['price']} сообщений"
        text += f"/{key} - {item['name']} ({cost})\n{item['description']}\n\n"
    text += "Чтобы купить, используй /buy [товар]. Например: /buy mystery_box"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("buy"))
async def buy_command(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        await message.reply("⚠️ Укажи товар для покупки. Пример: /buy mystery_box")
        return

    item_key = args[1].lower()
    item = SHOP_ITEMS.get(item_key)
    if not item:
        await message.reply("⚠️ Товар не найден. Открой магазин: /shop")
        return

    record = get_user_record(message.from_user.id)

    if item['cost_type'] == 'coins':
        if record['coins'] < item['price']:
            await message.reply(f"⚠️ У тебя недостаточно вайтов. Нужно {item['price']} вайтов.")
            return
    else:
        if record['total_messages'] < item['price']:
            await message.reply(f"⚠️ Для покупки нужно иметь минимум {item['price']} сообщений.")
            return

    if item_key == 'mystery_box':
        record['coins'] -= item['price']
        reward = random.choice(['coins', 'nickname'])
        if reward == 'coins':
            bonus = random.randint(50, 1000)
            record['coins'] += bonus
            await message.reply(f"🎁 Ты купил Тайную коробку и получил {bonus} вайтов!")
        else:
            nickname = f"Player{random.randint(100, 3999)}"
            record['nickname'] = nickname
            await message.reply(f"🎁 Ты купил Тайную коробку и получил ник: {nickname}")
    elif item_key == 'super_joke':
        record['coins'] -= item['price']
        await message.reply("😎 Вот твоя супер-шутка: Почему сервер не отвечает? Потому что он ещё не успел выпить кофе.")
    elif item_key == 'nickname_change':
        if len(args) < 3 or not args[2].strip():
            await message.reply("⚠️ Укажи новый ник: /buy nickname_change НовыйНик")
            return
        new_nick = args[2].strip()[:32]
        record['coins'] -= item['price']
        record['nickname'] = new_nick
        await message.reply(f"✅ Ты сменил ник на: {new_nick}")
    elif item_key == 'profile_frame':
        record['coins'] -= item['price']
        badge = 'Рамка профиля'
        if badge not in record.get('badges', []):
            record.setdefault('badges', []).append(badge)
        await message.reply("🖼 Ты купил рамку профиля! Она добавлена в твой профиль.")
    elif item_key == 'vip_pass':
        if record['vip_member']:
            await message.reply("⚠️ У тебя уже есть VIP-статус.")
            return
        if record['total_messages'] < item['price']:
            await message.reply(f"⚠️ Нужно не менее {item['price']} сообщений для VIP-статуса.")
            return
        record['vip_member'] = True
        await message.reply("🌟 Поздравляю! У тебя теперь VIP-статус.")
    else:
        await message.reply("⚠️ Этот товар пока недоступен.")
        return

    db.save_user(message.from_user.id, record)

@dp.message(Command("promo"))
async def promo_command(message: types.Message):
    text = "🎟 **Промокоды**\n\n"
    text += "Введи /redeem [код], чтобы активировать промокод.\n"
    text += "Например: /redeem WELCOME50\n\n"
    text += "Доступные промокоды:\n"
    for code, info in promo_codes.items():
        text += f"{code} — {info['description']}\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("redeem"))
async def redeem_command(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("⚠️ Укажи код: /redeem WELCOME50")
        return

    code = args[1].strip().upper()
    promo = promo_codes.get(code)
    if not promo:
        await message.reply("⚠️ Этот промокод не найден.")
        return

    record = get_user_record(message.from_user.id)
    if code in record['redeemed_codes']:
        await message.reply("⚠️ Ты уже активировал этот промокод.")
        return

    if promo['type'] == 'coins':
        record['coins'] += promo['value']
        message_text = f"✅ Промокод {code} активирован! Ты получил {promo['value']} вайтов."
    elif promo['type'] == 'vip':
        record['vip_member'] = True
        message_text = f"🌟 Промокод {code} активирован! VIP-статус включён."
    else:
        message_text = f"✅ Промокод {code} активирован!"

    record['redeemed_codes'].append(code)
    db.save_user(message.from_user.id, record)
    await message.reply(message_text)

@dp.message(Command("create_promo"))
async def create_promo(message: types.Message):
    if message.from_user.id not in STAFF_IDS:
        return

    args = message.text.split(maxsplit=4)
    if len(args) < 5:
        await message.reply("⚠️ Использование: /create_promo CODE type value Описание")
        return

    code = args[1].strip().upper()
    promo_type = args[2].strip().lower()
    value_text = args[3].strip()
    description = args[4].strip()

    if code in promo_codes:
        await message.reply(f"⚠️ Промокод {code} уже существует.")
        return

    if promo_type not in ('coins', 'vip'):
        await message.reply("⚠️ Тип промокода должен быть coins или vip.")
        return

    value = None
    if promo_type == 'coins':
        try:
            value = int(value_text)
        except ValueError:
            await message.reply("⚠️ Укажи числовое значение для coins. Пример: /create_promo WIN100 coins 100 Описание")
            return
    elif promo_type == 'vip':
        value = None

    promo = {
        'type': promo_type,
        'value': value,
        'description': description,
    }
    promo_codes[code] = promo
    db.save_promo_code(code, promo)
    await message.reply(f"✅ Промокод {code} создан: {description}")

@dp.message(F.text.regexp(r'(?i)^help$'))
async def help_plain_text(message: types.Message):
    await help_command(message)

@dp.message(Command("profile"))
async def profile_command(message: types.Message):
    args = message.text.split(maxsplit=1)
    target_id = message.from_user.id
    
    if len(args) > 1 and args[1].strip():
        identifier = args[1].strip()
        found_id = find_user_id(identifier)
        if found_id is None:
            await message.answer("⚠️ Пользователь не найден по ID, нику или username.")
            return
        target_id = found_id
    
    record = get_user_record(target_id)
    
    nick = record.get('nickname') or 'Нету'
    title = record.get('title') or 'Нету'
    bio = record.get('bio') or 'Нету'
    style = record.get('custom_style') or 'Дефолтный'
    emoji = record.get('favorite_emoji') or '—'
    badges = record.get('badges') or []
    badge_text = '\n'.join(f'• {badge}' for badge in badges) if badges else 'Нету'
    muted_status = "Нет"
    if record.get('muted_until') and record['muted_until'] > datetime.now():
        muted_status = f"До {record['muted_until'].strftime('%d.%m.%Y %H:%M')}"

    if record.get('total_messages', 0) >= 3000:
        rank = 'Легенда'
    elif record.get('total_messages', 0) >= 900:
        rank = 'Ветеран'
    elif record.get('total_messages', 0) >= 500:
        rank = 'Игрок'
    else:
        rank = 'Новичок'

        

    profile_text = (
        f"👤 **Профиль игрока {target_id}{nick}**\n\n "
         f"├ Твой Ранг: {rank}\n"
        f"📝 Описание: {bio}\n"
        f"🎨 Стиль: {style}\n"
        f"✨ Эмодзи профиля: {emoji}\n"
        f"🏅 Ранг игрока: {rank}\n"
        f"💰 Баланс: {record.get('coins', 0)} вайтов\n"
        f"🚫 Нарушений: {record.get('infractions', 0)}\n"
        f"🌟 VIP-статус: {'Подключён' if record.get('vip_member') else 'Не подключён'}\n"
        f"🕒 Первый вход в бота: {record.get('first_seen').strftime('%d.%m.%Y %H:%M') if record.get('first_seen') else 'Неизвестно'}\n"
        f"├  Сообщений всего: {record['total_messages']}\n"
         
    )
    
    await message.answer(profile_text, parse_mode="Markdown")

@dp.message(Command("give_coins"))
async def give_money(message: types.Message):
    if message.from_user.id not in STAFF_IDS:
        return
    
    try:
        args = message.text.split()
        if len(args) < 6:
            raise ValueError
        
        target_id = int(args[1])
        amount = int(args[2])
        record = get_user_record(target_id)
        record['coins'] += amount
        await message.answer(f"✅ Игроку {target_id} начислено {amount} вайтов.")
        db.save_user(target_id, record)
    except (IndexError, ValueError):
        await message.answer("⚠️ Ошибка. Пример: `/give_coins 1234567 1000`", parse_mode="Markdown")

@dp.message(Command("stats"))
async def bot_stats(message: types.Message):
    if message.from_user.id not in STAFF_IDS:
        return

    total_users = len(user_data)
    total_infractions = sum(record.get('infractions', 0) for record in user_data.values())
    active_mutes = [uid for uid, record in user_data.items() if record.get('muted_until') and record['muted_until'] > datetime.now()]

    await message.answer(
        f"📊 Статистика бота:\n"
        f"Пользователей в БД: {total_users}\n"
        f"Всего Нарушений: {total_infractions}\n"
        f"Активных мутов: {len(active_mutes)}"
    )

@dp.message(Command("users"))
async def list_users(message: types.Message):
    if message.from_user.id not in STAFF_IDS:
        return

    if not user_data:
        await message.answer("⚠️ Пока нет пользователей в базе данных.")
        return

    lines = []
    for uid, record in sorted(user_data.items(), key=lambda item: item[0]):
        name = record.get('full_name') or record.get('username') or 'Не поставил ник'
        nickname = record.get('nickname') or '-'
        first_seen = record.get('first_seen')
        first_seen_text = first_seen.strftime('%d.%m.%Y %H:%M') if first_seen else 'Неизвестно'
        lines.append(f"{uid}: {name} | ник: {nickname} | первый заход в бота: {first_seen_text}")

    text = "👥 Известные пользователи:\n" + "\n".join(lines[:40])
    if len(lines) > 40:
        text += f"\n...еще {len(lines) - 40} пользователей"

    await message.answer(text)

@dp.message(Command("infractions"))
async def infractions_info(message: types.Message):
    if message.from_user.id not in STAFF_IDS:
        return

    args = message.text.split()
    if len(args) < 2:
        top_offenders = sorted(
            [(uid, record.get('infractions', 0), record.get('last_violation')) for uid, record in user_data.items() if record.get('infractions', 0) > 0],
            key=lambda item: item[1],
            reverse=True
        )[:10]

        if not top_offenders:
            await message.answer("⚠️ Нет найденных нарушителей.")
            return

        text = "🔥 Топ нарушителей:\n"
        for uid, inf, last in top_offenders:
            text += f"ID {uid}: {inf} нарушений, последнее: {last or 'нет данных'}\n"
        await message.answer(text)
        return

    try:
        target_id = int(args[1])
        record = user_data.get(target_id)
        if not record:
            await message.answer(f"⚠️ Данный пользователь {target_id} не найден в базе.")
            return

        await message.answer(
            f"📌 Инфраструктура пользователя {target_id}:\n"
            f"Нарушений: {record.get('infractions', 0)}\n"
            f"Последнее нарушение: {record.get('last_violation') or 'нет данных'}\n"
            f"Мут до: {record.get('muted_until') or 'нету'}"
        )
    except ValueError:
        await message.answer("⚠️ Укажите правильный ID пользователя.")

@dp.message(Command("violators"))
async def list_violators(message: types.Message):
    if message.from_user.id not in STAFF_IDS:
        return

    violators = sorted(
        [(uid, record.get('infractions', 0)) for uid, record in user_data.items() if record.get('infractions', 0) > 0],
        key=lambda item: item[1],
        reverse=True
    )

    if not violators:
        await message.answer("⚠️ Список нарушителей пуст.")
        return

    text = "📝 Нарушители:\n"
    for uid, infractions in violators[:10]:
        text += f"ID {uid}: {infractions} нарушений\n"
    await message.answer(text)

@dp.message(Command("warn"))
async def warn_user(message: types.Message):
    if message.from_user.id not in STAFF_IDS:
        return

    try:
        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            raise ValueError
        target_id = int(args[1])
        reason = args[2].strip()
        record = get_user_record(target_id)
        record['infractions'] += 1
        record['last_violation'] = f"warn: {reason}"
        await message.answer(f"✅ Пользователь {target_id} получил предупреждение с причиной: {reason}")
        db.save_user(target_id, record)
    except ValueError:
        await message.answer("⚠️ Пример: `/warn 6723182 Причина нарушения`")

# Функция-помощник для проверки админа
async def is_user_admin(chat_id: int, user_id: int) -> bool:
    """Проверяет, является ли юзер админом в конкретном чате"""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False

# === МОДЕРАЦИЯ ===

@dp.message(Command("mute"))
async def mute_user_handler(message: types.Message):
    """Замутить пользователя"""
    if message.chat.type == "private":
        return await message.reply("❌ Мут работает только в группах.")

    if not await is_user_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Ты не админ.")

    args = message.text.split()
    target_id, display_name = await get_target_user(message, args)
    
    if not target_id:
        return await message.reply("⚠️ Юзай: /mute [мин] (ответ на сообщение) или /mute [@username|ID] [мин]")

    minutes = 30
    if message.reply_to_message and len(args) > 1 and args[1].isdigit():
        minutes = int(args[1])
    elif not message.reply_to_message and len(args) > 2 and args[2].isdigit():
        minutes = int(args[2])

    if await is_user_admin(message.chat.id, target_id):
        return await message.reply("🛡 Нельзя ограничить администратора.")

    until = datetime.now() + timedelta(minutes=minutes)
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_id,
            permissions=types.ChatPermissions(can_send_messages=False),
            until_date=until
        )
        
        record = get_user_record(target_id)
        record['muted_until'] = until
        db.save_user(target_id, record)

        await message.answer(f"🔇 {display_name} замучен на {minutes} мин.\nМод: {message.from_user.first_name}")
        await message.delete() 
    except Exception as e:
        await message.answer(f"❌ Ошибка API: {e}")

@dp.message(Command("unmute"))
async def unmute_user_handler(message: types.Message):
    """Размутить пользователя"""
    if message.chat.type == "private":
        return await message.reply("❌ Размут работает только в группах.")
    
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Ты не админ.")
    
    args = message.text.split()
    target_id, display_name = await get_target_user(message, args)
    
    if not target_id:
        return await message.reply("⚠️ Юзай: /unmute (ответ на сообщение) или /unmute [@username|ID]")
    
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_id,
            permissions=types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
        )
        
        record = get_user_record(target_id)
        record['muted_until'] = None
        db.save_user(target_id, record)
        
        await message.answer(f"🔊 {display_name} размучен.\nМод: {message.from_user.first_name}")
        await message.delete()
    except Exception as e:
        await message.answer(f"❌ Ошибка API: {e}")

@dp.message(Command("ban"))
async def ban_user_handler(message: types.Message):
    """Забанить пользователя"""
    if message.chat.type == "private":
        return await message.reply("❌ Бан работает только в группах.")
    
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Ты не админ.")
    
    args = message.text.split(maxsplit=2)
    target_id, display_name = await get_target_user(message, args)
    
    if not target_id:
        return await message.reply("⚠️ Юзай: /ban [причина] (ответ на сообщение) или /ban [@username|ID] [причина]")
    
    reason = "Не указана"
    if message.reply_to_message and len(args) > 1:
        reason = args[1]
    elif not message.reply_to_message and len(args) > 2:
        reason = args[2]
    
    if await is_user_admin(message.chat.id, target_id):
        return await message.reply("🛡 Нельзя забанить администратора.")
    
    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_id)
        
        record = get_user_record(target_id)
        record['infractions'] += 5
        record['last_violation'] = f"ban: {reason}"
        db.save_user(target_id, record)
        
        await message.answer(
            f"🔨 {display_name} забанен.\n"
            f"Причина: {reason}\n"
            f"Модератор: {message.from_user.first_name}"
        )
        await message.delete()
    except Exception as e:
        await message.answer(f"❌ Ошибка API: {e}")

@dp.message(Command("unban"))
async def unban_user_handler(message: types.Message):
    """Разбанить пользователя"""
    if message.chat.type == "private":
        return await message.reply("❌ Разбан работает только в группах.")
    
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Ты не админ.")
    
    args = message.text.split()
    target_id, display_name = await get_target_user(message, args)
    
    if not target_id:
        return await message.reply("⚠️ Юзай: /unban [@username|ID]")
    
    try:
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_id, only_if_banned=True)
        await message.answer(f"✅ {display_name} разбанен.\nМод: {message.from_user.first_name}")
        await message.delete()
    except Exception as e:
        await message.answer(f"❌ Ошибка API: {e}")

@dp.message(Command("kick"))
async def kick_user_handler(message: types.Message):
    """Кикнуть пользователя"""
    if message.chat.type == "private":
        return await message.reply("❌ Кик работает только в группах.")
    
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Ты не админ.")
    
    args = message.text.split(maxsplit=2)
    target_id, display_name = await get_target_user(message, args)
    
    if not target_id:
        return await message.reply("⚠️ Юзай: /kick [причина] (ответ на сообщение) или /kick [@username|ID] [причина]")
    
    reason = "Не указана"
    if message.reply_to_message and len(args) > 1:
        reason = args[1]
    elif not message.reply_to_message and len(args) > 2:
        reason = args[2]
    
    if await is_user_admin(message.chat.id, target_id):
        return await message.reply("🛡 Нельзя кикнуть администратора.")
    
    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_id)
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_id)
        
        record = get_user_record(target_id)
        record['infractions'] += 2
        record['last_violation'] = f"kick: {reason}"
        db.save_user(target_id, record)
        
        await message.answer(
            f"👢 {display_name} кикнут.\n"
            f"Причина: {reason}\n"
            f"Модератор: {message.from_user.first_name}"
        )
        await message.delete()
    except Exception as e:
        await message.answer(f"❌ Ошибка API: {e}")

@dp.message(Command("del"))
async def delete_message_handler(message: types.Message):
    """Удаляет сообщение, на которое сделан реплей"""
    if message.chat.type == "private":
        return
    
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return
    
    if message.reply_to_message:
        try:
            await message.reply_to_message.delete()
            await message.delete()
        except Exception as e:
            await message.reply(f"❌ Не удалось удалить: {e}")

@dp.message(Command("pin"))
async def pin_message_handler(message: types.Message):
    """Закрепить сообщение"""
    if message.chat.type == "private":
        return await message.reply("❌ Закрепление работает только в группах.")
    
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Ты не админ.")
    
    if not message.reply_to_message:
        return await message.reply("⚠️ Ответь на сообщение, которое хочешь закрепить.")
    
    try:
        await bot.pin_chat_message(
            chat_id=message.chat.id,
            message_id=message.reply_to_message.message_id,
            disable_notification=False
        )
        await message.answer(f"📌 Сообщение закреплено.\nМодератор: {message.from_user.first_name}")
        await message.delete()
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("unpin"))
async def unpin_message_handler(message: types.Message):
    """Открепить сообщение"""
    if message.chat.type == "private":
        return await message.reply("❌ Открепление работает только в группах.")
    
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Ты не админ.")
    
    try:
        if message.reply_to_message:
            await bot.unpin_chat_message(
                chat_id=message.chat.id,
                message_id=message.reply_to_message.message_id
            )
        else:
            await bot.unpin_chat_message(chat_id=message.chat.id)
        
        await message.answer(f"📌 Сообщение откреплено.\nМодератор: {message.from_user.first_name}")
        await message.delete()
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# === СИСТЕМА БРАКОВ ===

@dp.message(Command("marry"))
async def marry_command(message: types.Message):
    """Предложить брак пользователю"""
    args = message.text.split()
    target_id, display_name = await get_target_user(message, args)
    
    if not target_id:
        return await message.reply("⚠️ Укажи кому предложить брак: /marry (ответ на сообщение) или /marry [@username|ID]")
    
    if target_id == message.from_user.id:
        return await message.reply("😅 Нельзя жениться на самом себе!")
    
    sender_record = get_user_record(message.from_user.id)
    target_record = get_user_record(target_id)
    
    if sender_record.get('married_to'):
        return await message.reply("💔 Ты уже в браке! Сначала разведись: /divorce")
    
    if target_record.get('married_to'):
        return await message.reply(f"💔 {display_name} уже в браке!")
    
    # Создаем предложение брака
    sender_name = message.from_user.first_name
    await message.answer(
        f"💍 {sender_name} делает предложение {display_name}!\n\n"
        f"{display_name}, напиши /accept чтобы принять или /reject чтобы отклонить."
    )
    
    # Сохраняем временное предложение
    if 'marriage_proposals' not in user_data:
        user_data['marriage_proposals'] = {}
    user_data['marriage_proposals'][target_id] = message.from_user.id

@dp.message(Command("accept"))
async def accept_marriage(message: types.Message):
    """Принять предложение брака"""
    user_id = message.from_user.id
    
    if 'marriage_proposals' not in user_data or user_id not in user_data['marriage_proposals']:
        return await message.reply("⚠️ У тебя нет предложений брака.")
    
    partner_id = user_data['marriage_proposals'][user_id]
    
    user_record = get_user_record(user_id)
    partner_record = get_user_record(partner_id)
    
    if user_record.get('married_to') or partner_record.get('married_to'):
        del user_data['marriage_proposals'][user_id]
        return await message.reply("💔 Кто-то из вас уже в браке!")
    
    # Оформляем брак
    marriage_date = datetime.now()
    user_record['married_to'] = partner_id
    user_record['marriage_date'] = marriage_date
    partner_record['married_to'] = user_id
    partner_record['marriage_date'] = marriage_date
    
    db.save_user(user_id, user_record)
    db.save_user(partner_id, partner_record)
    
    del user_data['marriage_proposals'][user_id]
    
    partner_name = partner_record.get('nickname') or partner_record.get('full_name') or f"ID{partner_id}"
    user_name = message.from_user.first_name
    
    await message.answer(
        f"💒 Поздравляем! {user_name} и {partner_name} теперь в браке! 🎉\n"
        f"Дата свадьбы: {marriage_date.strftime('%d.%m.%Y')}"
    )

@dp.message(Command("reject"))
async def reject_marriage(message: types.Message):
    """Отклонить предложение брака"""
    user_id = message.from_user.id
    
    if 'marriage_proposals' not in user_data or user_id not in user_data['marriage_proposals']:
        return await message.reply("⚠️ У тебя нет предложений брака.")
    
    del user_data['marriage_proposals'][user_id]
    await message.reply("💔 Ты отклонил предложение брака.")

@dp.message(Command("divorce"))
async def divorce_command(message: types.Message):
    """Развестись"""
    user_id = message.from_user.id
    user_record = get_user_record(user_id)
    
    if not user_record.get('married_to'):
        return await message.reply("⚠️ Ты не в браке!")
    
    partner_id = user_record['married_to']
    partner_record = get_user_record(partner_id)
    
    # Разводим
    user_record['married_to'] = None
    user_record['marriage_date'] = None
    partner_record['married_to'] = None
    partner_record['marriage_date'] = None
    
    db.save_user(user_id, user_record)
    db.save_user(partner_id, partner_record)
    
    partner_name = partner_record.get('nickname') or partner_record.get('full_name') or f"ID{partner_id}"
    
    await message.answer(f"💔 Развод оформлен. {message.from_user.first_name} и {partner_name} больше не в браке.")

@dp.message(Command("marriage"))
async def marriage_info(message: types.Message):
    """Информация о браке"""
    args = message.text.split()
    
    if len(args) > 1:
        target_id, display_name = await get_target_user(message, args)
        if not target_id:
            return await message.reply("⚠️ Пользователь не найден.")
    else:
        target_id = message.from_user.id
        display_name = message.from_user.first_name
    
    record = get_user_record(target_id)
    
    if not record.get('married_to'):
        return await message.answer(f"💔 {display_name} не в браке.")
    
    partner_id = record['married_to']
    partner_record = get_user_record(partner_id)
    partner_name = partner_record.get('nickname') or partner_record.get('full_name') or f"ID{partner_id}"
    
    marriage_date = record.get('marriage_date')
    if marriage_date:
        if isinstance(marriage_date, str):
            marriage_date = datetime.fromisoformat(marriage_date)
        days_married = (datetime.now() - marriage_date).days
        date_str = marriage_date.strftime('%d.%m.%Y')
    else:
        days_married = 0
        date_str = "Неизвестно"
    
    await message.answer(
        f"💑 Информация о браке:\n\n"
        f"{display_name} 💕 {partner_name}\n"
        f"Дата свадьбы: {date_str}\n"
        f"В браке: {days_married} дней"
    )

# === РП КОМАНДЫ ===

@dp.message(Command("обнять"))
async def  hug_command(message: types.Message):
    """Обнять пользователя"""
    args = message.text.split()
    target_id, display_name = await get_target_user(message, args)
    
    if not target_id:
        return await message.reply("⚠️ Укажи кого обнять: /обнять (ответ на сообщение) или /обнять [@username|ID]")
    
    sender_name = message.from_user.first_name
    await message.answer(f"🤗 {sender_name} обнимает {display_name}!")

@dp.message(Command("kiss"))
async def kiss_command(message: types.Message):
    """Поцеловать пользователя"""
    args = message.text.split()
    target_id, display_name = await get_target_user(message, args)
    
    if not target_id:
        return await message.reply("⚠️ Укажи кого поцеловать: /kiss (ответ на сообщение) или /kiss [@username|ID]")
    
    sender_name = message.from_user.first_name
    await message.answer(f"😘 {sender_name} целует {display_name}!")

@dp.message(Command("slap"))
async def slap_command(message: types.Message):
    """Дать пощечину пользователю"""
    args = message.text.split()
    target_id, display_name = await get_target_user(message, args)
    
    if not target_id:
        return await message.reply("⚠️ Укажи кого ударить: /slap (ответ на сообщение) или /slap [@username|ID]")
    
    sender_name = message.from_user.first_name
    await message.answer(f"👋 {sender_name} дает пощечину {display_name}!")

@dp.message(Command("pat"))
async def pat_command(message: types.Message):
    """Погладить пользователя"""
    args = message.text.split()
    target_id, display_name = await get_target_user(message, args)
    
    if not target_id:
        return await message.reply("⚠️ Укажи кого погладить: /pat (ответ на сообщение) или /pat [@username|ID]")
    
    sender_name = message.from_user.first_name
    await message.answer(f"🤲 {sender_name} гладит {display_name} по голове!")

@dp.message(Command("poke"))
async def poke_command(message: types.Message):
    """Тыкнуть пользователя"""
    args = message.text.split()
    target_id, display_name = await get_target_user(message, args)
    
    if not target_id:
        return await message.reply("⚠️ Укажи кого тыкнуть: /poke (ответ на сообщение) или /poke [@username|ID]")
    
    sender_name = message.from_user.first_name
    await message.answer(f"👉 {sender_name} тыкает {display_name}!")

@dp.message(Command("bite"))
async def bite_command(message: types.Message):
    """Укусить пользователя"""
    args = message.text.split()
    target_id, display_name = await get_target_user(message, args)
    
    if not target_id:
        return await message.reply("⚠️ Укажи кого укусить: /bite (ответ на сообщение) или /bite [@username|ID]")
    
    sender_name = message.from_user.first_name
    await message.answer(f" {sender_name} кусает {display_name}!")

@dp.message(Command("cuddle"))
async def cuddle_command(message: types.Message):
    """Обнять и прижать пользователя"""
    args = message.text.split()
    target_id, display_name = await get_target_user(message, args)
    
    if not target_id:
        return await message.reply("⚠️ Укажи кого обнять: /cuddle (ответ на сообщение) или /cuddle [@username|ID]")
    
    sender_name = message.from_user.first_name
    await message.answer(f"🫂 {sender_name} нежно обнимает {display_name}!")

@dp.message(Command("dance"))
async def dance_command(message: types.Message):
    """Потанцевать с пользователем"""
    args = message.text.split()
    
    if len(args) > 1 or message.reply_to_message:
        target_id, display_name = await get_target_user(message, args)
        if target_id:
            sender_name = message.from_user.first_name
            await message.answer(f"💃🕺 {sender_name} танцует с {display_name}!")
        else:
            await message.answer(f"💃 {message.from_user.first_name} танцует!")
    else:
        await message.answer(f"💃 {message.from_user.first_name} танцует!")

@dp.message(Command("cry"))
async def cry_command(message: types.Message):
    """Плакать"""
    await message.answer(f"😭 {message.from_user.first_name} плачет...")

@dp.message(Command("laugh"))
async def laugh_command(message: types.Message):
    """Смеяться"""
    await message.answer(f"😂 {message.from_user.first_name} смеется!")

@dp.message(Command("sleep"))
async def sleep_command(message: types.Message):
    """Спать"""
    await message.answer(f"😴 {message.from_user.first_name} спит... Zzz...")


        

# --- СЛЕЖКА ЗА ЧАТОМ (Должен быть последним среди текстовых хендлеров) ---

@dp.message()
async def all_messages(message: types.Message):
    print(f"Получено сообщение: {message.text} от {message.from_user.id} {message.from_user.username} в чате {message.chat.id} тип {message.chat.type}")
    record = get_user_record(message.from_user.id)
    record['total_messages'] += 1
    record['daily_messages'] += 1
    record['username'] = message.from_user.username
    record['full_name'] = message.from_user.full_name
    db.save_user(message.from_user.id, record)

    if message.chat:
        db.update_chat_message(message.chat.id, message.from_user.id)

@dp.message(F.text)
async def monitor_chat(message: types.Message):
    text = message.text.lower()
    
    # Модерация
    if any(word in text for word in BANNED_WORDS):
        record = get_user_record(message.from_user.id)
        record['infractions'] += 1
        record['last_violation'] = f"мат: {text}"

        if message.chat.type in ("group", "supergroup"):
            try:
                await message.delete()
            except:
                pass

            try:
                until = datetime.now() + timedelta(minutes=30)
                await bot.restrict_chat_member(
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                    permissions=types.ChatPermissions(
                        can_send_messages=False,
                        can_send_media_messages=False,
                        can_send_polls=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                    ),
                    until_date=until
                )
                record['muted_until'] = until
                await message.answer(f"🚫 {message.from_user.first_name}, ты замучен на 30 минут за некорректное слово.")
            except Exception:
                await message.answer("⚠️ Не удалось замутить пользователя. Проверь права бота и уровень администратора.")
        else:
            try:
                await message.delete()
            except:
                pass
            await message.answer(f"🤫 {message.from_user.first_name}, не материтесь!")
        return # Прерываем выполнение, чтобы бот не отвечал на "бот" в матерном сообщении






# --- ЗАПУСК БОТА ---

async def main():
    print("🚀 Бот запущен и готов к работе!")
    print("Ожидание обновлений...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    
    print("Ожидание обновлений...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
    finally:
        print("Сохранение данных...")
        db.save_all_users(user_data)
        print("Данные сохранены!") 
