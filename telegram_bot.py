#!/usr/bin/python3

import subprocess
import os
import stat
import tempfile
import telebot
from telebot import types
from telethon.sync import TelegramClient
import requests
import telegram_bot_config as config

token = config.token
usernames = config.usernames
userid = config.userid
bot = telebot.TeleBot(token)
action = ""

@bot.message_handler(commands=['start'])
def start(message):
    if (message.from_user.username not in usernames) and (message.from_user.id not in userid):
        bot.send_message(message.chat.id, 'Вы не авторизованы, внесите свой логин или ID в список')
        return
    startMenu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Управление хостами")
    item2 = types.KeyboardButton("Сервис")
    startMenu.add(item1, item2)
    bot.send_message(message.chat.id, 'Добро пожаловать в панель управления КВАС', reply_markup=startMenu)

@bot.message_handler(content_types=['text'])
def bot_message(message):
    try:
        mainMenu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m1 = types.KeyboardButton("Управление хостами")
        m2 = types.KeyboardButton("Сервис")
        mainMenu.add(m1, m2)

        serviceMenu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        s1 = types.KeyboardButton("Запустить debug")
        s2 = types.KeyboardButton("Перезагрузить роутер")
        s3 = types.KeyboardButton("Обновить бота")
        backward = types.KeyboardButton("Назад")
        serviceMenu.add(s1, s2)
        serviceMenu.add(s3, backward)
        
        hostsMenu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        h1 = types.KeyboardButton("Добавить хост")
        h2 = types.KeyboardButton("Удалить хост")
        h3 = types.KeyboardButton("Список хостов")
        backward = types.KeyboardButton("Назад")
        hostsMenu.add(h1, h2)
        hostsMenu.add(h3, backward)
        
        if (message.from_user.username not in usernames) and (message.from_user.id not in userid):
            bot.send_message(message.chat.id, 'Вы не авторизованы, внесите свой логин или ID в список')
            return
            
        if message.chat.type == 'private':
            global action
            
            if message.text == 'Управление хостами':
                bot.send_message(message.chat.id, 'Управление хостами:', reply_markup=hostsMenu)
                return
                
            if message.text == 'Сервис':
                bot.send_message(message.chat.id, 'Сервисное меню', reply_markup=serviceMenu)
                return
               
            if message.text == 'Добавить хост':
                bot.send_message(message.chat.id, 'Введите домен:', reply_markup=hostsMenu)
                action = "hostAdd"
                return
                
            if action == "hostAdd":
                bot.send_message(message.chat.id, 'Выполняется добавление адреса, ожидайте', reply_markup=serviceMenu)
                with tempfile.TemporaryFile() as tempf:
                    hostAdd = subprocess.Popen(['kvas', 'add', message.text, 'yes'], stdout=tempf)
                    hostAdd.wait()
                    tempf.seek(0)
                    a = tempf.read().decode('utf-8')
                    #Удаляем лишние символы и отправляем ответ
                    bot.send_message(message.chat.id, a.replace('-', '').replace('[33m', '').replace('[m', '').replace('[10D', '').replace('[1;32m', ''), reply_markup=hostsMenu)
                action = ""
                return
                
            if message.text == 'Удалить хост':
                bot.send_message(message.chat.id, 'Введите домен:', reply_markup=hostsMenu)
                action = "hostDel"
                return
                
            if action == "hostDel":
                bot.send_message(message.chat.id, 'Выполняется удаление адреса, ожидайте', reply_markup=serviceMenu)
                with tempfile.TemporaryFile() as tempf:
                    hostDel = subprocess.Popen(['kvas', 'del', message.text], stdout=tempf)
                    hostDel.wait()
                    tempf.seek(0)
                    a = tempf.read().decode('utf-8')
                    #Удаляем лишние символы и отправляем ответ
                    bot.send_message(message.chat.id, a.replace('-', '').replace('[33m', '').replace('[m', '').replace('[8D', '').replace('[1;32m', ''), reply_markup=hostsMenu)
                action = ""
                return
              
            if message.text == 'Список хостов':
                file = open('/opt/etc/hosts.list')
                flag = True
                s = '```'
                sites = []
                for line in file:
                    sites.append(line)
                    flag = False
                if flag:
                    s = 'Список пуст'
                file.close()
                sites.sort()
                if not flag:
                    for line in sites:
                        s = str(s) + '\n' + line.replace("\n", "")
                s = str(s) + '\n```'
                if len(s) > 4096:
                    for x in range(0, len(s), 4096):
                        bot.send_message(message.chat.id, s[x:x + 4096])
                else:
                    bot.send_message(message.chat.id, s, parse_mode="Markdown")
                return

            if message.text == 'Запустить debug':
                bot.send_message(message.chat.id, 'Файл kvas.debug готовится к отправке', reply_markup=serviceMenu) 
                debug = subprocess.Popen(["kvas", "debug", "kvas.debug"])
                debug.wait()
                bot.send_document(message.chat.id, open(r'/opt/root/kvas.debug', 'rb'), reply_markup=serviceMenu)
                
            if message.text == 'Обновить бота':
                bot.send_message(message.chat.id, 'Запущено обновление бота', reply_markup=serviceMenu) 
                os.system('curl -o /opt/upgrade.sh https://raw.githubusercontent.com/dnstkrv/telegram4kvas/main/upgrade.sh && sh /opt/upgrade.sh && rm /opt/upgrade.sh')
                return

            if message.text == "Назад":
                bot.send_message(message.chat.id, 'Добро пожаловать в панель управления КВАС', reply_markup=mainMenu)
                return
                
            if message.text == 'Перезагрузить роутер':
                bot.send_message(message.chat.id, 'Отправлена команда для перезагрузки роутера, ожидайте', reply_markup=serviceMenu)
                os.system('reboot')
                return

    except Exception as error:
        file = open("/opt/error.log", "w")
        file.write(str(error))
        file.close()
        os.chmod(r"/opt/error.log", 0o0755)

try:
    bot.infinity_polling()
except Exception as err:
    fl = open("/opt/error.log", "w")
    fl.write(str(err))
    fl.close()
