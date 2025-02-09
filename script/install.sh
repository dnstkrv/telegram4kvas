#!/bin/sh

bot_path="/opt/etc/telegram4kvas"
config_path="${bot_path}/telegram_bot_config.py"
release_url="https://api.github.com/repos/dnstkrv/telegram4kvas/releases"
latest_version=$(curl -sH "Accept: application/vnd.github.v3+json" "${release_url}/latest" | grep tag_name | awk -F\" '{print $4}')
PACKAGES="python3-base python3 python3-light libpython3 python3-logging python3-email python3-urllib python3-urllib3 python3-idna python3-requests python3-certifi python3-chardet python3-openssl python3-codecs"

install_packages() {
    freespace=$(df -k /opt | awk 'NR==2 {print $4}')

    if [ "$freespace" -gt 30000 ]; then
        echo "Свободного места достаточно (${freespace} KB), устанавливаю все пакеты сразу..."
        opkg install --nodeps $PACKAGES &> /dev/null
        return
    fi

    echo "Свободного места мало (${freespace} KB), устанавливаю пакеты по одному..."

    index=0
    for pkg in $PACKAGES; do
        attempts=0

        while true; do
            freespace=$(df -k /opt | awk 'NR==2 {print $4}')
            pkg_size=$(opkg info "$pkg" 2>/dev/null | awk '/^Size:/ {print $2}')

            if [ -z "$pkg_size" ]; then
                echo -e "\nОшибка: Не удалось определить размер пакета $pkg. Проверьте интернет-соединение."
                exit 1
            fi

            pkg_size_kb=$((pkg_size / 1024))

            if [ "$freespace" -le "$pkg_size_kb" ]; then
                attempts=$((attempts + 1))
                if [ "$attempts" -ge 3 ]; then
                    echo -e "\nОшибка: Недостаточно места для установки $pkg (нужно ${pkg_size_kb} KB, доступно ${freespace} KB) после 3 попыток."
                    exit 1
                fi
                echo -e "\nНедостаточно места для $pkg (нужно ${pkg_size_kb} KB, доступно ${freespace} KB). Ожидание 5 секунд..."
                sleep 5
                continue
            fi

            opkg install --nodeps "$pkg" &> /dev/null
            index=$((index + 1))
            echo -ne "\rУстановлено пакетов: ${index} из 14"
            sleep 1
            break
        done
    done
    echo ""
}


if [ "$1" = "-remove" ]; then
    /opt/etc/init.d/S98telegram4kvas stop
    rm -f /opt/etc/init.d/S98telegram4kvas
    opkg remove --force-removal-of-dependent-packages python3*
    rm -rf "${bot_path}"
    echo "Бот, конфиг и зависимости удалены."
    exit 0
fi

if [ "$1" = "-install" ]; then
    freespace=$(df -k | grep opt | awk '/[0-9]%/{print $(NF-2)}')
    freespaceh=$(df -kh | grep opt | awk '/[0-9]%/{print $(NF-2)}')
    if [ $freespace -le 10000 ]; then
        echo "У вас доступно ${freespaceh}, а для установки необходимо минимум 10M."
        exit 1
    fi

    opkg update &> /dev/null

    if opkg list-installed | grep -q kvas; then
        echo "КВАС установлен, продолжаем..."
    else
        echo "Сначала установите КВАС. Прерывание установки."
        exit 1
    fi

    install_packages

    mkdir -p "${bot_path}"

    echo "Скачивание архива с GitHub..."
    curl -Lo /opt/tmp/main.zip https://github.com/dnstkrv/telegram4kvas/archive/refs/tags/v1.1.10-old.zip &> /dev/null

    echo "Распаковка архива..."
    unzip -q /opt/tmp/main.zip -d /opt/tmp

    echo "Копирование файлов..."
    cp /opt/tmp/telegram4kvas-1.1.10-old/telegram_bot_config.py "${bot_path}"
    cp /opt/tmp/telegram4kvas-1.1.10-old/telegram_bot.py "${bot_path}"
    cp -r /opt/tmp/telegram4kvas-1.1.10-old/telebot "${bot_path}"
    cp /opt/tmp/telegram4kvas-1.1.10-old/S98telegram4kvas /opt/etc/init.d/S98telegram4kvas

    chmod +x /opt/etc/init.d/S98telegram4kvas

    echo -e "\nВведите API ключ, полученный от BotFather:"
    read api
    sed -i "s/\(token = \).*/\1\'${api}\'/" "${config_path}"
    echo -e "\nИзменения сохранены в файл ${config_path}."

    sed -i '/version/d' "${config_path}"
    echo "version = '${latest_version}'" >> "${config_path}"

    /opt/etc/init.d/S98telegram4kvas start

    echo "Очистка временных файлов..."
    rm -rf /opt/tmp/main.zip /opt/tmp/telegram4kvas-main

    echo "Установка завершена!"
    exit 0
fi

if [ "$1" = "-help" ] || [ -z "$1" ]; then
    echo "Использование: $0 [опция]"
    echo "Опции:"
    echo "  -install  Установить бота"
    echo "  -remove   Удалить бота и все зависимости"
    exit 0
fi




curl -OLf https://raw.githubusercontent.com/dnstkrv/telegram4kvas/refs/heads/v1.10-old/script/install.sh && sh install.sh -install