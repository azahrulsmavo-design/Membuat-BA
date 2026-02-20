# Auto-AssetOpname Generator

Aplikasi untuk membuat Berita Acara (BA) Aset kendaraan secara otomatis dengan fitur pemrosesan gambar (cropping), download dari Google Drive, dan export ke PDF/Word.

## Persyaratan Sistem

Pastikan komputer Anda sudah terinstall:
1.  Python (versi 3.8 atau lebih baru)
2.  Node.js (versi 16 atau lebih baru)
3.  Git (opsional, untuk clone repository)

## Instalasi

Ikuti langkah-langkah berikut untuk menginstall aplikasi pertama kali.

### 1. Backend (Python)

Buka terminal/command prompt, arahkan ke folder `backend`:
```bash
cd backend
```

Buat virtual environment (opsional tapi disarankan):
```bash
python -m venv venv
```

Aktifkan virtual environment:
-   Windows: `venv\Scripts\activate`
-   Mac/Linux: `source venv/bin/activate`

Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Frontend (Vue.js)

Buka terminal baru, arahkan ke folder `frontend`:
```bash
cd frontend
```

Install library yang dibutuhkan:
```bash
npm install
```

---

## Cara Menjalankan Aplikasi

Ada dua cara untuk menjalankan aplikasi:

### Cara 1: Menggunakan Script Otomatis (Windows)

Cukup klik dua kali file `start_app.bat` di folder utama. Script ini akan otomatis menjalankan Backend dan Frontend sekaligus.

### Cara 2: Menjalankan Manual

Anda perlu membuka **dua** terminal berbeda.

**Terminal 1 (Backend):**
```bash
cd backend
# Pastikan venv aktif jika Anda menggunakannya
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev -- --host
```

Akses aplikasi melalui browser di: `http://localhost:5173` atau sesuai alamat IP yang muncul di terminal frontend (misal: `http://192.168.1.5:5173`).

---

## Panduan Penggunaan.
sss


### 1. Mengisi Data Unit
-   Isi "Unit Bisnis" dan "Lokasi" di bagian atas halaman (wajib).
-   Masukkan Nomor Polisi (Nopol) untuk setiap unit.
-   Anda bisa menambah unit baru dengan tombol "+" di sidebar kiri.
-   Gunakan tombol "Bulk Import" untuk memasukkan banyak data sekaligus dari Excel (Copy-Paste).

### 2. Mengupload Gambar
-   Klik kotak gambar (STNK, Pajak, Fisik Kendaraan, dll) untuk mengupload file.
-   Jika menggunakan link Google Drive, paste link tersebut saat diminta. Gambar akan otomatis didownload dan di-crop (khusus dokumen).
-   Fitur "Download All" (tombol hijau di atas) akan mendownload semua gambar dari link ..Google Drive yang ada di semua unit secara otomatis.

### 3. Generate Laporan
-   Klik tombol **Preview** untuk melihat hasil sementara.
-   Klik tombol **PDF** untuk mendownload laporan dalam format PDF siap cetak.
-   Klik tombol **Word** untuk mendownload dalam format .docx jika ingin diedit manual.

---

## Troubleshooting (Masalah Umum)

### Gambar Tidak Muncul di Komputer Lain (Jaringan LAN)
Jika teman Anda bisa membuka aplikasi tetapi gambar tidak muncul atau gagal download:

1.  **Cek Firewall di Komputer Server (Tempat aplikasi berjalan):**
    -   Buka "Windows Defender Firewall with Advanced Security".
    -   Pilih "Inbound Rules" -> "New Rule".
    -   Pilih "Port" -> TCP.
    -   Masukkan "Specific local ports": **8000** (Port Backend).
    -   Pilih "Allow the connection".
    -   Ber nama rule tersebut (misal: "Python Backend").

2.  **Pastikan Server Berjalan di Host 0.0.0.0:**
    -   Perintah backend harus menggunakan `--host 0.0.0.0` agar bisa diakses dari luar.

### Error "Missing catch or finally clause"
-   Pastikan kode program sudah yang terbaru. Error ini biasanya karena kesalahan sintaks pada file `App.vue` yang sudah diperbaiki.

### Aplikasi Blank Putih
-   Coba refresh halaman (Ctrl + R).
-   Pastikan Backend (Terminal 1) tidak ada error.
-   Buka Console Browser (Tekan F12 -> Console) untuk melihat pesan error detail.
