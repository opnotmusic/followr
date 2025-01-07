[app]
title = Social Media Bot
package.name = social_media_bot
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,python-dotenv,cryptography,sqlite3,requests,telegram,matplotlib
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
presplash.filename = presplash.png
icon.filename = icon.png

[buildozer]
log_level = 2
warn_on_root = 1
