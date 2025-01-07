[app]
title = floww
package.name = floww
package.domain = aking
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,cryptography,sqlite3,python-telegram-bot,cython
icon.filename = icons/icon.png
orientation = portrait

# Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE

# Build Options
android.archs = armeabi-v7a, arm64-v8a
android.api = 31
android.minapi = 21
android.ndk = 21b
android.sdk = 20
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
