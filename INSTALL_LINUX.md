# 🐧 Instalación de Dependencias en Linux (Debian/Ubuntu)

## Problema: "externally-managed-environment"

Python 3.11 en Debian/Ubuntu modernos usa **PEP 668** que previene la instalación de paquetes globalmente.

---

## ✅ Solución 1: Usar el Script Actualizado (Recomendado)

El script `build_apk.sh` ahora maneja esto automáticamente:

```bash
# Ejecutar el script
./build_apk.sh

# El script:
# 1. Detecta si hay un entorno virtual
# 2. Usa pipx si está disponible
# 3. Crea un entorno virtual automáticamente
# 4. Instala buildozer en el entorno
```

---

## ✅ Solución 2: Manual con Entorno Virtual

```bash
# 1. Crear entorno virtual
python3 -m venv venv_buildozer

# 2. Activar el entorno
source venv_buildozer/bin/activate

# 3. Actualizar pip
pip install --upgrade pip

# 4. Instalar buildozer
pip install buildozer

# 5. Instalar dependencias adicionales
pip install kivy kivymd

# 6. Compilar APK
./build_apk.sh

# 7. Cuando termines, desactiva el entorno
deactivate
```

---

## ✅ Solución 3: Usar pipx (Alternativa Limpia)

```bash
# Instalar pipx
sudo apt install pipx
pipx ensurepath

# Instalar buildozer con pipx
pipx install buildozer

# Compilar APK
./build_apk.sh
```

---

## 📦 Dependencias del Sistema Requeridas

### Ubuntu/Debian

```bash
sudo apt update

# Dependencias básicas
sudo apt install -y \
    git \
    ffmpeg \
    cmake \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libgstreamer1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    libgtk-3-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    autoconf \
    automake \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    libtiff5-dev \
    libjpeg8-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libxml2-dev \
    libxslt1-dev \
    wget \
    openjdk-17-jdk

# Java (alternativa si openjdk-17 no está disponible)
sudo apt install -y openjdk-11-jdk
```

### Fedora

```bash
sudo dnf install -y \
    python3-devel \
    python3-pip \
    python3-virtualenv \
    java-17-openjdk \
    java-17-openjdk-devel \
    SDL2-devel \
    SDL2_image-devel \
    SDL2_mixer-devel \
    SDL2_ttf-devel \
    gstreamer1-devel \
    gstreamer1-plugins-base-devel \
    libffi-devel \
    openssl-devel
```

### Arch Linux

```bash
sudo pacman -S \
    python-pip \
    python-virtualenv \
    jdk17-openjdk \
    sdl2 \
    sdl2_image \
    sdl2_mixer \
    sdl2_ttf \
    gstreamer \
    gst-plugins-base \
    gst-plugins-good
```

---

## 🔍 Verificar Instalación

```bash
# Verificar Java
java -version

# Debería mostrar algo como:
# openjdk version "17.0.x"

# Verificar buildozer (después de instalar)
buildozer --version

# Verificar Python
python3 --version
```

---

## 🚀 Compilación Rápida

```bash
# 1. Instalar dependencias del sistema (solo una vez)
sudo apt install -y autoconf automake build-essential \
    libssl-dev libffi-dev python3-dev \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    openjdk-17-jdk

# 2. Crear y activar entorno virtual
python3 -m venv venv_buildozer
source venv_buildozer/bin/activate

# 3. Instalar buildozer
pip install buildozer

# 4. Compilar APK
./build_apk.sh

# 5. Desactivar entorno virtual cuando termines
deactivate
```

---

## ⚠️ Errores Comunes y Soluciones

### Error: "No module named 'venv'"
```bash
sudo apt install python3.11-venv
```

### Error: "Java no encontrado"
```bash
sudo apt install openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

### Error: "ANDROIDNDKHOME no está configurado"
Buildozer descarga el NDK automáticamente la primera vez. Solo espera.

### Error: "Permission denied" al ejecutar build_apk.sh
```bash
chmod +x build_apk.sh
./build_apk.sh
```

---

## 📊 Tiempo de Compilación

| Primera vez | Subsecuentes |
|-------------|--------------|
| 15-30 minutos | 3-5 minutos |

La primera vez descarga:
- Android SDK (~3 GB)
- Android NDK (~1 GB)
- Dependencias de Python

---

## 🎯 Una Vez Compilado

El APK estará en:
```
bin/organizador_finanzas-1.0.0-debug.apk
```

Para instalar:
```bash
# Con ADB
adb install bin/organizador_finanzas-1.0.0-debug.apk

# O transfiere el archivo al celular e instálalo manualmente
```

---

## 📞 ¿Problemas?

1. Revisa los logs: `tail -f .buildozer/android/platform/build-*/dists/*/build.log`
2. Limpia y recompila: `./build_apk.sh --clean`
3. Verifica Java: `java -version`

---

**¡Con esto deberías poder compilar sin problemas!** 🚀
