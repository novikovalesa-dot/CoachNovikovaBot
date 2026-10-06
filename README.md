# CoachNovikovaBot

Telegram-бот Coach Novikova по открытию детского центра в Казахстане.

## Версия 2
- меню
- диагностика проекта из 10 вопросов
- персональная карточка проекта
- финансовый калькулятор
- PDF-презентация по требованиям к помещению отправляется прямо в Telegram
- кнопки «Проверить моё помещение» и «Получить консультацию»
- webhook для Render

## Переменные окружения
- TELEGRAM_BOT_TOKEN
- RENDER_EXTERNAL_URL

## Start command
uvicorn app:app --host 0.0.0.0 --port $PORT
