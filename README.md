
---

```markdown
# 🤖 Telegram Bot Absensi & Lembur (Open Source)

Selamat datang di *repository* **Telegram Bot Absensi & Lembur**! 
Bot ini dirancang menggunakan Python (`pyTelegramBotAPI`) dan SQLite untuk membantu manajemen absensi karyawan, pencatatan lembur, dan pengajuan izin secara otomatis dan praktis langsung melalui Telegram.

---

## ✨ Fitur Utama

- **🟢 Absensi Masuk & Pulang Real-time:** Mencatat jam kehadiran karyawan yang disesuaikan dengan jam shift mereka.
- **🔄 Rolling Shift Mandiri:** Karyawan dapat mengubah atau me-rolling jam shift mereka sendiri secara mandiri melalui menu Pengaturan.
- **⏱️ Manajemen Lembur Dinamis:** Perhitungan otomatis untuk **Lembur di Hari Kerja** dan **Lembur di Hari Libur**.
- **⚠️ Sistem Keadaan Darurat & Izin:** Fitur khusus untuk "Pulang Mendadak" saat jam kerja/lembur berlangsung, serta fitur pelaporan Sakit/Izin *Full Day*.
- **📊 Ekspor Laporan CSV:** Menghasilkan rekap absensi dan total jam lembur dalam format `.csv` (Excel-ready) yang bisa diunduh kapan saja oleh Admin/Developer.
- **🔒 Keamanan Data:** Menggunakan file `.env` untuk mengamankan Token Bot Telegram agar tidak bocor. Database menggunakan SQLite lokal.

---

## 📂 Struktur Folder
```text
bot-absensi/
├── bot_absensi.py       # Script utama bot Telegram
├── .env                 # File konfigurasi token (tidak di-upload ke GitHub)
├── .gitignore           # Aturan mengabaikan file tertentu oleh Git
├── database_absensi.db  # File database utama SQLite (Dibuat otomatis)
├── database_testing.db  # File database untuk keperluan testing
└── README.md            # Dokumentasi project ini

```

---

## 🛠️ Persyaratan Sistem

Sebelum menjalankan bot ini, pastikan Anda telah menginstal:

1. **Python 3.8+** (https://www.python.org/downloads/)
2. **Git** (https://git-scm.com/)
3. **Token Bot Telegram** (Dapatkan dari [@BotFather](https://t.me/BotFather) di Telegram).

---

## 🚀 Cara Pemasangan & Konfigurasi (Lokal)

**1. Clone Repository**
Buka terminal/PowerShell Anda, lalu jalankan:

```bash
git clone [https://github.com/TestwayWeb3/bot-absensi.git](https://github.com/TestwayWeb3/bot-absensi.git)
cd bot-absensi

```

**2. Instalasi Dependensi**
Instal *library* Python yang dibutuhkan dengan menjalankan perintah berikut:

```bash
pip install pyTelegramBotAPI python-dotenv pytz

```

**3. Konfigurasi Kredensial (`.env`)**
Buat sebuah file baru bernama `.env` di dalam folder utama project ini. Isi file tersebut dengan format berikut:

```env
BOT_TOKEN=MASUKKAN_TOKEN_BOT_ANDA_DISINI
DEV_CHAT_ID=MASUKKAN_ID_TELEGRAM_DEVELOPER_DISINI
MODE=PROD
MAINTENANCE=False

```

*(File ini sudah didaftarkan ke dalam `.gitignore` sehingga aman dan tidak akan ter-upload ke publik).*

**4. Jalankan Bot**
Setelah konfigurasi selesai, jalankan bot dengan perintah:

```bash
python bot_absensi.py

```

*(Database `database_absensi.db` akan langsung dibuat otomatis jika belum ada).*
Buka aplikasi Telegram Anda, cari bot Anda, lalu ketik `/start`.

---

## 🌐 Tips Deployment 24/7 (VPS / Server)

Agar bot absensi ini selalu online tanpa harus menyalakan komputer terus-menerus, Anda bisa menjalankannya di VPS (Virtual Private Server) berbasis Linux.

Anda bisa menggunakan perintah `nohup` untuk menjalankannya di latar belakang (*background*):

```bash
nohup python3 bot_absensi.py > bot.log 2>&1 &

```

Atau menggunakan *process manager* seperti **PM2** atau **Systemd** agar bot otomatis *restart* saat server *reboot*.

---

## 🤝 Berkontribusi (Contributing)

Proyek ini bersifat *Open Source*. Jika Anda ingin menambahkan fitur, memperbaiki *bug*, atau melakukan *refactoring* kode, Anda sangat dipersilakan!

1. Lakukan *Fork* pada *repository* ini.
2. Buat *branch* untuk fitur baru Anda (`git checkout -b fitur-baru`).
3. Lakukan *Commit* (`git commit -m 'Menambahkan fitur XYZ'`).
4. *Push* ke branch tersebut (`git push origin fitur-baru`).
5. Ajukan *Pull Request* di GitHub.

---

## 📝 Lisensi

Proyek ini bebas untuk digunakan, dimodifikasi, dan didistribusikan. Cocok untuk dikembangkan oleh *developer*, perusahaan, atau komunitas.

⭐ *Jangan lupa berikan Star pada repository ini jika bermanfaat!* ⭐

```

```