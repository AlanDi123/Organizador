; ============================================================================
;  INSTALADOR NSIS - Organizador v1.0.0
;  Generador de instaladores profesionales para Windows
; ============================================================================

!include "MUI2.nsh"
!include "x64.nsh"
!include "LogicLib.nsh"
!include "nsDialogs.nsh"

; ============================================================================
; DEFINICIONES Y VARIABLES
; ============================================================================

!define APP_NAME "Organizador"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Whiterman"
!define APP_WEBSITE "https://github.com/AlanDi123/Organizador"
!define APP_EXE "Organizador.exe"
!define INSTALL_DIR "$PROGRAMFILES\Organizador"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\Organizador"
!define ICON_PATH "assets\icon.ico"

; Detectar arquitectura (32 o 64 bits)
${If} ${RunningX64}
  !define ARCH "64-bit"
  InstallDir "$PROGRAMFILES64\Organizador"
${Else}
  !define ARCH "32-bit"
  InstallDir "$PROGRAMFILES\Organizador"
${EndIf}

; ============================================================================
; CONFIGURACIÓN DE PÁGINAS (MUI)
; ============================================================================

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "Spanish"

; ============================================================================
; PROPIEDADES DEL INSTALADOR
; ============================================================================

Name "${APP_NAME} ${APP_VERSION}"
OutFile "Organizador-v${APP_VERSION}-Installer.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "${UNINSTALL_KEY}" "InstallLocation"

ShowInstDetails show
ShowUninstDetails show
SetCompress auto
SetDatablockOptimize on
SetOverwrite ifnewer
XPStyle on

; ============================================================================
; SECCIONES DE INSTALACIÓN
; ============================================================================

Section "Instalar Organizador"
  SectionIn RO
  
  ; Crear directorio de instalación
  CreateDirectory "$INSTDIR"
  SetOutPath "$INSTDIR"
  
  ; Copiar archivos compilados
  File /r "dist\Organizador\*.*"
  
  ; Crear acceso directo en el escritorio
  CreateShortCut "$DESKTOP\Organizador.lnk" "$INSTDIR\${APP_EXE}" \
    "" "$INSTDIR\${APP_EXE}" 0 SW_SHOWNORMAL
  
  ; Crear acceso directo en el menú Inicio
  CreateDirectory "$SMPROGRAMS\Organizador"
  CreateShortCut "$SMPROGRAMS\Organizador\Organizador.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortCut "$SMPROGRAMS\Organizador\Desinstalar.lnk" "$INSTDIR\Uninstall.exe"
  
  ; Registrar información en el registro de Windows
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayName" "${APP_NAME} ${APP_VERSION}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "URLInfoAbout" "${APP_WEBSITE}"
  WriteRegDWord HKLM "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWord HKLM "${UNINSTALL_KEY}" "NoRepair" 1
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
  
  ; Crear el programa desinstalador
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Mostrar mensaje de finalización
  DetailPrint "✓ Instalación completada exitosamente"
  DetailPrint "✓ La aplicación está lista en: $INSTDIR"
  DetailPrint "✓ Accesos directos creados en el escritorio y menú Inicio"
SectionEnd

; ============================================================================
; SECCIÓN DE DESINSTALACIÓN
; ============================================================================

Section "Uninstall"
  ; Eliminar accesos directos
  Delete "$DESKTOP\Organizador.lnk"
  RMDir /r "$SMPROGRAMS\Organizador"
  
  ; Eliminar archivos instalados
  RMDir /r "$INSTDIR"
  
  ; Eliminar claves del registro
  DeleteRegKey HKLM "${UNINSTALL_KEY}"
  
  DetailPrint "✓ Desinstalación completada"
SectionEnd

; ============================================================================
; FUNCIONES
; ============================================================================

Function .onInstSuccess
  MessageBox MB_OK "${APP_NAME} se ha instalado correctamente.$\n$\nHaz clic en Finalizar para completar la instalación."
FunctionEnd

Function un.onUninstSuccess
  MessageBox MB_OK "${APP_NAME} se ha desinstalado correctamente.$\n$\nGracias por usar ${APP_NAME}."
FunctionEnd

; ============================================================================
; FIN DEL INSTALADOR
; ============================================================================
  WriteRegStr HKLM "${APP_UNINSTALL_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "${APP_UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  
  ; Crear el desinstalador
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

; Sección de desinstalación
Section "Uninstall"
  ; Eliminar acceso directo del escritorio
  Delete "$DESKTOP\Organizador.lnk"
  
  ; Eliminar accesos directos del menú Inicio
  Delete "$SMPROGRAMS\Organizador\Organizador.lnk"
  Delete "$SMPROGRAMS\Organizador\Desinstalar.lnk"
  RMDir "$SMPROGRAMS\Organizador"
  
  ; Eliminar archivos de la aplicación
  RMDir /r "$INSTDIR"
  
  ; Eliminar registro de desinstalación
  DeleteRegKey HKLM "${APP_UNINSTALL_KEY}"
SectionEnd

; Función para mostrar mensaje de finalización
Function .onInstSuccess
  MessageBox MB_OK "¡${APP_NAME} ha sido instalado correctamente! Se ha creado un acceso directo en el escritorio."
FunctionEnd
