#!/bin/bash

# PART1 - setup.sh - интерактивный установщик виртуального окружения

# Запрашиваем имя окружения (по умолчанию - env)
read -p "Введите название виртуального окружения [по умолчанию: env]: " venv_name
venv_name=${venv_name:-env}

# Проверяем существует ли окружение
if [ -d "$venv_name" ]; then
    echo "⚠️ Виртуальное окружение '$venv_name' уже существует."
    read -p "Пересоздать? (y/N) " rebuild
    if [[ "$rebuild" =~ ^[Yy]$ ]]; then
        rm -rf "$venv_name"
    else
        echo "Обновляем зависимости в существующем окружении..."
        "$venv_name/bin/pip" install -U -r requirements.txt
        # Удалено exit 0, чтобы скрипт продолжал выполнение
    fi
fi

# Создаём виртуальное окружение (если оно было удалено или не существовало)
if [ ! -d "$venv_name" ]; then
    echo "🛠 Создаём виртуальное окружение '$venv_name'..."
    python3 -m venv "$venv_name"

    # Устанавливаем зависимости
    echo "📦 Устанавливаем зависимости из requirements.txt..."
    "$venv_name/bin/pip" install -U pip setuptools wheel  # Обновляем базовые инструменты
    "$venv_name/bin/pip" install -r requirements.txt
fi

# Создание директории для логов
mkdir logs

# PART2 - Создаём/обновляем run.sh
echo "⚙️ Генерируем run.sh..."
cat > run.sh <<EOF
#!/bin/bash

# Перемещаемся в директорию проекта
real=\$(realpath "\$(dirname "\$0")")
cd "\$real"

# Проверяем, актуальны ли зависимости
$venv_name/bin/pip install -q -r requirements.txt

# Пример запускаемого скрипта
$venv_name/bin/python playlist-Example_Name_Playlist.py # изменить на cвоё название

# Ротируем логи
$venv_name/bin/python logs-rotate.py

EOF


echo "✅ Готово! Запускайте проект командой: ./run.sh"
