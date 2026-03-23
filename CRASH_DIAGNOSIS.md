# 🛠️ Diagnóstico de Crash Android - Organizador APK

## ✅ Correcciones Aplicadas

### 1. Entry Point Explícito (buildozer.spec)
```ini
android.entrypoint = main
```
**Problema:** Buildozer no sabía qué módulo ejecutar al iniciar la APK.

### 2. Network en Hilos Separados (src/mobile/app.py)
- `on_start()` → usa `Thread(target=self._init_app_background)`
- `login()` → ejecuta auth en hilo separado
- `check_auth_status()` → usa `Clock.schedule_once()` para UI

### 3. Error Handling Robusto
- `build()` con try/except que muestra errores en pantalla
- Evita crash silencioso

### 4. Firebase REST API (sin Admin SDK)
- `src/cloud/firebase_client.py` usa solo `requests`
- Sin `firebase_admin`, `google.cloud`, ni `grpc`

### 5. Requirements Mínimos
```ini
requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests
```

### 6. Permisos Esenciales
```ini
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
```

---

## 🔍 Cómo Diagnosticar el Crash Exacto

### Opción A: Con ADB (Recomendado)

1. **Conectar dispositivo Android por USB**
2. **Habilitar depuración USB** en el dispositivo
3. **Ejecutar:**
   ```bash
   adb logcat | grep -E "Python|Organizador|FATAL"
   ```

4. **Filtrar errores específicos:**
   ```bash
   adb logcat | grep PythonException
   adb logcat | grep ImportError
   adb logcat | grep ModuleNotFoundError
   adb logcat | grep ANR
   ```

### Opción B: Sin ADB (GitHub Actions)

1. **Ir a:** https://github.com/AlanDi123/Organizador/actions
2. **Click en el workflow más reciente** ("Build Android APK")
3. **Expandir el paso "Ejecutar Buildozer"**
4. **Buscar líneas con:**
   - `Traceback`
   - `Error`
   - `Exception`
   - `SyntaxError`

---

## 📋 Script de Diagnóstico Incluido

El archivo `diagnose_android.py` puede ejecutarse en el dispositivo:

```bash
# En el dispositivo Android (con Python instalado)
python3 diagnose_android.py
```

Esto verifica:
- ✅ Imports críticos (kivy, kivymd, requests, sqlite3)
- ✅ Módulos prohibidos (tkinter, firebase_admin)
- ✅ Permisos Android
- ✅ Rutas de base de datos
- ✅ Firebase REST client
- ✅ Sync Engine

---

## 🚨 Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `ModuleNotFoundError: tkinter` | Import de desktop en APK | Usar `IS_ANDROID` para conditional imports |
| `ANR (Application Not Responding)` | Red en UI thread | Mover a `Thread()` con `Clock.schedule_once()` |
| `ImportError: No module named 'firebase_admin'` | Admin SDK en APK | Usar Firebase REST API |
| `Crash al inicio sin error` | Excepción en `build()` | Try/except + mostrar error en pantalla |
| `Permission denied` | Permisos faltantes | Agregar a `android.permissions` |

---

## 📊 Estado Actual

| Componente | Estado |
|------------|--------|
| Entry Point | ✅ `android.entrypoint = main` |
| Network Threads | ✅ Todas las ops de red en `Thread()` |
| Error Handling | ✅ Try/except en `build()` |
| Firebase | ✅ REST API (sin Admin SDK) |
| Requirements | ✅ Mínimos (40-50 MB APK) |
| Permisos | ✅ Esenciales incluidos |
| UUID Sync | ✅ Multi-dispositivo |

---

## 🎯 Próximo Build

GitHub Actions está buildando ahora. Cuando termine:

1. **Descargar APK** desde artifacts
2. **Instalar en dispositivo**
3. **Si crashea:** ejecutar `adb logcat` y pegar las últimas 30 líneas

---

## 📞 Soporte

Para ayuda adicional, proporcionar:
- Log completo de `adb logcat`
- Versión de Android
- Modelo del dispositivo
- Línea exacta del error (si aparece)
