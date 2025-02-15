import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
from bs4 import BeautifulSoup

# URL-адрес для курсов валют Сбербанка
URL = "https://ru.myfin.by/bank/sberbank/currency"

# Заголовки для корректной работы запроса
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def parse_rate(rate_str):
    """Преобразует строку в число с округлением до двух знаков после запятой, если возможно."""
    if isinstance(rate_str, str):
        try:
            return round(float(rate_str.replace(',', '.')), 2)  # Заменяем запятую на точку, если она есть
        except ValueError:
            return None  # Возвращаем None, если не удалось преобразовать строку в число
    elif isinstance(rate_str, float):
        return round(rate_str, 2)  # Если уже число, просто округляем до 2 знаков
    return None  # Если тип данных не поддерживается

def get_sberbank_rate(currency_url):
    """Получает курсы валют в Сбербанке (покупка и продажа)."""
    response = requests.get(currency_url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Ошибка {response.status_code}: сайт недоступен")
        return None, None, None

    soup = BeautifulSoup(response.text, "html.parser")
    banks = soup.find_all("tr")

    # Инициализируем переменные для курсов
    usd_rate, eur_rate, cny_rate = None, None, None

    # Ищем курсы для каждой валюты
    for bank in banks:
        # Проверяем наличие ссылки для USD
        if bank.find("a", href="/currency/usd"):
            columns = bank.find_all("td")
            if len(columns) >= 3:
                usd_rate = parse_rate(columns[2].text.strip())
        
        # Проверяем наличие ссылки для EUR
        if bank.find("a", href="/currency/eur"):
            columns = bank.find_all("td")
            if len(columns) >= 3:
                eur_rate = parse_rate(columns[2].text.strip())

        # Проверяем наличие ссылки для CNY
        if bank.find("a", href="/currency/cny"):
            columns = bank.find_all("td")
            if len(columns) >= 3:
                cny_rate = parse_rate(columns[2].text.strip())

    return usd_rate, eur_rate, cny_rate

def get_exchange_rates_tai():
    url = "https://www.superrichthailand.com/api/v1/rates"
    headers = {
        "Cookie": "_ga=GA1.1.1957919004.1739356415; _ga_JJ951DKF1N=GS1.1.1739356414.1.1.1739356446.0.0.0",
        "Authorization": "Basic c3VwZXJyaWNoVGg6aFRoY2lycmVwdXM="
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Ошибка запроса: {response.status_code}")
        return None, None, None
    
    data = response.json()
    exchange_rates = data.get("data", {}).get("exchangeRate", [])
    
    target_currencies = {"USD": None, "EUR": None, "CNY": None}
    
    for currency in exchange_rates:
        if currency["cUnit"] in target_currencies:
            # Проверяем, если список ставок не пуст
            if currency.get("rate") and len(currency["rate"]) > 0:
                target_currencies[currency["cUnit"]] = parse_rate(currency["rate"][0].get("cSelling"))
    
    # Возвращаем три курса валют
    return target_currencies.get("USD"), target_currencies.get("EUR"), target_currencies.get("CNY")

# Функция для обработки команды /start
async def start(update: Update, context):
    await update.message.reply_text("Привет! Я бот, который поможет тебе узнать актуальные курсы валют. Напиши /rates для получения информации.")

# Функция для обработки команды /rates
async def get_rates(update: Update, context):
    # Получаем курсы валют
    usd_thb_rate, eur_thb_rate, cny_thb_rate = get_exchange_rates_tai()
    usd_rub_rate, eur_rub_rate, cny_rub_rate = get_sberbank_rate(URL)

    # Формируем сообщение
    message = f"""
    💰 **Курсы валют**:

    🇺🇸 USD: {usd_rub_rate} ₽ (Сбербанк) / {usd_thb_rate} THB (Super Rich Thailand) / {usd_rub_rate / usd_thb_rate:.2f} RUB/THB
    🇪🇺 EUR: {eur_rub_rate} ₽ (Сбербанк) / {eur_thb_rate} THB (Super Rich Thailand) / {eur_rub_rate / eur_thb_rate:.2f} RUB/THB
    🇨🇳 CNY: {cny_rub_rate} ₽ (Сбербанк) / {cny_thb_rate} THB (Super Rich Thailand) / {cny_rub_rate / cny_thb_rate:.2f} RUB/THB
    """

    # Отправляем сообщение
    await update.message.reply_text(message)

# Функция для обработки сообщений в группе
async def message_handler(update: Update, context):
    if update.message.text.startswith('/rates'):
        await get_rates(update, context)

# Функция для добавления обработчика
def main():
    # Включаем логирование для отладки
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Токен вашего бота
    token = '7570397611:AAGg8ohFxSSEEIzw5TKrlXh1ZKO4mYnd-xE'  # Замените на ваш токен

    # Создаем приложение (Application)
    application = Application.builder().token(token).build()

    # Добавляем обработчики команд и нажатий на кнопки
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rates", get_rates))  # Обрабатываем команду /rates
    application.add_handler(MessageHandler(filters.TEXT, message_handler))  # Обрабатываем текстовые сообщения

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()
