[app]
title = Проверка Чеков
package.name = kktscanner
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 3.0

# 1. pyjnius - мост к Android
# 2. pillow, openssl - защита от вылетов KivyMD
requirements = python3, kivy==2.3.0, kivymd, requests, urllib3, certifi, idna, charset-normalizer, pillow, openssl, pyjnius

orientation = portrait
fullscreen = 0

# Разрешения
android.permissions = INTERNET, CAMERA, RECORD_AUDIO

# ПОДКЛЮЧАЕМ НАТИВНЫЙ СКАНЕР (ZXing)
# Это скачает Java-библиотеки автоматически при сборке
android.gradle_dependencies = com.google.zxing:core:3.4.1, com.journeyapps:zxing-android-embedded:4.3.0, androidx.appcompat:appcompat:1.4.2

# Важно для новых библиотек
android.enable_androidx = True

# Стандартные настройки
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
