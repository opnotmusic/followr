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
osx.kivy_version = 2.0.0

# Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE

# Build Options
android.archs = armeabi-v7a, arm64-v8a
package.exclude_dirs = tests, bin, build
android.api = 31
android.minapi = 21
android.ndk = 21b
android.sdk = 20
android.gradle_dependencies = com.android.support:appcompat-v7:28.0.0
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
