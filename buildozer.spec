[app]
# (str) Title of your application
title = Floww

# (str) Package name
package.name = floww

# (str) Package domain (unique reverse domain-style identifier)
package.domain = com.example

# (str) Source code where your main.py is located
source.dir = .

# (str) Main script to run
source.include_exts = py,png,jpg,kv,atlas

# (list) Permissions required by your application
android.permissions = INTERNET

# (str) Application version
version = 1.0

# (str) Supported orientation (one of: landscape, portrait, all)
orientation = portrait

# (bool) Indicate if the application is fullscreen
fullscreen = 1

# (str) Presplash of the application
presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/data/icon.png

# (str) Supported platforms for Android
# Ensure only Android is set here
android.archs = armeabi-v7a, arm64-v8a

# (list) Add additional Java .jar or .aar libraries
android.add_jars =

# (list) Gradle dependencies to add
android.gradle_dependencies =

# (str) Minimum API level for Android
android.minapi = 21

# (str) Android SDK path
android.sdk_path = D:\Android

# (str) Android NDK path
android.ndk_path = D:\Android\ndk

# (str) Application entry point
entrypoint = main.py

[buildozer]
# (str) Log level (one of: info, debug, error, warning)
log_level = 2

# (bool) Automatically accept SDK license agre
