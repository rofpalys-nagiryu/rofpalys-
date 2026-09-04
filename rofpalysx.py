#!/usr/bin/env python3
import os
import sys

# --- CEK CURSES DI AWAL (Windows tidak punya curses bawaan) ---
# Catatan: teks konsol di bawah ini (sebelum tampilan utama muncul) sengaja
# selalu bahasa Inggris dan TIDAK terpengaruh oleh fitur ganti bahasa [X],
# karena tampil sebelum sistem bahasa dalam aplikasi diinisialisasi.
try:
    import curses
except ImportError:
    print("=" * 60)
    print("ERROR: the 'curses' module was not found.")
    if sys.platform == "win32":
        print("On Windows, curses is not included with Python by default.")
        print("Install it first with:")
        print()
        print("    pip install windows-curses")
        print()
        print("Then run the program again.")
    else:
        print("Make sure your Python installation includes curses support.")
    print("=" * 60)
    sys.exit(1)

import glob
import time
import threading
import subprocess
import urllib.request
import urllib.parse
import json
import locale
import re
import shutil
import math
import random

try:
    locale.setlocale(locale.LC_ALL, '')
except Exception:
    pass

# --- EKSTENSI AUDIO (Gabungan Ekstensif) ---
AUDIO_EXTS = (
    '.mp3', '.aac', '.wav', '.flac', '.alac', '.aiff', '.aif', '.ogg',
    '.wma', '.opus', '.mid', '.midi', '.m4a', '.m4b', '.m4p', '.pcm',
    '.dsd', '.dsf', '.dff', '.amr', '.ape', '.wv', '.mpc', '.ac3',
    '.dts', '.truehd', '.eac3', '.ra', '.au', '.caf', '.voc', '.iff',
    '.tak', '.tta', '.mp4', '.webm', '.mka'
)

# --- STATUS UTAMA ---
songs_all = []
songs = []
selected_idx = 0
playing_song_name = None
is_playing = False
play_mode = 0
favorites = set()

# --- STATUS UI & LANJUTAN ---
ui_mode = 'playlist'
current_lang = 'en'
current_lyrics = []
synced_lyrics = []
is_synced_lyrics = False
lyrics_scroll = 0
last_scroll_time = 0.0
search_query = ""
is_searching = False

# --- FITUR CANGGIH YT-DLP ---
is_downloading = False
dl_progress_text = ""

# --- FITUR CANGGIH ---
auto_dj = False
aura_mode = False
x3_vis = False
anim_enabled = True  # [2E] toggle: status ini disimpan ke rof_settings.json

# --- STATUS ENGINE / ERROR PLAYBACK ---
engine_status_msg = ""
engine_status_time = 0.0

# --- SMART ENGINE AUTO-DETECTION ---
AVAILABLE_ENGINES = []
ACTIVE_ENGINE_IDX = 0


def detect_audio_engines():
    """Deteksi semua audio player yang tersedia di sistem (Windows/Linux/Mac)."""
    engines = []

    # 1. MPV - stabil di semua platform, tidak butuh IPC socket sama sekali
    if shutil.which("mpv"):
        engines.append({"name": "mpv", "cmd": ["mpv", "--no-video", "--really-quiet", "--no-terminal"]})

    # 2. FFplay - sangat stabil, ikut paket ffmpeg
    if shutil.which("ffplay"):
        engines.append({"name": "ffplay", "cmd": ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]})

    # 3. VLC (CLI) - deteksi yang benar-benar memverifikasi keberadaannya
    vlc_path = None
    if sys.platform == "win32":
        for p in [r"C:\Program Files\VideoLAN\VLC\vlc.exe", r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"]:
            if os.path.exists(p):
                vlc_path = p
                break
        if not vlc_path and shutil.which("vlc"):
            vlc_path = "vlc"
    else:
        if shutil.which("cvlc"):
            vlc_path = "cvlc"
        elif shutil.which("vlc"):
            vlc_path = "vlc"
    if vlc_path:
        engines.append({"name": "VLC", "cmd": [vlc_path, "-I", "dummy", "--no-video", "--play-and-exit", "--quiet"]})

    # 4. MPlayer
    if shutil.which("mplayer"):
        engines.append({"name": "mplayer", "cmd": ["mplayer", "-novideo", "-really-quiet"]})

    # 5. MPG123 (ringan, khusus mp3)
    if shutil.which("mpg123"):
        engines.append({"name": "mpg123", "cmd": ["mpg123", "-q"]})

    # 6. SoX (play)
    if shutil.which("play"):
        engines.append({"name": "SoX (play)", "cmd": ["play", "-q"]})

    # 7. afplay (bawaan macOS)
    if sys.platform == "darwin" and shutil.which("afplay"):
        engines.append({"name": "afplay (Mac)", "cmd": ["afplay"]})

    # 8. Foobar2000 (khusus Windows)
    if sys.platform == "win32":
        for p in [r"C:\Program Files (x86)\foobar2000\foobar2000.exe", r"C:\Program Files\foobar2000\foobar2000.exe"]:
            if os.path.exists(p):
                engines.append({"name": "Foobar2000", "cmd": [p, "/play"]})
                break

    # 9. aplay (raw ALSA Linux - dukungan format terbatas, jadi fallback terakhir)
    if sys.platform == "linux" and shutil.which("aplay"):
        engines.append({"name": "aplay", "cmd": ["aplay", "-q"]})

    # 10. PyGame - fallback murni Python, bekerja di semua platform kalau terinstall
    try:
        import pygame
        pygame.mixer.init()
        engines.append({"name": "PyGame", "cmd": "INTERNAL_PYGAME"})
    except Exception:
        pass

    return engines


AVAILABLE_ENGINES = detect_audio_engines()

# --- STATUS ANIMASI ---
current_anim_idx = 0
last_anim_time = 0.0
TOTAL_ANIMATIONS = 19

current_process = None
progress_pct = 0.0
current_time_str = "00:00"
total_time_str = "00:00"
current_time_seconds = 0.0
total_time_seconds = 1.0
start_time = 0.0
manual_stop = False
duration_known = False

lock = threading.Lock()
exit_flag = False
tick = 0

LANG = {
    'en': {
        'no_music': 'No music playing',
        'track': 'Track',
        'm_single': 'Single',
        'm_rep1': 'Repeat 1',
        'm_seq': 'Sequential',
        'm_loopx': 'Loop All',
        'm_shuffle': 'Shuffle',
        'lyric_title': '✦ KARAOKE SYNCED LYRICS ✦',
        'visual_title': '⚡ QUANTUM MATRIX BASS SURGE ⚡',
        'lyric_empty': 'Lyrics unavailable.',
        'lyric_dl': 'Syncing with LRCLIB...',
        'lyric_fail': 'Lyrics not found in database.',
        'ctrl_1': '[Z] Lyric | [C] Vis | [X] Lang | [M] Mode | [L] Fav | [R] Reset',
        'ctrl_2': '[V] Search | [Y] yt-dlp | [F] Play | [P] Prev | [N] Next | [Q] Quit',
        'ctrl_3': '[7xz] Engine | [A] AutoDJ | [4a] Aura | [x3] VisX3 | [1b] Anim | [2e] Anim On/Off',
        'nav': '↑/↓: Scroll • W/Enter: Play',
        'search': 'Search: ',
        'no_engine': 'No player engine found! Install mpv, ffplay, vlc, or pip install pygame.',
        'all_fail': 'All engines failed to play this file.'
    },
    'id': {
        'no_music': 'Belum ada lagu',
        'track': 'Lagu',
        'm_single': 'Normal',
        'm_rep1': 'Ulangi 1',
        'm_seq': 'Berurutan',
        'm_loopx': 'Ulangi Semua',
        'm_shuffle': 'Acak',
        'lyric_title': '✦ LIRIK SINKRON KARAOKE ✦',
        'visual_title': '⚡ QUANTUM MATRIX BASS SURGE ⚡',
        'lyric_empty': 'Lirik tidak tersedia.',
        'lyric_dl': 'Menghubungkan ke LRCLIB...',
        'lyric_fail': 'Lirik tidak ditemukan di database.',
        'ctrl_1': '[Z] Lirik | [C] Vis | [X] Bahasa | [M] Mode | [L] Fav | [R] Reset',
        'ctrl_2': '[V] Cari | [Y] yt-dlp | [F] Putar | [P] Mundur | [N] Maju | [Q] Keluar',
        'ctrl_3': '[7xz] Mesin | [A] AutoDJ | [4a] Aura | [x3] VisX3 | [1b] Anim | [2e] Anim On/Off',
        'nav': '↑/↓: Arahkan • W/Enter: Putar',
        'search': 'Cari: ',
        'no_engine': 'Tidak ada player terdeteksi! Install mpv, ffplay, vlc, atau pip install pygame.',
        'all_fail': 'Semua engine gagal memutar file ini.'
    },
    'zh': {
        'no_music': '未播放音乐',
        'track': '曲目',
        'm_single': '单曲',
        'm_rep1': '单曲循环',
        'm_seq': '顺序播放',
        'm_loopx': '循环全部',
        'm_shuffle': '随机播放',
        'lyric_title': '✦ 卡拉OK 同步歌词 ✦',
        'visual_title': '⚡ 量子矩阵低音冲击 ⚡',
        'lyric_empty': '没有歌词。',
        'lyric_dl': '正在从 LRCLIB 同步...',
        'lyric_fail': '数据库中未找到歌词。',
        'ctrl_1': '[Z] 歌词 | [C] 可视化 | [X] 语言 | [M] 模式 | [L] 收藏 | [R] 重置',
        'ctrl_2': '[V] 搜索 | [Y] yt-dlp | [F] 播放 | [P] 上一首 | [N] 下一首 | [Q] 退出',
        'ctrl_3': '[7xz] 引擎 | [A] 自动DJ | [4a] 极光 | [x3] 视觉x3 | [1b] 动画 | [2e] 动画开关',
        'nav': '↑/↓: 滚动 • W/回车: 播放',
        'search': '搜索: ',
        'no_engine': '未检测到播放器！请安装 mpv、ffplay、vlc，或运行 pip install pygame。',
        'all_fail': '所有引擎均无法播放此文件。'
    },
    'de': {
        'no_music': 'Keine Musik wird abgespielt',
        'track': 'Titel',
        'm_single': 'Einzeln',
        'm_rep1': 'Wiederholen',
        'm_seq': 'Fortlaufend',
        'm_loopx': 'Alle wiederholen',
        'm_shuffle': 'Zufällig',
        'lyric_title': '✦ KARAOKE SYNCHRONER TEXT ✦',
        'visual_title': '⚡ QUANTUM MATRIX BASS SURGE ⚡',
        'lyric_empty': 'Songtext nicht verfügbar.',
        'lyric_dl': 'Synchronisiere mit LRCLIB...',
        'lyric_fail': 'Songtext nicht in der Datenbank gefunden.',
        'ctrl_1': '[Z] Text | [C] Visual | [X] Sprache | [M] Modus | [L] Favorit | [R] Reset',
        'ctrl_2': '[V] Suche | [Y] yt-dlp | [F] Abspielen | [P] Zurück | [N] Weiter | [Q] Beenden',
        'ctrl_3': '[7xz] Engine | [A] AutoDJ | [4a] Aura | [x3] VisX3 | [1b] Animation | [2e] Anim. An/Aus',
        'nav': '↑/↓: Scrollen • W/Enter: Abspielen',
        'search': 'Suche: ',
        'no_engine': 'Kein Player gefunden! Installiere mpv, ffplay, vlc oder pip install pygame.',
        'all_fail': 'Alle Engines konnten diese Datei nicht abspielen.'
    },
    'ja': {
        'no_music': '再生中の曲はありません',
        'track': 'トラック',
        'm_single': 'シングル',
        'm_rep1': '1曲リピート',
        'm_seq': '順番再生',
        'm_loopx': '全曲リピート',
        'm_shuffle': 'シャッフル',
        'lyric_title': '✦ カラオケ同期歌詞 ✦',
        'visual_title': '⚡ クァンタムマトリックス・ベースサージ ⚡',
        'lyric_empty': '歌詞がありません。',
        'lyric_dl': 'LRCLIBと同期中...',
        'lyric_fail': 'データベースに歌詞が見つかりません。',
        'ctrl_1': '[Z] 歌詞 | [C] ビジュアル | [X] 言語 | [M] モード | [L] お気に入り | [R] リセット',
        'ctrl_2': '[V] 検索 | [Y] yt-dlp | [F] 再生 | [P] 前へ | [N] 次へ | [Q] 終了',
        'ctrl_3': '[7xz] エンジン | [A] オートDJ | [4a] オーラ | [x3] ビジュアルx3 | [1b] アニメ | [2e] アニメON/OFF',
        'nav': '↑/↓: スクロール • W/Enter: 再生',
        'search': '検索: ',
        'no_engine': 'プレイヤーが見つかりません！mpv、ffplay、vlcをインストールするか、pip install pygame を実行してください。',
        'all_fail': 'すべてのエンジンでこのファイルを再生できませんでした。'
    },
    'ru': {
        'no_music': 'Музыка не воспроизводится',
        'track': 'Трек',
        'm_single': 'Одиночный',
        'm_rep1': 'Повтор 1',
        'm_seq': 'По порядку',
        'm_loopx': 'Повтор всех',
        'm_shuffle': 'Перемешать',
        'lyric_title': '✦ СИНХРОННЫЙ ТЕКСТ ПЕСНИ ✦',
        'visual_title': '⚡ QUANTUM MATRIX BASS SURGE ⚡',
        'lyric_empty': 'Текст песни недоступен.',
        'lyric_dl': 'Синхронизация с LRCLIB...',
        'lyric_fail': 'Текст песни не найден в базе данных.',
        'ctrl_1': '[Z] Текст | [C] Визуал | [X] Язык | [M] Режим | [L] Избранное | [R] Сброс',
        'ctrl_2': '[V] Поиск | [Y] yt-dlp | [F] Играть | [P] Пред. | [N] След. | [Q] Выход',
        'ctrl_3': '[7xz] Движок | [A] АвтоDJ | [4a] Аура | [x3] ВизуалX3 | [1b] Анимация | [2e] Анимация Вкл/Выкл',
        'nav': '↑/↓: Прокрутка • W/Enter: Играть',
        'search': 'Поиск: ',
        'no_engine': 'Плеер не найден! Установите mpv, ffplay, vlc или выполните pip install pygame.',
        'all_fail': 'Все движки не смогли воспроизвести этот файл.'
    }
}

# Urutan siklus [X]: Inggris, China, Indonesia, Jerman, Jepang, Rusia
SUPPORTED_LANGS = ['en', 'zh', 'id', 'de', 'ja', 'ru']


def t(key):
    return LANG[current_lang][key]


def load_favorites():
    global favorites
    try:
        if os.path.exists("rof_favorites.json"):
            with open("rof_favorites.json", "r", encoding="utf-8") as f:
                favorites = set(json.load(f))
    except Exception:
        favorites = set()


def save_favorites():
    try:
        with open("rof_favorites.json", "w", encoding="utf-8") as f:
            json.dump(list(favorites), f)
    except Exception:
        pass


def detect_system_language():
    """Deteksi bahasa OS. Kalau tidak yakin/tidak didukung, otomatis pakai Inggris (default aman)."""
    try:
        for var in ('LC_ALL', 'LC_MESSAGES', 'LANG', 'LANGUAGE'):
            val = os.environ.get(var)
            if val:
                code = val.split(':')[0].split('.')[0].split('_')[0].lower()
                if code in SUPPORTED_LANGS:
                    return code
        loc = None
        try:
            loc = locale.getlocale()[0]
        except Exception:
            loc = None
        if not loc:
            try:
                loc = locale.getdefaultlocale()[0]
            except Exception:
                loc = None
        if loc:
            code = loc.split('_')[0].lower()
            if code in SUPPORTED_LANGS:
                return code
    except Exception:
        pass
    return 'en'


def load_settings():
    global anim_enabled, current_lang
    current_lang = detect_system_language()
    try:
        if os.path.exists("rof_settings.json"):
            with open("rof_settings.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                anim_enabled = bool(data.get("anim_enabled", True))
                saved_lang = data.get("language")
                if saved_lang in SUPPORTED_LANGS:
                    current_lang = saved_lang
    except Exception:
        anim_enabled = True


def save_settings():
    try:
        with open("rof_settings.json", "w", encoding="utf-8") as f:
            json.dump({"anim_enabled": anim_enabled, "language": current_lang}, f)
    except Exception:
        pass


def get_audio_files():
    files = [f for f in glob.glob("*") if f.lower().endswith(AUDIO_EXTS)]
    return sorted(files)


def update_search():
    global songs, selected_idx
    if search_query.strip() == "":
        songs = songs_all.copy()
    else:
        songs = [s for s in songs_all if search_query.lower() in s.lower()]
    selected_idx = 0


def refresh_playlist():
    global songs_all, songs
    songs_all = get_audio_files()
    if search_query.strip() == "":
        songs = songs_all.copy()
    else:
        songs = [s for s in songs_all if search_query.lower() in s.lower()]


# --- FUNGSI YT-DLP OTOMATIS ---
def download_and_play_yt(url):
    global is_downloading, dl_progress_text
    is_downloading = True
    dl_progress_text = "Mengekstrak Audio (MP3)..."
    try:
        if not shutil.which("yt-dlp"):
            dl_progress_text = "yt-dlp tidak ditemukan! (pip install yt-dlp)"
            time.sleep(2)
            return
        cflags = 0x08000000 if sys.platform == "win32" else 0
        cmd = ["yt-dlp", "-f", "ba", "-x", "--audio-format", "mp3", "-o", "%(title)s.%(ext)s", url]
        subprocess.run(cmd, creationflags=cflags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dl_progress_text = "Selesai! Memutar..."
        time.sleep(1)
        refresh_playlist()
        mp3_files = glob.glob("*.mp3")
        if mp3_files:
            latest_file = max(mp3_files, key=os.path.getctime)
            play_song(latest_file)
    except Exception:
        dl_progress_text = "Gagal Mengunduh!"
        time.sleep(2)
    finally:
        is_downloading = False


def deep_reset():
    global favorites, current_lyrics, synced_lyrics, play_mode, is_playing, playing_song_name
    global current_process, manual_stop, ui_mode
    if os.path.exists("rof_favorites.json"):
        try:
            os.remove("rof_favorites.json")
        except Exception:
            pass
    for f in glob.glob("*.lrc"):
        try:
            os.remove(f)
        except Exception:
            pass
    favorites.clear()
    current_lyrics = []
    synced_lyrics = []
    play_mode = 0
    ui_mode = 'playlist'
    with lock:
        manual_stop = True
        if current_process:
            try:
                current_process.terminate()
            except Exception:
                pass
            current_process = None
        try:
            if "PyGame" in [e["name"] for e in AVAILABLE_ENGINES]:
                import pygame
                pygame.mixer.music.stop()
        except Exception:
            pass
        is_playing = False
        playing_song_name = None
    refresh_playlist()


def process_lyrics_data(raw_text):
    global current_lyrics, synced_lyrics, is_synced_lyrics
    current_lyrics = []
    synced_lyrics = []
    is_synced_lyrics = False
    lines = raw_text.split('\n')
    lrc_pattern = re.compile(r'\[(\d{2}):(\d{2}\.\d{2,3})\](.*)')
    for line in lines:
        match = lrc_pattern.match(line.strip())
        if match:
            is_synced_lyrics = True
            m, s, text = match.groups()
            seconds = int(m) * 60 + float(s)
            if text.strip():
                synced_lyrics.append((seconds, text.strip()))
                current_lyrics.append(text.strip())
        else:
            if line.strip() and not line.startswith('['):
                current_lyrics.append(line.strip())


def fetch_lyrics_online(song_filename):
    global current_lyrics, synced_lyrics, is_synced_lyrics
    base_name = os.path.splitext(song_filename)[0]
    clean_name = base_name.replace("_", " ").strip()
    current_lyrics = [t('lyric_dl'), "█▒▒▒▒▒▒▒▒▒", clean_name]

    # Coba pisahkan "Artis - Judul" kalau ada, ini sangat membantu akurasi
    # pencarian untuk lagu berbahasa asing (China, Rusia, Jepang, dll)
    # karena LRCLIB bisa mencocokkan artist_name + track_name secara terpisah.
    artist_guess, title_guess = None, clean_name
    if " - " in clean_name:
        parts = clean_name.split(" - ", 1)
        artist_guess, title_guess = parts[0].strip(), parts[1].strip()

    queries = []
    if artist_guess:
        queries.append("https://lrclib.net/api/search?" + urllib.parse.urlencode(
            {"track_name": title_guess, "artist_name": artist_guess}))
    queries.append("https://lrclib.net/api/search?" + urllib.parse.urlencode(
        {"q": clean_name.replace("-", " ")}))
    if artist_guess:
        queries.append("https://lrclib.net/api/search?" + urllib.parse.urlencode(
            {"q": title_guess}))

    for url in queries:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'RofPalysX-CLI/4.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data and len(data) > 0:
                    lyrics = data[0].get('syncedLyrics') or data[0].get('plainLyrics')
                    if lyrics:
                        process_lyrics_data(lyrics)
                        try:
                            with open(base_name + '.lrc', 'w', encoding='utf-8') as f:
                                f.write(lyrics)
                        except Exception:
                            pass
                        return
        except Exception:
            continue
    current_lyrics = [t('lyric_fail'), "T_T", clean_name]
    synced_lyrics = []
    is_synced_lyrics = False


def load_lyrics(song_filename):
    global current_lyrics, synced_lyrics, lyrics_scroll, last_scroll_time, is_synced_lyrics
    current_lyrics = []
    synced_lyrics = []
    is_synced_lyrics = False
    lyrics_scroll = 0
    last_scroll_time = 0.0
    base_name = os.path.splitext(song_filename)[0]
    for ext in ['.lrc', '.txt']:
        if os.path.exists(base_name + ext):
            try:
                with open(base_name + ext, 'r', encoding='utf-8') as f:
                    process_lyrics_data(f.read())
                return
            except Exception:
                pass
    current_lyrics = [t('lyric_dl')]
    threading.Thread(target=fetch_lyrics_online, args=(song_filename,), daemon=True).start()


def format_time(seconds):
    if seconds < 0:
        return "??:??"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def get_audio_duration(song_path):
    if shutil.which("ffprobe"):
        try:
            cflags = 0x08000000 if sys.platform == "win32" else 0
            res = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", song_path],
                capture_output=True, text=True, timeout=3, creationflags=cflags
            )
            if res.stdout.strip():
                return float(res.stdout.strip())
        except Exception:
            pass
    return -1.0


def try_start_one_engine(engine, song_path):
    """Coba jalankan satu engine. Return 'PYGAME', proc, atau None kalau gagal."""
    try:
        if engine["cmd"] == "INTERNAL_PYGAME":
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play()
            return "PYGAME"
        else:
            cflags = 0x08000000 if sys.platform == "win32" else 0
            full_cmd = engine["cmd"] + [song_path]
            proc = subprocess.Popen(
                full_cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=cflags
            )
            time.sleep(0.2)
            if proc.poll() is not None:
                # Proses langsung berhenti = kemungkinan besar gagal
                return None
            return proc
    except Exception:
        return None


def run_player_engine(song_path):
    global current_process, is_playing, progress_pct, start_time
    global current_time_str, total_time_str, current_time_seconds, total_time_seconds, manual_stop, duration_known
    global ACTIVE_ENGINE_IDX, engine_status_msg, engine_status_time, playing_song_name

    if not AVAILABLE_ENGINES:
        engine_status_msg = t('no_engine')
        engine_status_time = time.time()
        with lock:
            is_playing = False
            playing_song_name = None
        return

    dur = get_audio_duration(song_path)

    with lock:
        duration_known = (dur > 0)
        total_time_seconds = dur if duration_known else 1.0
        total_time_str = format_time(dur)
        current_time_seconds = 0.0
        current_time_str = "00:00"
        progress_pct = 0.0

    # Coba engine aktif dulu, lalu otomatis fallback ke engine lain kalau gagal
    n = len(AVAILABLE_ENGINES)
    order = [(ACTIVE_ENGINE_IDX + i) % n for i in range(n)]
    proc = None
    use_pygame = False
    use_simulate = False
    engine = None

    for idx in order:
        candidate = AVAILABLE_ENGINES[idx]
        result = try_start_one_engine(candidate, song_path)
        if result == "PYGAME":
            engine = candidate
            use_pygame = True
            ACTIVE_ENGINE_IDX = idx
            break
        elif result is not None:
            proc = result
            engine = candidate
            use_simulate = (candidate["name"] == "Foobar2000")
            ACTIVE_ENGINE_IDX = idx
            break

    if engine is None:
        engine_status_msg = t('all_fail')
        engine_status_time = time.time()
        with lock:
            is_playing = False
            playing_song_name = None
        return

    with lock:
        current_process = proc
        is_playing = True
        manual_stop = False
        start_time = time.time()

    while True:
        if exit_flag or manual_stop:
            if use_pygame:
                try:
                    import pygame
                    pygame.mixer.music.stop()
                except Exception:
                    pass
            elif proc:
                try:
                    if not use_simulate:
                        proc.terminate()
                        proc.kill()
                except Exception:
                    pass
            break

        is_natively_finished = False
        if use_pygame:
            try:
                import pygame
                if not pygame.mixer.music.get_busy():
                    is_natively_finished = True
            except Exception:
                is_natively_finished = True
        elif use_simulate:
            if not duration_known and (time.time() - start_time >= 300.0):
                is_natively_finished = True
            elif duration_known and (time.time() - start_time >= total_time_seconds):
                is_natively_finished = True
        elif proc is not None:
            if proc.poll() is not None:
                is_natively_finished = True

        if is_natively_finished:
            break
        elapsed = time.time() - start_time

        if auto_dj and duration_known and elapsed >= total_time_seconds - 10.0:
            if use_pygame:
                try:
                    import pygame
                    pygame.mixer.music.stop()
                except Exception:
                    pass
            elif proc:
                try:
                    proc.terminate()
                except Exception:
                    pass
            break

        with lock:
            current_time_seconds = elapsed
            current_time_str = format_time(elapsed)
            if duration_known:
                progress_pct = min(1.0, elapsed / total_time_seconds)
            else:
                progress_pct = -1.0
        time.sleep(0.1)

    should_handle_end = False
    with lock:
        if (use_pygame and is_playing) or (not use_pygame and current_process == proc) or (proc is None and not use_pygame):
            current_process = None
            is_playing = False
            progress_pct = 0.0
            current_time_str = "00:00"
            if not exit_flag and not manual_stop:
                should_handle_end = True

    if should_handle_end:
        handle_song_end()


def play_song(song_name):
    global playing_song_name, current_process, manual_stop
    if not song_name:
        return
    with lock:
        manual_stop = True
        if current_process:
            try:
                current_process.terminate()
                current_process.wait(timeout=1)
            except Exception:
                pass
            current_process = None
        try:
            if "PyGame" in [e["name"] for e in AVAILABLE_ENGINES]:
                import pygame
                pygame.mixer.music.stop()
        except Exception:
            pass
        playing_song_name = song_name
        load_lyrics(song_name)
    t_thread = threading.Thread(target=run_player_engine, args=(song_name,), daemon=True)
    t_thread.start()


def handle_song_end():
    global playing_song_name, play_mode
    if not playing_song_name:
        return
    try:
        idx = songs_all.index(playing_song_name)
    except ValueError:
        return

    if play_mode == 0:
        playing_song_name = None
    elif play_mode == 1:
        play_song(playing_song_name)
    elif play_mode == 2:
        if idx < len(songs_all) - 1:
            play_song(songs_all[idx + 1])
        else:
            playing_song_name = None
    elif play_mode == 3:
        play_song(songs_all[(idx + 1) % len(songs_all)])
    elif play_mode == 4:
        if len(songs_all) > 0:
            play_song(songs_all[random.randint(0, len(songs_all) - 1)])


def toggle_play():
    global current_process, is_playing, manual_stop
    if not songs:
        return
    if playing_song_name is None:
        play_song(songs[selected_idx])
    else:
        if is_playing:
            manual_stop = True
            if current_process:
                try:
                    current_process.terminate()
                except Exception:
                    pass
                current_process = None
            try:
                if "PyGame" in [e["name"] for e in AVAILABLE_ENGINES]:
                    import pygame
                    pygame.mixer.music.stop()
            except Exception:
                pass
            is_playing = False
        else:
            play_song(playing_song_name)


def get_mode_string():
    modes = [t('m_single'), t('m_rep1'), t('m_seq'), t('m_loopx'), t('m_shuffle')]
    return modes[play_mode]


def generate_smooth_progressbar(pct, width, tick_val):
    width = max(1, width)
    if pct < 0:
        pos = (tick_val // 2) % (width * 2)
        if pos >= width:
            pos = (width * 2) - 1 - pos
        bar = ["░"] * width
        if 0 <= pos < width:
            bar[pos] = "█"
        if 0 <= pos - 1 < width:
            bar[pos - 1] = "▓"
        if 0 <= pos + 1 < width:
            bar[pos + 1] = "▓"
        return "".join(bar)

    blocks = ["", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
    fill_width = pct * width
    full_blocks = int(fill_width)
    remainder = fill_width - full_blocks
    if full_blocks >= width:
        return "█" * width
    bar = "█" * full_blocks
    if full_blocks < width:
        bar += blocks[int(remainder * len(blocks))]
        bar += "░" * (width - full_blocks - 1)
    return bar


def get_wave_equalizer(t_val):
    bars = [' ', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    eq = ""
    for i in range(4):
        val = int((math.sin(t_val * 0.4 + i * 0.8) + 1) / 2 * 7)
        eq += bars[max(0, min(7, val))]
    return f" [{eq}]"


def safe_addstr(stdscr, y, x, text, attr, max_w=999):
    safe_text = text[:max_w]
    try:
        stdscr.addstr(y, x, safe_text, attr)
    except Exception:
        pass


def get_aura_color(base_pair, is_dim=True):
    if aura_mode:
        return curses.color_pair(3) | (curses.A_DIM if is_dim else curses.A_BOLD)
    return curses.color_pair(base_pair) | (curses.A_DIM if is_dim else curses.A_NORMAL)


# ================= 19 ANIMASI PENUH LAYAR LENGKAP =================
def draw_full_screen_animations(stdscr, h, w, tick):
    global current_anim_idx, last_anim_time, is_playing, TOTAL_ANIMATIONS
    if is_playing and time.time() - last_anim_time > 5.0:
        current_anim_idx = (current_anim_idx + 1) % TOTAL_ANIMATIONS
        last_anim_time = time.time()

    if not is_playing:
        color_idx = (tick // 62) % 6
        matrix_colors = [20, 21, 22, 23, 24, 25]
        base_color = get_aura_color(matrix_colors[color_idx], is_dim=False)
        bright_color = base_color | curses.A_BOLD
        WHITE = curses.color_pair(2) | curses.A_BOLD
        for x in range(0, w, 2):
            speed = 1 + (x % 2)
            head_y = ((tick * 3) // speed + (x * 11)) % (h + 8)
            for dy in range(6):
                y = head_y - dy
                if 0 <= y < h:
                    char = chr(random.randint(33, 126)) if random.random() > 0.05 else " "
                    attr = WHITE if dy == 0 else (bright_color if dy == 1 else base_color)
                    try:
                        stdscr.addstr(y, x, char, attr)
                    except Exception:
                        pass
        return

    for y in range(h):
        if current_anim_idx == 0:
            attr_c = get_aura_color(13)
            for x in range(0, w, 2):
                drop_y = (tick // (1 + (x % 3)) + hash(str(x))) % (h + 8)
                if y == drop_y or drop_y - 3 < y < drop_y:
                    try:
                        stdscr.addstr(y, x, chr(random.randint(33, 126)), attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 1:
            attr_c = get_aura_color(11)
            for x in range(w):
                wave_y = int((math.sin(x * 0.15 + tick * 0.4) + 1) / 2 * (h - 1))
                wave2_y = int((math.cos(x * 0.1 - tick * 0.2) + 1) / 2 * (h - 1))
                if y == wave_y or y == wave2_y:
                    try:
                        stdscr.addstr(y, x, "≈", attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 2:
            attr_c = get_aura_color(14)
            chars = " .-+*#%@"
            for x in range(w):
                v = math.sin(x * 0.1 + tick * 0.2) + math.sin(y * 0.3 + tick * 0.3)
                idx = max(0, min(len(chars) - 1, int((v + 2) / 4 * len(chars))))
                if chars[idx] != ' ':
                    try:
                        stdscr.addstr(y, x, chars[idx], attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 3:
            attr_c = get_aura_color(15)
            for x in range(w):
                star_pos = (hash(str(y)) - tick * (1 + hash(str(y)) % 3)) % w
                if x == star_pos:
                    try:
                        stdscr.addstr(y, x, "★" if hash(str(x * y)) % 5 == 0 else "·", attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 4:
            attr_c = get_aura_color(12)
            for x in range(w):
                w1 = int((math.sin(x * 0.1 + tick * 0.3) + 1) / 2 * (h - 1))
                w2 = int((math.cos(x * 0.1 + tick * 0.3) + 1) / 2 * (h - 1))
                if y == w1 and y == w2:
                    char = "X"
                elif y == w1:
                    char = "/" if math.cos(x * 0.1 + tick * 0.3) > 0 else "\\"
                elif y == w2:
                    char = "\\" if math.cos(x * 0.1 + tick * 0.3) > 0 else "/"
                elif min(w1, w2) < y < max(w1, w2) and x % 4 == 0:
                    char = "|"
                else:
                    char = " "
                if char != " ":
                    try:
                        stdscr.addstr(y, x, char, attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 5:
            attr_c = get_aura_color(10)
            chars = " .,:;+*#@"
            for x in range(w):
                intensity = (math.sin(x * 0.3 + tick * 0.7) + math.cos(x * 0.5 - tick * 1.1) + 2) / 4
                height = int(intensity * h) + random.randint(0, 1)
                if y >= h - height:
                    heat = int(((y - (h - height)) / max(1, height)) * (len(chars) - 1))
                    try:
                        stdscr.addstr(y, x, chars[min(len(chars) - 1, heat)], attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 6:
            attr_c = get_aura_color(2)
            for x in range(w):
                drift = int(math.sin(tick * 0.1 + y * 0.5) * 4)
                drop_y = (tick // 3 + hash(str(x - drift))) % h
                if y == drop_y and hash(str(x)) % 5 == 0:
                    try:
                        stdscr.addstr(y, x, "❄" if hash(str(x * y)) % 3 == 0 else "*", attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 7:
            attr_c = get_aura_color(10)
            cx, cy = w // 2, h // 2
            for x in range(w):
                dist = math.sqrt((x - cx) ** 2 + ((y - cy) * 3) ** 2)
                v = math.sin(dist * 0.4 - tick * 0.6)
                if v > 0.7:
                    char = "█"
                elif v > 0.4:
                    char = "▓"
                else:
                    char = " "
                if char != " ":
                    try:
                        stdscr.addstr(y, x, char, attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 8:
            attr_c = get_aura_color(11)
            for x in range(w):
                eq_h = (math.sin(x * 0.2 + tick * 0.6) + math.cos(x * 0.4 - tick * 0.4) + 2) / 4
                bar_top = h - int(eq_h * h) - 1
                if y > bar_top:
                    try:
                        stdscr.addstr(y, x, "█", attr_c)
                    except Exception:
                        pass
                elif y == bar_top:
                    try:
                        stdscr.addstr(y, x, "▄", attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 9:
            attr_c = get_aura_color(21)
            for x in range(0, w, 2):
                drop_y = (tick // (1 + (x % 3)) + hash(str(x))) % (h + 8)
                if y == drop_y or drop_y - 4 < y < drop_y:
                    try:
                        stdscr.addstr(y, x, chr(random.randint(33, 126)), attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 10:
            attr_c = get_aura_color(14)
            cx, cy = w // 2, h // 2
            for x in range(w):
                dist = math.sqrt((x - cx) ** 2 + ((y - cy) * 2.5) ** 2)
                if int(dist - tick * 0.8) % 12 == 0:
                    try:
                        stdscr.addstr(y, x, "◎", attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 11:
            attr_c = get_aura_color(15)
            for x in range(w):
                y1 = int(h // 2 + math.sin(x * 0.15 + tick * 0.3) * (h // 3))
                y2 = int(h // 2 + math.sin(x * 0.15 + tick * 0.3 + math.pi) * (h // 3))
                if y == y1:
                    try:
                        stdscr.addstr(y, x, "▤", attr_c)
                    except Exception:
                        pass
                elif y == y2:
                    try:
                        stdscr.addstr(y, x, "▥", get_aura_color(12))
                    except Exception:
                        pass
                elif min(y1, y2) < y < max(y1, y2) and x % 6 == 0:
                    try:
                        stdscr.addstr(y, x, "|", get_aura_color(11))
                    except Exception:
                        pass
        elif current_anim_idx == 12:
            attr_c = get_aura_color(2)
            cx, cy = w // 2, h // 2
            for x in range(w):
                dist = math.sqrt((x - cx) ** 2 + ((y - cy) * 2) ** 2)
                ang = math.atan2((y - cy) * 2, x - cx)
                if int(dist - tick * 2) % 15 == 0 and hash(str(int(ang * 10))) % 4 == 0:
                    try:
                        stdscr.addstr(y, x, "✦" if hash(str(x)) % 2 == 0 else ".", attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 13:
            attr_c = get_aura_color(13)
            for x in range(0, w, 4):
                speed = 2 + (hash(str(x)) % 3)
                bubble_y = h - ((tick // speed + hash(str(x))) % (h + 5))
                if y == bubble_y:
                    char = ["o", "O", "°", "0", "@"][hash(str(x)) % 5]
                    try:
                        stdscr.addstr(y, x, char, attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 14:
            attr_c = get_aura_color(10)
            if hash(str(tick + y)) % 5 == 0:
                for x in range(w):
                    if hash(str(tick + x + y)) % 4 == 0:
                        try:
                            stdscr.addstr(y, x, random.choice(["█", "▓", "▒", "░", "≡"]), attr_c)
                        except Exception:
                            pass
        elif current_anim_idx == 15:
            attr_c1 = get_aura_color(11)
            attr_c2 = get_aura_color(14)
            for x in range(w):
                if (x + y * 2 - tick) % 25 == 0:
                    try:
                        stdscr.addstr(y, x, "/", attr_c1)
                    except Exception:
                        pass
                elif (x - y * 2 + tick) % 25 == 0:
                    try:
                        stdscr.addstr(y, x, "\\", attr_c2)
                    except Exception:
                        pass
        elif current_anim_idx == 16:
            attr_c = get_aura_color(15)
            if y % 3 == 0:
                for x in range(0, w, 4):
                    pulse = math.sin(x * 0.1 + y * 0.2 + tick * 0.3)
                    char = "┼" if pulse > 0.6 else ("·" if pulse > 0.1 else " ")
                    if char != " ":
                        try:
                            stdscr.addstr(y, x, char, attr_c)
                        except Exception:
                            pass
        elif current_anim_idx == 17:
            attr_c = get_aura_color(12)
            for x in range(w):
                drop_pos = (tick + hash(str(x))) % (h + 10)
                if y == drop_pos or drop_pos - 6 < y < drop_pos:
                    char = "1" if random.random() > 0.5 else "0"
                    try:
                        stdscr.addstr(y, x, char, attr_c)
                    except Exception:
                        pass
        elif current_anim_idx == 18:
            for x in range(w):
                for i in range(2):
                    cx = hash(str((tick // 15) + i * 10)) % w
                    cy = hash(str((tick // 15) + i * 10 + 100)) % (h // 2 + h // 4)
                    radius = (tick % 15)
                    dist = math.sqrt((x - cx) ** 2 + ((y - cy) * 2) ** 2)
                    if abs(dist - radius) < 1.0:
                        attr_c = get_aura_color(10 + i + (tick // 15) % 4)
                        try:
                            stdscr.addstr(y, x, "✦" if hash(str(x + y)) % 2 == 0 else "✧", attr_c)
                        except Exception:
                            pass


def draw_ui(stdscr):
    global tick, lyrics_scroll, last_scroll_time, is_downloading, dl_progress_text
    global auto_dj, aura_mode, x3_vis, ACTIVE_ENGINE_IDX, ui_mode

    stdscr.erase()
    h, w = stdscr.getmaxyx()
    if anim_enabled:
        draw_full_screen_animations(stdscr, h, w, tick)

    box_w = min(w - 4, 85)
    box_h = 24
    content_w = box_w - 4

    if h < box_h or w < 40:
        try:
            stdscr.addstr(0, 0, "Terminal Window too small!", curses.color_pair(2) | curses.A_BOLD)
        except Exception:
            pass
        return

    start_y = max(0, (h - box_h) // 2)
    start_x = max(0, (w - box_w) // 2)

    for fill_y in range(start_y, start_y + box_h):
        try:
            stdscr.addstr(fill_y, start_x, " " * box_w, curses.color_pair(2))
        except Exception:
            pass

    BORDER_CYAN = curses.color_pair(1) | (curses.A_BOLD if tick % 15 < 7 else curses.A_NORMAL)
    dynamic_color = curses.color_pair(10 + (tick // 3) % 6) | curses.A_BOLD
    LOGO_COLOR = dynamic_color if is_playing else curses.color_pair(1) | curses.A_BOLD
    WHITE_BOLD = curses.color_pair(2) | curses.A_BOLD
    NORMAL = curses.color_pair(2)
    DIM = curses.color_pair(2) | curses.A_DIM
    ACTIVE_TXT = curses.color_pair(3) | curses.A_BOLD
    INFO_TXT = curses.color_pair(4) | curses.A_BOLD
    HEART_COLOR = curses.color_pair(5) | curses.A_BOLD
    ALERT_COLOR = curses.color_pair(10) | curses.A_BOLD

    logo = [
        "╦═╗┌─┐┌─┐┌─┐┌─┐┬ ┬ ┬ ┬  ─┐ ┬",
        "╠╦╝│ │├┤ ├─┘├─┤│ └┬┘└─┐  ┌┴┬┐",
        "╩╚═└─┘└  ┴  ┴ ┴┴─┘┴ └─┘  ┴ └─"
    ]
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'][tick % 10]
    row = start_y

    safe_addstr(stdscr, row, start_x, "╔" + "═" * (box_w - 2) + "╗", BORDER_CYAN, box_w); row += 1
    for line in logo:
        safe_addstr(stdscr, row, start_x, "║", BORDER_CYAN, 1)
        safe_addstr(stdscr, row, start_x + 1, line.center(box_w - 2), LOGO_COLOR, box_w - 2)
        safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1
    safe_addstr(stdscr, row, start_x, "╠" + "═" * (box_w - 2) + "╣", BORDER_CYAN, box_w); row += 1

    tab_playlist = " [ PLAYLIST ] " if ui_mode == 'playlist' else "  PLAYLIST  "
    tab_lyrics = " [ LYRICS ] " if ui_mode == 'lyrics' else "   LYRICS   "
    tab_visual = " [ VISUALIZER ] " if ui_mode == 'visualizer' else "  VISUALIZER  "

    tab_menu = f" {tab_playlist} │ {tab_lyrics} │ {tab_visual} "
    safe_addstr(stdscr, row, start_x, "║", BORDER_CYAN, 1)
    safe_addstr(stdscr, row, start_x + 1, tab_menu.center(box_w - 2), dynamic_color | curses.A_BOLD, box_w - 2)
    safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1
    safe_addstr(stdscr, row, start_x, "╠" + "═" * (box_w - 2) + "╣", BORDER_CYAN, box_w); row += 1

    if is_downloading:
        dl_str = f"{spinner} [YT-DLP] {dl_progress_text}"
        safe_addstr(stdscr, row, start_x, "║", BORDER_CYAN, 1)
        safe_addstr(stdscr, row, start_x + 2, dl_str.ljust(content_w), ALERT_COLOR, content_w)
        safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1
        safe_addstr(stdscr, row, start_x, "╠" + "═" * (box_w - 2) + "╣", BORDER_CYAN, box_w); row += 1
    elif is_searching:
        search_disp = f"{spinner} {t('search')}{search_query}" + ("█" if tick % 10 < 5 else "_")
        safe_addstr(stdscr, row, start_x, "║", BORDER_CYAN, 1)
        safe_addstr(stdscr, row, start_x + 2, search_disp.ljust(content_w), INFO_TXT, content_w)
        safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1
        safe_addstr(stdscr, row, start_x, "╠" + "═" * (box_w - 2) + "╣", BORDER_CYAN, box_w); row += 1

    max_view = 6
    active_lyric_idx, active_lyric_text = -1, ""
    if is_synced_lyrics and is_playing:
        for idx, (sec, l_text) in enumerate(synced_lyrics):
            if current_time_seconds >= sec:
                active_lyric_idx, active_lyric_text = idx, l_text
            else:
                break
        if time.time() - last_scroll_time > 3.0:
            lyrics_scroll = max(0, active_lyric_idx - (max_view // 2))

    if ui_mode == 'playlist':
        start_win = max(0, min(selected_idx - max_view // 2, max(0, len(songs) - max_view)))
        for i in range(start_win, start_win + max_view):
            safe_addstr(stdscr, row, start_x, "║ ", BORDER_CYAN, 2)
            if i < len(songs):
                song_raw = songs[i]
                song_name = os.path.splitext(song_raw)[0]
                is_active = (song_raw == playing_song_name)
                is_fav = (song_raw in favorites)
                max_title_w = max(4, content_w - 20)
                display_title = song_name[:max_title_w]
                if is_active and len(song_name) > max_title_w:
                    scroll_pos = (tick // 3) % (len(song_name) + 4)
                    display_title = (song_name + " • " + song_name)[scroll_pos: scroll_pos + max_title_w]

                attr = WHITE_BOLD if i == selected_idx else (ACTIVE_TXT if is_active else NORMAL)
                safe_addstr(stdscr, row, start_x + 2, "➤ " if i == selected_idx else "  ", attr, 2)
                safe_addstr(stdscr, row, start_x + 4, "♥ " if is_fav else "  ", HEART_COLOR if is_fav else NORMAL, 2)
                safe_addstr(stdscr, row, start_x + 6, f"{i + 1:02d}. {display_title:<{max_title_w}}", attr, max_title_w)
                if is_active and is_playing:
                    wave = get_wave_equalizer(tick)
                    safe_addstr(stdscr, row, start_x + 6 + max_title_w, wave, dynamic_color, len(wave))
            else:
                safe_addstr(stdscr, row, start_x + 2, " " * content_w, NORMAL, content_w)
            safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1

    elif ui_mode == 'lyrics':
        safe_addstr(stdscr, row, start_x, "║", BORDER_CYAN, 1)
        safe_addstr(stdscr, row, start_x + 1, t('lyric_title').center(box_w - 2), INFO_TXT, box_w - 2)
        safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1
        for i in range(lyrics_scroll, lyrics_scroll + max_view - 1):
            safe_addstr(stdscr, row, start_x, "║ ", BORDER_CYAN, 2)
            if i < len(current_lyrics):
                if i == active_lyric_idx and is_playing:
                    text = f" {current_lyrics[i]} "
                    pad = max(0, (content_w - len(text)) // 2)
                    safe_addstr(stdscr, row, start_x + 2, " " * pad, NORMAL, pad)
                    safe_addstr(stdscr, row, start_x + 2 + pad, text, dynamic_color | curses.A_REVERSE | curses.A_BOLD, len(text))
                    safe_addstr(stdscr, row, start_x + 2 + pad + len(text), " " * max(0, content_w - len(text) - pad), NORMAL, content_w)
                else:
                    attr = WHITE_BOLD if is_synced_lyrics and i == active_lyric_idx + 1 else (DIM if is_synced_lyrics and i < active_lyric_idx else NORMAL)
                    safe_addstr(stdscr, row, start_x + 2, current_lyrics[i].center(content_w), attr, content_w)
            else:
                safe_addstr(stdscr, row, start_x + 2, " " * content_w, NORMAL, content_w)
            safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1

    elif ui_mode == 'visualizer':
        safe_addstr(stdscr, row, start_x, "║", BORDER_CYAN, 1)
        safe_addstr(stdscr, row, start_x + 1, t('visual_title').center(box_w - 2), dynamic_color, box_w - 2)
        safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1
        vis_h = max_view - 1
        bars_count = content_w
        for y_vis in range(vis_h):
            safe_addstr(stdscr, row, start_x, "║ ", BORDER_CYAN, 2)
            line_str = ""
            for b in range(bars_count):
                if is_playing:
                    bass_surge = math.sin(tick * 0.4) * 0.3 if b % 4 == 0 else 0.0
                    interference = (math.sin(tick * 0.3 + b * 0.2) + math.cos(tick * 0.15 - b * 0.4) + 2) / 4
                    pulse = random.random() * 0.3 * (math.sin(tick * 0.6) + 1)
                    val = min(1.0, interference + pulse + bass_surge)
                    if x3_vis:
                        val = min(1.0, val * 1.5)
                else:
                    val = 0.0

                threshold = 1.0 - (y_vis / vis_h)
                if val >= threshold:
                    line_str += "█"
                elif val >= threshold - (1 / (vis_h * 2)):
                    line_str += "▓"
                else:
                    if is_playing and (b + y_vis + tick) % 17 == 0:
                        line_str += "✧"
                    elif is_playing and (b * y_vis - tick) % 29 == 0:
                        line_str += "·"
                    else:
                        line_str += " "
            safe_addstr(stdscr, row, start_x + 2, line_str[:content_w].center(content_w), dynamic_color, content_w)
            safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1

    if ui_mode != 'lyrics' and is_playing and active_lyric_text:
        safe_addstr(stdscr, row, start_x, "╠" + "═" * (box_w - 2) + "╣", BORDER_CYAN, box_w); row += 1
        safe_addstr(stdscr, row, start_x, "║ ", BORDER_CYAN, 2)
        floating_text = f" 🎤 {active_lyric_text} "
        if len(floating_text) > content_w:
            scroll_p = (tick // 3) % (len(active_lyric_text))
            floating_text = f" 🎤 {(active_lyric_text + ' • ' + active_lyric_text)[scroll_p: scroll_p + content_w - 6]} "
        safe_addstr(stdscr, row, start_x + 2, floating_text.center(content_w), dynamic_color | curses.A_REVERSE | curses.A_BOLD, content_w)
        safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1

    safe_addstr(stdscr, row, start_x, "╠" + "═" * (box_w - 2) + "╣", BORDER_CYAN, box_w); row += 1
    engine_name = AVAILABLE_ENGINES[ACTIVE_ENGINE_IDX]['name'].upper() if AVAILABLE_ENGINES else "NONE"
    active_title = os.path.splitext(playing_song_name)[0] if playing_song_name else t('no_music')
    mode_indicators = f"{'[AUTO-DJ]' if auto_dj else ''}{'[AURA]' if aura_mode else ''}{'[X3]' if x3_vis else ''}{'[ANIM OFF]' if not anim_enabled else ''}"

    show_warning = bool(engine_status_msg) and (time.time() - engine_status_time < 4.0)
    if show_warning:
        track_disp = f"⚠ {engine_status_msg}"
        track_attr = ALERT_COLOR
    else:
        track_disp = f"[{engine_name}] {active_title[:max(1, content_w - 28)]} [{get_mode_string()}] {mode_indicators}"
        track_attr = WHITE_BOLD

    safe_addstr(stdscr, row, start_x, "║ ", BORDER_CYAN, 2)
    safe_addstr(stdscr, row, start_x + 2, track_disp.center(content_w), track_attr, content_w)
    safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1

    time_line = f"{current_time_str}  {generate_smooth_progressbar(progress_pct, content_w - 16, tick)}  {total_time_str}"
    safe_addstr(stdscr, row, start_x, "║ ", BORDER_CYAN, 2)
    safe_addstr(stdscr, row, start_x + 2, time_line.center(content_w), LOGO_COLOR, content_w)
    safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1

    safe_addstr(stdscr, row, start_x, "╠" + "═" * (box_w - 2) + "╣", BORDER_CYAN, box_w); row += 1
    safe_addstr(stdscr, row, start_x, "║ ", BORDER_CYAN, 2)
    safe_addstr(stdscr, row, start_x + 2, t('ctrl_1').center(content_w), NORMAL, content_w)
    safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1

    safe_addstr(stdscr, row, start_x, "║ ", BORDER_CYAN, 2)
    safe_addstr(stdscr, row, start_x + 2, t('ctrl_2').center(content_w), NORMAL, content_w)
    safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1

    safe_addstr(stdscr, row, start_x, "║ ", BORDER_CYAN, 2)
    safe_addstr(stdscr, row, start_x + 2, t('ctrl_3').center(content_w), NORMAL, content_w)
    safe_addstr(stdscr, row, start_x + box_w - 1, "║", BORDER_CYAN, 1); row += 1

    safe_addstr(stdscr, row, start_x, "╚" + "═" * (box_w - 2) + "╝", BORDER_CYAN, box_w); row += 1


def main(stdscr):
    global songs_all, songs, exit_flag, tick, is_searching, search_query
    global auto_dj, aura_mode, x3_vis, ACTIVE_ENGINE_IDX, ui_mode, play_mode
    global current_lang, selected_idx, lyrics_scroll, last_scroll_time, current_anim_idx, last_anim_time, favorites
    global anim_enabled

    load_favorites()
    load_settings()
    refresh_playlist()

    try:
        curses.curs_set(0)
    except Exception:
        pass
    stdscr.keypad(True)
    stdscr.timeout(80)
    curses.start_color()
    try:
        curses.use_default_colors()
    except Exception:
        pass

    def _safe_init_pair(n, fg, bg):
        try:
            curses.init_pair(n, fg, bg)
        except Exception:
            pass

    for i, c in enumerate([curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_MAGENTA]):
        _safe_init_pair(i + 1, c, -1)
    for i, c in enumerate([curses.COLOR_RED, curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_MAGENTA, curses.COLOR_YELLOW]):
        _safe_init_pair(i + 10, c, -1)
        _safe_init_pair(i + 20, c, -1)

    key_buffer = ""
    buffer_time = 0.0
    last_anim_time = time.time()

    try:
        while not exit_flag:
            draw_ui(stdscr)
            stdscr.refresh()
            tick += 1

            if key_buffer and time.time() - buffer_time > 0.8:
                key_buffer = ""
            try:
                ch = stdscr.getch()
            except Exception:
                continue

            if ch == -1:
                continue
            if ch == curses.KEY_RESIZE:
                stdscr.clear()
                continue

            if is_searching:
                if ch in [27, 10, 13, curses.KEY_ENTER]:
                    is_searching = False
                elif ch in (curses.KEY_BACKSPACE, 127, 8):
                    search_query = search_query[:-1]
                    update_search()
                elif 32 <= ch <= 126:
                    search_query += chr(ch)
                    update_search()
                continue

            if ch == curses.KEY_UP:
                if ui_mode == 'playlist' and selected_idx > 0:
                    selected_idx -= 1
                elif ui_mode == 'lyrics' and lyrics_scroll > 0:
                    lyrics_scroll -= 1
                    last_scroll_time = time.time()
                continue
            elif ch == curses.KEY_DOWN:
                if ui_mode == 'playlist' and selected_idx < len(songs) - 1:
                    selected_idx += 1
                elif ui_mode == 'lyrics' and lyrics_scroll < max(0, len(current_lyrics) - 1):
                    lyrics_scroll += 1
                    last_scroll_time = time.time()
                continue

            # ENTER harus dicek terpisah: kode 10/13/KEY_ENTER ada DI LUAR
            # rentang 32-126, jadi kalau dicek di dalam blok karakter biasa
            # (seperti sebelumnya) Enter tidak akan pernah terdeteksi sama sekali.
            if ch in (10, 13, curses.KEY_ENTER):
                if ui_mode == 'playlist' and songs:
                    play_song(songs[selected_idx])
                key_buffer = ""
                continue

            if 32 <= ch <= 126:
                char_str = chr(ch)
                key_buffer += char_str
                buffer_time = time.time()
                buf_lower = key_buffer.lower()

                if buf_lower == "7xz" and AVAILABLE_ENGINES:
                    ACTIVE_ENGINE_IDX = (ACTIVE_ENGINE_IDX + 1) % len(AVAILABLE_ENGINES)
                    key_buffer = ""
                    continue
                elif buf_lower == "4a":
                    aura_mode = not aura_mode
                    key_buffer = ""
                    continue
                elif buf_lower == "x3":
                    x3_vis = not x3_vis
                    key_buffer = ""
                    continue
                elif buf_lower == "1b":
                    current_anim_idx = (current_anim_idx + 1) % TOTAL_ANIMATIONS
                    last_anim_time = time.time()
                    key_buffer = ""
                    continue
                elif buf_lower == "2e":
                    anim_enabled = not anim_enabled
                    save_settings()
                    key_buffer = ""
                    continue

                if len(key_buffer) == 1:
                    c = key_buffer.lower()
                    if c == 'q':
                        exit_flag = True
                        break
                    elif c == 'w':
                        if ui_mode == 'playlist' and songs:
                            play_song(songs[selected_idx])
                    elif c == 'f':
                        toggle_play()
                    elif c == 'v':
                        is_searching = True
                        search_query = ""
                        update_search()
                    elif c == 'p' and playing_song_name:
                        try:
                            play_song(songs_all[(songs_all.index(playing_song_name) - 1) % len(songs_all)])
                        except Exception:
                            pass
                    elif c == 'n' and playing_song_name:
                        try:
                            play_song(songs_all[(songs_all.index(playing_song_name) + 1) % len(songs_all)])
                        except Exception:
                            pass
                    elif c == 'm':
                        play_mode = (play_mode + 1) % 5
                    elif c == 'r':
                        deep_reset()
                    elif c == 'l':
                        if ui_mode == 'playlist' and songs:
                            s = songs[selected_idx]
                            favorites.remove(s) if s in favorites else favorites.add(s)
                            save_favorites()
                    elif c == 'z':
                        ui_mode = 'playlist' if ui_mode == 'lyrics' else 'lyrics'
                        last_scroll_time = 0.0
                    elif c == 'c':
                        ui_mode = 'playlist' if ui_mode == 'visualizer' else 'visualizer'
                    elif c == 'x':
                        idx = SUPPORTED_LANGS.index(current_lang) if current_lang in SUPPORTED_LANGS else 0
                        current_lang = SUPPORTED_LANGS[(idx + 1) % len(SUPPORTED_LANGS)]
                        save_settings()
                    elif c == 'a':
                        auto_dj = not auto_dj
                    elif c == 'y':
                        curses.endwin()
                        print("\n=== DOWNLOAD AUDIO DARI YOUTUBE (Otomatis Putar) ===")
                        try:
                            url_input = input("Masukkan URL YouTube: ").strip()
                        except (EOFError, KeyboardInterrupt):
                            url_input = ""
                        if url_input:
                            threading.Thread(target=download_and_play_yt, args=(url_input,), daemon=True).start()
                        stdscr.clear()
                        try:
                            curses.curs_set(0)
                        except Exception:
                            pass
                        stdscr.keypad(True)

    finally:
        exit_flag = True
        if current_process:
            try:
                current_process.terminate()
            except Exception:
                pass
        try:
            if "PyGame" in [e["name"] for e in AVAILABLE_ENGINES]:
                import pygame
                pygame.mixer.music.stop()
        except Exception:
            pass


if __name__ == '__main__':
    # Console startup text ini permanen bahasa Inggris (tidak terikat [X]).
    print("Detecting audio player on this system...")
    if AVAILABLE_ENGINES:
        print("Engine detected: " + ", ".join(e["name"] for e in AVAILABLE_ENGINES))
        print(f"Active engine (default): {AVAILABLE_ENGINES[0]['name']}")
    else:
        print("WARNING: No audio player detected on this system.")
        print("Install one of these before running the program:")
        print("  - mpv             : https://mpv.io")
        print("  - ffmpeg (ffplay) : https://ffmpeg.org")
        print("  - VLC             : https://videolan.org")
        print("  - or run: pip install pygame")
        print()
        print("The program will still run (playlist & lyrics still work),")
        print("but no audio will play until one of the above is installed.")
    print("Playlist found:", len(get_audio_files()), "audio files in this folder.")
    print("Launching the interface in 2 seconds...")
    time.sleep(2)
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("The program has stopped safely.")
        sys.exit(1)

