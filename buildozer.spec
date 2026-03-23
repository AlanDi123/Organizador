[app]
title = Organizador de Gastos
package.name = organizador_finanzas
package.domain = org.alandin123
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.exclude_dirs = tests,.git,.github,bin,dist,build,instaladores_ready,__pycache__,.venv,venv,venv_buildozer,.buildozer,installer,instaladores_ready
source.exclude_patterns = *.exe,*.zip,*.tar.gz,*.spec,*.nsi,*.sh,*.bat,*.md,*.txt,*.log,*.pyc,*.pyo
version = 1.0.0

# Requirements MINIMOS para APK (evitar libs de servidor)
requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests

# Entry point EXPLÍCITO para Android (main.py contiene run_mobile_app)
entrypoint = main.py

orientation = portrait
fullscreen = 0

# Permisos ESENCIALES para sync y DB
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
