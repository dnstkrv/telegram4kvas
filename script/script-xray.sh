#!/bin/sh

if [ "$1" = "-install" ]; then
    opkg update > /dev/null
    opkg install xray > /dev/null

    chmod 755 /opt/etc/init.d/S24xray || chmod +x /opt/etc/init.d/S24xray
    sed -i 's|ARGS="-confdir /opt/etc/xray"|ARGS="run -c /opt/etc/xray/config.json"|g' /opt/etc/init.d/S24xray > /dev/null 2>&1
    /opt/etc/init.d/S24xray start
    
    echo "XRay установлен и запущен. Проверьте, что у Вас установлен компонент \"Прокси-клиент\", в WebUI роутера зайдите в \"Другие подключения\", в разделе \"Прокси подключения\" нажмите \"Добавить\", \
    поставьте чек-бокс \"Использовать для выхода в интернет\", тип подключения - \"SOCKS5\", адрес прокси сервера - ip-адрес_роутера:1081 (например, 192.168.0.1:1081). После этого в КВАСе будет доступен новый интерфейс"
fi

if [ "$1" = "-uninstall" ]; then
    opkg remove xray > /dev/null
    chmod 777 /opt/etc/init.d/S24xray || rm -Rfv /opt/etc/init.d/S24xray
    chmod 777 /opt/etc/xray || rm -Rfv /opt/etc/xray
    echo "XRay и конфиг удалены"
fi