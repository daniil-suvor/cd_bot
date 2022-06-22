import telebot
from aiogram import types
import os
import numpy as np
from scipy.optimize import curve_fit
import theor_spectra as ts
import matplotlib as mpl
import matplotlib.pyplot as plt


token = "" # add your token 

bot = telebot.TeleBot(token)

d_users = {}

class Example(object):
    def __init__(self, name):
        self.data_name = name
        self.left = None
        self.right = None
        self.data = None

    def load_data(self, file_name):
        b, data = np.swapaxes(np.loadtxt(file_name, skiprows = 23, usecols = (0,1)), 0,1)
        self.left = b[-1]
        self.right = b[0]
        self.data = data[::-1]
    def get_data(self, left, right):
        if (left < self.left):
            left = self.left
        if (right > self.right):
            right = self.right
        res = self.data
        res = res[int(left - self.left) : int(self.right - self.left + self.right - right)]
        return res

class User(object):
    def __init__(self):
        self.minus_base = False
        self.id = None
        self.base = None
        self.data = None
        self.left = 190
        self.right = 240
        self.menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    def ubdate_menu(self):
        self.menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if (self.base == None):
            button = types.KeyboardButton("добавить базовую линию")
        elif (self.minus_base):
            button = types.KeyboardButton("не вычитать базовую линию")
        else:
            button = types.KeyboardButton("вычитать базовую линию")
        self.menu.add(button)
        button = types.KeyboardButton("добавить файл образца")
        self.menu.add(button)
        if (self.data != None):
            button = types.KeyboardButton("старт")
            self.menu.add(button)


def spectra(x, a, b, c):
	return x[0]*a + x[1]*b + x[2]*c

@bot.message_handler(commands=["start"])
def start(message, res=False):
    chat_id = message.chat.id
    user = User()
    user.id = chat_id
    d_users[chat_id] = user
    d_users[chat_id].ubdate_menu()
    bot.send_message(message.chat.id, 'Я на связи. Напиши мне что-нибудь )')
    bot.send_message(message.chat.id, text="выберите действие в меню", reply_markup=[user.menu])

@bot.message_handler(func = lambda message: message.text == "вычитать базовую линию")
def minus(message):
    chat_id = message.chat.id
    d_users[chat_id].minus_base = True
    d_users[chat_id].ubdate_menu()
    bot.send_message(message.chat.id, text="выберите действие в меню", reply_markup=[d_users[chat_id].menu])

@bot.message_handler(func = lambda message: message.text == "не вычитать базовую линию")
def ne_minus(message):
    chat_id = message.chat.id
    d_users[chat_id].minus_base = False
    d_users[chat_id].ubdate_menu()
    bot.send_message(message.chat.id, text="выберите действие в меню", reply_markup=[d_users[chat_id].menu])

@bot.message_handler(func = lambda message: message.text == "добавить базовую линию")
def send_wel(message):
    chat_id = message.chat.id
    if (not(chat_id in d_users)):
        user = User()
        user.id = chat_id
        d_users[chat_id] = user
    bot.send_message(message.chat.id, 'Загрузите файл базовой линии')
    bot.register_next_step_handler(message, download_baseline)

def download_baseline(message):
    chat_id = message.chat.id
    file_name = message.document.file_name
    file_id = message.document.file_name
    file_id_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_id_info.file_path)
    src = file_name
    if not os.path.exists('baseline'): os.makedirs('baseline')
    save_dir = r'baseline'
    full_name = save_dir + '/' + src

    with open(full_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    d_users[chat_id].base = Example(src.split('.')[0])
    d_users[chat_id].base.load_data(full_name)
    d_users[chat_id].ubdate_menu()
    bot.send_message(message.chat.id, text="выберите действие в меню", reply_markup=[d_users[chat_id].menu])

@bot.message_handler(func = lambda message: message.text == "добавить файл образца")
def send_welcome(message):
    chat_id = message.chat.id
    if (not(chat_id in d_users)):
        user = User()
        user.id = chat_id
        d_users[chat_id] = user
    bot.send_message(message.chat.id, 'Загрузите файл образца')
    bot.register_next_step_handler(message, download_ex)
def download_ex(message):
    chat_id = message.chat.id
    file_name = message.document.file_name
    file_id = message.document.file_name
    file_id_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_id_info.file_path)
    src = file_name
    if not os.path.exists('ex'): os.makedirs('ex')
    save_dir = r'ex'
    full_name = save_dir + '/' + src

    with open(full_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    d_users[chat_id].data = Example(src.split('.')[0])
    d_users[chat_id].data.load_data(full_name)
    d_users[chat_id].ubdate_menu()
    bot.send_message(message.chat.id, text="выберите действие в меню", reply_markup=[d_users[chat_id].menu])

@bot.message_handler(func = lambda message: message.text == "старт")
def send_graph(message):
    chat_id = message.chat.id
    left = int(d_users[chat_id].left)
    right = int(d_users[chat_id].right)
    data = d_users[chat_id].data.get_data(left, right)
    if (d_users[chat_id].minus_base):
        base = d_users[chat_id].base.get_data(left, right)
        data = data - base
    xdata = ts.lst_theor(left, right)
    lst = curve_fit(spectra, xdata, data, bounds = (0, [10000, 10000, 10000]))
    x = np.arange(left, right)
    theor = (lst[0][0]*xdata[0]+ lst[0][1]*xdata[1]+lst[0][2]*xdata[2])
    lst_err = np.abs(data-theor)
    fig, ax1 = plt.subplots()
    ax1.grid()
    ax1.plot(x, data, color = 'blue', label = 'sample')
    ax1.plot(x, theor, color = 'green', label = 'theor')
    #ax1.set_yticks(np.arange(-1*size-3,size+4,2))
    ax1.set_xlabel('Wavelength[nm]')
    ax1.set_ylabel('CD')
    ax1.set_title(d_users[chat_id].data.data_name)
    ax2 = ax1.twinx()
    ax2.bar(x, lst_err, color = 'red')
    size = int(np.max(abs(data)))
    ax2.set_yticks(np.arange(0,size+4))
    ax2.set_ylabel('Error')
    ax1.legend()
    if not os.path.exists('img'): os.makedirs('img')
    save_dir = r'img'
    full_name = save_dir + '/' + d_users[chat_id].data.data_name + '.png'
    plt.savefig(full_name)
    s = lst[0][0] + lst[0][1] + lst[0][2]
    ans = ('alpha = ' + str(round(lst[0][0]/s*100,2)) + '%\n' +
    	   'beta = ' +  str(round(lst[0][1]/s*100,2)) + '%\n' +
    	   'apereod = ' + str(round(lst[0][2]/s*100,2)) + '%\n' +
        str(round(lst[0][0], 4)) + '\n' +
        str(round(lst[0][1], 4)) + '\n' +
        str(round(lst[0][2], 4)))

    bot.send_photo(chat_id, photo=open(full_name, 'rb'), caption=ans)
    d_users[chat_id].ubdate_menu()
    bot.send_message(message.chat.id, text="выберите действие в меню", reply_markup=[d_users[chat_id].menu])


"""@bot.message_handler(commands=['my_data'])
def my_data(message):
    chat_id = message.chat.id
    bot.send_message(message.chat.id, d_users[chat_id].base.data_name)
    bot.send_message(message.chat.id, d_users[chat_id].base.left)
    bot.send_message(message.chat.id, d_users[chat_id].base.right)
    bot.send_message(message.chat.id, d_users[chat_id].data.data_name)
    bot.send_message(message.chat.id, d_users[chat_id].data.left)
    bot.send_message(message.chat.id, d_users[chat_id].data.right)"""

# Получение сообщений от юзера
@bot.message_handler(content_types=["text"])
def handle_text(message):
    bot.send_message(message.chat.id, 'Вы написали: ' + message.text)

# Запускаем бота
bot.polling(none_stop=True)

#os.remove(full_name)
