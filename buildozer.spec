[app]
title = Проверка Чеков
package.name = kktscanner
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 3.0

# Основные требования для KivyMD и вашего API
requirements = python3, kivy==2.3.0, kivymd==1.2.0, requests, urllib3, certifi, idna, charset-normalizer, pillow, openssl, pyjnius, android

orientation = portrait
fullscreen = 0
android.permissions = INTERNET, CAMERA, RECORD_AUDIO

# --- ФИКСАЦИЯ ДЛЯ УСТРАНЕНИЯ ОШИБКИ LICENSE/AIDL ---
android.api = 33
android.minapi = 21
android.build_tools_version = 34.0.0
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.enable_androidx = True
# --------------------------------------------------

android.archs = arm64-v8a

# Оптимизированные зависимости для QR-сканера
android.gradle_dependencies = 'com.journeyapps:zxing-android-embedded:4.3.0', 'com.google.zxing:core:3.4.1', 'androidx.appcompat:appcompat:1.4.2'

# Разрешаем сетевой трафик (нужно для работы с вашим доменом кктрф.рф)
android.manifest.usesCleartextTraffic = true

android.entrypoint = main.py
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 1
