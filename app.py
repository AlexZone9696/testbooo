import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from tronpy import Tron
from tronpy.keys import PrivateKey
import os

# Установим уровень логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Подключаемся к TRON Testnet (Nile)
client = Tron(network="nile")

# Фиксированная комиссия за транзакцию
TRANSACTION_FEE = 0.5  # Комиссия в TRX

# Функция для создания нового кошелька
def create_wallet():
    private_key = PrivateKey.random()
    address = private_key.public_key.to_base58check_address()
    return private_key.hex(), address

# Команда /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Я ваш крипто-бот. Используйте /create_wallet для создания кошелька или /balance для проверки баланса.')

# Команда для создания кошелька
def create_wallet_command(update: Update, context: CallbackContext) -> None:
    private_key, address = create_wallet()
    context.user_data['private_key'] = private_key
    context.user_data['address'] = address
    update.message.reply_text(f'Кошелек создан!\nАдрес: {address}\nПриватный ключ: {private_key}\nСохраните этот ключ в безопасном месте!')

# Команда для проверки баланса
def balance_command(update: Update, context: CallbackContext) -> None:
    address = context.user_data.get('address')
    if address:
        balance = client.get_account_balance(address)
        update.message.reply_text(f'Баланс для адреса {address}: {balance / 1_000_000} TRX')
    else:
        update.message.reply_text('Сначала создайте кошелек с помощью /create_wallet.')

# Команда для отправки TRX
def send_trx_command(update: Update, context: CallbackContext) -> None:
    address = context.user_data.get('address')
    private_key = context.user_data.get('private_key')

    if address and private_key and len(context.args) == 2:
        to_address = context.args[0]
        try:
            amount = float(context.args[1])
            total_amount = amount + TRANSACTION_FEE

            # Проверяем, достаточно ли средств для отправки
            balance = client.get_account_balance(address)
            if balance < total_amount * 1_000_000:
                update.message.reply_text("Недостаточно средств для выполнения транзакции.")
                return

            # Создаем и подписываем транзакцию
            txn = (
                client.trx.transfer(address, to_address, int(amount * 1_000_000))
                .build()
                .sign(PrivateKey(bytes.fromhex(private_key)))
            )
            txn.broadcast().wait()

            update.message.reply_text(f"Транзакция успешно отправлена! TxID: {txn.txid}")
        except Exception as e:
            update.message.reply_text(f"Ошибка при отправке: {str(e)}")
    else:
        update.message.reply_text('Используйте: /send_trx <адрес> <сумма>')

def main():
    # Замените 'YOUR_TOKEN' на токен вашего бота
    updater = Updater("5271341496:AAEyC-OYUpaSj21VsxO5SP6_BB1LF3ce378", use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Определяем команды
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("create_wallet", create_wallet_command))
    dp.add_handler(CommandHandler("balance", balance_command))
    dp.add_handler(CommandHandler("send_trx", send_trx_command))

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
