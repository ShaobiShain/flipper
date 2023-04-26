import requests
from bs4 import BeautifulSoup as BS
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
import urllib.parse as parse
import datetime
from fuzzywuzzy import process

bot = Bot(token="5840612207:AAETHr3RfCnSArR2SCJG9S0MPLZhWywiceU")
storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)

MONTHES = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября',
           'декабря']

schedule_page = requests.post('https://www.rksi.ru/mobile_schedule')
schedule_soup = BS(schedule_page.text, "html.parser")
select_tag = schedule_soup.find('select', {'id': 'group'})
options = select_tag.find_all('option')
    
GROUPS = [option['value'] for option in options]

def parse_site(group) -> list:
    global cur_date, cur_time, cur_para, GROUPS
    data = f'group={parse.quote(f"{group}", encoding="windows-1251")}&stt=%CF%EE%EA%E0%E7%E0%F2%FC%21'
    schedule_page = requests.post('https://www.rksi.ru/mobile_schedule',
                                  headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=data)

    schedule_soup = str(BS(schedule_page.text, "html.parser")).replace(
        str(BS(schedule_page.text, "html.parser").find_all("form")[0]), "").replace(
        str(BS(schedule_page.text, "html.parser").find_all("form")[1]), "")
    cleared_sch = str(schedule_soup)[266:len(str(schedule_soup)) - 47]

    sch = BS(cleared_sch, "html.parser").get_text("||").split("||")
    schedule = [i for i in sch if sch.index(i) != 0 and i != ' ' and i != '\n']

    i = 1
    while i < len(schedule):
        if schedule[i][0].isnumeric() and schedule[i][-1].isalpha():
            dM = schedule[i].split(", ")[0].split(" ")
            month = MONTHES.index(dM[1]) + 1
            cur_date = f'{datetime.datetime.now().year}-{month if len(str(month)) == 2 else "0"+str(month)}-{dM[0] if len(str(dM[0]))==2 else f"0{dM[0]}"}'
            i += 1
        if schedule[i][0].isnumeric() and schedule[i][-1].isnumeric():
            cur_time = schedule[i].replace("  —  ", "-")
            i += 1
        if schedule[-1] != schedule[i] and schedule[i][0].isalpha() and schedule[i + 1][0].isalpha():
            cur_para = f'{schedule[i]}: {schedule[i + 1]}'
            i += 2
        elif schedule[-1] != schedule[i] and schedule[i][0].isalpha() and schedule[i - 1][0].isalpha():
            cur_para = f'{schedule[i - 1]}: {schedule[i]}'
            i += 3
        elif schedule[-1] != schedule[i] and schedule[i][0].isalpha() and not schedule[i + 1][0].isalpha():
            cur_para = f'{schedule[i]}'
            i += 1
        elif schedule[i][0].isalpha():
            cur_para = f'{schedule[i]}'
            i += 1
        if cur_para.__contains__("с/з"):
            cur_para = cur_para.replace(cur_para.split(" ")[-1], "с/з")
        elif cur_para.__contains__("-1") or cur_para.__contains__("-2"):
            cur_para = cur_para.replace("-1", "").replace("-2", "")
        yield [cur_date, cur_time, cur_para]


def sch_format(schedule: list, type: int) -> str:
    # получаем сегодняшнюю дату
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    today = today.strftime('%Y-%m-%d')
    tomorrow = tomorrow.strftime('%Y-%m-%d')

    formatted_schedule = ""
    date = ""
    prev_date = ""

    for para in schedule:
        date = para[0]
        if type == 0:
            if date == prev_date:
                formatted_schedule += f" {para[1]}\n  {para[2]}\n\n"
            else:   
                formatted_schedule += f"{date}\n {para[1]}\n  {para[2]}\n\n"
        elif type == 1 and date == today:
            if date == prev_date:
                formatted_schedule += f" {para[1]}\n  {para[2]}\n\n"
            else:   
                formatted_schedule += f"{date}\n {para[1]}\n  {para[2]}\n\n"
        elif type == 2 and date == tomorrow:
            if date == prev_date:
                formatted_schedule += f" {para[1]}\n  {para[2]}\n\n"
            else:   
                formatted_schedule += f"{date}\n {para[1]}\n  {para[2]}\n\n" 
        prev_date = date
    return formatted_schedule

def check_data(chat_id: int, user_id: int) -> None:
    userdata = storage.get_data(chat=chat_id, user=user_id)
    if userdata["group"] is None:
        storage.set_data(chat=chat_id, user=user_id, group="", state=None)
    else: pass

# Tekegram bot


class States(StatesGroup):
    group = State()


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await bot.send_message(message.chat.id, 'Привет, я бот. Напиши свою группу, чтобы получить расписание.')

# Обработчик нажатия на кнопку
@dp.message_handler()
async def button_handler(message: types.Message) -> None:
    data = process.extract(message.text, GROUPS, limit=1)
    group = data[0][0]
    percentage = data[0][1]
    if percentage > 75:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        States.group.set()
        btn_week = types.KeyboardButton('На всю неделю.')
        btn_today = types.KeyboardButton("На сегодня.")
        btn_tomorrow = types.KeyboardButton('На завтра.')

        markup.add(btn_week)
        markup.add(btn_today)
        markup.add(btn_tomorrow)
        
        await bot.send_message(message.chat.id, text=f"Принято! Работаю с группой {group}.\nВыберите нужную функцию: ", reply_markup=markup)
    else:
        await bot.send_message(message.chat.id, text="Такой группы нет.")
        # bot.send_message(message.chat.id, sch_format([*parse_site(GRP)]))
        # Отправляем переменную result в ответ на нажатие кнопкb


@bot.message_handler(state=States.group)
async def btn_handler(message: types.Message):
   if message.text == "На всю неделю.":
       await bot.send_message(chat_id=message.chat.id, text=sch_format([*parse_site(group=group)], 0))
       


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)