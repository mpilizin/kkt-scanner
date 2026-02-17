[app]
title = Проверка Чеков
package.name = kktscanner
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0

# ВАЖНО:
# 1. pyzbar - оставляем (это питон-библиотека).
# 2. zbar/libzbar - УБРАЛИ (из-за них была ошибка "Command failed").
# 3. pillow, openssl - нужны, чтобы не вылетало.
requirements = python3, kivy==2.3.0, kivymd, requests, urllib3, certifi, idna, charset-normalizer, pillow, openssl, pyzbar

orientation = portrait
fullscreen = 0

# Разрешения (Интернет + Камера)
android.permissions = INTERNET, CAMERA, RECORD_AUDIO

# Настройки Android
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
