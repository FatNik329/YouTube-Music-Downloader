import yt_dlp
import time
import os
import subprocess
from datetime import datetime

# Конфигурация
PLAYLIST_URL = "https://www.youtube.com/playlist?list=<Your_Playlist_YouTube>"  # Заменить на свой плейлист
SAVE_PATH = "/path/to/save/local/playlist"  # Директория для сохранения
AUDIO_QUALITY = "192"  # 128, 192, 320 (kbps)
DELAY_BETWEEN_DOWNLOADS = 5  # Задержка между треками (секунды)
SKIP_EXISTING = True  # Пропускать уже скачанные файлы
LOG_FILE = "logs/playlist-<Your_Playlist_YouTube>.log"  # Файл логов плейлиста - изменить на название скрипта

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except:
        return False

# Логирование
def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)

if not check_ffmpeg():
    log("❌ FFmpeg не установлен! Скачать: https://ffmpeg.org/")
    exit(1)

def download_playlist(url):
    try:
        # Конфигурация для получения информации о плейлисте
        ydl_info = yt_dlp.YoutubeDL({
            'ignoreerrors': True,
            'extract_flat': True,
            'socket_timeout': 30,
            'source_address': '0.0.0.0',
            'quiet': True
        })

        info = ydl_info.extract_info(url, download=False)

        if not info or 'entries' not in info:
            log("❌ Не удалось получить данные плейлиста")
            return

        playlist_title = info.get('title', 'unknown_playlist').replace('/', '_')
        playlist_dir = os.path.join(SAVE_PATH, playlist_title)
        os.makedirs(playlist_dir, exist_ok=True)

        log(f"🎵 Плейлист: {playlist_title} ({len(info['entries'])} треков)")
        log(f"📁 Папка: {playlist_dir}")

        # Основные параметры загрузки
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{playlist_dir}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': AUDIO_QUALITY,
            }],
            'ignoreerrors': True,
            'quiet': True,
            'retries': 3,
            'fragment_retries': 3,
            'socket_timeout': 30,
            'source_address': '0.0.0.0',
            # Убираем все специфичные клиенты и токены
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls']
                }
            },
            # Альтернативные стратегии загрузки
            'format_sort': ['ext:mp3:m4a', 'vcodec:none'],
            'allow_multiple_video_streams': True,
            'allow_multiple_audio_streams': True,
            # User-Agent
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.youtube.com/',
                'Origin': 'https://www.youtube.com',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'DNT': '1',
            }
        }

        downloaded = 0
        skipped = 0
        failed = 0

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for i, entry in enumerate(info['entries'], 1):
                if not entry:
                    failed += 1
                    log(f"❌ [{i}/{len(info['entries'])}] Пустая запись в плейлисте")
                    continue

                video_id = entry.get('id')
                video_url = f"https://youtu.be/{video_id}" if video_id else entry.get('url')
                video_title = entry.get('title', f'Трек {i}').replace('/', '_')
                output_file = f"{playlist_dir}/{video_title}.mp3"

                if SKIP_EXISTING and os.path.exists(output_file):
                    log(f"⏩ [{i}/{len(info['entries'])}] Пропущен: {video_title} (уже есть)")
                    skipped += 1
                    continue

                try:
                    # Стратегия 1: Стандартная загрузка
                    try:
                        ydl.download([video_url])
                        if os.path.exists(output_file):
                            log(f"✅ [{i}/{len(info['entries'])}] Загружен: {video_title} (стандарт)")
                            downloaded += 1
                            continue
                    except Exception as e:
                        log(f"⚠️ [{i}/{len(info['entries'])}] Стандартный метод: {str(e)}")

                    # Стратегия 2: Альтернативный URL
                    try:
                        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
                        if os.path.exists(output_file):
                            log(f"✅ [{i}/{len(info['entries'])}] Загружен: {video_title} (альтернативный URL)")
                            downloaded += 1
                            continue
                    except Exception as e:
                        log(f"⚠️ [{i}/{len(info['entries'])}] Альтернативный URL: {str(e)}")

                    # Стратегия 3: Embed-страница
                    try:
                        ydl.download([f"https://www.youtube.com/embed/{video_id}"])
                        if os.path.exists(output_file):
                            log(f"✅ [{i}/{len(info['entries'])}] Загружен: {video_title} (embed URL)")
                            downloaded += 1
                            continue
                    except Exception as e:
                        log(f"⚠️ [{i}/{len(info['entries'])}] Embed метод: {str(e)}")

                    # Если все попытки не удались
                    log(f"❌ [{i}/{len(info['entries'])}] Ошибка: {video_title} (все методы не сработали)")
                    failed += 1

                except Exception as e:
                    log(f"❌ [{i}/{len(info['entries'])}] Критическая ошибка: {video_title} ({str(e)})")
                    failed += 1

                time.sleep(DELAY_BETWEEN_DOWNLOADS)

        log(f"\nИтог: Загружено - {downloaded}, Пропущено - {skipped}, Ошибок - {failed}")

    except Exception as e:
        log(f"🔥 Критическая ошибка: {str(e)}")

if __name__ == "__main__":
    log("="*30)
    log("🚀 Запуск скачивания плейлиста")
    download_playlist(PLAYLIST_URL)
    log("✅ Скрипт завершил работу\n")
