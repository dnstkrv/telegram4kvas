import os
import subprocess
import tempfile

import telebot
from telebot import types
from telebot.formatting import mbold, mcode, mlink
from telebot.handler_backends import BaseMiddleware, CancelUpdate
from telebot.types import InputFile

import telegram_bot_config

user_states = {}

bot = telebot.TeleBot(
    telegram_bot_config.token,
    use_class_middlewares=True,
)


class Middleware(BaseMiddleware):
    def __init__(self):
        self.update_types = ["message"]

    def pre_process(self, message: types.Message, data: dict):
        if (
            message.from_user.username not in telegram_bot_config.usernames
            and message.from_user.id not in telegram_bot_config.userid
        ):
            bot.send_message(message.chat.id, "Вы не авторизованы")
            return CancelUpdate()

    def post_process(self, message, data, exception):
        pass


@bot.message_handler(commands=["start"], chat_types=["private"])
def handle_start(message: types.Message):
    startMenu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Управление хостами")
    item2 = types.KeyboardButton("Сервис")
    startMenu.add(item1, item2)
    bot.send_message(
        message.chat.id,
        "Панель управления КВАС",
        reply_markup=startMenu,
    )


@bot.message_handler(regexp="Управление хостами", chat_types=["private"])
def hosts_message(message: types.Message):
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


@bot.message_handler(regexp="Сервис", chat_types=["private"])
def service_message(message: types.Message):
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
    bot.send_message(
        message.chat.id,
        "Сервисное меню",
        reply_markup=keyboard,
    )


@bot.message_handler(regexp="Добавить хост", chat_types=["private"])
def add_host_prompt(message: types.Message):
    answer = bot.send_message(
        message.chat.id,
        "Введите домен(или несколько доменов, разделенных пробелом) для добавления:",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(answer, handle_add_host)


@bot.message_handler(regexp="Удалить хост", chat_types=["private"])
def delete_host_prompt(message: types.Message):
    answer = bot.send_message(
        message.chat.id,
        "Введите домен(или несколько доменов, разделенных пробелом) для удаления:",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(answer, handle_delete_host)

@bot.message_handler(regexp="Терминал", chat_types=["private"])
def custom_command_prompt(message: types.Message):
    user_states[message.chat.id] = True
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    button = [
        types.KeyboardButton("Назад"),
    ]
    keyboard.add(*button)
    answer = bot.send_message(
        message.chat.id,
        "Вы вошли в режим терминала. Вы можете писать любые команды, не требующие интерактива(Например, cat /opt/etc/kvas.conf, ps | grep bot). Для выхода из режима терминала нажмите Назад",
        reply_markup=keyboard,
    )
    bot.register_next_step_handler(answer, custom_command)

def clean_string(text: str) -> str:
    return (
        text.replace("-", "")
        .replace("[33m", "")
        .replace("[m", "")
        .replace("[1;32mВ", "")
        .replace("[1;32m", "")
        .replace("[1;31m", "")
        .replace("[8D", "")
        .replace("[10D", "")
        .replace("[9D", "")
        .replace("[11D", "")
        .replace("[6D", "")
        .replace("[12D", "")
        .replace("[1;31m", "")
        .replace("[36m", "")
        .replace("[14D", "")
    )


def handle_add_host(message: types.Message):
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
                mcode("\n" + output_clean + "\n"),
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
            )


def handle_delete_host(message: types.Message):
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
                mcode("\n" + output_clean + "\n"),
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
            )


@bot.message_handler(regexp="Список хостов", chat_types=["private"])
def list_hosts(message: types.Message):
    src = "/opt/etc/hosts.list"
    with open(src) as file:
        sites = file.readlines()

    if not sites:
        bot.send_message(message.chat.id, "Список пуст")
    else:
        sites.sort()
        response = mcode("\r".join(sites))

        if len(response) > 4096:
            for x in range(0, len(response), 4096):
                bot.send_message(
                    message.chat.id, mcode("\n" + response[x : x + 4096] + "\n"), parse_mode="MarkdownV2"
                )
        else:
            bot.send_message(message.chat.id, response, parse_mode="MarkdownV2")


@bot.message_handler(regexp="Очистить список", chat_types=["private"])
def clear_hosts(message: types.Message):
    bot.send_message(
        message.chat.id,
        "Если вы уверены, что хотите удалить все хосты, отправьте /removeall",
    )


@bot.message_handler(commands=["removeall"], chat_types=["private"])
def remove_all_hosts(message: types.Message):
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


@bot.message_handler(regexp="Импорт", chat_types=["private"])
def import_prompt(message: types.Message):
    answer = bot.send_message(
        message.chat.id,
        f"Пришлите файл для импорта в формате, который {mlink('поддерживает', 'https://github.com/qzeleza/kvas/wiki')} {mbold('КВАС')}",
        parse_mode="MarkdownV2",
    )
    bot.register_next_step_handler(answer, handle_import)


def handle_import(message: types.Message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    src = "/opt/kvastelegram.import"
    with open(src, "wb") as file_import:
        file_import.write(downloaded_file)

    with tempfile.TemporaryFile() as tempf:
        subprocess.Popen(["kvas", "import", src], stdout=tempf).wait()
        tempf.seek(0)
        output = clean_string(tempf.read().decode("utf-8"))
        if len(output) > 4096:
            for x in range(0, len(output), 4096):
                bot.send_message(
                    message.chat.id,
                    mcode("\n" + output[x : x + 4096] + "\n"),
                    parse_mode="MarkdownV2",
                )
        else:
            bot.send_message(
                message.chat.id,
                mcode("\n" + output + "\n"),
                parse_mode="MarkdownV2",
                )

    os.system(
        "awk 'NF > 0' /opt/etc/hosts.list > /opt/etc/hostsb.list && cp /opt/etc/hostsb.list /opt/etc/hosts.list && rm /opt/etc/hostsb.list"
    )


@bot.message_handler(regexp="Экспорт", chat_types=["private"])
def export_hosts(message: types.Message):
    src = "/opt/etc/.kvas/backup/kvas_export.txt"
    subprocess.Popen(["kvas", "export", src]).wait()
    #export_file = InputFile(src)
    bot.send_document(message.chat.id, open(src, 'rb'))


@bot.message_handler(regexp="Перезагрузить роутер", chat_types=["private"])
def reboot_router(message: types.Message):
    bot.send_message(message.chat.id, "Роутер перезагружается")
    subprocess.Popen(["reboot"])

@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id], chat_types=["private"])
def custom_command(message: types.Message):
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
        bot.send_message(message.chat.id, "Вы вышли из режима терминала.", reply_markup=keyboard)
    else:
        with tempfile.TemporaryFile() as tempf:
            output_proc = subprocess.Popen([message.text], shell = True, stdout=tempf)
            output_proc.wait()
            tempf.seek(0)
            output = tempf.read().decode("utf-8")
            if len(output) > 4096:
                for x in range(0, len(output), 4096):
                    bot.send_message(
                        message.chat.id,
                        mcode("\n" + output[x : x + 4096] + "\n"),
                        parse_mode="MarkdownV2",
                    )
            else:
                bot.send_message(
                    message.chat.id,
                    mcode("\n" + output + "\n"),
                    parse_mode="MarkdownV2",
                    )

@bot.message_handler(regexp="Запустить test", chat_types=["private"])
def run_test(message: types.Message):
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
        if len(output) > 4096:
            for x in range(0, len(output), 4096):
                bot.send_message(
                    message.chat.id,
                    mcode("\n" + output[x : x + 4096] + "\n"),
                    parse_mode="MarkdownV2",
                )
        else:
            bot.send_message(
                message.chat.id,
                mcode("\n" + output + "\n"),
                parse_mode="MarkdownV2",
            )


@bot.message_handler(regexp="Запустить debug", chat_types=["private"])
def run_debug(message: types.Message):
    bot.send_message(
        message.chat.id,
        f"Запущена команда {mcode('kvas debug')}",
        parse_mode="MarkdownV2",
    )
    subprocess.Popen(["kvas", "debug", "/opt/root/kvas.debug"]).wait()
    debug_file = InputFile("/opt/root/kvas.debug")
    bot.send_document(message.chat.id, debug_file, parse_mode="MarkdownV2")


@bot.message_handler(regexp="Запустить reset", chat_types=["private"])
def run_reset(message: types.Message):
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


@bot.message_handler(regexp="Обновить бота", chat_types=["private"])
def update_bot(message: types.Message):
    bot.send_message(message.chat.id, "Запущено обновление бота")
    os.system(
        "curl -o /opt/upgrade.sh https://raw.githubusercontent.com/dnstkrv/telegram4kvas/main/upgrade.sh && sh /opt/upgrade.sh && rm /opt/upgrade.sh"
    )


@bot.message_handler(regexp="Назад", chat_types=["private"])
def go_back(message: types.Message):
    handle_start(message)


try:
    bot.setup_middleware(Middleware())
    bot_me = bot.get_me()
    print(f"Bot @{bot_me.username} running...")
    os.system(f"logger -s -t telegram4kvas Bot @{bot_me.username} running...")
    bot.infinity_polling(skip_pending=True, timeout=60)
except Exception as err:
    with open("/opt/error.log", "a") as error_log:
        error_log.write(f"Error: {err}\n")