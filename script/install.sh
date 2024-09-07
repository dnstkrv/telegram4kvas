#!/bin/sh

bot_path="/opt/etc/telegram4kvas/telegram_bot.py"
config_path="/opt/etc/telegram4kvas/telegram_bot_config.py"
release_url=https://api.github.com/repos/dnstkrv/telegram4kvas/releases
package_url=$(curl -sH "Accept: application/vnd.github.v3+json" ${release_url}/latest | sed -n 's/.*browser_download_url\": "\(.*\)\"/\1/p;'| tr -d ' ' |  sed '/^$/d')
latest_version=$(curl -sH "Accept: application/vnd.github.v3+json" ${release_url}/latest | grep tag_name | awk -F\" '{print $4}')

if [ "$1" = "-remove" ]; then
    /opt/etc/init.d/S98telegram4kvas stop
	echo "Y" | pip uninstall pip 
    opkg remove --force-removal-of-dependent-packages python3 python3-pip
    rm -rf /opt/etc/telegram4kvas/
    echo "Бот, конфиг и зависимости удалены"
fi

if [ "$1" = "-install" ]; then
    freespace=$(df -k | grep opt | awk '/[0-9]%/{print $(NF-2)}')
    freespaceh=$(df -kh | grep opt | awk '/[0-9]%/{print $(NF-2)}')
    if [ $freespace -le 71680 ]; then
    echo 'У вас доступно '$freespaceh', а для установки необходимо минимум 70M'
    exit
    fi;
    
    opkg update &> /dev/null
    
    i=`opkg list-installed | grep kvas | cut -d' ' -f1`
    
    if [ -n "$i" ]; then
    echo "КВАС установлен, продолжаем..."
    else
    echo "Сначала установите КВАС, прерывание установки"
    exit
    fi;
    
    
    opkg install python3 python3-pip
    curl -O https://bootstrap.pypa.io/get-pip.py &> /dev/null
    python get-pip.py
    rm get-pip.py
    pip install pyTelegramBotAPI pathlib
    
    mkdir -p "/opt/etc/telegram4kvas"
    
    curl -o /opt/etc/telegram4kvas/telegram_bot_config.py https://raw.githubusercontent.com/dnstkrv/telegram4kvas/main/telegram_bot_config.py
    curl -o /opt/etc/init.d/S98telegram4kvas https://raw.githubusercontent.com/dnstkrv/telegram4kvas/main/S98telegram4kvas
    chmod +x /opt/etc/init.d/S98telegram4kvas
    
    curl -JLo $bot_path $package_url

    config_file="/opt/etc/telegram4kvas/telegram_bot_config.py"
    echo -e "\nВведите API ключ, полученный от BotFather:"
    read api
    sed -i "s/\(token = \).*/\1\'${api}\'/" "${config_file}"
        
    echo -e "\nВведите Ваш userID:"
    read userID
    sed -i "s/\(userid = \[\).*/\1${userID}\]/" "${config_file}"
    
    echo -e "\nИзменения сохранены в файл /opt/etc/telegram4kvas/telegram_bot_config.py"

    sed -i '/version/d' $config_path 
    echo "version = '$latest_version'" >> $config_path

    /opt/etc/init.d/S98telegram4kvas start
    
fi

if [ "$1" = "-help" ]; then
    echo "-install - Установить бота"
    echo "-remove - Удалить бота и все зависимости"
fi

if [ -z "$1" ]; then
    echo "-install - Установить бота"
    echo "-remove - Удалить бота и все зависимости"
fi
