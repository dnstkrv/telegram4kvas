# telegram4kvas
Telegram bot for [KVAS](https://github.com/qzeleza/kvas) by [qzeleza](https://github.com/qzeleza)

# Установка
Скачайте и запустите установочный скрипт:
```
curl -OLf https://raw.githubusercontent.com/dnstkrv/telegram4kvas/main/install.sh && sh install.sh
```
# Настройка
Для создания бота напишите в https://t.me/BotFather команду /newbot и выберите название для бота. В ответном сообщении выполучите API ключ

Откройте файл /opt/etc/telegram4kvas/telegram_bot.py
```
nano /opt/etc/telegram4kvas/telegram_bot_config.py
```
В параметр **token** необходимо ввести ключ, полученный от @BotFather. Ключ должен быть в 'кавычках'

В параметр **usernames** необходимо ввести Ваш логин Телеграм. Логин должен быть в кавычках со ['скобками']
# Запуск
Бот запускается командой 
```
/opt/etc/init.d/S98telegram4kvas start
```
