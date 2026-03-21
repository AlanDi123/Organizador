[app]
title = Organizador de Gastos
package.name = organizador_finanzas
package.domain = org.alandin123
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,md,txt
version = 1.0.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests,pillow,Cython==0.29.37
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.release_artifact = apk
android.debug_artifact = apk
android.enable_androidx = True
p4a.bootstrap = sdl2
p4a.arch = arm64-v8a
p4a.extra_args = --ignore-setup-py

[buildozer]
log_level = 2
warn_on_root = 1
debug = 0
