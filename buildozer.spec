[app]
title = Organizador Gastos
package.name = organizador
package.domain = org.alandin123
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.exclude_dirs = tests,bin,.buildozer,venv,.venv_buildozer,__pycache__,dist,build
source.exclude_patterns = *_old.py,*.bak
version = 1.0.0

# Sin pydantic (usa Rust, no compila en Android)
# Sin matplotlib (demasiado pesado, no necesario en mobile)
# Sin tkcalendar/tkinter (no existen en Android)
requirements = kivy==2.3.0,kivymd==1.2.0,requests==2.31.0,python-dotenv==1.0.0,Pillow==10.0.0

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a,armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
