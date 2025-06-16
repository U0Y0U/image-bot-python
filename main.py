import os
import telebot
from telebot import types
from datetime import datetime

botToken = "7079073146:AAGT4kC-hn4uPfYXnqT0BjoOvyTD2sm-_MQ"
bot = telebot.TeleBot(botToken)

baseFolderPath = "./folders"
userSelectedFolder = {}
userPage = {}

pageSize = 5

def getFolders():
    return [f for f in os.listdir(baseFolderPath) if os.path.isdir(os.path.join(baseFolderPath, f))]

def sendFolderButtons(chatId, messageId, userId, page=0):
    folders = getFolders()
    totalPages = (len(folders) + pageSize - 1) // pageSize
    page = max(0, min(page, totalPages - 1))
    userPage[userId] = page

    start = page * pageSize
    end = start + pageSize
    currentFolders = folders[start:end]

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for folder in currentFolders:
        keyboard.add(types.InlineKeyboardButton(folder, callback_data=f"folder_{folder}"))

    navButtons = []
    if page > 0:
        navButtons.append(types.InlineKeyboardButton("⬅️ Назад", callback_data="pagePrev"))
    if page < totalPages - 1:
        navButtons.append(types.InlineKeyboardButton("Вперёд ➡️", callback_data="pageNext"))
    if navButtons:
        keyboard.row(*navButtons)

    text = f"Выберите папку (страница {page + 1} из {totalPages}):"
    if messageId:
        bot.edit_message_text(chat_id=chatId, message_id=messageId, text=text, reply_markup=keyboard)
    else:
        bot.send_message(chatId, text, reply_markup=keyboard)

def sendPhotoModeButtons(chatId, messageId, folder):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("Завершить", callback_data="actionFinish"),
        types.InlineKeyboardButton("Отмена", callback_data="actionCancel")
    )
    text = f"Отправляйте фото в папку: {folder}\nКогда закончите, нажмите «Завершить»."
    if messageId:
        bot.edit_message_text(chat_id=chatId, message_id=messageId, text=text, reply_markup=keyboard)
    else:
        bot.send_message(chatId, text, reply_markup=keyboard)

@bot.message_handler(commands=["start"])
def startHandler(message):
    sendFolderButtons(message.chat.id, None, message.from_user.id, 0)

@bot.callback_query_handler(func=lambda call: True)
def callbackHandler(call):
    userId = call.from_user.id
    data = call.data
    chatId = call.message.chat.id
    messageId = call.message.message_id

    if data == "pagePrev":
        sendFolderButtons(chatId, messageId, userId, userPage.get(userId, 0) - 1)
        bot.answer_callback_query(call.id)
    elif data == "pageNext":
        sendFolderButtons(chatId, messageId, userId, userPage.get(userId, 0) + 1)
        bot.answer_callback_query(call.id)
    elif data.startswith("folder_"):
        folder = data[len("folder_"):]
        userSelectedFolder[userId] = folder
        userPage.pop(userId, None)
        bot.answer_callback_query(call.id, f"Папка выбрана: {folder}")
        sendPhotoModeButtons(chatId, messageId, folder)
    elif data == "actionCancel":
        userSelectedFolder.pop(userId, None)
        sendFolderButtons(chatId, messageId, userId, 0)
        bot.answer_callback_query(call.id, "Возврат к выбору папки")
    elif data == "actionFinish":
        userSelectedFolder.pop(userId, None)
        sendFolderButtons(chatId, messageId, userId, 0)
        bot.answer_callback_query(call.id, "Загрузка фото завершена. Возврат в меню.")

@bot.message_handler(content_types=['photo'])
def photoHandler(message):
    userId = message.from_user.id
    folder = userSelectedFolder.get(userId)
    if not folder:
        bot.send_message(message.chat.id, "Пожалуйста, выберите папку с помощью /start.")
        return

    dateFolder = datetime.now().strftime("%Y-%m-%d")
    folderPath = os.path.join(baseFolderPath, folder, dateFolder)
    os.makedirs(folderPath, exist_ok=True)

    photo = message.photo[-1]
    fileInfo = bot.get_file(photo.file_id)
    photoData = bot.download_file(fileInfo.file_path)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#    username = message.from_user.username or message.from_user.first_name or "unknown"
    fileName = f"{timestamp}_{folder}.jpg"
    fullPath = os.path.join(folderPath, fileName)

    with open(fullPath, "wb") as f:
        f.write(photoData)

    bot.send_message(message.chat.id, f"Фото сохранено как:\n📁 {fileName}", parse_mode="Markdown")

bot.polling()