# 🚀 Guía de Inicio Rápido

## ⚡ Instalación en 5 minutos

### Desktop (Windows/Linux/Mac)

```bash
# 1. Clonar repositorio
git clone https://github.com/AlanDi123/Organizador.git
cd Organizador

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Copiar configuración
cp .env.example .env

# 4. Ejecutar
python run.py
```

**¡Listo!** La app se abrirá en tu escritorio.

---

## 📱 Compilar APK para Android

### Opción A: Script automático (Recomendado)

```bash
# En Linux
./build_apk.sh

# El APK estará en: bin/organizador_finanzas-1.0.0-debug.apk
```

### Opción B: Manual

```bash
# Instalar buildozer
pip install buildozer

# Inicializar (si es la primera vez)
buildozer init

# Compilar
buildozer -v android debug

# El APK estará en: bin/
```

### Instalar en tu celular

1. **Habilitar depuración USB** en tu Android:
   - Ve a Configuración → Acerca del teléfono
   - Toca 7 veces "Número de compilación"
   - Regresa a Configuración → Opciones de desarrollador
   - Activa "Depuración USB"

2. **Conectar vía USB** a tu computadora

3. **Instalar con ADB**:
   ```bash
   adb install bin/organizador_finanzas-1.0.0-debug.apk
   ```

4. **O transfiere el APK** al celular e instálalo manualmente

---

## ☁️ Activar Sincronización (Opcional)

### Sin configuración (Offline)

La app funciona **sin configuración** en modo offline. Todos los datos se guardan localmente.

### Con sync en la nube

Para sincronizar entre dispositivos:

1. **Configurar Firebase** (10 minutos):
   - Sigue la guía en `FIREBASE_SETUP.md`
   - Obtén tu archivo `firebase_credentials.json`

2. **Editar `.env`**:
   ```bash
   FIREBASE_ENABLED=True
   FIREBASE_CREDENTIALS_PATH=firebase_credentials.json
   FIREBASE_PROJECT_ID=tu-proyecto-id
   SYNC_ENABLED=True
   ```

3. **Ejecutar la app**:
   - Regístrate con tu email
   - Inicia sesión
   - ¡Los datos se sincronizarán automáticamente!

---

## 📚 Comandos Útiles

### Desktop

```bash
# Ejecutar app
python run.py

# Ejecutar tests
pytest

# Ver logs
tail -f app.log
```

### Móvil

```bash
# Compilar APK debug
./build_apk.sh

# Compilar APK release (firmado)
./build_apk.sh --release

# Limpiar build anterior
./build_apk.sh --clean

# Reinstalar en dispositivo
adb install -r bin/organizador_finanzas-1.0.0-debug.apk
```

---

## 🆘 Problemas Comunes

### Error: "No module named 'kivy'"
```bash
pip install -r requirements.txt
```

### Error: "Buildozer no encontrado"
```bash
pip install buildozer
```

### Error: "Firebase credentials not found"
- Verifica que `firebase_credentials.json` existe
- Usa ruta absoluta en `.env`

### La app no se abre en Linux
```bash
# Dar permisos de ejecución
chmod +x run.py
python run.py
```

### APK no se instala en Android
- Habilita "Orígenes desconocidos" en tu Android
- Usa `adb install` en lugar de instalación manual

---

## 📖 Siguientes Pasos

1. **Explora la app**: Agrega gastos, ingresos, revisa el dashboard
2. **Configura Firebase**: Para sync entre dispositivos
3. **Personaliza**: Edita `.env` para ajustar configuración
4. **Contribuye**: Reporta bugs o sugiere mejoras

---

## 🔗 Enlaces de Ayuda

- [Documentación completa](README.md)
- [Configuración de Firebase](FIREBASE_SETUP.md)
- [Issues en GitHub](https://github.com/AlanDi123/Organizador/issues)

---

**¿Necesitas ayuda?** Abre un issue en GitHub o revisa la documentación completa.
