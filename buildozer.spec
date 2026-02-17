[app]
# Название приложения (будет под иконкой)
title = Проверка Чеков

# Техническое имя (только английские буквы)
package.name = kktscanner
package.domain = org.test

# Где лежит код
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# Версия
version = 0.1

# ВАЖНО: Список библиотек (добавлены pillow и openssl от вылетов)
requirements = python3, kivy==2.3.0, kivymd, requests, urllib3, certifi, idna, charset-normalizer, pillow, openssl

# Настройки экрана
orientation = portrait
fullscreen = 0

# Разрешения (Интернет + Камера)
android.permissions = INTERNET, CAMERA

# Настройки Android (современные)
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21

# Архитектура (одна, чтобы GitHub не зависал)
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
