#!/bin/sh

/opt/etc/init.d/S98telegram4kvas stop

rm /opt/etc/telegram4kvas/telegram_bot.py
rm /opt/etc/init.d/S98telegram4kvas

curl -o /opt/etc/telegram4kvas/telegram_bot.py https://raw.githubusercontent.com/dnstkrv/telegram4kvas/dev/telegram_bot.py
curl -o /opt/etc/init.d/S98telegram4kvas https://raw.githubusercontent.com/dnstkrv/telegram4kvas/dev/S98telegram4kvas

chmod +x /opt/etc/init.d/S98telegram4kvas

logger -s -t telegram4kvas 'Бот обновлен'

/opt/etc/init.d/S98telegram4kvas start