import configparser
import logging
import os
import re
import subprocess
import tempfile
import time
import sys
from contextlib import suppress
from logging.handlers import RotatingFileHandler
from urllib.parse import parse_qs, urlparse

import requests
import telebot
from telebot import types
from telebot.formatting import mbold, mcode, mlink
from telebot.handler_backends import BaseMiddleware, CancelUpdate
from telebot.types import InputFile

import telegram_bot_config

config = configparser.ConfigParser()
CONFIG_PATH = "/opt/etc/telegram4kvas/config.ini"

# Настройка логирования
logger = logging.getLogger(name="telegram4kvas")
logger.setLevel(logging.DEBUG)

handler = RotatingFileHandler(
    filename="/opt/etc/telegram4kvas/telegram4kvas_log.txt",
    maxBytes=1 * 1024 * 1024,
    backupCount=3,
    encoding="UTF-8",
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

user_states = {}

bot = telebot.TeleBot(
    telegram_bot_config.token,
    use_class_middlewares=True,
)


class Middleware(BaseMiddleware):
    def __init__(self):
        self.update_types = ["message"]

    def _get_admins(self):
        admins = []
        with suppress(Exception):
            config.read(CONFIG_PATH, encoding="UTF-8")
            admins.extend([int(a) for a in config.get("ADMINS", "users_ids").split(",")])
        admins.extend(telegram_bot_config.userid)
        return admins

    def pre_process(self, message: types.Message, data: dict):
        logger.debug("Processing message from %s", message.from_user.username)
        admins = self._get_admins()
        if not admins:
            config["ADMINS"] = {
                "users_ids": message.from_user.id,
            }
            with open(CONFIG_PATH, "w", encoding="UTF-8") as config_file:
                config.write(config_file)
            admins.append(message.from_user.id)

        if message.from_user.id not in admins:
            logger.warning(
                "Unauthorized access attempt by %s",
                message.from_user.username,
            )
            bot.send_message(message.chat.id, "Вы не авторизованы")

            username = "Неизвестно"
            if message.from_user.username is not None:
                username = f"@{message.from_user.username}"
            
            user_link = f"[{message.from_user.full_name}](tg://user?id={message.from_user.id})"

            for id in admins:
                bot.send_message(
                    id,
                    f"Попытка неавторизованного доступа:\n{user_link}\({username}\), UserID: {message.from_user.id}",
                    parse_mode="MarkdownV2",
                )
            return CancelUpdate()

    def post_process(self, message, data, exception):
        if exception:
            logger.error("Error in processing message: %s", str(exception))


def send_startup_message():
    admins = Middleware._get_admins('')
    startMenu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Управление хостами")
    item2 = types.KeyboardButton("Управление подключениями")
    item3 = types.KeyboardButton("Сервис")
    startMenu.add(item1, item2, item3)

    for id in admins:
        bot.send_message(id,
                         f"Бот запущен, версия: {telegram_bot_config.version}",
                         reply_markup=startMenu,
                         )


@bot.message_handler(commands=["start"], chat_types=["private"])
def handle_start(message: types.Message):
    try:
        logger.info("User %s started the bot", message.from_user.username)
        startMenu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Управление хостами")
        item2 = types.KeyboardButton("Управление подключениями")
        item3 = types.KeyboardButton("Сервис")
        startMenu.add(item1, item2, item3)
        bot.send_message(
            message.chat.id,
            "Панель управления КВАС",
            reply_markup=startMenu,
        )
    except Exception as e:
        logger.exception("Error in handle_start: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")


@bot.message_handler(regexp="Управление хостами", chat_types=["private"])
def hosts_message(message: types.Message):
    try:
        logger.info("User %s requested host management", message.from_user.username)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [
            types.KeyboardButton("Добавить хост"),
            types.KeyboardButton("Удалить хост"),
            types.KeyboardButton("Список хостов"),
            types.KeyboardButton("Очистить список"),
            types.KeyboardButton("Импорт"),
            types.KeyboardButton("Экспорт"),
            types.KeyboardButton("Назад"),
        ]
        keyboard.add(*buttons)
        bot.send_message(
            message.chat.id,
            "Панель управления хостами",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.exception("Error in hosts_message: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")


@bot.message_handler(regexp="Сервис", chat_types=["private"])
def service_message(message: types.Message):
    try:
        logger.info("User %s requested service menu", message.from_user.username)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [
            types.KeyboardButton("Запустить test"),
            types.KeyboardButton("Запустить debug"),
            types.KeyboardButton("Запустить reset"),
            types.KeyboardButton("Перезагрузить роутер"),
            types.KeyboardButton("Терминал"),
            types.KeyboardButton("Обновить бота"),
            types.KeyboardButton("Добавить пользователя"),
            types.KeyboardButton("Запросить лог"),
            types.KeyboardButton("Назад"),
        ]
        keyboard.add(*buttons)
        bot.send_message(
            message.chat.id,
            "Сервисное меню",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.exception("Error in service_message: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")


@bot.message_handler(regexp="Добавить пользователя", chat_types=["private"])
def add_admin_handler(message: types.Message):
    logger.info("User %s requested add new admin menu", message.from_user.username)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        types.KeyboardButton("Назад"),
    ]
    keyboard.add(*buttons)
    answer = bot.send_message(
        message.chat.id,
        f"Введите корректный id пользователя, которого нужно добавить как администратора\nНапример:\n{message.from_user.id}",
        reply_markup=keyboard,
    )
    bot.register_next_step_handler(answer, handle_add_new_admin)


def handle_add_new_admin(message: types.Message):
    if message.text == "Назад":
        service_message(message=message)
        return
    try:
        new_admin = int(message.text)
        admins = [new_admin]
        
        if os.path.isfile(CONFIG_PATH):
            config.read(CONFIG_PATH, encoding="UTF-8")
            existing_admins = config.get("ADMINS", "users_ids", fallback="")
            if existing_admins:
                admins.extend([int(a) for a in existing_admins.split(",") if a.strip().isdigit()])
        
        config['ADMINS'] = {
            'users_ids': ','.join(map(str, set(admins))),
        }
        
        with open(CONFIG_PATH, 'w', encoding="UTF-8") as config_file:
            config.write(config_file)
        
        bot.send_message(message.chat.id, f"Пользователь {new_admin} добавлен")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}")
        add_admin_handler(message=message)


@bot.message_handler(regexp="Управление подключениями", chat_types=["private"])
def connections_message(message: types.Message):
    try:
        logger.info(
            "User %s requested connection management", message.from_user.username
        )
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [
            types.KeyboardButton("Список интерфейсов"),
            types.KeyboardButton("Смена интерфейса"),
            types.KeyboardButton("Установить XRay"),
            types.KeyboardButton("Удалить XRay"),
            types.KeyboardButton("Назад"),
        ]
        keyboard.add(*buttons)
        bot.send_message(
            message.chat.id,
            "Управление подключениями",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.exception("Error in connections_message: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")


@bot.message_handler(regexp="Добавить хост", chat_types=["private"])
def add_host_prompt(message: types.Message):
    try:
        logger.info("User %s prompted to add host", message.from_user.username)
        answer = bot.send_message(
            message.chat.id,
            "Введите домен(или несколько доменов, разделенных пробелом) для добавления:",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        bot.register_next_step_handler(answer, handle_add_host)
    except Exception as e:
        logger.exception("Error in add_host_prompt: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")


@bot.message_handler(regexp="Удалить хост", chat_types=["private"])
def delete_host_prompt(message: types.Message):
    try:
        logger.info("User %s prompted to delete host", message.from_user.username)
        answer = bot.send_message(
            message.chat.id,
            "Введите домен(или несколько доменов, разделенных пробелом) для удаления:",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        bot.register_next_step_handler(answer, handle_delete_host)
    except Exception as e:
        logger.exception("Error in delete_host_prompt: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")


@bot.message_handler(regexp="Терминал", chat_types=["private"])
def custom_command_prompt(message: types.Message):
    try:
        logger.info("User %s entered terminal mode", message.from_user.username)
        user_states[message.chat.id] = True
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button = [types.KeyboardButton("Назад")]
        keyboard.add(*button)
        answer = bot.send_message(
            message.chat.id,
            "Вы вошли в режим терминала. Вы можете писать любые команды, не требующие интерактива...",
            reply_markup=keyboard,
        )
        bot.register_next_step_handler(answer, custom_command)
    except Exception as e:
        logger.exception("Error in custom_command_prompt: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")


def clean_string(text: str) -> str:
    return (
        text.replace("-", "")
        .replace("[33m", "")
        .replace("[m", "")
        .replace("[1;32m", "")
        .replace("[1;31m", "")
        .replace("[7D", "")
        .replace("[8D", "")
        .replace("[10D", "")
        .replace("[9D", "")
        .replace("[11D", "")
        .replace("[6D", "")
        .replace("[12D", "")
        .replace("[1;31m", "")
        .replace("[36m", "")
        .replace("[14D", "")
        .replace("[1;37m", "")
        .replace("[42D", "")
        .replace("[56D", "")
        .replace("[45D", "")
    )


def clean_string_interfaces(text: str) -> str:
    return (
        text.replace("-", "")
        .replace("[36m", "")
        .replace("[m", "")
        .replace("[8D", "")
        .replace("[1;32m", "")
        .replace("[9D", "")
        .replace("[1;31m", "")
    )


def send_long_message(output, message: types.Message):
    if len(output) > 4090:
        for x in range(0, len(output), 4090):
            bot.send_message(
                message.chat.id,
                mcode(output[x : x + 4090] + "\n"),
                parse_mode="MarkdownV2",
            )
            time.sleep(1)
    else:
        bot.send_message(
            message.chat.id,
            mcode(output),
            parse_mode="MarkdownV2",
        )


def scan_interfaces(param="Q"):
    try:
        logger.info("Scanning interfaces with parameter: %s", param)
        if param == "no_shadowsocks":
            command = [
                f'echo "Q" | kvas vpn set | grep -v "shadowsocks" | grep "Интерфейс"'
            ]
        else:
            command = [f'echo "{param}" | kvas vpn set | grep "Интерфейс"']
        with tempfile.TemporaryFile() as tempf:
            process = subprocess.Popen(command, shell=True, stdout=tempf)
            process.wait()
            tempf.seek(0)
            output = tempf.read().decode("utf-8")
            output_clean = clean_string_interfaces(output)
        return output_clean
    except Exception as e:
        logger.exception("Error during interface scanning: %s", str(e))
        return "Ошибка при сканировании интерфейсов"


def make_keyboard_interfaces(list_interfaces):
    try:
        logger.debug("Creating keyboard for interfaces")
        list_interfaces_split = list_interfaces.split()
        word_seek = "Интерфейс"
        interface_next = []
        for word in list_interfaces_split:
            if word == word_seek:
                ind = list_interfaces_split.index(word_seek)
                list_interfaces_split.pop(list_interfaces_split.index(word_seek))
                interface_next.append(list_interfaces_split[ind])

        keyboard_interfaces = types.InlineKeyboardMarkup()
        for i in range(0, len(interface_next)):
            keyboard_interfaces.add(
                types.InlineKeyboardButton(text=interface_next[i], callback_data=str(i))
            )

        return keyboard_interfaces
    except Exception as e:
        logger.exception("Error in make_keyboard_interfaces: %s", str(e))
        return types.InlineKeyboardMarkup()  # Вернём пустую клавиатуру в случае ошибки


def vless(url):
    try:
        logger.info("Creating XRay config from VLESS URL")
        replace_symbol = "[\[|'|\]]"
        dict_str = parse_qs(urlparse(url).query)
        dict_netloc = {}
        dict_netloc["id"] = re.split("@|:|\n", (urlparse(url).netloc))[0]
        dict_netloc["server"] = re.split("@|:|\n", (urlparse(url).netloc))[1]
        dict_netloc["port"] = re.split("@|:|\n", (urlparse(url).netloc))[2]
        dict_result = {**dict_str, **dict_netloc}
        get_routerip = '/opt/sbin/ip a | grep ": br0:" -A4 | grep "inet " | tr -s " " | cut -d" " -f3 | cut -d"/" -f1'
        routerip = (
            str(subprocess.check_output(get_routerip, shell=True))
            .replace("b", "")
            .replace("'", "")
            .replace("\n", "")
        )

        if "flow" not in dict_result:
            dict_result["flow"] = ""
        if "sid" not in dict_result:
            dict_result["sid"] = ""
        if "spx" not in dict_result:
            dict_result["spx"] = ""

        json_data = (
            '{"log": {"loglevel": "info"},"routing": {"rules": [],"domainStrategy": "AsIs"},'
            '"inbounds": [{"listen":"'
            + str(routerip)
            + '","port": "1081","protocol": "socks"}],'
            '"outbounds": [{"tag": "vless","protocol": "vless","settings": {"vnext": ['
            '{"address":"'
            + re.sub(replace_symbol, "", str(dict_result["server"]))
            + '",'
            '"port":'
            + re.sub(replace_symbol, "", str(dict_result["port"]))
            + ',"users": ['
            '{"id":"' + re.sub(replace_symbol, "", str(dict_result["id"])) + '",'
            '"flow":"' + re.sub(replace_symbol, "", str(dict_result["flow"])) + '",'
            '"encryption": "none"}]}]},"streamSettings": {'
            '"network":"' + re.sub(replace_symbol, "", str(dict_result["type"])) + '",'
            '"security":"'
            + re.sub(replace_symbol, "", str(dict_result["security"]))
            + '",'
            '"realitySettings": {'
            '"publicKey":"' + re.sub(replace_symbol, "", str(dict_result["pbk"])) + '",'
            '"fingerprint":"'
            + re.sub(replace_symbol, "", str(dict_result["fp"]))
            + '",'
            '"serverName":"'
            + re.sub(replace_symbol, "", str(dict_result["sni"]))
            + '",'
            '"shortId":"' + re.sub(replace_symbol, "", str(dict_result["sid"])) + '",'
            '"spiderX":"' + re.sub(replace_symbol, "", str(dict_result["spx"])) + '"'
            '},"tcpSettings": {"header": {"type": "none"}}}}]}'
        )

        with open("/opt/etc/xray/config.json", "w") as file:
            file.write(json_data)
    except Exception as e:
        logger.exception("Error in vless function: %s", str(e))


@bot.message_handler(regexp="Установить XRay", chat_types=["private"])
def install_xray_prompt(message: types.Message):
    try:
        logger.info("User %s prompted to install XRay", message.from_user.username)
        answer = bot.send_message(
            message.chat.id,
            "Введите ключ в формате vless://",
        )
        bot.register_next_step_handler(answer, handle_install_xray)
    except Exception as e:
        logger.exception("Error in install_xray_prompt: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")


@bot.message_handler(regexp="Список интерфейсов", chat_types=["private"])
def handle_list_interfaces(message: types.Message):
    try:
        logger.info("User %s requested list of interfaces", message.from_user.username)
        bot.send_message(
            message.chat.id,
            "Производится сканирование интерфейсов",
        )

        bot.send_message(
            message.chat.id,
            mcode(scan_interfaces()),
            parse_mode="MarkdownV2",
        )
    except Exception as e:
        logger.exception("Error in handle_list_interfaces: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")

@bot.message_handler(regexp="Запросить лог", chat_types=["private"])
def log_request_handler(message: types.Message):
    logger.info("User %s requested log", message.from_user.username)
    answer = bot.send_message(
        message.chat.id,
        "Введите количество строк лога, которые необходимо прислать. Нумерация начинается с конца файла"
    )
    bot.register_next_step_handler(answer, handle_log_request)


def handle_log_request(message: types.Message):
    try:
        with tempfile.TemporaryFile() as tempf:
            process = subprocess.Popen(
                [
                    f'cat "/opt/etc/telegram4kvas/telegram4kvas_log.txt" | tail -n {message.text}'
                ],
                shell=True,
                stdout=tempf,
            )
            process.wait()
            tempf.seek(0)
            output = tempf.read().decode("utf-8")
            log_message = clean_string(output)


        send_long_message(log_message, message)
    except Exception as e:
        logger.exception("Error in log request: %s", str(e))
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}")


@bot.message_handler(regexp="Смена интерфейса", chat_types=["private"])
def vpn_set_prompt(message: types.Message):
    try:
        logger.info("User %s prompted to change interface", message.from_user.username)
        bot.send_message(
            message.chat.id,
            "Производится сканирование интерфейсов:",
        )
        list_interfaces = scan_interfaces("no_shadowsocks")
        keyboard = make_keyboard_interfaces(list_interfaces)

        answer = bot.send_message(
            message.chat.id,
            mcode(list_interfaces),
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )

        bot.register_next_step_handler(answer, handle_vpn_set)
    except Exception as e:
        logger.exception("Error in vpn_set_prompt: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")


@bot.callback_query_handler(func=lambda call: True)
def handle_vpn_set(call):
    try:
        interface_num = int(call.data) + 2
        logger.info(
            "User %s selected interface %d", call.from_user.username, interface_num
        )
        bot.edit_message_reply_markup(
            call.message.chat.id, message_id=call.message.message_id, reply_markup=None
        )

        bot.send_message(
            call.message.chat.id,
            "Производится выбор интерфейса",
            parse_mode="MarkdownV2",
        )

        bot.send_message(
            call.message.chat.id,
            mcode(scan_interfaces(interface_num)),
            parse_mode="MarkdownV2",
        )
    except Exception as e:
        logger.exception("Error in handle_vpn_set: %s", str(e))
        bot.send_message(call.message.chat.id, "Произошла ошибка при смене интерфейса.")


def handle_install_xray(message: types.Message):
    try:
        logger.info("User %s is installing XRay", message.from_user.username)
        os.system("mkdir /opt/etc/xray")
        os.system("touch /opt/etc/xray/config.json")
        vless(message.text)

        bot.send_message(
            message.chat.id,
            "Ключ установлен, устанавливается XRay",
        )

        subprocess.Popen(
            [
                "sed",
                "-i",
                '\'s/"L2TP"/"L2TP","Proxy"/',
                "/opt/apps/kvas/bin/libs/vpn",
            ]
        ).wait()

        with tempfile.TemporaryFile() as tempf:
            process = subprocess.Popen(
                [
                    "curl -o /opt/script-xray.sh https://raw.githubusercontent.com/dnstkrv/telegram4kvas/main/script/script-xray.sh && sh /opt/script-xray.sh -install && rm /opt/script-xray.sh"
                ],
                shell=True,
                stdout=tempf,
            )
            process.wait()
            tempf.seek(0)
            output = tempf.read().decode("utf-8")
            output_clean = clean_string(output)

            bot.send_message(
                message.chat.id,
                mcode("\n" + output_clean + "\n"),
                parse_mode="MarkdownV2",
            )
    except Exception as e:
        logger.exception("Error in handle_install_xray: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка при установке XRay.")


@bot.message_handler(regexp="Удалить XRay", chat_types=["private"])
def uninstall_xray(message: types.Message):
    try:
        logger.info("User %s is uninstalling XRay", message.from_user.username)
        with tempfile.TemporaryFile() as tempf:
            process = subprocess.Popen(
                [
                    "curl -o /opt/script-xray.sh https://raw.githubusercontent.com/dnstkrv/telegram4kvas/main/script/script-xray.sh && sh /opt/script-xray.sh -uninstall && rm /opt/script-xray.sh"
                ],
                shell=True,
                stdout=tempf,
            )
            process.wait()
            tempf.seek(0)
            output = tempf.read().decode("utf-8")

            bot.send_message(
                message.chat.id,
                mcode("\n" + output + "\n"),
                parse_mode="MarkdownV2",
            )
    except Exception as e:
        logger.exception("Error in uninstall_xray: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка при удалении XRay.")


def handle_add_host(message: types.Message):
    try:
        logger.info("User %s is adding host(s)", message.from_user.username)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [
            types.KeyboardButton("Добавить хост"),
            types.KeyboardButton("Удалить хост"),
            types.KeyboardButton("Список хостов"),
            types.KeyboardButton("Очистить список"),
            types.KeyboardButton("Импорт"),
            types.KeyboardButton("Экспорт"),
            types.KeyboardButton("Назад"),
        ]
        keyboard.add(*buttons)
        domain_list = message.text.split()
        for domain in domain_list:
            with tempfile.TemporaryFile() as tempf:
                process = subprocess.Popen(["kvas", "add", domain, "yes"], stdout=tempf)
                process.wait()
                tempf.seek(0)
                output = tempf.read().decode("utf-8")
                output_clean = clean_string(output)

                bot.send_message(
                    message.chat.id,
                    mcode(output_clean + "\n"),
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard,
                )

                if len(domain_list) > 1 and domain == domain_list[-1]:
                    bot.send_message(
                    message.chat.id,
                    "Добавление окончено",
                    reply_markup=keyboard,
                )
    except Exception as e:
        logger.exception("Error in handle_add_host: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка при добавлении хоста.")


def handle_delete_host(message: types.Message):
    try:
        logger.info("User %s is deleting host(s)", message.from_user.username)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [
            types.KeyboardButton("Добавить хост"),
            types.KeyboardButton("Удалить хост"),
            types.KeyboardButton("Список хостов"),
            types.KeyboardButton("Очистить список"),
            types.KeyboardButton("Импорт"),
            types.KeyboardButton("Экспорт"),
            types.KeyboardButton("Назад"),
        ]
        keyboard.add(*buttons)
        domain_list = message.text.split()
        for domain in domain_list:
            with tempfile.TemporaryFile() as tempf:
                process = subprocess.Popen(["kvas", "del", domain], stdout=tempf)
                process.wait()
                tempf.seek(0)
                output = tempf.read().decode("utf-8")
                output_clean = clean_string(output)

                bot.send_message(
                    message.chat.id,
                    mcode(output_clean + "\n"),
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard,
                )
                if len(domain_list) > 1 and domain == domain_list[-1]:
                    bot.send_message(
                    message.chat.id,
                    "Удаление окончено",
                    reply_markup=keyboard,
                )
    except Exception as e:
        logger.exception("Error in handle_delete_host: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка при удалении хоста.")


@bot.message_handler(regexp="Список хостов", chat_types=["private"])
def list_hosts(message: types.Message):
    try:
        logger.info("User %s requested list of hosts", message.from_user.username)
        src = "/opt/etc/hosts.list"
        with open(src) as file:
            sites = file.readlines()

        if not sites:
            bot.send_message(message.chat.id, "Список пуст")
        else:
            sites.sort()
            response = "\r".join(sites)
            send_long_message(response, message)
    except Exception as e:
        logger.exception("Error in list_hosts: %s", str(e))
        bot.send_message(
            message.chat.id, "Произошла ошибка при получении списка хостов."
        )


@bot.message_handler(regexp="Очистить список", chat_types=["private"])
def clear_hosts(message: types.Message):
    try:
        logger.info(
            "User %s requested to clear the list of hosts", message.from_user.username
        )
        bot.send_message(
            message.chat.id,
            "Если вы уверены, что хотите удалить все хосты, отправьте /removeall",
        )
    except Exception as e:
        logger.exception("Error in clear_hosts: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")


@bot.message_handler(commands=["removeall"], chat_types=["private"])
def remove_all_hosts(message: types.Message):
    try:
        logger.info("User %s is removing all hosts", message.from_user.username)
        with tempfile.TemporaryFile() as tempf:
            subprocess.Popen(['echo "Y" | kvas purge'], shell=True, stdout=tempf).wait()
            tempf.seek(0)
            output = clean_string(
                tempf.read()
                .decode("utf-8")
                .replace("Список разблокировки будет полностью очищен. Уверены?", "")
            )
            bot.send_message(
                message.chat.id, mcode("\n" + output + "\n"), parse_mode="MarkdownV2"
            )

        backup_file = InputFile("/opt/etc/.kvas/backup/hosts.list")
        bot.send_document(message.chat.id, backup_file)
    except Exception as e:
        logger.exception("Error in remove_all_hosts: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка при удалении всех хостов.")


@bot.message_handler(regexp="Импорт", chat_types=["private"])
def import_prompt(message: types.Message):
    try:
        logger.info("User %s prompted to import hosts", message.from_user.username)
        answer = bot.send_message(
            message.chat.id,
            f"Пришлите файл для импорта в формате, который {mlink('поддерживает', 'https://github.com/qzeleza/kvas/wiki')} {mbold('КВАС')}",
            parse_mode="MarkdownV2",
        )
        bot.register_next_step_handler(answer, handle_import)
    except Exception as e:
        logger.exception("Error in import_prompt: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")


def handle_import(message: types.Message):
    try:
        logger.info("User %s is importing hosts", message.from_user.username)
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = "/opt/kvastelegram.import"
        with open(src, "wb") as file_import:
            file_import.write(downloaded_file)

        with tempfile.TemporaryFile() as tempf:
            subprocess.Popen(["kvas", "import", src], stdout=tempf).wait()
            tempf.seek(0)
            output = clean_string(tempf.read().decode("utf-8"))
            send_long_message(output, message)

        os.system(
            "awk 'NF > 0' /opt/etc/hosts.list > /opt/etc/hostsb.list && cp /opt/etc/hostsb.list /opt/etc/hosts.list && rm /opt/etc/hostsb.list"
        )
    except Exception as e:
        logger.exception("Error in handle_import: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка при импорте хостов.")


@bot.message_handler(regexp="Экспорт", chat_types=["private"])
def export_hosts(message: types.Message):
    try:
        logger.info("User %s requested to export hosts", message.from_user.username)
        src = "/opt/etc/.kvas/backup/kvas_export.txt"
        result = subprocess.run(["kvas", "export", src], capture_output=True, text=True)

        if result.returncode != 0:
            logger.error("kvas export failed: %s", result.stderr)
            bot.send_message(message.chat.id, "Произошла ошибка при экспорте хостов.")
            return

        bot.send_document(message.chat.id, open(src, "rb"))
    except Exception as e:
        logger.exception("Error in export_hosts: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка при экспорте хостов.")



@bot.message_handler(regexp="Перезагрузить роутер", chat_types=["private"])
def reboot_router(message: types.Message):
    try:
        logger.warning(
            "User %s requested to reboot the router", message.from_user.username
        )
        bot.send_message(message.chat.id, "Роутер перезагружается")
        logger.warning("Rebooting the router...")
        subprocess.Popen(["reboot"])
    except Exception as e:
        logger.exception("Error in reboot_router: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка при перезагрузке роутера.")


@bot.message_handler(
    func=lambda message: message.chat.id in user_states
    and user_states[message.chat.id],
    chat_types=["private"],
)
def custom_command(message: types.Message):
    try:
        logger.info(
            "User %s executed command in terminal mode: %s",
            message.from_user.username,
            message.text,
        )
        interrupt_command = ["Отмена", "отмена", "Назад"]
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [
            types.KeyboardButton("Запустить test"),
            types.KeyboardButton("Запустить debug"),
            types.KeyboardButton("Запустить reset"),
            types.KeyboardButton("Перезагрузить роутер"),
            types.KeyboardButton("Терминал"),
            types.KeyboardButton("Обновить бота"),
            types.KeyboardButton("Назад"),
        ]
        keyboard.add(*buttons)
        if message.text in interrupt_command:
            user_states.pop(message.chat.id)
            bot.send_message(
                message.chat.id, "Вы вышли из режима терминала.", reply_markup=keyboard
            )
        else:
            with tempfile.TemporaryFile() as tempf:
                output_proc = subprocess.Popen([message.text], shell=True, stdout=tempf)
                output_proc.wait()
                tempf.seek(0)
                output = tempf.read().decode("utf-8")
                send_long_message(clean_string(output), message)
    except Exception as e:
        logger.exception("Error in custom_command: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка при выполнении команды.")


@bot.message_handler(regexp="Запустить test", chat_types=["private"])
def run_test(message: types.Message):
    try:
        logger.info("User %s requested to run test", message.from_user.username)
        bot.send_message(message.chat.id, "Тест запущен, ожидайте несколько минут")
        subprocess.Popen(
            [
                "sed",
                "-i",
                "/\tipset_site_visit_check/s/^/#\ /",
                "/opt/apps/kvas/bin/libs/check",
            ]
        ).wait()
        with tempfile.TemporaryFile() as tempf:
            test_proc = subprocess.Popen(["kvas", "test"], stdout=tempf)
            test_proc.wait()
            tempf.seek(0)
            output = clean_string(tempf.read().decode("utf-8"))
            send_long_message(output, message)
    except Exception as e:
        logger.exception("Error in run_test: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка при запуске теста.")


@bot.message_handler(regexp="Запустить debug", chat_types=["private"])
def run_debug(message: types.Message):
    try:
        logger.info("User %s requested to run debug", message.from_user.username)
        bot.send_message(
            message.chat.id,
            f"Запущена команда {mcode('kvas debug')}",
            parse_mode="MarkdownV2",
        )
        src = "/opt/root/kvas.debug"
        process = subprocess.Popen(["kvas", "debug", src])
        process.wait()
        debug_file = InputFile(src)
        bot.send_document(message.chat.id, debug_file, parse_mode="MarkdownV2")
    except Exception as e:
        logger.exception("Error in run_debug: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка при запуске debug.")


@bot.message_handler(regexp="Запустить reset", chat_types=["private"])
def run_reset(message: types.Message):
    try:
        logger.info("User %s requested to run reset", message.from_user.username)
        bot.send_message(
            message.chat.id,
            f"Запущена команда {mcode('kvas reset')}",
            parse_mode="MarkdownV2",
        )
        with tempfile.TemporaryFile() as tempf:
            reset_proc = subprocess.Popen(["kvas", "reset"], stdout=tempf)
            reset_proc.wait()
            tempf.seek(0)
            output = clean_string(tempf.read().decode("utf-8"))
            bot.send_message(
                message.chat.id,
                mcode("\n" + output + "\n"),
                parse_mode="MarkdownV2",
            )
    except Exception as e:
        logger.exception("Error in run_reset: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка при запуске сброса.")


@bot.message_handler(regexp="Обновить бота", chat_types=["private"])
def update_bot(message: types.Message):
    try:
        logger.warning(
            "User %s requested to update the bot", message.from_user.username
        )

        response = requests.get(
            "https://api.github.com/repos/dnstkrv/telegram4kvas/releases/latest"
        )
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve latest version: {response.text}")
        version_now = telegram_bot_config.version
        version_new = response.json()["tag_name"]
        changelog = response.json()["body"]

        if version_now != version_new:
            bot.send_message(
                message.chat.id,
                f"Текущая версия бота: {version_now}, устанавливается версия: {version_new}",
            )
            if changelog:
                send_long_message(changelog, message)
            os.system(
                "curl -o /opt/upgrade.sh https://raw.githubusercontent.com/dnstkrv/telegram4kvas/main/upgrade.sh && sh /opt/upgrade.sh && rm /opt/upgrade.sh"
            )
            bot.send_message(message.chat.id, "Запущено обновление бота")
        else:
            bot.send_message(
                message.chat.id,
                f"Текущая версия актуальна ({version_now})",
            )

        logger.warning("The bot has started updating")

    except Exception as e:
        logger.exception("Error in update_bot: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка при обновлении бота.")


@bot.message_handler(regexp="Назад", chat_types=["private"])
def go_back(message: types.Message):
    try:
        logger.info("User %s requested to go back", message.from_user.username)
        handle_start(message)
    except Exception as e:
        logger.exception("Error in go_back: %s", str(e))
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте позже.")


if __name__ == "__main__":
    try:
        bot.setup_middleware(Middleware())
        connection_attempt = 0
        while connection_attempt != telegram_bot_config.reconnection_attempts:
            connection_attempt +=1
            logger.info(f'Trying to connect to the telegram server. Attempt №{connection_attempt}')
            os.system(
                f"logger -s -t telegram4kvas Trying to connect to the telegram server. Attempt №{connection_attempt}"
                      )
            try:     
                bot_me = bot.get_me()
                connection_attempt = telegram_bot_config.reconnection_attempts
            except Exception as e: 
                if connection_attempt != telegram_bot_config.reconnection_attempts: 
                    logger.warning(f'Connection attempt №{connection_attempt} failed. Wait {telegram_bot_config.reconnection_timeout} seconds before trying to connect again.')
                    os.system(
                        f"logger -s -t telegram4kvas Connection attempt №{connection_attempt} failed. Wait {telegram_bot_config.reconnection_timeout} seconds before trying to connect again."
                             )
                    time.sleep(telegram_bot_config.reconnection_timeout)
                else: 
                    logger.warning(f'Connection failed after {connection_attempt} attempts.')
                    logger.error(f'Connection failed after {connection_attempt} attempts. Check internet connection! Bot is shutdown.')
                    os.system(
                        f"logger -s -t telegram4kvas Connection failed after {connection_attempt} attempts. Check internet connection! Bot shutdown."
                             )
                    sys.exit()
        os.system(
            f"logger -s -t telegram4kvas Connection successful. Bot @{bot_me.username} running [{telegram_bot_config.version}]."
                 )
        logger.info(f'Connection successful. Bot @{bot_me.username} running [{telegram_bot_config.version}].')
        send_startup_message()
        bot.infinity_polling(skip_pending=True, timeout=60)
    except Exception as e:
        logger.exception("Fatal error occurred while running the bot")
