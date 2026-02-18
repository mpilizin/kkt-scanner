[app]
title = Проверка Чеков
package.name = kktscanner
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 3.0

# Необходимые библиотеки для работы KivyMD и сетевых запросов
requirements = python3, kivy==2.3.0, kivymd==1.2.0, requests, urllib3, certifi, idna, charset-normalizer, pillow, openssl, pyjnius, android

orientation = portrait
fullscreen = 0

# Разрешения для работы сканера и интернета
android.permissions = INTERNET, CAMERA, RECORD_AUDIO

# Параметры SDK/NDK
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a
android.enable_androidx = True

# Современные зависимости для QR-сканера без конфликтов
android.gradle_dependencies = 'com.journeyapps:zxing-android-embedded:4.3.0', 'com.google.zxing:core:3.4.1', 'androidx.appcompat:appcompat:1.4.2'

# Разрешение незащищенного трафика для API
android.manifest.usesCleartextTraffic = true

android.entrypoint = main.py
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 1
