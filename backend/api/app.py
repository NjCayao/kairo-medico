"""
API REST V2.1 - Con soporte para dudas post-diagnóstico
CORREGIDO: sesion_id en procesar_mensaje
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from datetime import datetime
import traceback

def handle_options():
    """Manejar peticiones OPTIONS (CORS preflight)"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response, 200

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.core.session_manager import SessionManager
from backend.database.database_manager import DatabaseManager

app = Flask(__name__)
CORS(app)

# Managers globales
sessions = {}
db = DatabaseManager()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENDPOINTS - SESIONES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/sesion/nueva', methods=['POST'])
def crear_sesion():
    """Crear nueva sesión"""
    try:
        data = request.get_json() or {}
        
        manager = SessionManager(
            evento=data.get('evento', 'Consulta Kairos Web'),
            ubicacion=data.get('ubicacion', 'Interfaz Web'),
            dispositivo=data.get('dispositivo', 'web-browser')
        )
        
        exito, sesion_id, info = manager.nueva_sesion()
        
        if exito:
            sessions[sesion_id] = manager
            
            return jsonify({
                'success': True,
                'sesion_id': sesion_id,
                'info': info
            })
        else:
            return jsonify({'success': False, 'error': 'No se pudo crear sesión'}), 500
            
    except Exception as e:
        print(f"❌ Error crear sesión: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sesion/capturar-datos', methods=['POST'])
def capturar_datos():
    """Capturar datos del paciente"""
    try:
        data = request.get_json()
        sesion_id = data.get('sesion_id')
        
        if sesion_id not in sessions:
            return jsonify({'success': False, 'error': 'Sesión no encontrada'}), 404
        
        manager = sessions[sesion_id]
        
        exito, info = manager.capturar_datos_paciente(
            data['nombre'],
            data['dni'],
            data.get('edad')
        )
        
        return jsonify({
            'success': exito,
            'info': info
        })
        
    except Exception as e:
        print(f"❌ Error capturar datos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sesion/mensaje', methods=['POST', 'OPTIONS'])
def procesar_mensaje():
    """Procesar mensaje del usuario"""
    if request.method == 'OPTIONS':
        return handle_options()
    
    try:
        data = request.json
        sesion_id = data.get('sesion_id')  # ⭐ CORREGIDO: Agregar sesion_id
        mensaje = data.get('mensaje')
        
        # ⭐ VERIFICAR SESIÓN
        if sesion_id not in sessions:
            return jsonify({'success': False, 'error': 'Sesión no encontrada'}), 404
        
        # ⭐ OBTENER MANAGER
        manager = sessions[sesion_id]
        
        # Procesar mensaje
        resultado = manager.procesar_mensaje(mensaje)
        
        # ⭐ LIMPIAR RESPUESTA (solo texto, sin metadatos)
        if isinstance(resultado.get('respuesta'), dict):
            # Si es objeto, extraer solo el content
            resultado['respuesta'] = resultado['respuesta'].get('content', str(resultado['respuesta']))
        
        return jsonify({
            'success': True,
            'resultado': resultado
        })
    
    except Exception as e:
        print(f"❌ Error procesar mensaje: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sesion/diagnostico', methods=['POST'])
def generar_diagnostico():
    """Generar diagnóstico y receta"""
    try:
        data = request.get_json()
        sesion_id = data.get('sesion_id')
        
        if sesion_id not in sessions:
            return jsonify({'success': False, 'error': 'Sesión no encontrada'}), 404
        
        manager = sessions[sesion_id]
        
        # Generar diagnóstico
        exito, resultado = manager.generar_diagnostico_y_receta()
        
        if not exito:
            return jsonify({'success': False, 'error': 'Error generando diagnóstico'}), 500
        
        return jsonify({
            'success': True,
            'diagnostico': resultado
        })
        
    except Exception as e:
        print(f"❌ Error diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sesion/duda', methods=['POST'])
def responder_duda():
    """
    ⭐ NUEVO: Responder duda post-diagnóstico
    """
    try:
        data = request.get_json()
        sesion_id = data.get('sesion_id')
        pregunta = data.get('pregunta')
        
        if sesion_id not in sessions:
            return jsonify({'success': False, 'error': 'Sesión no encontrada'}), 404
        
        manager = sessions[sesion_id]
        
        # Procesar duda
        resultado = manager._procesar_duda_post_diagnostico(pregunta)
        
        return jsonify({
            'success': True,
            'resultado': resultado
        })
        
    except Exception as e:
        print(f"❌ Error respondiendo duda: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sesion/imprimir', methods=['POST'])
def imprimir_receta():
    """Imprimir receta"""
    try:
        data = request.get_json()
        sesion_id = data.get('sesion_id')
        
        if sesion_id not in sessions:
            return jsonify({'success': False, 'error': 'Sesión no encontrada'}), 404
        
        manager = sessions[sesion_id]
        
        exito, info = manager.imprimir_receta()
        
        return jsonify({
            'success': exito,
            'info': info
        })
        
    except Exception as e:
        print(f"❌ Error imprimir: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sesion/finalizar', methods=['POST'])
def finalizar_sesion():
    """Finalizar sesión"""
    try:
        data = request.get_json()
        sesion_id = data.get('sesion_id')
        
        if sesion_id not in sessions:
            return jsonify({'success': False, 'error': 'Sesión no encontrada'}), 404
        
        manager = sessions[sesion_id]
        
        # Finalizar
        resumen = manager.finalizar_sesion()
        
        # Limpiar sesión
        del sessions[sesion_id]
        
        return jsonify({
            'success': True,
            'resumen': resumen
        })
        
    except Exception as e:
        print(f"❌ Error finalizar: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENDPOINTS - ESTADÍSTICAS Y SISTEMA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/estadisticas', methods=['GET'])
def estadisticas():
    """Obtener estadísticas del día"""
    try:
        stats = db.obtener_estadisticas_hoy()
        
        return jsonify({
            'success': True,
            'estadisticas': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check del sistema"""
    try:
        mysql_ok = db.conexion and db.conexion.is_connected()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'mysql': mysql_ok,
            'sesiones_activas': len(sessions),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config', methods=['GET'])
def obtener_config():
    """Obtener configuración"""
    try:
        config = {
            'sistema': 'Kairos V2.1',
            'gpt_activo': True,
            'sesiones_activas': len(sessions)
        }
        
        return jsonify({'success': True, 'config': config})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INICIAR SERVIDOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == '__main__':
    print("="*70)
    print("🚀 KAIROS API REST V2.1")
    print("="*70)
    print("Puerto: 5000")
    print("Características:")
    print("  ✅ Conversación GPT natural")
    print("  ✅ Diagnóstico con causas")
    print("  ✅ Chat post-diagnóstico")
    print("  ✅ Detalles de uso en receta")
    print("="*70 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )