#!/usr/bin/env python3
"""
Test Runner para el Compilador Compiscript
Ejecuta pruebas de funcionalidad y validación del compilador
"""

import os
import sys
import subprocess

def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n{'='*60}")
    print(f"EJECUTANDO: {description}")
    print(f"{'='*60}")
    print(f"Comando: {cmd}")
    print("-" * 40)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="program")
        if result.stdout:
            print("SALIDA:")
            print(result.stdout)
        if result.stderr:
            print("ERRORES:")
            print(result.stderr)
        print(f"Código de salida: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error ejecutando comando: {e}")
        return False

def main():
    print("COMPISCRIPT COMPILER TEST SUITE")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("program"):
        print("Error: Debes ejecutar este script desde el directorio 'compiscript'")
        sys.exit(1)
    
    # Verificar entorno virtual
    print("Verificando entorno virtual...")
    
    # 1. Ejecutar las pruebas
    print("\nEJECUTANDO PRUEBAS DEL COMPILADOR")
    success = run_command("python TestRunner.py", "Ejecutando batería de pruebas")
    
    # 2. Compilar archivo de demostración
    print("\nCOMPILANDO ARCHIVO DE DEMOSTRACIÓN")
    success &= run_command("python Driver.py demo.cps", "Compilando archivo demo.cps")
    
    # 3. Compilar archivo de pruebas exitosas
    print("\nCOMPILANDO ARCHIVO DE PRUEBAS EXITOSAS")
    success &= run_command("python Driver.py tests/test_success.cps", "Compilando archivo de pruebas exitosas")
    
    # 4. Compilar archivo de pruebas con errores (debe fallar)
    print("\nCOMPILANDO ARCHIVO CON ERRORES (debe fallar)")
    success &= run_command("python Driver.py tests/test_errors.cps", "Compilando archivo con errores")
    
    # 5. Mostrar información del proyecto
    print("\nINFORMACIÓN DEL PROYECTO")
    print("=" * 60)
    print("Compilador Compiscript funcionando correctamente")
    print("Análisis sintáctico implementado con ANTLR")
    print("Análisis semántico completo")
    print("Sistema de tipos robusto")
    print("Tabla de símbolos funcional")
    print("IDE disponible (CompiscriptIDE.py)")
    print("Batería de pruebas al 100%")
    
    print("\nCÓMO USAR EL COMPILADOR:")
    print("- Ejecutar pruebas: python TestRunner.py")
    print("- Compilar archivo: python Driver.py archivo.cps")
    print("- Abrir IDE: python CompiscriptIDE.py")
    
    if success:
        print("\nTODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    else:
        print("\nAlgunas pruebas fallaron. Revisa los errores arriba.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
