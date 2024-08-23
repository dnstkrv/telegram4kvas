#!/usr/bin/python3

import subprocess
import os
import tempfile
import telebot
from telebot import types
#import requests
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
        m3 = types.KeyboardButton('Помощь')
        mainMenu.add(m1, m2)
        mainMenu.add(m3)

        serviceMenu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        s1 = types.KeyboardButton('Запустить test')
        s2 = types.KeyboardButton('Запустить debug')
        s3 = types.KeyboardButton('Перезагрузить роутер')
        s4 = types.KeyboardButton('Обновить бота')
        backward = types.KeyboardButton('Назад')
        serviceMenu.add(s1, s2)
        serviceMenu.add(s3, s4)
        serviceMenu.add(backward)
        
        hostsMenu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        h1 = types.KeyboardButton("Добавить хост")
        h2 = types.KeyboardButton("Удалить хост")
        h3 = types.KeyboardButton("Список хостов")
        h4 = types.KeyboardButton('Очистить список')
        h5 = types.KeyboardButton('Импорт')
        h6 = types.KeyboardButton('Экспорт')
        backward = types.KeyboardButton("Назад")
        hostsMenu.add(h1, h2)
        hostsMenu.add(h3, h4)
        hostsMenu.add(h5, h6)
        hostsMenu.add(backward)

        helpMenu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        hm1 = types.KeyboardButton('Помощь от автора бота')
        hm2 = types.KeyboardButton('На чай автору бота')
        hm3 = types.KeyboardButton('Донат разработчику КВАС')
        backward = types.KeyboardButton('Назад')
        helpMenu.add(hm1, hm2)
        helpMenu.add(hm3, backward)
        
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

            if message.text == 'Помощь':

                bot.send_message(message.chat.id, 'Помощь:', reply_markup=helpMenu)
                
                return
               
            if message.text == 'Добавить хост':

                bot.send_message(message.chat.id, 'Введите домен(или несколько доменов, разделенных пробелом)', reply_markup=hostsMenu)
                action = "hostAdd"

                return
                
            if action == "hostAdd":
            
                domainList = message.text.split()
                if len(domainList) > 1:
                    bot.send_message(message.chat.id, 'Выполняется добавление адресов, дождитесь сообщения о добавлении последнего адреса', reply_markup=hostsMenu)
                else:
                    bot.send_message(message.chat.id, 'Выполняется добавление адреса', reply_markup=hostsMenu)
                for domain in domainList:
                    with tempfile.TemporaryFile() as tempf:
                        hostAdd = subprocess.Popen(['kvas', 'add', domain, 'yes'], stdout=tempf)
                        hostAdd.wait()
                        tempf.seek(0)
                        a = tempf.read().decode('utf-8')
                        #Удаляем лишние символы и отправляем ответ
                        bot.send_message(message.chat.id, a.replace('-', '').replace('[33m', '').replace('[m', '').replace('[10D', '').replace('[1;32m', ''), reply_markup=hostsMenu)
                action = ""

                return
                
            if message.text == 'Удалить хост':

                bot.send_message(message.chat.id, 'Введите домен (или несколько доменов, разделенных пробелом)', reply_markup=hostsMenu)
                action = "hostDel"

                return
                
            if action == "hostDel":

                domainList = message.text.split()
                if len(domainList) > 1:
                    bot.send_message(message.chat.id, 'Выполняется удаление адресов, дождитесь сообщения о добавлении последнего адреса', reply_markup=hostsMenu)
                else:
                    bot.send_message(message.chat.id, 'Выполняется удаление адреса', reply_markup=hostsMenu)
                for domain in domainList:
                    with tempfile.TemporaryFile() as tempf:
                        hostDel = subprocess.Popen(['kvas', 'del', domain], stdout=tempf)
                        hostDel.wait()
                        tempf.seek(0)
                        a = tempf.read().decode('utf-8')
                        #Удаляем лишние символы и отправляем ответ
                        bot.send_message(message.chat.id, a.replace('-', '').replace('[1;31m', '').replace('[33m', '').replace('[m', '').replace('[8D', '').replace('[1;32m', ''), reply_markup=hostsMenu)
                action = ""

                return
              
            if message.text == 'Список хостов':

                src = '/opt/etc/hosts.list'
                file = open(src)
                flag = True
                s = '```'
                sites = []
                for line in file:
                    sites.append(line)
                    flag = False
                if os.stat(src).st_size == 0:
                    s = 'Список пуст'
                    bot.send_message(message.chat.id, s)
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
                    bot.send_message(message.chat.id, s, parse_mode='MarkdownV2')

                return

            if message.text == 'Очистить список':
                bot.send_message(message.chat.id, 'Если вы уверены, что хотите удалить все хосты, отправьте /removeall', reply_markup=hostsMenu)
                return

            if message.text == '/removeall':

                bot.send_message(message.chat.id, 'Выполняется очистка списка, ожидайте', reply_markup=hostsMenu)
                with tempfile.TemporaryFile() as tempf:
                    clearHosts = subprocess.Popen(['echo "Y" | kvas purge'], shell=True, stdout=tempf)
                    clearHosts.wait()
                    tempf.seek(0)
                    a = tempf.read().decode('utf-8')
                    #Удаляем лишние символы и отправляем ответ
                    bot.send_message(message.chat.id, a.replace(' [8D', '').replace('[8D', '').replace('Список разблокировки будет полностью очищен. Уверены?', '').replace('-', '').replace('[1;32m', '').replace('[m', ''), reply_markup=hostsMenu)
                    tempf.close()

                return

            if message.text == 'Импорт':
                bot.send_message(message.chat.id, 'Пришлите файл для импорта в формате, который [поддерживает](https://github.com/qzeleza/kvas/wiki/%D0%9E%D0%BF%D0%B8%D1%81%D0%B0%D0%BD%D0%B8%D0%B5-%D0%BA%D0%BE%D0%BC%D0%B0%D0%BD%D0%B4#%D1%83%D0%BF%D1%80%D0%B0%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5-%D1%8D%D0%BA%D1%81%D0%BF%D0%BE%D1%80%D1%82%D0%BE%D0%BC%D0%B8%D0%BC%D0%BF%D0%BE%D1%80%D1%82%D0%BE%D0%BC) КВАС', parse_mode='MarkdownV2', reply_markup=hostsMenu)
                action = 'import'
                return

            if message.text == 'Экспорт':
                bot.send_message(message.chat.id, 'Файл kvas.export готовится к отправке', reply_markup=serviceMenu) 
                src = '/opt/kvas.export'
                debug = subprocess.Popen(['kvas', 'export', src])
                debug.wait()
                bot.send_document(message.chat.id, open(src, 'rb'), reply_markup=hostsMenu)
                return

            if message.text == 'Запустить test':
                bot.send_message(message.chat.id, 'Тест запущен, ответа не будет, просто подождите пару минут :)', reply_markup=serviceMenu)
                subprocess.Popen(['sed', '-i', '/\tipset_site_visit_check/s/^/#\ /', '/opt/apps/kvas/bin/libs/check'])
                os.system('kvas test') #временная мера
                #with tempfile.TemporaryFile() as tempf:
                    #test = subprocess.Popen(['kvas', 'test'], stdout=tempf)
                    #test.wait()
                    #tempf.seek(0)
                    #a = tempf.read().decode('utf-8')
                    #Удаляем лишние символы и отправляем ответ
                    #bot.send_message(message.chat.id, tempf.read(), reply_markup=hostsMenu)
                    #tempf.close()
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

            if message.text == 'Помощь от автора бота':

                bot.send_message(message.chat.id, 'Если испытываете трудности, хотите задать вопрос или написать пожелания - пишите @dnstkrv, всегда помогу :)', reply_markup=helpMenu)

                return

            if message.text == 'Донат разработчику КВАС':

                bot.send_message(message.chat.id, 'Донат разработчику КВАС - [Кошелек ЮМани](https://yoomoney.ru/to/4100117756734493)', parse_mode='Markdown', reply_markup=helpMenu)

                return

            if message.text == 'На чай автору бота':

                bot.send_message(message.chat.id, 'МИР `2202201523445100`, [Кошелек ЮМани](https://yoomoney.ru/to/410013576101136)', parse_mode='Markdown', reply_markup=helpMenu)

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


@bot.message_handler(content_types=['document'])
def bot_document(message):
    global action

    if action == 'import':
        bot.send_message(message.chat.id, 'Выполняется импорт, ожидайте')
        fileInfo = bot.get_file(message.document.file_id)
        downloadedFile = bot.download_file(fileInfo.file_path)
        src = '/opt/kvastelegram.import'
        with open(src, 'wb') as fileImport:
            fileImport.write(downloadedFile)
        with tempfile.TemporaryFile() as tempf:
            importProc = subprocess.Popen(['kvas', 'import', src], stdout=tempf)
            importProc.wait()
            tempf.seek(0)
            a = tempf.read().decode('utf-8')
            bot.send_message(message.chat.id, a.replace('[9D', '').replace('[1;32m', '').replace('[33m69', '').replace('[m', '').replace('-', ''))
        os.system("awk 'NF > 0' /opt/etc/hosts.list > /opt/etc/hostsb.list && cp /opt/etc/hostsb.list /opt/etc/hosts.list && rm /opt/etc/hostsb.list")
        #os.system('rm ' + src)
    else:
        bot.send_message(message.chat.id, 'Файл не ожидается, выберите команду')
    action = ''

try:
    bot.infinity_polling()
except Exception as err:
    fl = open("/opt/error.log", "w")
    fl.write(str(err))
    fl.close()