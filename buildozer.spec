[app]

# (str) Title of your application
title = Проверка Чеков

# (str) Package name
package.name = kktscanner

# (str) Package domain (needed for android packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning (method 1)
version = 3.0

# (list) Application requirements
# Добавлены: android (для разрешений), certifi и openssl (для https)
requirements = python3, kivy==2.3.0, kivymd==1.2.0, requests, urllib3, certifi, idna, charset-normalizer, pillow, openssl, pyjnius, android

# (str) Supported orientation (one of landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET, CAMERA, RECORD_AUDIO

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android NDK API to use. This is the minimum API your app will support.
android.ndk_api = 21

# (list) Architecture to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# (bool) Use --private data storage (True) or external storage (False)
android.private_storage = True

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) The Android arch to build for
android.arch = arm64-v8a

# (bool) Enable AndroidX support
android.enable_androidx = True

# (list) Gradle dependencies
# Добавлена интеграция ZXing для работы IntentIntegrator из вашего кода
android.gradle_dependencies = 'com.google.zxing:core:3.4.1', 'com.google.zxing:android-integration:3.3.0', 'com.journeyapps:zxing-android-embedded:4.3.0', 'androidx.appcompat:appcompat:1.4.2'

# (bool) If True, then skip trying to update the python-for-android directory.
android.skip_update = False

# (bool) If True, then trust the system CA certs
android.manifest.usesCleartextTraffic = true

# (str) Android entry point, default is to use start.py
android.entrypoint = main.py

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = off, 1 = on)
warn_on_root = 1
