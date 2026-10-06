# CoachNovikovaBot

Telegram-бот Coach Novikova по открытию детского центра в Казахстане.

## MVP
- меню
- диагностика проекта из 10 вопросов
- персональная карточка проекта
- базовые рекомендации
- финансовый калькулятор
- webhook для Render

## Переменные окружения
- TELEGRAM_BOT_TOKEN — токен Telegram от BotFather
- RENDER_EXTERNAL_URL — Render задаёт автоматически

## Start command
uvicorn app:app --host 0.0.0.0 --port $PORT
