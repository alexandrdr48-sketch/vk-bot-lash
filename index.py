import json
import urllib.request
import urllib.parse
import os

# ==========================================
# НАСТРОЙКИ ВКОНТАКТЕ
# ==========================================
VK_TOKEN = os.environ.get('VK_TOKEN')
VK_API_VERSION = "5.199"
CONFIRM_STR = os.environ.get('CONFIRMATION_CODE')
WEB_APP_URL = "https://ole4kalashes.ru/book.html"

# ==========================================
# БАЗОВЫЕ ФУНКЦИИ БОТА
# ==========================================
def send_message(user_id, text, keyboard=None):
    url = "https://api.vk.com/method/messages.send"
    data = {"user_id": user_id, "message": text, "random_id": 0, "access_token": VK_TOKEN, "v": VK_API_VERSION}
    if keyboard: data["keyboard"] = json.dumps(keyboard)
    try: urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode(data).encode('utf-8')), timeout=5)
    except Exception: pass

def send_event_answer(event_id, user_id, peer_id):
    url = "https://api.vk.com/method/messages.sendMessageEventAnswer"
    data = {"event_id": event_id, "user_id": user_id, "peer_id": peer_id, "access_token": VK_TOKEN, "v": VK_API_VERSION}
    try: urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode(data).encode('utf-8')), timeout=5)
    except Exception: pass

def get_user_name(user_id):
    url = f"https://api.vk.com/method/users.get?user_ids={user_id}&access_token={VK_TOKEN}&v={VK_API_VERSION}"
    try:
        data = json.loads(urllib.request.urlopen(url, timeout=5).read().decode('utf-8'))
        if "response" in data and len(data["response"]) > 0: return data["response"][0].get("first_name", "Клиент")
    except Exception: pass
    return "Клиент"

def get_main_keyboard(user_id, first_name):
    safe_name = urllib.parse.quote(first_name)
    personalized_url = f"{WEB_APP_URL}?uid={user_id}&name={safe_name}&platform=vk"
    return {
        "inline": False,
        "buttons": [
            [{"action": {"type": "open_link", "link": personalized_url, "label": "📅 Записаться"}}],
            [{"action": {"type": "text", "label": "🌸 Прайс-лист"}, "color": "secondary"},
             {"action": {"type": "text", "label": "✨ Подобрать эффект"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "⏱ Калькулятор времени"}, "color": "secondary"},
             {"action": {"type": "text", "label": "📸 Примеры моих работ"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "🛠 Материалы и инструменты"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "📋 Чек-лист ухода"}, "color": "secondary"},
             {"action": {"type": "text", "label": "📝 Памятка клиенту"}, "color": "secondary"}]       
        ]
    }

def get_inline_keyboard(buttons_data):
    buttons = [[{"action": {"type": "callback", "label": btn["label"], "payload": json.dumps({"cmd": btn["payload"]})}, "color": "primary"}] for btn in buttons_data]
    return {"inline": True, "buttons": buttons}

# ==========================================
# ОСНОВНОЙ ОБРАБОТЧИК (HANDLER)
# ==========================================
def handler(event, context):
    try:
        data = json.loads(event.get('body', '{}'))
        if data.get('type') == 'confirmation': return {'statusCode': 200, 'body': CONFIRMATION_CODE}

        if data.get('type') == 'message_event':
            obj = data.get('object', {})
            cmd = obj.get('payload', {}).get('cmd', '')
            reply_text = ""
            
            if cmd == "quiz_almond": reply_text = "✨ Для миндалевидных глаз идеально подойдет Лисий или Беличий эффект!"
            elif cmd == "quiz_round": reply_text = "✨ Для круглых глаз отлично подойдет Натуральный эффект или легкая Лиса!"
            elif cmd == "quiz_hooded": reply_text = "✨ С нависшим веком круто работает L-изгиб или Кукольный эффект!"
            elif cmd == "calc_rare": reply_text = "⏱ Твои реснички не очень густые. Наращивание займет примерно 1 час 30 минут."
            elif cmd == "calc_medium": reply_text = "⏱ Твои реснички средней густоты. Наращивание займет около 2 часов."
            elif cmd == "calc_dense": reply_text = "⏱ У тебя густые ресницы! Процедура займет около 2 часов 30 минут."
            
            if reply_text:
                send_event_answer(obj.get('event_id'), obj.get('user_id'), obj.get('peer_id'))
                send_message(obj.get('user_id'), reply_text)
            return {'statusCode': 200, 'body': 'ok'}

        if data.get('type') == 'message_new':
            msg = data.get('object', {}).get('message', {})
            user_id = msg.get('from_id')
            text = msg.get('text', '')
            first_name = get_user_name(user_id)
            keyboard = get_main_keyboard(user_id, first_name)
            inline_kb = None

            # Переводим текст в нижний регистр для удобного поиска ключевых слов
            t_low = text.lower()

            # Приветствие
            if t_low in ["начать", "привет", "здравствуйте", "добрый день", "меню"]:
                reply = f"Привет, {first_name}! 🌸\n\nРада видеть тебя в бьюти-пространстве Ольги Маликовой!\n\nЯ — твой виртуальный бьюти-ассистент. Знаю всё о том, как сделать твои утренние сборы быстрыми, а взгляд — безупречным без капли туши. ✨\n\nВыбирай нужный раздел в меню внизу 👇"
            
            # Прайс-лист
            elif text == "🌸 Прайс-лист" or any(word in t_low for word in ["прайс", "цен", "стоимост", "скольк", "почем"]):
                reply = "Наш прайс-лист:\n\n✨ Классика — 1700 руб.\n✨ Объём 1.5D - 1700 руб.\n✨ Объем 2D — 1800 руб.\n✨ Объем 2,5D — 2000 руб.\n✨ Объем 3D — 2200 руб.\n✨ Мокрый эффект — 2D-2000/3D-2200 руб.\n✨ Трендовые эффекты — 2500 руб.\n✨ Лучики — 500 руб.\n✨ Снятие чужой работы/на отдых — 400 руб."
            
            # Материалы
            elif text == "🛠 Материалы и инструменты" or any(word in t_low for word in ["материал", "инструмент", "клей", "фирм", "бренд"]):
                reply = "Я использую только премиум-материалы:\n\n💧 Клей: Lovely Focus, Enigma «Nova».\n🎀 Ресницы: Lovely, Enigma, Posh Lash, Le mat. Мягкие, легкие, не ощущаются.\n✨ Инструменты: Все проходят тщательную стерилизацию."
            
            # Уход
            elif text == "📋 Чек-лист ухода" or any(word in t_low for word in ["уход", "умыва", "мочи", "спать", "чесат", "расчес"]):
                reply = "Чек-лист: Как продлить жизнь ресничкам 📋\n\n❌ Первые 24 часа: не мочить, не посещать баню/сауну.\n🧴 Умывание: используй средства без масел.\n🧹 Расчесывание: щеточкой 1-2 раза в день, только сухие ресницы!\n😴 Сон: не спать лицом в подушку."
            
            # Памятка
            elif text == "📝 Памятка клиенту" or any(word in t_low for word in ["памятк", "правил", "опозда", "подготов"]):
                reply = "Твой взгляд — мой главный проект ✨\n\nПравила работы:\n1️⃣ Приходите без макияжа глаз.\n2️⃣ Опоздание — 15 минут.\n3️⃣ Время процедуры: 1.5 - 2.5 часов.\n4️⃣ Если недомогание — давайте перенесем запись. ❤️"
            
            # Примеры работ
            elif text == "📸 Примеры моих работ" or any(word in t_low for word in ["фот", "пример", "работ", "портфолио"]):
                reply = "✨ Посмотреть мои работы во всей красе можно в основном разделе группы!\n\n🌸 Там я собрала для вас лучшие примеры наращивания.\n\n👉 Переходите в альбомы группы: https://vk.ru/album-224960770_301899290"
            
            # Подобрать эффект
            elif text == "✨ Подобрать эффект" or any(word in t_low for word in ["эффект", "подобрать", "какой выбрать", "какой мне"]):
                reply = "Давай подберем идеальное наращивание! 👁\nКакая у тебя форма глаз?"
                inline_kb = get_inline_keyboard([{"label": "Миндалевидная", "payload": "quiz_almond"}, {"label": "Круглая", "payload": "quiz_round"}, {"label": "С нависшим веком", "payload": "quiz_hooded"}])
            
            # Калькулятор времени
            elif text == "⏱ Калькулятор времени" or any(word in t_low for word in ["врем", "долг", "длит", "часов", "минут"]):
                reply = "Давай рассчитаем время процедуры ⏱\nКак бы ты оценила густоту своих родных ресниц?"
                inline_kb = get_inline_keyboard([{"label": "Редкие", "payload": "calc_rare"}, {"label": "Средние", "payload": "calc_medium"}, {"label": "Очень густые", "payload": "calc_dense"}])
            
            # Если текст не распознан
            else:
                reply = "Пожалуйста, воспользуйтесь кнопками меню 👇"

            send_message(user_id, reply, inline_kb if inline_kb else keyboard)

        return {'statusCode': 200, 'body': 'ok'}
    except Exception as e: 
        print(f"Global Error: {e}")
        return {'statusCode': 200, 'body': 'ok'}