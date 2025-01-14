# telegram4kvas
Telegram bot for [KVAS](https://github.com/qzeleza/kvas) by [qzeleza](https://github.com/qzeleza)

# Установка
Скачайте и запустите установочный скрипт:
```
curl -OLf https://raw.githubusercontent.com/dnstkrv/telegram4kvas/main/script/install.sh && sh install.sh -install
```
В конце установки скрипт запросит у Вас **API-токен**. 

Для создания бота напишите в [@BotFather](https://t.me/BotFather) команду **/newbot** и выберите название для бота. В ответном сообщении вы получите API-токен.

Конфигурация хранится в файле **/opt/etc/telegram4kvas/telegram_bot_config.py**.

Изменением **reconnection_timeout** и **reconnection_attempts** вы можете изменять количество переподключений и таймаут, если при старте роутера интернет появляется не сразу

# Запуск
Бот запускается командой 
```
/opt/etc/init.d/S98telegram4kvas start
```
# Удаление
Для удаления бота выполните команду
```
curl -OLf https://raw.githubusercontent.com/dnstkrv/telegram4kvas/main/script/install.sh && sh install.sh -remove
```
# На чай автору бота

**МИР** 2202201523445100

[Кошелек ЮМани](https://yoomoney.ru/to/410013576101136) 

