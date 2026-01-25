#!/bin/bash

###############################################################################
#                    INSTALADOR - ORGANIZADOR v1.0.0                         #
#                      Para sistemas Linux                                    #
###############################################################################

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con formato
print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}➜${NC} $1"
}

# Verificar que se ejecute con sudo
if [[ $EUID -ne 0 ]]; then
    print_error "Este instalador debe ejecutarse con sudo"
    echo "Ejecuta: sudo bash install_linux.sh"
    exit 1
fi

print_header "Instalador de Organizador v1.0.0"

# Detectar si se está en el directorio correcto
if [ ! -f "run.py" ]; then
    print_error "No se encontró run.py. Asegúrate de ejecutar este script desde la carpeta de Organizador"
    exit 1
fi

print_info "Sistema detectado: $(lsb_release -d | cut -f2)"
print_info "Usuario actual: $SUDO_USER"

# Crear directorio de instalación
INSTALL_DIR="/opt/organizador"
print_info "Directorio de instalación: $INSTALL_DIR"

if [ -d "$INSTALL_DIR" ]; then
    print_info "Directorio existente detectado. Actualizando instalación..."
    rm -rf "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"
print_success "Directorio de instalación creado"

# Copiar archivos
print_info "Copiando archivos de aplicación..."
cp -r src "$INSTALL_DIR/"
cp -r assets "$INSTALL_DIR/"
cp -r data "$INSTALL_DIR/"
cp -r config "$INSTALL_DIR/"
cp run.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
cp README.md "$INSTALL_DIR/" 2>/dev/null || true
print_success "Archivos copiados"
echo -e "${GREEN}✓ Archivos copiados${NC}\n"

# Instalar dependencias de Python
echo -e "${YELLOW}Instalando dependencias de Python...${NC}"
cd "$INSTALL_DIR"
sudo pip3 install -r requirements.txt
echo -e "${GREEN}✓ Dependencias instaladas${NC}\n"

# Crear script ejecutable
echo -e "${YELLOW}Creando script ejecutable...${NC}"
sudo tee /usr/local/bin/organizador > /dev/null <<'EOF'
#!/bin/bash
# Crear archivo ejecutable
print_info "Creando archivo ejecutable..."
cat > /usr/local/bin/organizador << 'EOF'
#!/bin/bash
cd /opt/organizador
python3 run.py "$@"
EOF

chmod +x /usr/local/bin/organizador
print_success "Ejecutable creado: /usr/local/bin/organizador"

# Crear entrada de menú (desktop entry)
print_info "Creando entrada de menú..."
cat > /usr/share/applications/organizador.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Organizador
Comment=Aplicación de Gestión Financiera
Exec=/usr/local/bin/organizador
Icon=application-utilities
Categories=Office;Finance;
Terminal=false
Version=1.0.0
EOF

print_success "Entrada de menú creada"

# Cambiar permisos
chown -R $SUDO_USER:$SUDO_USER "$INSTALL_DIR"
print_success "Permisos configurados"

# Instalar dependencias
print_info "Instalando dependencias Python..."
pip install -q -r "$INSTALL_DIR/requirements.txt" || {
    print_error "No se pudieron instalar algunas dependencias"
    echo "Intenta ejecutar manualmente:"
    echo "  pip install -r /opt/organizador/requirements.txt"
}
print_success "Dependencias instaladas"

# Resumen
print_header "¡Instalación completada!"
print_success "Organizador está listo para usar"
echo -e "
${GREEN}Opciones para ejecutar:${NC}
  • Comando terminal: ${YELLOW}organizador${NC}
  • Menú aplicaciones: Busca 'Organizador'
  • Archivo: ${YELLOW}/opt/organizador/run.py${NC}

${GREEN}Para desinstalar:${NC}
  sudo rm -rf /opt/organizador
  sudo rm /usr/local/bin/organizador
  sudo rm /usr/share/applications/organizador.desktop

${YELLOW}Soporte:${NC}
  https://github.com/AlanDi123/Organizador
"

print_success "¡Gracias por usar Organizador!"

# Crear acceso directo del escritorio si es posible
DESKTOP="$HOME/Desktop"
if [ -d "$DESKTOP" ]; then
  cp "$DESKTOP_FILE" "$DESKTOP/Organizador.desktop"
  chmod +x "$DESKTOP/Organizador.desktop"
  echo -e "${GREEN}✓ Acceso directo creado en el escritorio${NC}\n"
fi

# Información de finalización
echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}¡Instalación completada! ✓${NC}"
echo -e "${GREEN}=================================${NC}\n"

echo -e "Para ejecutar la aplicación:"
echo -e "  ${YELLOW}organizador${NC}\n"

echo -e "O si lo prefieres:"
echo -e "  ${YELLOW}python3 /opt/organizador/run.py${NC}\n"

echo -e "Para desinstalar:"
echo -e "  ${YELLOW}sudo rm -rf /opt/organizador && sudo rm /usr/local/bin/organizador${NC}\n"

echo -e "${GREEN}Gracias por usar Organizador${NC}"
