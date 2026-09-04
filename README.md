
<div align="center">

<!-- HEADER / BANNER -->
<h1>🎧 RofPalysX</h1>
<p><b>Your Ultimate Cross-Platform Terminal Music Player</b></p>
<p><i>With Synced Lyrics, Visualizer, and Automatic Engine Detection</i></p>

<br>

<!-- IMAGE / SCREENSHOT GALLERY -->
<img src="https://github.com/rofpalys-nagiryu/rofpalys-/raw/main/Screenshot_20260904_130743_Termux.jpg" alt="Main Interface" width="600" style="border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 2px solid #00FFFF;">

<br><br>

<img src="https://github.com/rofpalys-nagiryu/rofpalys-/raw/main/Screenshot_20260904_133612_Termux.jpg" alt="Visualizer View" width="600" style="border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 2px solid #00FFFF;">

<br><br>

<img src="https://github.com/rofpalys-nagiryu/rofpalys-/raw/main/Screenshot_20260904_133755_Termux.jpg" alt="Lyrics View" width="600" style="border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 2px solid #00FFFF;">

<br><br>

<!-- BADGES -->
<img src="https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/Platform-Cross--OS-00FFFF?style=for-the-badge">
<img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge">

</div>

---

### ⚡ Key Features
<div align="center">
<table>
  <tr>
    <td align="center">🎵 <br><b>Multi-Format</b><br>MP3, FLAC, WAV</td>
    <td align="center">📄 <br><b>Synced Lyrics</b><br>Real-time Karaoke</td>
    <td align="center">📺 <br><b>Visualizer</b><br>19 Matrix Animations</td>
    <td align="center">🌐 <br><b>6 Languages</b><br>Multi-Language Support</td>
  </tr>
  <tr>
    <td align="center">⬇️ <br><b>Downloader</b><br>yt-dlp YouTube</td>
    <td align="center">🔀 <br><b>AutoDJ</b><br>Smart & Random</td>
    <td align="center">📦 <br><b>Multi-Engine</b><br>mpv, ffplay, VLC</td>
    <td align="center">⭐ <br><b>Favorites</b><br>Saved Safely</td>
  </tr>
</table>
</div>

---

### 📥 Installation & Setup (Full English)

*Important: After installation, you can simply type `RofPalysX` to run it. No need to type `python3 refpalysx.py`.*

#### 1️⃣ Option A: Linux (Arch Linux / Pure Linux)

**Step 1:** Update your system packages.
```bash
sudo pacman -Syu
```

Step 2: Install Python, pip, mpv, and ffmpeg.

```bash
sudo pacman -S python python-pip mpv ffmpeg
```

(Note: If you are using Debian/Ubuntu, use sudo apt update && sudo apt install python3 python3-pip mpv ffmpeg)

Step 3: Install Python dependencies.

```bash
pip install yt-dlp pygame
```

Step 4: Move the script to your system bin and rename it.

```bash
sudo mv refpalysx.py /usr/local/bin/RofPalysX
```

Step 5: Make it executable.

```bash
sudo chmod +x /usr/local/bin/RofPalysX
```

Step 6: Run the program.

```bash
RofPalysX
```

---

2️⃣ Option B: Termux (Android)

Step 1: Update your packages.

```bash
pkg update && pkg upgrade
```

Step 2: Install Python, mpv, and ffmpeg.

```bash
pkg install python mpv ffmpeg
```

Step 3: Install Python dependencies.

```bash
pip install yt-dlp pygame
```

Step 4: Move the script to your system bin and rename it.

```bash
cp refpalysx.py $PREFIX/bin/RofPalysX
```

Step 5: Make it executable.

```bash
chmod +x $PREFIX/bin/RofPalysX
```

Step 6: Run the program.

```bash
RofPalysX
```

---

3️⃣ macOS

Step 1: Install Homebrew (if you don't have it).

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Step 2: Install Python, mpv, and ffmpeg.

```bash
brew install python mpv ffmpeg
```

Step 3: Install Python dependencies.

```bash
pip3 install yt-dlp pygame
```

Step 4: Move the script to your system bin and rename it.

```bash
sudo mv refpalysx.py /usr/local/bin/RofPalysX
```

Step 5: Make it executable.

```bash
sudo chmod +x /usr/local/bin/RofPalysX
```

Step 6: Run the program.

```bash
RofPalysX
```

---

4️⃣ Windows

Step 1: Install Python (Make sure you check "Add Python to PATH" during installation).
Step 2: Install VLC (For better audio support).

Step 3: Open CMD or PowerShell and install Python dependencies.

```cmd
pip install windows-curses yt-dlp pygame
```

Step 4: Create a new file named RofPalysX.bat in the same folder as refpalysx.py, and add this line inside:

```bat
@echo off
python "%~dp0refpalysx.py" %*
```

Step 5: Run the program by double-clicking the .bat file or typing RofPalysX in the command prompt.

```cmd
RofPalysX
```

---

🚀 How to Use (Keyboard Controls)

Key Function
F Play / Pause
V Search Song
N / P Next / Previous Song
M Change Mode (Normal, Repeat, Shuffle)
Z Show Lyrics
C Show Visualizer
Y Download Audio from YouTube
X Change Language
Q Quit

---

🛠️ About the Audio Engine

"Don't worry if you don't have a specific music player installed."

The program automatically scans your system to find available audio engines (like mpv, ffplay, VLC, or PyGame) and uses them immediately. 
If one engine fails, it smoothly switches to another so your music keeps playing without interruption! 🎶

---

📦 Requirements

· Python 3 (Required)
· mpv / ffmpeg / vlc (Optional, for better audio quality)
· yt-dlp (Optional, for YouTube downloads)

<br>

<div align="center">
  <i>Made with ❤️ by rofpalys-nagiryu</i>
</div>
