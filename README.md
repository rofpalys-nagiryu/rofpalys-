
<div align="center">

<h1>🎧 RofPalysX</h1>
<p><b>Cross-Platform Terminal Music Player</b></p>
<p><i>Synced Lyrics • Visualizer • Auto Engine Detection</i></p>

<br>

<table>
<tr>
<td><img src="https://github.com/rofpalys-nagiryu/rofpalys-/raw/main/Screenshot_20260904_130743_Termux.jpg" width="260"></td>
<td><img src="https://github.com/rofpalys-nagiryu/rofpalys-/raw/main/Screenshot_20260904_133612_Termux.jpg" width="260"></td>
<td><img src="https://github.com/rofpalys-nagiryu/rofpalys-/raw/main/Screenshot_20260904_133755_Termux.jpg" width="260"></td>
</tr>
<tr>
<td align="center">Main Interface</td>
<td align="center">Visualizer</td>
<td align="center">Lyrics</td>
</tr>
</table>

<br>

<img src="https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/Platform-Cross--OS-00FFFF?style=for-the-badge">
<img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge">

</div>

---

### ⚡ Features
<div align="center">
<table>
  <tr>
    <td align="center">🎵<br><b>Multi-Format</b><br>MP3, FLAC, WAV</td>
    <td align="center">📄<br><b>Synced Lyrics</b><br>Real-time Karaoke</td>
    <td align="center">📺<br><b>Visualizer</b><br>19 Animations</td>
    <td align="center">🌐<br><b>6 Languages</b></td>
  </tr>
  <tr>
    <td align="center">⬇️<br><b>YT Downloader</b><br>via yt-dlp</td>
    <td align="center">🔀<br><b>AutoDJ</b><br>Smart & Random</td>
    <td align="center">📦<br><b>Multi-Engine</b><br>mpv, ffplay, VLC</td>
    <td align="center">⭐<br><b>Favorites</b></td>
  </tr>
</table>
</div>

---

### 📥 Installation

*After install, just type `RofPalysX` to run — no need for `python3 rofpalysx.py`.*

Setiap platform di bawah punya **Metode Utama** (download manual) dan **Metode Cadangan** (`git clone`, dipakai kalau metode utama gagal atau file rusak/hilang).

---

#### 1️⃣ Arch Linux (native Linux distro)

**Metode Utama**
```bash
sudo pacman -Syu
sudo pacman -S python python-pip mpv ffmpeg
pip install yt-dlp pygame
sudo mv rofpalysx.py /usr/local/bin/RofPalysX
sudo chmod +x /usr/local/bin/RofPalysX
RofPalysX
```

**Metode Cadangan (Git Clone)**
```bash
sudo pacman -S git
git clone https://github.com/rofpalys-nagiryu/rofpalys-.git
cd rofpalys-
sudo mv rofpalysx.py /usr/local/bin/RofPalysX
sudo chmod +x /usr/local/bin/RofPalysX
RofPalysX
```

---

#### 2️⃣ Debian / Ubuntu (native Linux distro)

**Metode Utama**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip mpv ffmpeg -y
pip3 install yt-dlp pygame
sudo mv rofpalysx.py /usr/local/bin/RofPalysX
sudo chmod +x /usr/local/bin/RofPalysX
RofPalysX
```

**Metode Cadangan (Git Clone)**
```bash
sudo apt install git -y
git clone https://github.com/rofpalys-nagiryu/rofpalys-.git
cd rofpalys-
sudo mv rofpalysx.py /usr/local/bin/RofPalysX
sudo chmod +x /usr/local/bin/RofPalysX
RofPalysX
```

---

#### 3️⃣ Termux (Android — bukan Linux desktop, walau berbasis Linux)

> ⚠️ Termux berjalan di atas Android, jadi command dan lokasi filenya beda dari Linux biasa (pakai `pkg`, bukan `apt`/`pacman`, dan bin path-nya `$PREFIX/bin`).

**Metode Utama**
```bash
pkg update && pkg upgrade -y
pkg install python mpv ffmpeg -y
termux-setup-storage
pip install yt-dlp pygame
ls
cp rofpalysx.py $PREFIX/bin/RofPalysX
chmod +x $PREFIX/bin/RofPalysX
RofPalysX
```

**Metode Cadangan (Git Clone)**
```bash
pkg install git -y
git clone https://github.com/rofpalys-nagiryu/rofpalys-.git
cd rofpalys-
cp rofpalysx.py $PREFIX/bin/RofPalysX
chmod +x $PREFIX/bin/RofPalysX
RofPalysX
```

---

#### 4️⃣ macOS

**Metode Utama**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python mpv ffmpeg
pip3 install yt-dlp pygame
sudo mv rofpalysx.py /usr/local/bin/RofPalysX
sudo chmod +x /usr/local/bin/RofPalysX
RofPalysX
```

**Metode Cadangan (Git Clone)**
```bash
brew install git
git clone https://github.com/rofpalys-nagiryu/rofpalys-.git
cd rofpalys-
sudo mv rofpalysx.py /usr/local/bin/RofPalysX
sudo chmod +x /usr/local/bin/RofPalysX
RofPalysX
```

---

#### 5️⃣ Windows

**Metode Utama**
1. Install Python — centang **"Add Python to PATH"** saat instalasi
2. Install VLC (opsional, untuk audio lebih baik)
3. Buka CMD atau PowerShell:
```cmd
pip install windows-curses yt-dlp pygame
```
4. Buat file `RofPalysX.bat` di folder yang sama dengan `rofpalysx.py`, isi:
```bat
@echo off
python "%~dp0rofpalysx.py" %*
```
5. Jalankan dengan double-click file `.bat`, atau ketik `RofPalysX` di CMD

**Metode Cadangan (Git Clone)**
1. Install [Git for Windows](https://git-scm.com/download/win)
2. Buka CMD atau PowerShell:
```cmd
git clone https://github.com/rofpalys-nagiryu/rofpalys-.git
cd rofpalys-
pip install windows-curses yt-dlp pygame
```

3. Buat file `RofPalysX.bat` di folder yang sama, isi:
```bat
@echo off
python "%~dp0rofpalysx.py" %*
```
4. Jalankan dengan double-click file `.bat`, atau ketik `RofPalysX` di CMD

---

### 🔧 Troubleshooting Cepat

| Pesan Error | Penyebab | Solusi |
|---|---|---|
| `command not found: RofPalysX` | Belum ke-refresh terminal | Tutup & buka ulang terminal |
| `command not found: git` | Git belum terinstall | Install git dulu (lihat baris pertama tiap Metode Cadangan) |
| `No player engine found!` | mpv/ffmpeg belum terinstall | Cek dengan `mpv --version` |
| `Permission denied` | Lupa beri izin eksekusi | Jalankan ulang `chmod +x` |
| `No such file or directory` | Nama file salah/typo, atau belum `cd` ke folder repo hasil clone | Cek dengan `ls` (Linux/Termux/Mac) atau `dir` (Windows) |
| File musik tidak muncul | Belum di folder yang sama, atau (Termux) belum `termux-setup-storage` | Pindahkan file musik ke folder yang sama saat run |

---

### 🚀 Keyboard Controls

| Key | Function |
|---|---|
| F | Play / Pause |
| V | Search Song |
| N / P | Next / Previous |
| M | Change Mode |
| Z | Show Lyrics |
| C | Show Visualizer |
| Y | Download from YouTube |
| X | Change Language |
| Q | Quit |

---

### 📦 Requirements

- Python 3 (required)
- mpv / ffmpeg / vlc (optional, better audio)
- yt-dlp (optional, YouTube downloads)
- git (optional, hanya untuk Metode Cadangan)

<br>

<div align="center"><i>Made with ❤️ by rofpalys-nagiryu</i></div>
