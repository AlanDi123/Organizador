# 🔥 Configuración de Firebase para Sincronización

Esta guía te ayudará a configurar Firebase Firestore para sincronizar tus datos entre dispositivos.

## 📋 Requisitos Previos

- Cuenta de Google
- Proyecto creado en Firebase Console
- 10-15 minutos

---

## Paso 1: Crear Proyecto en Firebase

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Haz clic en **"Add project"** o **"Crear proyecto"**
3. Ingresa un nombre (ej: "Organizador Finanzas")
4. Deshabilita Google Analytics (opcional, no necesario)
5. Haz clic en **"Create project"**

---

## Paso 2: Habilitar Firestore Database

1. En el menú lateral, haz clic en **"Build"** → **"Firestore Database"**
2. Haz clic en **"Create database"**
3. Selecciona **"Start in test mode"** (luego configuraremos reglas de seguridad)
4. Elige una ubicación (recomendado: us-central o southamerica-east1 para Latinoamérica)
5. Haz clic en **"Enable"**

---

## Paso 3: Habilitar Authentication

1. En el menú lateral, haz clic en **"Build"** → **"Authentication"**
2. Haz clic en **"Get started"**
3. En la pestaña **"Sign-in method"**, habilita **"Email/Password"**
4. Haz clic en **"Save"**

---

## Paso 4: Obtener Credenciales (Service Account)

1. Haz clic en el ícono de ⚙️ (Settings) junto a "Project Overview"
2. Selecciona **"Project settings"**
3. Ve a la pestaña **"Service accounts"**
4. Haz clic en **"Generate new private key"**
5. Guarda el archivo JSON descargado como `firebase_credentials.json`
6. **⚠️ IMPORTANTE:** Nunca compartas este archivo ni lo subas a GitHub

---

## Paso 5: Colocar Credenciales en el Proyecto

```bash
# Mover el archivo de credenciales al directorio del proyecto
mv ~/Downloads/firebase_credentials.json /path/to/organizador/

# Verificar que existe
ls -la firebase_credentials.json
```

---

## Paso 6: Configurar Variables de Entorno

Edita el archivo `.env`:

```bash
# Cloud Sync
FIREBASE_ENABLED=True
FIREBASE_CREDENTIALS_PATH=firebase_credentials.json
FIREBASE_PROJECT_ID=tu-proyecto-firebase  # Copia el ID de Firebase Console
SYNC_ENABLED=True
AUTO_SYNC_INTERVAL=300
```

---

## Paso 7: Configurar Reglas de Seguridad

En Firebase Console → Firestore Database → Rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Función auxiliar para verificar autenticación
    function isAuthenticated() {
      return request.auth != null;
    }
    
    // Función para verificar que el usuario es dueño del dato
    function isOwner(userId) {
      return request.auth.uid == userId;
    }
    
    // Reglas para colección de gastos
    match /gastos/{gastoId} {
      allow read: if isAuthenticated() && isOwner(resource.data.user_id);
      allow create: if isAuthenticated() && isOwner(request.resource.data.user_id);
      allow update: if isAuthenticated() && isOwner(resource.data.user_id);
      allow delete: if isAuthenticated() && isOwner(resource.data.user_id);
    }
    
    // Reglas para colección de ingresos
    match /ingresos/{ingresoId} {
      allow read: if isAuthenticated() && isOwner(resource.data.user_id);
      allow create: if isAuthenticated() && isOwner(request.resource.data.user_id);
      allow update: if isAuthenticated() && isOwner(resource.data.user_id);
      allow delete: if isAuthenticated() && isOwner(resource.data.user_id);
    }
    
    // Reglas para colección de presupuesto
    match /presupuesto/{presupuestoId} {
      allow read: if isAuthenticated() && isOwner(resource.data.user_id);
      allow create: if isAuthenticated() && isOwner(request.resource.data.user_id);
      allow update: if isAuthenticated() && isOwner(resource.data.user_id);
      allow delete: if isAuthenticated() && isOwner(resource.data.user_id);
    }
    
    // Reglas para sync_logs (solo escritura)
    match /sync_logs/{logId} {
      allow create: if isAuthenticated();
      allow read: if isAuthenticated() && isOwner(resource.data.user_id);
    }
    
    // Reglas para sync_metadata
    match /sync_metadata/{metaId} {
      allow read, write: if isAuthenticated() && isOwner(resource.data.user_id);
    }
    
    // Denegar todo lo demás por defecto
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

---

## Paso 8: Publicar Reglas

1. Copia las reglas de arriba
2. Pégalas en el editor de reglas de Firebase Console
3. Haz clic en **"Publish"**

---

## Paso 9: Instalar Dependencias de Firebase

```bash
pip install firebase-admin google-cloud-firestore
```

---

## Paso 10: Probar la Conexión

Crea un archivo de test `test_firebase.py`:

```python
from src.cloud.firebase_client import FirebaseClient

# Crear cliente
client = FirebaseClient()

# Verificar si está habilitado
print(f"Firebase habilitado: {client.enabled}")

# Si está habilitado, probar operación
if client.enabled:
    # Test de escritura
    test_data = {
        'test': True,
        'timestamp': '2024-01-01T00:00:00'
    }
    doc_id = client.save_record('test_collection', test_data)
    print(f"Documento guardado con ID: {doc_id}")
    
    # Test de lectura
    doc = client.get_record('test_collection', doc_id)
    print(f"Documento leído: {doc}")
```

Ejecuta:
```bash
python test_firebase.py
```

---

## 🔧 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'firebase_admin'"
```bash
pip install firebase-admin
```

### Error: "Credential file not found"
- Verifica que `firebase_credentials.json` esté en el directorio correcto
- Usa ruta absoluta en `.env`: `FIREBASE_CREDENTIALS_PATH=/ruta/completa/firebase_credentials.json`

### Error: "Permission denied"
- Verifica que las reglas de Firestore estén publicadas
- Asegúrate de que el usuario esté autenticado

### Error: "Project ID not found"
- Copia el Project ID exacto desde Firebase Console
- Verifica que no haya espacios en blanco en `.env`

---

## 📊 Monitoreo de Uso

Firebase tiene un plan gratuito generoso:

| Recurso | Límite Free Tier |
|---------|------------------|
| Lecturas | 50,000 / día |
| Escrituras | 20,000 / día |
| Almacenamiento | 1 GB |
| Transferencia | 10 GB / mes |

Para monitorear:
1. Firebase Console → Project Overview
2. Ver uso actual en tiempo real

---

## 🚀 Siguientes Pasos

1. **Registrar usuario**: Implementa registro en la app
2. **Primer sync**: Ejecuta sincronización manual
3. **Configurar sync automático**: Establece intervalo de sync
4. **Probar multi-dispositivo**: Instala en móvil y desktop

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs: `cat app.log | grep firebase`
2. Verifica credenciales en Firebase Console
3. Consulta la [documentación oficial de Firebase](https://firebase.google.com/docs)

---

**¡Listo! Tu app ahora sincroniza datos en la nube ☁️**
