# Dashboard Absensi Bot — Tampilan Web (Public)

Dashboard statis untuk menampilkan data absensi bot Telegram di peramban (web).
Tampilan **read-only** (tidak mengubah data), dua mode (Ringkas / Rinci), aman
ketika data kosong.

## Arsitektur

```
[Bot Telegram] ──(SQLite local)──► [export_absensi.py] ──► [absensi_data.json]
                                                                    │
                                                                    ▼
[User / HP / PC] ──(browser)──► [dashboard/index.html] ── fetch(DATA_URL) ──▶ JSON publik
```

> 🔑 Hanya dashboard web yang dimaksud **public di Vercel**. Bot Telegram sendiri
> tetap butuh proses 24/7 (VPS / Render / server lama), karena bot butuh polling
> terus-menerus dan SQLite lokal.

## File ini

| File | Keterangan |
|---|---|
| `dashboard/index.html` | Halaman dashboard web (CSS+JS dalam satu file) |
| `export_absensi.py` | Export SQLite → JSON |

## Konfigurasi DATA_URL (sudah di dalam `index.html`)

Buat file `absensi_data.json` yang bisa diakses publik, lalu isi baris ini:

```js
const DATA_URL = "https://raw.githubusercontent.com/<user>/<repo>/main/absensi_data.json";
```

Format JSON yang dibaca (contoh):

```json
{
  "updated_at": "2026-10-08T16:46:40",
  "entries": [
    {
      "id": 20,
      "user_id": 1210522333,
      "nama": "aris",
      "divisi": "developer",
      "shift": "07:30-17:00",
      "tanggal": "2026-10-07",
      "status": "Hadir",
      "waktu_masuk": "07:21:37",
      "waktu_pulang": "16:46:40"
    }
  ]
}
```

## Cara jalankan (local / dev)

```bash
cd "/c/Users/Aris Widiyanto/absensi bot"
# 1. buat data JSON dari database
python export_absensi.py
# 2. buka di browser
start index.html
```

> Saat lokal belum ada `DATA_URL`, halaman menampilkan pesan "Belum ada data."

## Cara deploy ke Vercel (langkah ringkas)

1. Buat repo baru (misal `absensi-dashboard`) dan upload folder `dashboard/`
   (termasuk `index.html` + `export_absensi.py`).
2. Tambahkan `absensi_data.json` ke repo (karena Vercel static tidak bisa akses
   SQLite/lokal server). Pastikan repo **public** agar `raw.githubusercontent.com`
   bisa diakses tanpa autentikasi.
3. Import repo ke Vercel → framework **Other / Static** (Vercel otomatis deteksi
   `index.html` di root).
4. Aktifkan `PUBLIC_DATA_URL` (environment variable) → nilainya:
   `https://raw.githubusercontent.com/<user>/<repo>/main/absensi_data.json`
5. Deklare `index.html` sebagai root output → Vercel akan deploy sebagai static site.
6. Buka URL Vercel; dashboard akan fetch data dari `DATA_URL`.

### Vercel env yang disarankan

| Env | Nilai contoh |
|---|---|
|| `PUBLIC_DATA_URL` | `https://raw.githubusercontent.com/TestwayWeb3/bot-absensi/main/absensi_data.json` |
| `DATA_URL` | (sama seperti atas) — script membacanya dari `PUBLIC_DATA_URL` |

> 💡 Ganti `DATA_URL` di dalam `index.html` jika tidak ingin pakai env.

## Perbaikan yang masih perlu kamu lakukan (bot pusat)

Agar `/chat` dan data absensi berjalan, ingat dua hal cronis:

1. **Ganti token placeholder** di `bot_absensi.py` / `.env`: `BOT_TOKEN=***`
   → ganti dengan token asli dari [@BotFather](https://t.me/BotFather).
2. **Jangan jalankan dua kali** — satu proses saja. Error 409
   (`Conflict: terminated by other getUpdates`) terjadi kalau ada dua instance bot
   berjalan bersamaan.
