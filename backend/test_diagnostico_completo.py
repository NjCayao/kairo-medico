"""
Test del motor de diagnóstico completo
"""

import sys
import os

# Configurar paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(BASE_DIR))
sys.path.insert(0, BASE_DIR)

print("="*70)
print("INICIANDO TEST")
print("="*70)

try:
    print("\n1. Importando módulo...")
    from backend.core.diagnostico import DiagnosticoEngine
    print("   ✅ Import exitoso")
    
    print("\n2. Creando motor...")
    motor = DiagnosticoEngine()
    print("   ✅ Motor creado")
    
    print("\n3. Preparando contexto de prueba...")
    contexto = {
        'sintoma_principal': 'dolor de cabeza',
        'respuestas_usuario': [
            'En la frente',
            'Una semana',
            '7 de 10',
            'Mañanas',
            'Mejora con descanso'
        ]
    }
    print("   ✅ Contexto listo")
    
    print("\n4. Ejecutando análisis completo...")
    resultado = motor.analizar_completo(
        contexto=contexto,
        sesion_id='TEST-001',
        usuario_id=1
    )
    print("   ✅ Análisis completado")
    
    print("\n" + "="*70)
    print("RESULTADOS")
    print("="*70)
    
    print(f"\n📊 Diagnóstico: {resultado.get('condicion', 'N/A')}")
    print(f"📊 Confianza: {resultado.get('confianza', 0):.0%}")
    print(f"📊 Origen: {resultado.get('origen', 'N/A')}")
    print(f"📊 Productos: {len(resultado.get('productos', []))}")
    
    if 'receta' in resultado:
        print("\n📋 RECETA:")
        print(resultado['receta']['texto_ticket'][:500] + "...")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETADO EXITOSAMENTE")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n💡 SUGERENCIAS:")
    print("   1. Verificar que MySQL está corriendo")
    print("   2. Verificar que la BD 'kairos_medico' existe")
    print("   3. Verificar que todas las tablas están creadas")