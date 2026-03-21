; ============================================================================
;  INSTALADOR NSIS - Organizador v1.0.0
;  Instalador profesional para Windows
; ============================================================================

!include "MUI2.nsh"
!include "x64.nsh"
!include "LogicLib.nsh"
!include "nsDialogs.nsh"

; ============================================================================
; DEFINICIONES
; ============================================================================

!define APP_NAME "Organizador"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Whiterman"
!define APP_WEBSITE "https://github.com/AlanDi123/Organizador"
!define APP_EXE "Organizador.exe"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\Organizador"

; Detectar arquitectura
${If} ${RunningX64}
  InstallDir "$PROGRAMFILES64\Organizador"
${Else}
  InstallDir "$PROGRAMFILES\Organizador"
${EndIf}

; ============================================================================
; CONFIGURACIÓN DE PÁGINAS
; ============================================================================

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "Spanish"

; ============================================================================
; PROPIEDADES
; ============================================================================

Name "${APP_NAME} ${APP_VERSION}"
OutFile "Organizador-v${APP_VERSION}-Installer.exe"
ShowInstDetails show
ShowUninstDetails show
SetCompress auto
SetDatablockOptimize on
SetOverwrite ifnewer
XPStyle on

; ============================================================================
; INSTALACIÓN
; ============================================================================

Section "Instalar Organizador"
  SectionIn RO

  CreateDirectory "$INSTDIR"
  SetOutPath "$INSTDIR"

  ; Copiar archivos
  File /r "dist\Organizador\*.*"

  ; Accesos directos
  CreateShortCut "$DESKTOP\Organizador.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0 SW_SHOWNORMAL
  
  CreateDirectory "$SMPROGRAMS\Organizador"
  CreateShortCut "$SMPROGRAMS\Organizador\Organizador.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortCut "$SMPROGRAMS\Organizador\Desinstalar.lnk" "$INSTDIR\Uninstall.exe"

  ; Registro
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayName" "${APP_NAME} ${APP_VERSION}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "URLInfoAbout" "${APP_WEBSITE}"
  WriteRegDWord HKLM "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWord HKLM "${UNINSTALL_KEY}" "NoRepair" 1
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\${APP_EXE}"

  ; Desinstalador
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  DetailPrint "✓ Instalación completada"
  DetailPrint "✓ Aplicación en: $INSTDIR"
SectionEnd

; ============================================================================
; DESINSTALACIÓN
; ============================================================================

Section "Uninstall"
  Delete "$DESKTOP\Organizador.lnk"
  RMDir /r "$SMPROGRAMS\Organizador"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKLM "${UNINSTALL_KEY}"
  DetailPrint "✓ Desinstalación completada"
SectionEnd

; ============================================================================
; FUNCIONES
; ============================================================================

Function .onInstSuccess
  MessageBox MB_OK "${APP_NAME} se ha instalado correctamente.$\n$\nHaz clic en Finalizar para completar."
FunctionEnd

Function un.onUninstSuccess
  MessageBox MB_OK "${APP_NAME} se ha desinstalado correctamente.$\n$\nGracias por usar ${APP_NAME}."
FunctionEnd
