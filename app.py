import telebot
import requests
import time
from threading import Thread
from datetime import datetime, timedelta

# API token bot kamu
API_TOKEN = '7981292139:AAG6Sx0WhtjB6tdB3hN5iSO6koaCBiqrbjM'
bot = telebot.TeleBot(API_TOKEN)

# Fungsi untuk format angka ke format rupiah
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# Fungsi untuk mendapatkan harga Solana dalam USD dan IDR
def get_solana_price():
    try:
        url = 'https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd,idr'
        response = requests.get(url).json()
        if 'solana' in response:
            price_usd = response['solana']['usd']
            price_idr = response['solana']['idr']
            return price_usd, price_idr
        else:
            return None, None
    except requests.RequestException as e:
        print(f"Error while fetching Solana price: {e}")
        return None, None

# Variabel sementara untuk menyimpan input pengguna
user_data = {}

# Mulai bot dengan command /start
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Masukkan modal kamu:")
    bot.register_next_step_handler(message, get_modal)

# Fungsi untuk mendapatkan modal
def get_modal(message):
    try:
        chat_id = message.chat.id
        modal = float(message.text.replace(',', '').replace('Rp', ''))
        user_data[chat_id] = {'modal': modal}
        bot.send_message(chat_id, "Masukkan persentase yang kamu inginkan (contoh: 10 atau 10%):")
        bot.register_next_step_handler(message, get_persen)
    except ValueError:
        bot.send_message(message.chat.id, "Input tidak valid. Masukkan modal berupa angka.")
        bot.register_next_step_handler(message, get_modal)

# Fungsi untuk mendapatkan persentase
def get_persen(message):
    try:
        chat_id = message.chat.id
        persen_text = message.text.replace('%', '')
        persen = float(persen_text) / 100
        user_data[chat_id]['persen'] = persen
        bot.send_message(chat_id, "Berapa hari (contoh: 30) yang kamu inginkan untuk hitung hasil?")
        bot.register_next_step_handler(message, get_hari)
    except ValueError:
        bot.send_message(message.chat.id, "Input tidak valid. Masukkan persentase berupa angka.")
        bot.register_next_step_handler(message, get_persen)

# Fungsi untuk mendapatkan jumlah hari
def get_hari(message):
    try:
        chat_id = message.chat.id
        hari = int(message.text)
        user_data[chat_id]['hari'] = hari
        bot.send_message(chat_id, "Ketik 'mulai' untuk memulai perhitungan.")
        bot.register_next_step_handler(message, hitung_hasil)
    except ValueError:
        bot.send_message(message.chat.id, "Input tidak valid. Masukkan jumlah hari berupa angka.")
        bot.register_next_step_handler(message, get_hari)

# Fungsi untuk menghitung hasil setiap harinya
def hitung_hasil(message):
    if message.text.lower() == 'mulai':
        chat_id = message.chat.id
        modal = user_data[chat_id]['modal']
        persen = user_data[chat_id]['persen']
        hari = user_data[chat_id]['hari']
        
        hasil = modal
        tanggal_awal = datetime.now()
        hasil_list = []

        for i in range(hari):
            hasil_harian = hasil * persen
            total = hasil + hasil_harian
            tanggal = (tanggal_awal + timedelta(days=i)).strftime('%d/%m/%Y')
            hasil_rp = format_rupiah(hasil_harian)
            modal_rp = format_rupiah(hasil)
            hasil_list.append(f"{tanggal}: {modal_rp} x {persen * 100}% = {hasil_rp}")
            hasil = total

        bot.send_message(chat_id, "\n".join(hasil_list))
        bot.send_message(chat_id, "Ketik /start untuk memulai lagi ketik sol <angka>, RP <angka> dolar  <angka> unuk konversi.")
    else:
        bot.send_message(message.chat.id, "Ketik 'mulai' untuk memulai perhitungan.")
        bot.register_next_step_handler(message, hitung_hasil)

# Fungsi untuk konversi Solana, Rupiah, dan Dolar
@bot.message_handler(func=lambda message: True)
def converter(message):
    chat_id = message.chat.id
    text = message.text.lower()
    price_usd, price_idr = get_solana_price()

    if text.startswith('sol '):
        try:
            sol = float(text.split()[1])
            usd = sol * price_usd
            idr = sol * price_idr
            bot.send_message(chat_id, f"{sol} SOL = {format_rupiah(idr)} (IDR) | ${usd:.2f} (USD)")
        except ValueError:
            bot.send_message(chat_id, "Input tidak valid. Contoh: 'sol 1'")
    elif text.startswith('rp '):
        try:
            idr = float(text.replace('rp', '').replace(',', '').strip())
            sol = idr / price_idr
            usd = idr / price_usd
            bot.send_message(chat_id, f"Rp {format_rupiah(idr)} = {sol:.4f} SOL | ${usd:.2f} (USD)")
        except ValueError:
            bot.send_message(chat_id, "Input tidak valid. Contoh: 'RP 100000'")
    elif text.startswith('dolar '):
        try:
            usd = float(text.split()[1])
            sol = usd / price_usd
            idr = usd * price_idr
            bot.send_message(chat_id, f"${usd} = Rp {format_rupiah(idr)} | {sol:.4f} SOL")
        except ValueError:
            bot.send_message(chat_id, "Input tidak valid. Contoh: 'dolar 1'")
    else:
        bot.send_message(chat_id, "Ketik /start untuk memulai lagi ketik sol <angka>, RP <angka> dolar  <angka> unuk konversi..")

# Fungsi untuk update harga Solana setiap jam
def update_solana_price():
    while True:
        price_usd, price_idr = get_solana_price()
        now = datetime.now().strftime('%H:%M %d/%m/%Y')
        bot.send_message(935923063, f"Update harga Solana {now}:\n1 SOL = Rp {format_rupiah(price_idr)} | ${price_usd:.2f} (USD)")
        time.sleep(3600)  # Update setiap 1 jam

# Thread untuk update harga Solana setiap jam
thread = Thread(target=update_solana_price)
thread.start()

# Jalankan bot
bot.polling()
