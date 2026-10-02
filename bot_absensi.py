import os
import io
import re
import csv
import telebot
import logging
import sqlite3
import pytz
from datetime import datetime
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# 1. KONFIGURASI KEAMANAN & ENVIRONMENT (BUG FIXED)
# ==========================================
# Load variabel dari file .env (Jangan pernah hardcode Token di sini!)
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DEV_CHAT_ID = os.getenv("DEV_CHAT_ID")
MODE = os.getenv("MODE", "PROD")
MAINTENANCE = os.getenv("MAINTENANCE", "False").lower() == "true"

if not TOKEN:
    raise ValueError("FATAL ERROR: BOT_TOKEN tidak ditemukan di file .env!")

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
bot = telebot.TeleBot(TOKEN)
ZONA_WAKTU = pytz.timezone('Asia/Jakarta')
DB_FILE = 'database_testing.db' if MODE == "DEV" else 'database_absensi.db'

# ==========================================
# 2. AUTO-MIGRATION DATABASE
# ==========================================
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            user_id INTEGER PRIMARY KEY,
                            nama TEXT, divisi TEXT, shift TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS absensi (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER, tanggal DATE, status TEXT DEFAULT 'Hadir',
                            waktu_masuk DATETIME, waktu_pulang DATETIME,
                            mulai_lembur DATETIME, selesai_lembur DATETIME)''')
        conn.commit()
init_db()

# ==========================================
# 3. HELPER FUNCTION
# ==========================================
def get_now(): return datetime.now(ZONA_WAKTU)
def format_hari_indo(tgl_string):
    hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    dt = datetime.strptime(tgl_string, "%Y-%m-%d")
    return f"{hari_indo[dt.weekday()]}, {dt.strftime('%d-%m-%Y')}"
def jam_saja(dt_string): return dt_string.split(" ")[1][:5] if dt_string else "--:--"

def get_user(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        return conn.cursor().execute("SELECT nama, divisi, shift FROM users WHERE user_id = ?", (user_id,)).fetchone()

def get_open_session(user_id, tgl):
    with sqlite3.connect(DB_FILE) as conn:
        return conn.cursor().execute("SELECT * FROM absensi WHERE user_id = ? AND tanggal = ? ORDER BY id DESC LIMIT 1", (user_id, tgl)).fetchone()

# ==========================================
# 4. UI GENERATOR (NESTED MENUS)
# ==========================================
def get_markup(menu_type, user_id=None):
    markup = InlineKeyboardMarkup(row_width=2)
    
    if menu_type == "main":
        markup.add(
            InlineKeyboardButton("📝 Kehadiran", callback_data="menu_kehadiran"),
            InlineKeyboardButton("⏱ Lembur", callback_data="menu_lembur")
        )
        markup.add(
            InlineKeyboardButton("⚠️ Izin / Darurat", callback_data="menu_darurat"),
            InlineKeyboardButton("📊 Data & Laporan", callback_data="menu_laporan")
        )
        markup.add(InlineKeyboardButton("⚙️ Pengaturan", callback_data="menu_pengaturan"))
        if MODE == "DEV" and str(user_id) == str(DEV_CHAT_ID):
            markup.add(InlineKeyboardButton("☢️ Reset Sesi (Dev)", callback_data="dev_reset_sesi"))
            
    elif menu_type == "kehadiran":
        markup.add(InlineKeyboardButton("🟢 Absen Masuk", callback_data="action_masuk"))
        markup.add(InlineKeyboardButton("🔴 Absen Pulang (Sesuai Shift)", callback_data="action_pulang"))
        markup.add(InlineKeyboardButton("🔙 Beranda", callback_data="menu_main"))
        
    elif menu_type == "lembur":
        markup.add(
            InlineKeyboardButton("⏱ Mulai (Hari Kerja)", callback_data="action_lembur_kerja"),
            InlineKeyboardButton("🏖 Mulai (Hari Libur)", callback_data="action_lembur_libur")
        )
        markup.add(InlineKeyboardButton("🛑 Akhiri Lembur", callback_data="action_lembur_selesai"))
        markup.add(InlineKeyboardButton("🔙 Beranda", callback_data="menu_main"))
        
    elif menu_type == "darurat":
        markup.add(InlineKeyboardButton("🤧 Sakit (Full Day)", callback_data="action_sakit"))
        markup.add(InlineKeyboardButton("✈️ Izin (Full Day)", callback_data="action_izin"))
        markup.add(InlineKeyboardButton("🏃‍♂️ Pulang Mendadak (Awal)", callback_data="action_pulang_awal"))
        markup.add(InlineKeyboardButton("🔙 Beranda", callback_data="menu_main"))
        
    elif menu_type == "laporan":
        markup.add(InlineKeyboardButton("📜 Riwayat (30 Hari)", callback_data="action_riwayat"))
        markup.add(InlineKeyboardButton("📥 Ekspor Excel (.csv)", callback_data="action_csv"))
        markup.add(InlineKeyboardButton("🔙 Beranda", callback_data="menu_main"))
        
    elif menu_type == "pengaturan":
        markup.add(InlineKeyboardButton("🔄 Ubah Jam Shift", callback_data="action_ubah_shift"))
        markup.add(InlineKeyboardButton("🔙 Beranda", callback_data="menu_main"))
        
    return markup

def generate_teks_dashboard(user_id, status_pesan="", menu_aktif="MAIN MENU"):
    user = get_user(user_id)
    tgl_hari_ini = get_now().strftime("%Y-%m-%d")
    session = get_open_session(user_id, tgl_hari_ini)
    
    sts = session[3] if session else "Belum Absen"
    w_masuk = jam_saja(session[4]) if session else "--:--"
    w_pulang = jam_saja(session[5]) if session else "--:--"
    w_lm = jam_saja(session[6]) if session and session[6] else "--:--"
    
    teks = f"{status_pesan}\n\n" if status_pesan else ""
    teks += f"🪪 **{user[0].upper()}** | Shift: `{user[2]}`\n━━━━━━━━━━━━━━━━━━━━\n"
    
    if sts in ['Sakit', 'Izin']: 
        teks += f"📊 **STATUS:** ⚠️ {sts.upper()} SEHARIAN\n"
    elif sts == 'Lembur Libur':
        w_lp = jam_saja(session[7]) if session and session[7] else "Berjalan"
        teks += f"📊 **STATUS:** 🏖 LEMBUR HARI LIBUR\n⏱ Lembur : {w_lm} s/d {w_lp}\n"
    else:
        teks += f"📊 **STATUS:** {sts.upper()}\n🟢 Masuk  : {w_masuk}\n🔴 Pulang : {w_pulang}\n"
        if session and session[6]: 
            sts_l = "Berjalan" if not session[7] else jam_saja(session[7])
            teks += f"⏱ Lembur : {w_lm} s/d {sts_l}\n"
            
    teks += f"━━━━━━━━━━━━━━━━━━━━\n📍 Menu Aktif: **{menu_aktif}**"
    return teks

def ganti_menu(user_id, call_id, msg_id, menu_type, teks_notif="", judul_posisi="MAIN MENU"):
    bot.answer_callback_query(call_id) 
    teks = generate_teks_dashboard(user_id, teks_notif, judul_posisi)
    try:
        bot.edit_message_text(chat_id=user_id, message_id=msg_id, text=teks, reply_markup=get_markup(menu_type, user_id), parse_mode="Markdown")
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" not in str(e): logging.error(f"Error edit pesan: {e}")

# ==========================================
# 5. COMMANDS & STEP HANDLERS
# ==========================================
@bot.message_handler(commands=['start', 'absen'])
def menu_absen(message):
    user_id = message.from_user.id
    if MAINTENANCE and str(user_id) != str(DEV_CHAT_ID): return bot.reply_to(message, "🛠 Sistem sedang Maintenance. Kembali lagi nanti.")
    
    if message.text == '/start' and not get_user(user_id):
        msg = bot.reply_to(message, "✨ *Siapa nama panggilan Anda?*", parse_mode="Markdown")
        return bot.register_next_step_handler(msg, proses_nama)
    
    if not get_user(user_id): return bot.send_message(user_id, "⚠ Ketik /start terlebih dahulu.")
    bot.send_message(user_id, generate_teks_dashboard(user_id), reply_markup=get_markup("main", user_id), parse_mode="Markdown")

def proses_nama(message):
    user_id = message.from_user.id
    nama = message.text[:20] if message.text else "Tanpa Nama"
    msg = bot.send_message(user_id, f"Halo *{nama}*! Di Divisi apa Anda bekerja?", parse_mode="Markdown")
    bot.register_next_step_handler(msg, proses_divisi, nama)

def proses_divisi(message, nama):
    user_id = message.from_user.id
    divisi = message.text[:30] if message.text else "Staff"
    msg = bot.send_message(user_id, "⏰ *Ketik Jam Shift Anda dengan format HH:MM - HH:MM*\n_(Contoh wajib: 07:30 - 16:30)_", parse_mode="Markdown")
    bot.register_next_step_handler(msg, proses_shift, nama, divisi)

def proses_shift(message, nama, divisi):
    user_id = message.from_user.id
    shift = message.text.strip() if message.text else ""
    if not re.match(r'^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}$', shift):
        msg = bot.reply_to(message, "❌ Format salah! Harap gunakan format benar. Contoh: `07:30 - 16:30`\nSilakan ketik ulang:", parse_mode="Markdown")
        return bot.register_next_step_handler(msg, proses_shift, nama, divisi)

    with sqlite3.connect(DB_FILE) as conn:
        conn.cursor().execute("REPLACE INTO users (user_id, nama, divisi, shift) VALUES (?, ?, ?, ?)", (user_id, nama, divisi, shift))
        conn.commit()
    bot.send_message(user_id, "🎉 *PROFIL TERSIMPAN!* Ketik /absen untuk mulai bekerja.", parse_mode="Markdown")

def proses_ubah_shift(message):
    user_id = message.from_user.id
    shift = message.text.strip() if message.text else ""
    if not re.match(r'^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}$', shift):
        msg = bot.reply_to(message, "❌ Format salah! Contoh: `07:30 - 16:30`\nKetik ulang:")
        return bot.register_next_step_handler(msg, proses_ubah_shift)
    
    with sqlite3.connect(DB_FILE) as conn:
        conn.cursor().execute("UPDATE users SET shift = ? WHERE user_id = ?", (shift, user_id))
        conn.commit()
    
    bot.send_message(user_id, f"✅ *Shift Berhasil Diubah!*\nShift baru Anda: `{shift}`", parse_mode="Markdown")
    bot.send_message(user_id, generate_teks_dashboard(user_id, menu_aktif="MAIN MENU"), reply_markup=get_markup("main", user_id), parse_mode="Markdown")

# ==========================================
# 6. CALLBACK LOGIC (STATE MACHINE V6.0)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    if MAINTENANCE and str(user_id) != str(DEV_CHAT_ID): return bot.answer_callback_query(call.id, "🛠 Sistem Maintenance.", show_alert=True)
    
    user_data = get_user(user_id)
    if not user_data: return bot.answer_callback_query(call.id, "Ketik /start dulu!", show_alert=True)

    now = get_now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    tgl_hari_ini = now.strftime("%Y-%m-%d")
    session = get_open_session(user_id, tgl_hari_ini) 
    sts = session[3] if session else None

    if call.data.startswith("menu_"):
        judul = call.data.split("_")[1].upper() if call.data != "menu_main" else "MAIN MENU"
        return ganti_menu(user_id, call.id, call.message.message_id, call.data.split("_")[1], judul_posisi=judul)
        
    if call.data == "dev_reset_sesi" and MODE == "DEV":
        with sqlite3.connect(DB_FILE) as conn: conn.cursor().execute("DELETE FROM absensi WHERE user_id = ? AND tanggal = ?", (user_id, tgl_hari_ini))
        return ganti_menu(user_id, call.id, call.message.message_id, "main", "🧹 Data absen hari ini Dihapus (DEV).")

    # LOGIKA PENGATURAN (UBAH SHIFT)
    if call.data == "action_ubah_shift":
        msg = bot.send_message(user_id, "🔄 *Masukkan Jam Shift Baru Anda*\nFormat: HH:MM - HH:MM\n_(Contoh: 08:00 - 17:00)_", parse_mode="Markdown")
        bot.register_next_step_handler(msg, proses_ubah_shift)
        bot.delete_message(chat_id=user_id, message_id=call.message.message_id) # Hapus pesan menu lama agar rapi
        return bot.answer_callback_query(call.id)

    if sts in ['Sakit', 'Izin']:
        if call.data in ["action_masuk", "action_pulang", "action_lembur_kerja", "action_lembur_libur", "action_lembur_selesai", "action_pulang_awal"]:
            pesan = f"🚫 DITOLAK: Anda tidak bisa melakukan ini karena sudah melaporkan {sts.upper()} hari ini."
            return ganti_menu(user_id, call.id, call.message.message_id, "main", pesan, "MAIN MENU")

    pesan_notif = ""
    tipe_menu_kembali = "main"

    if call.data == "action_masuk":
        if session:
            if sts == 'Lembur Libur': pesan_notif = "⚠️ Sesi Anda hari ini adalah Lembur Hari Libur."
            elif session[6] and not session[7]: pesan_notif = "❌ Gagal: Sedang dalam sesi LEMBUR."
            else: pesan_notif = "⚠️ Anda sudah Absen Masuk hari ini."
        else:
            with sqlite3.connect(DB_FILE) as conn: conn.cursor().execute("INSERT INTO absensi (user_id, tanggal, waktu_masuk) VALUES (?, ?, ?)", (user_id, tgl_hari_ini, now_str))
            pesan_notif = "✅ **Masuk Berhasil!**"
        tipe_menu_kembali = "kehadiran"

    elif call.data == "action_pulang":
        if not session or not session[4]: pesan_notif = "❌ Anda belum Absen Masuk!"
        elif sts == 'Lembur Libur': pesan_notif = "❌ Gunakan tombol Akhiri Lembur."
        elif session[6] and not session[7]: pesan_notif = "❌ Gagal: Akhiri lembur Anda terlebih dahulu."
        elif session[5]: pesan_notif = "⚠️ Anda sudah absen pulang."
        else:
            shift_end_str = user_data[2].split('-')[1].strip() 
            shift_end_time = datetime.strptime(shift_end_str, "%H:%M").time()
            if now.time() < shift_end_time:
                return ganti_menu(user_id, call.id, call.message.message_id, "kehadiran", f"🚫 DITOLAK: Jam Shift Anda belum usai ({shift_end_str}). Gunakan Pulang Mendadak jika darurat.", "KEHADIRAN")
            
            with sqlite3.connect(DB_FILE) as conn: conn.cursor().execute("UPDATE absensi SET waktu_pulang = ? WHERE id = ?", (now_str, session[0]))
            pesan_notif = "✅ **Pulang Tercatat!**"
        tipe_menu_kembali = "kehadiran"

    elif call.data == "action_lembur_kerja":
        if not session or not session[4]: pesan_notif = "❌ Harus Absen Masuk terlebih dahulu."
        elif 'Pulang Darurat' in sts or 'Pulang Awal' in sts: pesan_notif = "❌ Tercatat Pulang Darurat, tidak bisa lanjut lembur."
        elif session[6]: pesan_notif = "⚠️ Sesi lembur sudah direkam."
        else:
            with sqlite3.connect(DB_FILE) as conn: conn.cursor().execute("UPDATE absensi SET mulai_lembur = ? WHERE id = ?", (now_str, session[0]))
            pesan_notif = "⏱️ **Lembur (Hari Kerja) Dimulai!**"
        tipe_menu_kembali = "lembur"

    elif call.data == "action_lembur_libur":
        if session and 'Lembur Libur' not in sts: pesan_notif = "❌ Anda memiliki sesi masuk reguler hari ini."
        elif session and 'Lembur Libur' in sts: pesan_notif = "⚠️ Lembur Libur sudah dicatat."
        else:
            with sqlite3.connect(DB_FILE) as conn: conn.cursor().execute("INSERT INTO absensi (user_id, tanggal, status, mulai_lembur) VALUES (?, ?, 'Lembur Libur', ?)", (user_id, tgl_hari_ini, now_str))
            pesan_notif = "🏖 **Lembur Hari Libur Dimulai!**"
        tipe_menu_kembali = "lembur"

    elif call.data == "action_lembur_selesai":
        if not session or not session[6]: pesan_notif = "❌ Belum ada lembur."
        elif session[7]: pesan_notif = "⚠️ Lembur sudah diakhiri."
        else:
            with sqlite3.connect(DB_FILE) as conn:
                if sts == 'Lembur Libur' or not session[5]: conn.cursor().execute("UPDATE absensi SET selesai_lembur = ?, waktu_pulang = ? WHERE id = ?", (now_str, now_str, session[0]))
                else: conn.cursor().execute("UPDATE absensi SET selesai_lembur = ? WHERE id = ?", (now_str, session[0]))
            pesan_notif = "✅ **Lembur Diselesaikan!**"
        tipe_menu_kembali = "lembur"

    elif call.data == "action_pulang_awal":
        if not session: pesan_notif = "❌ Belum ada sesi bekerja."
        elif not session[4] and sts != 'Lembur Libur': pesan_notif = "❌ Anda belum absen Masuk."
        elif session[5] or (sts == 'Lembur Libur' and session[7]): pesan_notif = "⚠ Sudah tercatat pulang."
        else:
            with sqlite3.connect(DB_FILE) as conn:
                if sts == 'Lembur Libur': conn.cursor().execute("UPDATE absensi SET waktu_pulang = ?, selesai_lembur = ?, status = 'Lembur Libur (Pulang Darurat)' WHERE id = ?", (now_str, now_str, session[0]))
                elif session[6] and not session[7]: conn.cursor().execute("UPDATE absensi SET waktu_pulang = ?, selesai_lembur = ?, status = 'Hadir (Pulang Darurat)' WHERE id = ?", (now_str, now_str, session[0]))
                else: conn.cursor().execute("UPDATE absensi SET waktu_pulang = ?, status = 'Hadir (Pulang Darurat)' WHERE id = ?", (now_str, session[0]))
            pesan_notif = "🏃‍♂️ **Pulang Darurat Tersimpan!**"
        tipe_menu_kembali = "darurat"

    elif call.data in ["action_izin", "action_sakit"]:
        sts_lapor = "Izin" if call.data == "action_izin" else "Sakit"
        if session: pesan_notif = "❌ DITOLAK: Ada rekam data hari ini."
        else:
            with sqlite3.connect(DB_FILE) as conn: conn.cursor().execute("INSERT INTO absensi (user_id, tanggal, status) VALUES (?, ?, ?)", (user_id, tgl_hari_ini, sts_lapor))
            pesan_notif = f"✅ **Laporan {sts_lapor} Tercatat!**"
        tipe_menu_kembali = "darurat"

    elif call.data == "action_riwayat":
        with sqlite3.connect(DB_FILE) as conn: rows = conn.cursor().execute("SELECT tanggal, status, waktu_masuk, waktu_pulang FROM absensi WHERE user_id = ? ORDER BY id DESC LIMIT 30", (user_id,)).fetchall()
        teks = "📜 **RIWAYAT 30 HARI TERAKHIR**\n━━━━━━━━━━━━━━━━━━━━\n"
        if not rows: teks += "Belum ada rekam jejak.\n"
        else:
            for r in rows:
                if r[1] in ['Sakit', 'Izin']: teks += f"🗓 {format_hari_indo(r[0])} | ⚠ {r[1].upper()}\n"
                elif 'Lembur Libur' in r[1]: teks += f"🗓 {format_hari_indo(r[0])} | 🏖 {r[1].upper()}\n"
                else: teks += f"🗓 {format_hari_indo(r[0])} | 🟢 {jam_saja(r[2])} - 🔴 {jam_saja(r[3])}\n"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Kembali", callback_data="menu_laporan"))
        bot.answer_callback_query(call.id)
        return bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=teks, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "action_csv":
        bot.answer_callback_query(call.id, "Mengalkulasi CSV...")
        with sqlite3.connect(DB_FILE) as conn: rows = conn.cursor().execute("SELECT tanggal, status, waktu_masuk, waktu_pulang, mulai_lembur, selesai_lembur FROM absensi WHERE user_id = ? ORDER BY tanggal ASC", (user_id,)).fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Hari & Tanggal', 'Nama', 'Divisi', 'Status', 'Masuk', 'Pulang', 'Mulai Lembur', 'Selesai Lembur'])
        
        th = ti = ts = tl_detik = 0
        for r in rows:
            writer.writerow([format_hari_indo(r[0]), user_data[0], user_data[1], r[1], jam_saja(r[2]), jam_saja(r[3]), jam_saja(r[4]), jam_saja(r[5])])
            if 'Hadir' in r[1] or 'Lembur Libur' in r[1]: th += 1
            elif r[1] == 'Izin': ti += 1
            elif r[1] == 'Sakit': ts += 1
            if r[4] and r[5]:
                d1, d2 = datetime.strptime(r[4], "%Y-%m-%d %H:%M:%S"), datetime.strptime(r[5], "%Y-%m-%d %H:%M:%S")
                if (d2 - d1).total_seconds() > 0: tl_detik += (d2 - d1).total_seconds()
                
        writer.writerows([[], ['=== REKAPAN ==='], ['Kehadiran Aktif', f'{th} Hari'], ['Sakit', f'{ts} Hari'], ['Izin', f'{ti} Hari'], ['Total Lembur', f'{int(tl_detik // 3600)} Jam {int((tl_detik % 3600) // 60)} Menit']])
        bot.send_document(chat_id=user_id, document=(f"Rekap_{user_data[0]}_{tgl_hari_ini}.csv", output.getvalue().encode('utf-8')))
        return ganti_menu(user_id, call.id, call.message.message_id, "laporan", "✅ File Excel berhasil dikirim.", "DATA & LAPORAN")

    if pesan_notif: ganti_menu(user_id, call.id, call.message.message_id, tipe_menu_kembali, pesan_notif, tipe_menu_kembali.upper().replace("_", " "))

if __name__ == "__main__":
    print("V6.0: Open Source Ready - Bot Aktif")
    bot.infinity_polling()