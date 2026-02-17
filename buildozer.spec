[app]
# Название на экране телефона
title = Проверка Чеков

# Технические имена
package.name = kktscanner
package.domain = org.test

# Папка с кодом
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# Версия приложения
version = 1.0

# --- ГЛАВНОЕ: СПИСОК БИБЛИОТЕК ---
# libzbar и pyzbar нужны для QR-кода
# pillow и openssl - чтобы не вылетало
requirements = python3, kivy==2.3.0, kivymd, requests, urllib3, certifi, idna, charset-normalizer, pillow, openssl, pyzbar, libzbar

# Ориентация (портретная, как у всех приложений)
orientation = portrait
fullscreen = 0

# --- РАЗРЕШЕНИЯ ---
# Интернет для проверки, Камера для сканера
android.permissions = INTERNET, CAMERA

# Настройки Android
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21

# Архитектура (одна, чтобы сборка не зависала)
android.archs = arm64-v8a

[buildozer]
# Уровень логов (2 - показывает ошибки)
log_level = 2
warn_on_root = 1
