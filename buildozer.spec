[app]
title = Value Stock Screener
package.name = valuestockscreener
package.domain = com.myapp
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3,kivy==2.3.0,requests,urllib3,certifi,charset-normalizer,idna

orientation = portrait

android.minapi = 21
android.api = 33
android.ndk = 28c
android.accept_sdk_license = True
android.build_tools_version = 33.0.2
android.archs = arm64-v8a
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.presplash_color = #0f1828

p4a.branch = master
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
