#!/usr/bin/env python3
# Telegram OSINT Bot – збирає дані за ім'ям користувача
# Команди: /start, /search <username>

import logging
import re
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
from bs4 import BeautifulSoup
import instaloader
import phonenumbers
from phonenumbers import carrier, geocoder, timezone

# ===== НАЛАШТУВАННЯ =====
TELEGRAM_TOKEN = "8510013282:AAEpzr8v3YUt4c_vtZB7p9RSi3Edc_jl_NY"
# =========================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def search_google(username):
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://www.google.com/search?q={username}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        links = []
        for g in soup.find_all('div', class_='r'):
            a = g.find('a')
            if a:
                links.append(a.get('href'))
        return links[:5]
    except:
        return []

def check_instagram(username):
    L = instaloader.Instaloader()
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        info = {
            'full_name': profile.full_name,
            'bio': profile.biography,
            'followers': profile.followers,
            'following': profile.followees,
            'posts': profile.mediacount,
            'is_private': profile.is_private,
            'external_url': profile.external_url,
        }
        return info
    except:
        return None

def check_phone_number(username):
    digits = re.sub(r'\D', '', username)
    if 10 <= len(digits) <= 15:
        try:
            num = phonenumbers.parse("+" + digits, None)
            if phonenumbers.is_valid_number(num):
                info = {
                    'country': geocoder.description_for_number(num, 'en'),
                    'carrier': carrier.name_for_number(num, 'en'),
                    'timezone': ', '.join(timezone.time_zones_for_number(num))
                }
                return info
        except:
            pass
    return None

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Надішли /search <ім'я користувача>, щоб знайти інформацію.")

def search(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Вкажи ім'я. Наприклад: /search johndoe")
        return
    username = ' '.join(context.args)
    update.message.reply_text(f"Шукаю `{username}`... зачекай хвилинку.", parse_mode=ParseMode.MARKDOWN)

    results = []

    # Google
    google_links = search_google(username)
    if google_links:
        results.append("*Google:*\n" + "\n".join(google_links))

    # Instagram
    insta = check_instagram(username)
    if insta:
        insta_text = f"*Instagram:*\nІм'я: {insta['full_name']}\nБіо: {insta['bio']}\nПідписники: {insta['followers']}\nПідписки: {insta['following']}\nПости: {insta['posts']}\nПриватний: {insta['is_private']}\nЗовнішнє посилання: {insta['external_url']}"
        results.append(insta_text)

    # Phone
    phone = check_phone_number(username)
    if phone:
        phone_text = f"*Телефон:*\nКраїна: {phone['country']}\nОператор: {phone['carrier']}\nЧасовий пояс: {phone['timezone']}"
        results.append(phone_text)

    if not results:
        update.message.reply_text("Нічого не знайдено.")
    else:
        full = "\n\n".join(results)
        if len(full) <= 4096:
            update.message.reply_text(full, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        else:
            for i in range(0, len(full), 4096):
                update.message.reply_text(full[i:i+4096], parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("search", search))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
