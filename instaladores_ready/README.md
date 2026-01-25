# 📦 Instaladores de Organizador v1.0.0

Este directorio contiene los instaladores compilados y portables para Organizador.

## 📥 Opciones de Instalación

### 1. **Organizador-Portable-v1.0.0.zip** (404 KB)
**Recomendado para usuarios que no tienen Python**

- ✅ Compatible con: Windows, Linux, Mac
- ✅ No requiere instalación previa de Python
- ✅ Auto-instala dependencias en primer uso
- 📝 Pasos:
  1. Descarga y extrae el ZIP
  2. En Windows: Haz doble clic en `Organizador.bat`
  3. En Linux/Mac: Ejecuta `bash Organizador.sh`

### 2. **Organizador-Linux-v1.0.0.tar.gz** (9.1 MB)
**Para usuarios de Linux**

- ✅ Ejecutable compilado (sin necesidad de Python)
- ✅ Script de instalación en el sistema
- 📝 Pasos:
  1. Extrae: `tar -xzf Organizador-Linux-v1.0.0.tar.gz`
  2. Instala: `sudo bash Organizador-Linux-v1.0.0/install_linux.sh`
  3. Ejecuta: `organizador` desde terminal

## 🚀 Para Distribución

**Windows:**
- Usa: `Organizador-Portable-v1.0.0.zip` (funciona en cualquier Windows)
- O: `Organizador.exe` + `requirements.txt` + carpeta `src/`

**Linux:**
- Usa: `Organizador-Linux-v1.0.0.tar.gz` (ejecutable compilado)
- O: `Organizador-Portable-v1.0.0.zip` si el usuario tiene Python

**Mac:**
- Usa: `Organizador-Portable-v1.0.0.zip` (requiere Python 3.7+)

## 📋 Requisitos

- **Windows**: Python 3.7+ (si usas el portable) o nada si usas el .exe
- **Linux**: Python 3.7+ (o el ejecutable compilado)
- **Mac**: Python 3.7+

## ❓ Preguntas Frecuentes

**¿Cuál debo usar?**
- Mejor opción: `Organizador-Portable-v1.0.0.zip` (funciona en todo)

**¿Se instala en el sistema?**
- El portable no instala en el sistema, solo funciona en la carpeta extraída
- El Linux tar.gz instala en `/opt/organizador` si ejecutas el installer

**¿Ocupa mucho espacio?**
- Portable: 404 KB comprimido (1-2 MB descomprimido)
- Linux: 9 MB comprimido (30-50 MB descomprimido)

---

**Versión**: 1.0.0  
**Última actualización**: 25 de enero de 2026  
**Repositorio**: https://github.com/AlanDi123/Organizador
