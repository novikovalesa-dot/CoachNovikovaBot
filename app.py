import os
from typing import Dict, Any
from pathlib import Path

import httpx
from fastapi import FastAPI, Request

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else ""

app = FastAPI(title="CoachNovikovaBot")

USERS: Dict[int, Dict[str, Any]] = {}
BASE_DIR = Path(__file__).resolve().parent
PREMISES_PDF = BASE_DIR / "assets" / "trebovaniya_SES_pomeshchenie.pdf"
OPENING_CHECKLIST_PDF = BASE_DIR / "assets" / "checklist_otkrytie_centra.pdf"

MENU = [
    ["🏢 Проверить помещение", "📑 Документы"],
    [
        {
            "text": "💰 Финансовый калькулятор открытия",
            "web_app": {"url": "https://coach-novikova.tilda.ws/open"}
        },
        {
            "text": "📊 Расчет доходов и расходов",
            "web_app": {"url": "https://coach-novikova.tilda.ws/odir"}
        }
    ],
    ["📚 Программы", "📣 Маркетинг"],
    ["🗺 Мой план открытия", "💬 Консультация"],
]

PREMISES_MENU = [
    ["💬 Получить консультацию"],
    ["⬅️ Главное меню"],
]

FINANCE_FIELDS = [
    ("rent", "Введите аренду в месяц, тг"),
    ("payroll", "Введите ФОТ в месяц, тг"),
    ("utilities", "Введите коммунальные расходы, тг"),
    ("food", "Введите расходы на питание, тг"),
    ("ads", "Введите рекламный бюджет, тг"),
    ("taxes", "Введите налоги и банковские комиссии, тг"),
    ("other", "Введите прочие расходы, тг"),
    ("children", "Сколько детей планируете?"),
    ("ticket", "Средний чек на одного ребёнка в месяц, тг"),
]


def keyboard(rows):
    def button(x):
        return x if isinstance(x, dict) else {"text": x}

    return {
        "keyboard": [[button(x) for x in row] for row in rows],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


async def send(chat_id: int, text: str, rows=None):
    if not BASE_URL:
        return
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if rows:
        payload["reply_markup"] = keyboard(rows)
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(f"{BASE_URL}/sendMessage", json=payload)


async def send_document(chat_id: int, file_path: Path, caption: str = ""):
    if not BASE_URL or not file_path.exists():
        return False
    data = {
        "chat_id": str(chat_id),
        "caption": caption,
        "parse_mode": "HTML",
    }
    with file_path.open("rb") as f:
        files = {"document": (file_path.name, f, "application/pdf")}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{BASE_URL}/sendDocument",
                data=data,
                files=files,
            )
    return response.status_code == 200


def state(chat_id: int):
    return USERS.setdefault(chat_id, {
        "mode": None, "answers": {}, "finance": {}, "f": 0
    })


async def start(chat_id: int):
    USERS[chat_id] = {"mode": None, "answers": {}, "finance": {}, "f": 0}
    text = (
        "Здравствуйте! 👋\n\n"
        "Я — виртуальный помощник <b>Coach Novikova</b> по открытию детских центров в Казахстане 🇰🇿\n\n"
        "Здесь вы сможете:\n"
        "🏢 разобраться с помещением\n"
        "📑 понять, какие документы нужны\n"
        "💰 рассчитать инвестиции при открытии\n"
        "📚 рассчитать финансовую модель, расходы и доходы центра\n"
        "📣 получить чек-лист по маркетингу\n"
        "✅ получить чек-лист по открытию"
    )
    await send(chat_id, text, MENU)



def plan_text(a):
    items = []
    if a.get("premises") in ("Нет помещения", "Рассматриваю варианты"):
        items.append("1. Подобрать помещение и проверить его до долгосрочной аренды и серьёзных вложений.")
    else:
        items.append("1. Проверить выбранное помещение по площади, планировке, санитарным и пожарным требованиям.")
    if a.get("finance") != "Да":
        items.append("2. Сделать финансовую модель: инвестиции, расходы, средний чек, загрузка и точка безубыточности.")
    else:
        items.append("2. Перепроверить финансовую модель по нескольким сценариям загрузки.")
    if a.get("docs") != "Да":
        items.append("3. Сформировать пакет организационных, кадровых и договорных документов.")
    else:
        items.append("3. Провести аудит документов перед запуском.")
    items += [
        "4. Утвердить возрастные группы, программы, расписание и дополнительные услуги.",
        "5. Рассчитать штат и фонд оплаты труда.",
        "6. Подготовить маркетинг до открытия: оффер, соцсети, реклама, пробные занятия и предзапись.",
        "7. Запускать продажи до официального открытия, а не после ремонта.",
    ]
    return "\n".join(items)


async def handle_menu(chat_id: int, text: str):
    s = state(chat_id)

    if text == "🏢 Проверить помещение":
        await send(
            chat_id,
            "🏢 <b>Проверка помещения</b>\n\n"
            "Я подготовила краткую презентацию по основным санитарно-эпидемиологическим "
            "требованиям к помещениям детских центров и дошкольных организаций в Казахстане.\n\n"
            "📄 Откройте презентацию ниже. После изучения можно перейти к проверке вашего помещения."
        )
        ok = await send_document(
            chat_id,
            PREMISES_PDF,
            "📄 <b>Требования СЭС к помещению детского центра</b>\nАктуально на 2026 год."
        )
        if not ok:
            await send(
                chat_id,
                "Не удалось отправить PDF. Напишите Coach Novikova в WhatsApp: +7 701 172 13 93"
            )
        await send(
            chat_id,
            "Выберите действие 👇",
            PREMISES_MENU
        )

    elif text == "💬 Получить консультацию":
        await send(
            chat_id,
            "💬 <b>Консультация Coach Novikova</b>\n\n"
            "Можно разобрать конкретное помещение до подписания аренды или начала ремонта.\n\n"
            "WhatsApp: +7 701 172 13 93",
            MENU
        )

    elif text == "⬅️ Главное меню":
        await send(chat_id, "Главное меню 👇", MENU)

    elif text == "📑 Документы":
        await send(
            chat_id,
            "📑 <b>Документы</b>\n\n"
            "Нужны организационные документы, договоры с родителями, кадровый блок, приказы, "
            "журналы, внутренние положения, документы по охране труда и безопасности. "
            "Точный набор зависит от формата организации.\n\n"
            "У Coach Novikova есть готовые пакеты документов на русском и казахском языках.\n"
            "WhatsApp: +7 701 172 13 93",
            MENU,
        )


    elif text == "📚 Программы":
        await send(
            chat_id,
            "📚 <b>Программы</b>\n\n"
            "Составьте продуктовую матрицу по возрастам: 2–3, 3–4, 4–5, 5–6 лет, "
            "подготовка к школе, продлёнка и кружки. Для каждой программы определите результат "
            "для родителя, продолжительность, расписание, цену и максимальную наполняемость.",
            MENU,
        )

    elif text == "📣 Маркетинг":
        await send(
            chat_id,
            "📣 <b>Маркетинг до открытия</b>\n\n"
            "Не ждите окончания ремонта. Начните заранее: название и позиционирование → "
            "оформление соцсетей → контент об открытии → WhatsApp/лид-форма → реклама → "
            "пробные занятия → предзапись → день открытых дверей.",
            MENU,
        )

    elif text == "🗺 Мой план открытия":
        await send(
            chat_id,
            "🗺 <b>Чек-лист открытия образовательного центра</b>\n\n"
            "Ниже — пошаговый чек-лист подготовки к открытию центра в Казахстане."
        )
        ok = await send_document(
            chat_id,
            OPENING_CHECKLIST_PDF,
            "📄 <b>Чек-лист подготовки к открытию образовательного центра</b>"
        )
        if not ok:
            await send(
                chat_id,
                "Не удалось отправить файл. Напишите Coach Novikova в WhatsApp: +7 701 172 13 93",
                MENU
            )
        else:
            await send(chat_id, "Файл готов 👇", MENU)

    elif text in ("💰 Финансовый калькулятор", "💰 Финансовый калькулятор открытия"):
        s.update({"mode": "finance", "finance": {}, "f": 0})
        await send(chat_id, "💰 <b>Финансовый калькулятор</b>\n\n" + FINANCE_FIELDS[0][1])

    elif text == "💬 Консультация":
        await send(
            chat_id,
            "💬 <b>Консультация Coach Novikova</b>\n\n"
            "Можно разобрать помещение, финансовую модель, документы, программы, персонал "
            "или план открытия центра.\n\nWhatsApp: +7 701 172 13 93",
            MENU,
        )

    else:
        await send(chat_id, "Выберите раздел в меню 👇", MENU)


async def handle_text(chat_id: int, text: str):
    s = state(chat_id)

    if text == "/start":
        await start(chat_id)
        return


    if s["mode"] == "finance":
        key, _ = FINANCE_FIELDS[s["f"]]
        try:
            value = float(text.replace(" ", "").replace(",", "."))
        except ValueError:
            await send(chat_id, "Введите только число. Например: 350000")
            return

        s["finance"][key] = value
        s["f"] += 1

        if s["f"] < len(FINANCE_FIELDS):
            await send(chat_id, FINANCE_FIELDS[s["f"]][1])
            return

        f = s["finance"]
        expenses = sum(f[k] for k in ["rent", "payroll", "utilities", "food", "ads", "taxes", "other"])
        revenue = f["children"] * f["ticket"]
        profit = revenue - expenses
        margin = (profit / revenue * 100) if revenue else 0
        breakeven = (expenses / f["ticket"]) if f["ticket"] else 0

        scenarios = []
        for pct in (50, 70, 90, 100):
            kids = f["children"] * pct / 100
            rev = kids * f["ticket"]
            scenarios.append(f"{pct}% загрузки: выручка {rev:,.0f} тг, результат {rev-expenses:,.0f} тг")

        result = (
            "💰 <b>Расчёт готов</b>\n\n"
            f"Выручка при 100% плане: {revenue:,.0f} тг\n"
            f"Ежемесячные расходы: {expenses:,.0f} тг\n"
            f"Прибыль: {profit:,.0f} тг\n"
            f"Рентабельность: {margin:.1f}%\n"
            f"Точка безубыточности: примерно {breakeven:.1f} ребёнка\n\n"
            + "\n".join(scenarios)
            + "\n\nРасчёт предварительный: для реального бизнес-плана отдельно учитываются "
              "инвестиции в ремонт, оборудование, сезонность, скидки и неполная оплата."
        )
        s["mode"] = None
        await send(chat_id, result, MENU)
        return

    await handle_menu(chat_id, text)


@app.get("/")
async def health():
    return {"status": "ok", "service": "CoachNovikovaBot"}


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    message = data.get("message") or data.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = message.get("chat", {}).get("id")
    text = message.get("text")
    if chat_id and text:
        await handle_text(chat_id, text)

    return {"ok": True}


@app.on_event("startup")
async def setup_webhook():
    public_url = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
    if TOKEN and public_url:
        async with httpx.AsyncClient(timeout=20) as client:
            await client.post(
                f"{BASE_URL}/setWebhook",
                json={"url": f"{public_url}/webhook", "drop_pending_updates": True},
            )
