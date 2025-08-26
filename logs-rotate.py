import os
import glob
import gzip
from datetime import datetime

# Конфигурация
LOG_DIR = "logs"  # Директория с логами
MAX_DIR_SIZE_MB = 10  # Максимальный размер папки с логами (МБ)
MAX_LOG_VERSIONS = 3  # Максимальное количество архивных версий логов

def get_dir_size(path):
    """Возвращает размер папки в мегабайтах"""
    total = 0
    for entry in os.scandir(path):
        if entry.is_file():
            total += entry.stat().st_size
    return total / (1024 * 1024)  # Конвертируем в МБ

def rotate_logs():
    print("🔄 Начинаем ротацию логов...")
    current_size = get_dir_size(LOG_DIR)
    print(f"📊 Текущий размер папки: {current_size:.2f} MB")

    # 1. Архивируем текущие логи (кроме уже сжатых)
    archived_count = 0
    current_logs = sorted(
        [f for f in glob.glob(os.path.join(LOG_DIR, "*.log")) if not f.endswith('.gz')],
        key=os.path.getmtime
    )

    for log_file in current_logs:
        try:
            # Проверяем, нужно ли ещё архивировать (по размеру)
            if get_dir_size(LOG_DIR) < MAX_DIR_SIZE_MB:
                break

            # Создаём имя для архива
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_name = f"{log_file}.{timestamp}.gz"

            # Сжимаем лог
            with open(log_file, 'rb') as f_in:
                with gzip.open(archive_name, 'wb') as f_out:
                    f_out.writelines(f_in)

            # Удаляем оригинальный файл
            os.remove(log_file)
            print(f"📦 Заархивирован: {os.path.basename(log_file)} -> {os.path.basename(archive_name)}")
            archived_count += 1
        except Exception as e:
            print(f"⚠️ Ошибка при архивации {log_file}: {str(e)}")

    # 2. Удаляем лишние архивные версии (оставляем только MAX_LOG_VERSIONS)
    all_archives = sorted(
        glob.glob(os.path.join(LOG_DIR, "*.log.*.gz")),
        key=os.path.getmtime,
        reverse=True
    )

    deleted_count = 0
    for old_archive in all_archives[MAX_LOG_VERSIONS:]:
        try:
            os.remove(old_archive)
            print(f"🧹 Удалён старый архив: {os.path.basename(old_archive)}")
            deleted_count += 1
        except Exception as e:
            print(f"⚠️ Ошибка при удалении {old_archive}: {str(e)}")

    print(f"✅ Выполнено. Удалено {deleted_count} архивов, заархивировано {archived_count} логов")
    print(f"📊 Новый размер папки: {get_dir_size(LOG_DIR):.2f} MB")

if __name__ == "__main__":
    if not os.path.exists(LOG_DIR):
        print(f"❌ Папка с логами не найдена: {LOG_DIR}")
        exit(1)

    rotate_logs()
