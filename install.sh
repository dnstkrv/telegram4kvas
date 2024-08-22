#!/bin/sh

opkg update &> /dev/null
opkg install python3 python3-pip
curl -O https://bootstrap.pypa.io/get-pip.py &> /dev/null
python get-pip.py
rm get-pip.py
pip install pyTelegramBotAPI pathlib

mkdir -p "/opt/etc/telegram4kvas"

curl -o /opt/etc/telegram4kvas/telegram_bot_config.py https://raw.githubusercontent.com/dnstkrv/telegram4kvas/dev/telegram_bot_config.py
curl -o /opt/etc/telegram4kvas/telegram_bot.py https://raw.githubusercontent.com/dnstkrv/telegram4kvas/dev/telegram_bot.py
curl -o /opt/etc/init.d/S98telegram4kvas https://raw.githubusercontent.com/dnstkrv/telegram4kvas/dev/S98telegram4kvas

chmod +x /opt/etc/init.d/S98telegram4kvas

echo -e "\n\nВнесите API ключ, полученный от BotFather и Ваш логин Телеграм в файл \"/opt/etc/telegram4kvas/telegram_bot_config.py\"\n\nПосле чего выполните команду \"/opt/etc/init.d/S98telegram4kvas start\" для запуска бота\n\n"