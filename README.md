# telegram4kvas
Telegram bot for [KVAS](https://github.com/qzeleza/kvas) by [qzeleza](https://github.com/qzeleza)

# Установка
Скачайте и запустите установочный скрипт:
```
curl -OLf https://raw.githubusercontent.com/dnstkrv/telegram4kvas/main/install.sh && sh install.sh
```
# Настройка
Для создания бота напишите в [@BotFather](https://t.me/BotFather) команду /newbot и выберите название для бота. В ответном сообщении выполучите API ключ

Откройте файл /opt/etc/telegram4kvas/telegram_bot.py
```
nano /opt/etc/telegram4kvas/telegram_bot_config.py
```
В параметр **token** необходимо ввести ключ, полученный от @BotFather. Ключ должен быть в 'кавычках'

В параметр **usernames** вносится Ваш логин Телеграм. Логин должен быть в кавычках со ['скобками']

В параметр **userid** вносится ваш UserId. UserID должен быть в [скобках], его можно получить написав боту [@UserInfoBot](https://t.me/userinfobot)

***Внимание***

Необязательно вносить и логин и UserId, достаточно чего-то одного


# Запуск
Бот запускается командой 
```
/opt/etc/init.d/S98telegram4kvas start
```
# Прочее
На чай автору бота
```
МИР 2202201523445100
```
