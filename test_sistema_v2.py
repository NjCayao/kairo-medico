"""
TEST COMPLETO DEL SISTEMA KAIROS V2.0
Prueba todo el flujo: captura → conversación → diagnóstico → receta
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from backend.core.session_manager import SessionManager

def test_sistema_completo():
    """Test completo del sistema"""
    
    print("="*70)
    print(" "*20 + "🧪 TEST SISTEMA COMPLETO")
    print("="*70)
    
    # Crear session manager
    manager = SessionManager(
        evento="Feria de Salud 2025",
        ubicacion="Stand Principal",
        dispositivo="Tablet-01"
    )
    
    # PASO 1: Nueva sesión
    print("\n" + "="*70)
    print("PASO 1: CREAR NUEVA SESIÓN")
    print("="*70)
    
    exito, sesion_id, info = manager.nueva_sesion()
    
    if not exito:
        print("❌ ERROR: No se pudo crear sesión")
        return
    
    print(f"✅ Sesión creada: {sesion_id}")
    
    # PASO 2: Capturar datos
    print("\n" + "="*70)
    print("PASO 2: CAPTURAR DATOS DEL PACIENTE")
    print("="*70)
    
    exito, usuario_info = manager.capturar_datos_paciente(
        nombre="María González López",
        dni="87654321",
        edad=35
    )
    
    if not exito:
        print(f"❌ ERROR: {usuario_info.get('errores')}")
        return
    
    print(f"✅ Paciente registrado: {usuario_info['nombre']}")
    print(f"   Es nuevo: {usuario_info['es_nuevo']}")
    
    # PASO 3: Conversación
    print("\n" + "="*70)
    print("PASO 3: CONVERSACIÓN MÉDICA")
    print("="*70)
    
    mensajes_test = [
        "Hola doctor, tengo mucho dolor de cabeza",
        "Me duele en las sienes y la frente",
        "Ya como una semana",
        "Es bien fuerte, como un 8 de 10",
        "Más por las mañanas",
        "Empeora cuando estoy estresada en el trabajo"
    ]
    
    for i, mensaje in enumerate(mensajes_test, 1):
        print(f"\n👤 Paciente (mensaje {i}): {mensaje}")
        
        resultado = manager.procesar_mensaje(mensaje)
        
        print(f"🤖 Kairos: {resultado['respuesta']}")
        print(f"   Tipo: {resultado['tipo']}")
        print(f"   Preguntas realizadas: {resultado['total_preguntas']}")
        
        if resultado['listo_diagnostico']:
            print("\n   ✅ Sistema listo para diagnosticar")
            break
        
        if i >= 6:
            print("\n   ⚠️ Máximo de preguntas alcanzado")
            break
    
    # PASO 4: Generar diagnóstico
    print("\n" + "="*70)
    print("PASO 4: GENERAR DIAGNÓSTICO Y RECETA")
    print("="*70)
    
    exito, diagnostico = manager.generar_diagnostico_y_receta()
    
    if not exito:
        print(f"❌ ERROR: {diagnostico.get('error')}")
        return
    
    print(f"\n✅ Diagnóstico generado:")
    print(f"   Condición: {diagnostico['diagnostico']}")
    print(f"   Confianza: {diagnostico['confianza']:.0%}")
    print(f"   Origen: {diagnostico['origen']}")
    
    print(f"\n📦 RECETA:")
    print(f"   Productos: {len(diagnostico['productos'])}")
    for p in diagnostico['productos']:
        print(f"      • {p['nombre']} - S/. {p['precio']:.2f}")
    
    print(f"\n   Plantas: {len(diagnostico['plantas'])}")
    for p in diagnostico['plantas']:
        print(f"      • {p['nombre_comun']}")
    
    print(f"\n   Remedios: {len(diagnostico['remedios'])}")
    for r in diagnostico['remedios']:
        print(f"      • {r['nombre']}")
    
    # PASO 5: Imprimir
    print("\n" + "="*70)
    print("PASO 5: IMPRIMIR RECETA")
    print("="*70)
    
    exito, impresion = manager.imprimir_receta()
    
    if exito:
        print("✅ Ticket impreso correctamente")
        print("\n📄 PREVIEW DEL TICKET:")
        print("-" * 35)
        print(impresion['ticket'][:500] + "...")
        print("-" * 35)
    else:
        print(f"❌ ERROR: {impresion.get('error')}")
    
    # PASO 6: Finalizar
    print("\n" + "="*70)
    print("PASO 6: FINALIZAR SESIÓN")
    print("="*70)
    
    resumen = manager.finalizar_sesion()
    
    print(f"\n✅ SESIÓN FINALIZADA")
    print(f"   ID: {resumen['sesion_id']}")
    print(f"   Paciente: {resumen['usuario']}")
    print(f"   Diagnóstico: {resumen['diagnostico']}")
    print(f"   Duración: {resumen['duracion_minutos']} minutos")
    print(f"   Productos: {resumen['productos']}")
    print(f"   Plantas: {resumen['plantas']}")
    print(f"   Remedios: {resumen['remedios']}")
    
    # Estadísticas finales
    print("\n" + "="*70)
    print("ESTADÍSTICAS DEL DISPOSITIVO")
    print("="*70)
    
    stats = manager.obtener_estadisticas()
    print(f"   Total sesiones: {stats['total_sesiones']}")
    print(f"   Sesiones exitosas: {stats['sesiones_exitosas']}")
    print(f"   Tasa de éxito: {stats['tasa_exito']:.1f}%")
    print(f"   Errores: {stats['total_errores']}")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETO FINALIZADO")
    print("="*70)


if __name__ == "__main__":
    try:
        test_sistema_completo()
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()