[app]
title = Trip Manager Pro
package.name = tripmanager
package.domain = org.asdar
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

# Kebutuhan library (Sangat Penting!)
requirements = python3,kivy==2.3.0,pillow

orientation = portrait
fullscreen = 0
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# Pengaturan API Android (Standar Play Store 2026)
android.api = 33
android.minapi = 21
android.ndk = 25b
android.skip_setup_py = 1

# Izin aplikasi jika nanti butuh simpan data di memori luar
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 1
