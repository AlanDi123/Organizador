# 📱 Organizador de Gastos e Ingresos - Multiplataforma

[![Build Android APK](https://github.com/AlanDi123/Organizador/actions/workflows/build-apk.yml/badge.svg)](https://github.com/AlanDi123/Organizador/actions/workflows/build-apk.yml)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Kivy](https://img.shields.io/badge/Kivy-2.3.0-green.svg)](https://kivy.org)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-orange.svg)](https://firebase.google.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Aplicación **multiplataforma** para gestión de finanzas personales con **sincronización en la nube**.

## 🌟 Características Principales

### Desktop (Windows/Linux/Mac)
- ✅ Interfaz Tkinter moderna con temas claro/oscuro
- ✅ Gestión de gastos e ingresos con historial
- ✅ Cálculo automático de fechas quincenales
- ✅ Dashboard financiero con gráficos
- ✅ Presupuesto inteligente con IA
- ✅ Widget del dólar en tiempo real
- ✅ Exportación/importación de datos

### Móvil (Android/iOS) 🆕
- ✅ App nativa compilada como APK
- ✅ Interfaz Material Design (KivyMD)
- ✅ **Sincronización bidireccional con la nube**
- ✅ Funcionamiento offline-first
- ✅ Autenticación de usuarios
- ✅ Sync automático de cambios

### Cloud Sync ☁️ 🆕
- ✅ **Firebase Firestore** como backend
- ✅ Sync en tiempo real entre dispositivos
- ✅ Resolución de conflictos por timestamp
- ✅ Encriptación de datos sensibles
- ✅ Multi-dispositivo: móvil ↔ desktop ↔ web

---

## 🚀 Instalación y Uso

### Desktop (Desarrollo)

```bash
# Clonar repositorio
git clone https://github.com/AlanDi123/Organizador.git
cd Organizador

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación desktop
python run.py
```

### Móvil (Compilar APK)

#### Requisitos previos
- Linux (Ubuntu/Debian recomendado)
- Python 3.11
- Java JDK 17
- Android SDK (buildozer lo descarga automáticamente)

```bash
# Instalar dependencias de sistema (Ubuntu/Debian)
sudo apt update
sudo apt install -y git ffmpeg cmake libsdl2-dev \
    libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libgstreamer1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    libgtk-3-dev libgl1-mesa-dev libglu1-mesa-dev autoconf automake \
    build-essential libssl-dev libffi-dev python3-dev libtiff5-dev \
    libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libxml2-dev \
    libxslt1-dev wget openjdk-17-jdk

# Instalar buildozer
pip install buildozer

# Compilar APK (debug)
./build_apk.sh

# Compilar APK (release - para producción)
./build_apk.sh --release
```

El APK se generará en: `bin/organizador_finanzas-1.0.0-debug.apk`

#### Instalar en dispositivo Android
```bash
# Opción 1: ADB (requiere depuración USB activada)
adb install bin/organizador_finanzas-1.0.0-debug.apk

# Opción 2: Transferir APK al dispositivo e instalar manualmente
```

---

## ☁️ Configuración de Sincronización Cloud

### 1. Crear proyecto en Firebase

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Crea un nuevo proyecto
3. Habilita **Firestore Database**
4. Habilita **Authentication** (Email/Password)
5. Descarga las credenciales (`firebase_credentials.json`)

### 2. Configurar archivo `.env`

```bash
# Cloud Sync
FIREBASE_ENABLED=True
FIREBASE_CREDENTIALS_PATH=firebase_credentials.json
FIREBASE_PROJECT_ID=tu-proyecto-firebase
SYNC_ENABLED=True
AUTO_SYNC_INTERVAL=300
```

### 3. Reglas de seguridad Firestore

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Solo usuarios autenticados pueden acceder
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
    
    // Cada usuario solo ve sus datos
    match /gastos/{gastoId} {
      allow read, write: if request.auth.uid == resource.data.user_id;
    }
    
    match /ingresos/{ingresoId} {
      allow read, write: if request.auth.uid == resource.data.user_id;
    }
  }
}
```

---

## 📁 Estructura del Proyecto

```
organizador/
├── src/
│   ├── cloud/              # ☁️ Sincronización Firebase
│   │   ├── __init__.py
│   │   ├── firebase_client.py
│   │   ├── sync_engine.py
│   │   └── models.py
│   │
│   ├── core/               # Lógica de negocio compartida
│   │   ├── __init__.py
│   │   ├── entities.py     # Entidades (Gasto, Ingreso, etc.)
│   │   └── services.py     # Servicios (CRUD operations)
│   │
│   ├── mobile/             # 📱 UI Móvil (KivyMD)
│   │   ├── __init__.py
│   │   ├── app.py          # App principal
│   │   └── screens.py      # Pantallas
│   │
│   ├── views/              # 🖥️ UI Desktop (Tkinter)
│   │   ├── main_app.py
│   │   ├── gastos_frame.py
│   │   ├── ingresos_frame.py
│   │   └── ...
│   │
│   ├── models/             # Modelos de datos
│   │   ├── data_manager.py
│   │   ├── gastos.py
│   │   ├── ingresos.py
│   │   └── ia_module.py
│   │
│   ├── controllers/        # Controladores MVC
│   │   └── app_controller.py
│   │
│   └── utils/              # Utilidades
│       ├── validators.py
│       ├── cache.py
│       └── logger.py
│
├── tests/                  # Tests unitarios
├── assets/                 # Recursos (imágenes, iconos)
├── data/                   # Datos locales (SQLite, configs)
│
├── main.py                 # Entry point para móvil
├── run.py                  # Entry point para desktop
├── buildozer.spec          # Configuración build APK
├── build_apk.sh            # Script compilación
├── requirements.txt        # Dependencias Python
└── README.md
```

---

## 🔧 Comandos Útiles

### Desktop
```bash
# Ejecutar en modo desarrollo
python run.py

# Ejecutar tests
pytest

# Crear ejecutable Windows
python build_exe.py
```

### Móvil
```bash
# Compilar APK debug
./build_apk.sh

# Compilar APK release
./build_apk.sh --release

# Limpiar build anterior
./build_apk.sh --clean

# Ver logs de buildozer
tail -f .buildozer/android/platform/build-*/dists/*/build.log
```

---

## 📊 Flujo de Sincronización

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Móvil     │      │   Firebase   │      │   Desktop   │
│  (Android)  │◄────►│   Firestore  │◄────►│  (Windows)  │
│             │      │              │      │             │
│ SQLite Local│      │  Cloud DB    │      │ SQLite Local│
└─────────────┘      └──────────────┘      └─────────────┘
       ▲                      ▲                      ▲
       │                      │                      │
       └──────────────────────┴──────────────────────┘
                    Sync Bidireccional
```

### Estrategia de Sync

1. **Offline-first**: Todos los datos se guardan localmente primero
2. **Sync automático**: Cada 5 minutos (configurable)
3. **Resolución de conflictos**: Último timestamp gana
4. **Sync diferencial**: Solo se transmiten cambios

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con coverage
pytest --cov=src tests/

# Tests específicos
pytest tests/test_gastos.py
pytest tests/test_sync.py
```

---

## 🛠️ Tecnologías

| Componente | Tecnología |
|------------|------------|
| **Desktop UI** | Tkinter, ttk, matplotlib |
| **Móvil UI** | Kivy 2.3, KivyMD 1.2 |
| **Backend Cloud** | Firebase Firestore |
| **DB Local** | SQLite 3 |
| **Autenticación** | Firebase Auth |
| **Build Tool** | Buildozer 1.5 |
| **Packaging** | PyInstaller 6 |

---

## 📝 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles

---

## 👥 Contribución

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -m 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

---

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/AlanDi123/Organizador/issues)
- **Email**: [tu-email@ejemplo.com]

---

## 🎯 Roadmap

- [ ] iOS app (compilación para iPhone)
- [ ] Notificaciones push de presupuesto
- [ ] Exportar a Excel/PDF
- [ ] Modo offline mejorado
- [ ] Widgets de escritorio
- [ ] Web app (React/Vue)
- [ ] Multi-moneda
- [ ] Reconocimiento de tickets con IA

---

**Hecho con ❤️ para mejorar tus finanzas personales**
