#!/bin/sh

if [ "$1" = "-install" ]; then
    opkg update > /dev/null
    opkg install xray > /dev/null

    touch /opt/etc/xray/config.json 

    chmod 755 /opt/etc/init.d/S24xray || chmod +x /opt/etc/init.d/S24xray
    sed -i 's|ARGS="-confdir /opt/etc/xray"|ARGS="run -c /opt/etc/xray/config.json"|g' /opt/etc/init.d/S24xray > /dev/null 2>&1

fi

if [ "$1" = "-uninstall" ]; then
    opkg remove xray
    chmod 777 /opt/etc/init.d/S24xray || rm -Rfv /opt/etc/init.d/S24xray
    chmod 777 /opt/etc/xray || rm -Rfv /opt/etc/xray

fi