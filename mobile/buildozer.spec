[app]
title = Verificación de Identidad
package.name = identidadapp
package.domain = org.proyectotitulo

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0
requirements = python3,kivy,kivymd,requests,plyer

# Permisos necesarios en Android para usar la cámara y el internet
android.permissions = CAMERA,INTERNET

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
