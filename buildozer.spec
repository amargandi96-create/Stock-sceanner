[app]
# Nama aplikasi
title = Value Stock Screener

# Nama package (harus unik, format: domain.nama)
package.name = valuestockscreener
package.domain = com.myapp

# File utama
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Versi
version = 1.0

# Dependensi Python yang dibutuhkan
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,charset-normalizer,idna

# Orientasi layar
orientation = portrait

# Android target
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.api = 33
android.accept_sdk_license = True
android.build_tools_version = 33.0.2
android.archs = arm64-v8a, armeabi-v7a

# Izin yang dibutuhkan
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# Icon & splash (ganti dengan file Anda sendiri)
# android.icon = assets/icon.png
# android.presplash = assets/presplash.png

# Warna splash screen
android.presplash_color = #0f1828

# Fullscreen
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
