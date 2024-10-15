import telebot
import requests
import time
from threading import Thread
from datetime import datetime, timedelta
import schedule
import time

# API token bot kamu
API_TOKEN = '7981292139:AAG6Sx0WhtjB6tdB3hN5iSO6koaCBiqrbjM'
bot = telebot.TeleBot(API_TOKEN)

# Menyimpan token yang sudah diproses sebelumnya
previous_tokens = set()

# Fungsi untuk format angka ke format rupiah
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# Fungsi untuk mendapatkan harga Solana dalam USD, IDR, dan kurs USD ke IDR
def get_prices():
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=solana,usd&vs_currencies=usd,idr'
    response = requests.get(url).json()
    
    price_usd = response['solana']['usd']  # Harga 1 SOL dalam USD
    price_idr = response['solana']['idr']  # Harga 1 SOL dalam IDR
    usd_to_idr = response['usd']['idr']    # Kurs USD ke IDR (Rupiah)

    return price_usd, price_idr, usd_to_idr

# Fungsi untuk menghitung trading plan
@bot.message_handler(commands=['trading_plan'])
def ask_modal(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Berapa modal kamu sekarang? (Contoh: '1000 dolar', '5 sol', '1000000 rupiah')")
    bot.register_next_step_handler(message, get_modal_for_plan)

def get_modal_for_plan(message):
    chat_id = message.chat.id
    text = message.text.lower()

    # Ambil harga SOL dan kurs
    price_usd_sol, price_idr_sol, usd_to_idr = get_prices()

    # Deteksi mata uang yang diinput oleh pengguna
    try:
        if "dolar" in text:
            modal = float(text.split()[0])
            mata_uang = "USD"
        elif "sol" in text:
            modal = float(text.split()[0])
            modal = modal * price_usd_sol  # Konversi SOL ke USD
            mata_uang = "SOL"
        elif "rupiah" in text:
            modal = float(text.split()[0])
            modal = modal / usd_to_idr  # Konversi Rupiah ke USD
            mata_uang = "Rupiah"
        else:
            bot.send_message(chat_id, "Mohon masukkan mata uang yang valid (dolar, sol, rupiah).")
            return
    except ValueError:
        bot.send_message(chat_id, "Input tidak valid. Masukkan modal dalam format angka diikuti mata uang.")
        return

    # Simpan modal ke dalam data sementara
    user_data[chat_id] = {'modal': modal, 'mata_uang': mata_uang}

    # Tanyakan berapa persen modal yang akan digunakan
    bot.send_message(chat_id, "Mau pakai berapa persen dari modal untuk transaksi? (Contoh: 30 atau 30%)")
    bot.register_next_step_handler(message, get_persen_for_plan)

def get_persen_for_plan(message):
    chat_id = message.chat.id
    text = message.text.lower()

    # Mengambil persentase dari input, baik ada simbol persen atau tidak
    try:
        persen = float(text.replace('%', '')) / 100  # Menghilangkan simbol '%' jika ada
    except ValueError:
        bot.send_message(chat_id, "Input tidak valid. Masukkan persentase sebagai angka (contoh: 30 atau 30%).")
        return

    # Simpan persentase ke dalam data sementara
    user_data[chat_id]['persen'] = persen

    # Tanyakan berapa persen profit harian yang diinginkan
    bot.send_message(chat_id, "Mau profit berapa persen sehari? (Contoh: 20 atau 20%)")
    bot.register_next_step_handler(message, get_profit_harian)

def get_profit_harian(message):
    chat_id = message.chat.id
    text = message.text.lower()

    try:
        # Menghilangkan simbol % jika ada dan ubah menjadi float
        profit_harian = float(text.replace('%', '').strip()) / 100
    except ValueError:
        bot.send_message(chat_id, "Input tidak valid. Masukkan persentase profit sebagai angka (contoh: 20 atau 20%).")
        bot.register_next_step_handler(message, get_profit_harian)
        return

    # Simpan profit harian ke dalam data sementara
    user_data[chat_id]['profit_harian'] = profit_harian

    # Lanjutkan perhitungan dan tampilkan hasil
    calculate_and_send_plan(chat_id)


    
def calculate_and_send_plan(chat_id):
    # Ambil data modal, persen, dan profit harian dari user_data
    modal = user_data[chat_id]['modal']
    persen = user_data[chat_id]['persen']
    profit_harian = user_data[chat_id]['profit_harian']

    # Hitung transaksi berdasarkan persentase dari modal
    transaksi = modal * persen

    # Hitung target profit harian
    target_profit_harian = modal * profit_harian

    # Hitung profit per transaksi (misalnya 20% per transaksi)
    profit_per_transaksi = transaksi * 0.20

    # Hitung jumlah transaksi yang harus dilakukan untuk mencapai target harian
    jumlah_transaksi = target_profit_harian / profit_per_transaksi

    # Ambil harga SOL dan kurs untuk konversi
    price_usd_sol, price_idr_sol, usd_to_idr = get_prices()

    # Format hasil dalam bentuk tabel ASCII
    transaksi_rp = transaksi * usd_to_idr
    profit_harian_rp = target_profit_harian * usd_to_idr
    profit_per_transaksi_rp = profit_per_transaksi * usd_to_idr

    tabel = (
        f"┌{'-'*44}┐\n"
        f"│ {'Deskripsi':<30}│ {'Nilai':<12}│\n"
        f"├{'-'*44}┤\n"
        f"│ Transaksi untuk Trading      │ Rp {format_rupiah(transaksi_rp):<10} │\n"
        f"│ Target Profit Harian         │ Rp {format_rupiah(profit_harian_rp):<10} │\n"
        f"│ Profit per Transaksi (20%)   │ Rp {format_rupiah(profit_per_transaksi_rp):<10} │\n"
        f"│ Jumlah Transaksi             │ {jumlah_transaksi:.2f} kali   │\n"
        f"└{'-'*44}┘"
    )

    # Kirim pesan menggunakan format teks
    bot.send_message(chat_id, f"<b>Hasil Trading Plan:</b>\n{tabel}", parse_mode='HTML')


# Fungsi untuk mengirim token trending ke bot Telegram
def send_trending_tokens():
    global previous_tokens
    tokens = get_trending_tokens()
    new_tokens = set()

    message = "Token yang baru diperdagangkan di DexScreener:\n\n"
    send_message = False  # Flag untuk mengirim pesan hanya jika ada token baru

    for token in tokens:
        name = token['baseToken']['name']
        price_usd = token['priceUsd']
        volume_24h = token['volume']['h24']
        
        token_id = f"{name}-{price_usd}-{volume_24h}"  # Buat ID unik token berdasarkan name, price, dan volume
        
        new_tokens.add(token_id)
        
        if token_id not in previous_tokens:  # Token baru atau yang diperbarui
            send_message = True
            message += f"Nama: {name}\nHarga: ${price_usd}\nVolume 24H: {volume_24h}\n\n"
    
    if send_message:  # Kirim pesan hanya jika ada token baru atau diperbarui
        bot.send_message(chat_id="935923063", text=message)

    # Perbarui token sebelumnya dengan token yang baru
    previous_tokens = new_tokens

def send_tutorial(chat_id):
    tutorial_message = (
        "📖 <b>Tutorial Lengkap:</b>\n\n"
        "1️⃣ Ketik /start untuk memulai bot dan ikuti instruksi.\n"
        "2️⃣ Gunakan perintah /trading_plan untuk memulai rencana trading.\n"
        "3️⃣ Ikuti instruksi untuk memasukkan modal, persentase, dan target profit harian.\n"
        "4️⃣ Setelah itu, bot akan menghitung target transaksi harian dan jumlah transaksi yang perlu dilakukan.\n\n"
        "💡 <b>Contoh:</b>\n"
        "- Ketik: '1000 dolar' untuk modal.\n"
        "- Ketik: '30' atau '30%' untuk persentase modal per transaksi.\n"
        "- Ketik: '20' atau '20%' untuk profit harian.\n\n"
        "Untuk informasi lebih lanjut, jangan ragu bertanya!"
    )
    bot.send_message(chat_id, tutorial_message, parse_mode='HTML')

@bot.message_handler(func=lambda message: True)
def handle_input(message):
    chat_id = message.chat.id
    text = message.text.lower()

    # Deteksi perintah salah atau input yang tidak valid
    if text not in ['start', 'trading_plan', 'dolar', 'sol', 'rp']:
        bot.send_message(chat_id, "Maaf, perintah tidak dikenal. Berikut adalah tutorial penggunaan bot:")
        send_tutorial(chat_id)
    else:
        # Proses input yang valid (seperti sebelumnya)
        converter(message)     

# Thread untuk menjalankan penjadwalan
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Mulai thread penjadwalan
thread = Thread(target=run_schedule)
thread.start()

# Fungsi untuk format angka ke format rupiah
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# Fungsi untuk mendapatkan harga Solana dalam USD, IDR, dan kurs USD ke IDR
def get_prices():
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=solana,usd&vs_currencies=usd,idr'
    response = requests.get(url).json()
    
    price_usd = response['solana']['usd']  # Harga 1 SOL dalam USD
    price_idr = response['solana']['idr']  # Harga 1 SOL dalam IDR
    usd_to_idr = response['usd']['idr']    # Kurs USD ke IDR (Rupiah)

    return price_usd, price_idr, usd_to_idr


# Fungsi untuk mendapatkan lokasi IP pengguna
def get_wifi_info():
    response = requests.get('https://ipinfo.io')
    data = response.json()
    ip = data.get('ip', 'Tidak diketahui')
    city = data.get('city', 'Tidak diketahui')
    region = data.get('region', 'Tidak diketahui')
    return f"IP: {ip}\nKota: {city}\nWilayah: {region}"    

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
        bot.send_message(chat_id, "Input tidak valid. Masukkan persentase berupa angka.")
        bot.register_next_step_handler(message, get_persen)

# Fungsi untuk mendapatkan jumlah hari
def get_hari(message):
    try:
        chat_id = message.chat.id
        hari = int(message.text)
        user_data[chat_id]['hari'] = hari
        
        # Menanyakan apakah data sudah benar
        modal = user_data[chat_id]['modal']
        persen = user_data[chat_id]['persen'] * 100
        bot.send_message(chat_id, f"Modal: Rp {format_rupiah(modal)}\nPersentase: {persen}%\nHari: {hari}\n\nApakah sudah benar? (Ketik 'Ya' atau 'Tidak')")
        bot.register_next_step_handler(message, konfirmasi_data)
    except ValueError:
        bot.send_message(chat_id, "Input tidak valid. Masukkan jumlah hari berupa angka.")
        bot.register_next_step_handler(message, get_hari)

# Fungsi untuk konfirmasi data sebelum hitung hasil
def konfirmasi_data(message):
    chat_id = message.chat.id
    if message.text.lower() == 'ya':
        # Jika data sudah benar, lanjut ke perhitungan
        hitung_hasil(message)
    elif message.text.lower() == 'tidak':
        # Jika data salah, mulai ulang
        bot.send_message(chat_id, "Mari kita mulai dari awal.")
        start(message)
    else:
        # Jika input tidak sesuai, tanyakan lagi
        bot.send_message(chat_id, "Mohon ketik 'Ya' atau 'Tidak'.")
        bot.register_next_step_handler(message, konfirmasi_data)

# Fungsi untuk menghitung hasil setiap harinya
def hitung_hasil(message):
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
        hasil_list.append(f"{i+1}. {tanggal}: {modal_rp} x {persen * 100}% = {hasil_rp}")
        hasil = total

    bot.send_message(chat_id, "\n".join(hasil_list))
    bot.send_message(chat_id, "Ketik /start untuk memulai lagi ketik sol <angka>, RP <angka>, dolar <angka> untuk konversi.")

# Fungsi untuk konversi Solana, Rupiah, dan Dolar
@bot.message_handler(func=lambda message: True)
def converter(message):
    chat_id = message.chat.id
    text = message.text.lower()
    
    # Ambil harga terbaru
    price_usd_sol, price_idr_sol, usd_to_idr = get_prices()

    if text.startswith('dolar '):
        try:
            usd = float(text.split()[1])
            # Konversi dari USD ke IDR
            idr = usd * usd_to_idr
            # Konversi dari USD ke SOL
            sol = usd / price_usd_sol
            # Kirim hasil konversi
            bot.send_message(chat_id, f"${usd} = {format_rupiah(idr)} (IDR) | {sol:.4f} SOL")
        except ValueError:
            bot.send_message(chat_id, "Input tidak valid. Contoh: 'dolar 1'")
    
    elif text.startswith('sol '):
        try:
            sol = float(text.split()[1])
            # Konversi dari SOL ke IDR
            idr = sol * price_idr_sol
            # Konversi dari SOL ke USD
            usd = sol * price_usd_sol
            # Kirim hasil konversi
            bot.send_message(chat_id, f"{sol} SOL = {format_rupiah(idr)} (IDR) | ${usd:.2f} (USD)")
        except ValueError:
            bot.send_message(chat_id, "Input tidak valid. Contoh: 'sol 1'")
    
    elif text.startswith('rp '):
        try:
            idr = float(text.replace('rp', '').replace(',', '').strip())
            # Konversi dari IDR ke SOL
            sol = idr / price_idr_sol
            # Konversi dari IDR ke USD
            usd = idr / usd_to_idr
            # Kirim hasil konversi
            bot.send_message(chat_id, f"Rp {format_rupiah(idr)} = {sol:.4f} SOL | ${usd:.2f} (USD)")
        except ValueError:
            bot.send_message(chat_id, "Input tidak valid. Contoh: 'rp 100000'")
    
    else:
        bot.send_message(chat_id, "Ketik sol <angka>, RP <angka>, atau dolar <angka> untuk konversi.")

# Fungsi untuk update harga Solana setiap jam
def update_solana_price():
    while True:
        price_usd, price_idr, usd_to_idr = get_prices()
        now = datetime.now().strftime('%H:%M %d/%m/%Y')
        bot.send_message(935923063, f"Update harga Solana {now}:\n1 SOL = Rp {format_rupiah(price_idr)} | ${price_usd:.2f} (USD)\nKurs USD: Rp {format_rupiah(usd_to_idr)}")
        time.sleep(3600)  # Update setiap 1 jam

# Thread untuk update harga Solana setiap jam
thread = Thread(target=update_solana_price)
thread.start()

# Jalankan bot
bot.polling()
