"""
API REST de Kairos - Flask
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.core.session_manager import SessionManager
from backend.core.learner import KairosLearner
from backend.database.database_manager import DatabaseManager
from config.settings import Config

app = Flask(__name__)
CORS(app)

# Managers globales
sessions = {}  # {sesion_id: SessionManager}
db = DatabaseManager()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENDPOINTS - SESIONES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/sesion/nueva', methods=['POST'])
def crear_sesion():
    """Crear nueva sesión"""
    try:
        data = request.get_json() or {}
        
        # Obtener configuración
        config_sistema = db.obtener_configuracion('evento_nombre') or Config.EVENTO_NOMBRE
        ubicacion = data.get('ubicacion') or db.obtener_configuracion('ubicacion') or Config.UBICACION
        dispositivo = data.get('dispositivo', 'web')
        
        # Crear session manager
        manager = SessionManager(
            evento=config_sistema,
            ubicacion=ubicacion,
            dispositivo=dispositivo,
            modo_offline=data.get('modo_offline', False)
        )
        
        # Nueva sesión
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
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sesion/mensaje', methods=['POST'])
def procesar_mensaje():
    """Procesar mensaje del usuario"""
    try:
        data = request.get_json()
        sesion_id = data.get('sesion_id')
        mensaje = data.get('mensaje')
        
        if sesion_id not in sessions:
            return jsonify({'success': False, 'error': 'Sesión no encontrada'}), 404
        
        manager = sessions[sesion_id]
        resultado = manager.procesar_mensaje(mensaje)
        
        return jsonify({
            'success': True,
            'resultado': resultado
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sesion/finalizar', methods=['POST'])
def finalizar_sesion():
    """Finalizar sesión y generar receta"""
    try:
        data = request.get_json()
        sesion_id = data.get('sesion_id')
        
        if sesion_id not in sessions:
            return jsonify({'success': False, 'error': 'Sesión no encontrada'}), 404
        
        manager = sessions[sesion_id]
        
        # Generar diagnóstico y receta
        exito, resultado = manager.generar_diagnostico_y_receta()
        
        if not exito:
            return jsonify({'success': False, 'error': 'Error generando diagnóstico'}), 500
        
        # Imprimir (si está configurado)
        exito_imp, info_imp = manager.imprimir_receta()
        
        # Finalizar
        resumen = manager.finalizar_sesion()
        
        # Limpiar sesión
        del sessions[sesion_id]
        
        return jsonify({
            'success': True,
            'diagnostico': resultado['diagnostico'],
            'receta': resultado['receta'],
            'impresion': info_imp,
            'resumen': resumen
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sesion/estado/<sesion_id>', methods=['GET'])
def estado_sesion(sesion_id):
    """Obtener estado de sesión"""
    try:
        if sesion_id not in sessions:
            return jsonify({'success': False, 'error': 'Sesión no encontrada'}), 404
        
        manager = sessions[sesion_id]
        estado = {
            'sesion_id': manager.sesion_id,
            'estado': manager.estado,
            'usuario': manager.usuario_data['nombre'] if manager.usuario_data else None,
            'mensajes': len(manager.mensajes_conversacion)
        }
        
        return jsonify({'success': True, 'estado': estado})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENDPOINTS - ESTADÍSTICAS
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


@app.route('/api/estadisticas/sesiones-activas', methods=['GET'])
def sesiones_activas():
    """Obtener sesiones activas"""
    try:
        activas = [{
            'sesion_id': sid,
            'estado': manager.estado,
            'usuario': manager.usuario_data['nombre'] if manager.usuario_data else None
        } for sid, manager in sessions.items()]
        
        return jsonify({
            'success': True,
            'total': len(activas),
            'sesiones': activas
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENDPOINTS - APRENDIZAJE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/aprender', methods=['POST'])
def ejecutar_aprendizaje():
    """Ejecutar ciclo de aprendizaje"""
    try:
        data = request.get_json() or {}
        dias = data.get('dias', 7)
        
        learner = KairosLearner(auto_entrenamiento=True)
        resultado = learner.ejecutar_ciclo_aprendizaje(dias)
        
        return jsonify({
            'success': True,
            'resultado': resultado
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENDPOINTS - CONFIGURACIÓN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/config', methods=['GET'])
def obtener_config():
    """Obtener configuración del sistema"""
    try:
        config = {
            'evento': db.obtener_configuracion('evento_nombre') or Config.EVENTO_NOMBRE,
            'ubicacion': db.obtener_configuracion('ubicacion') or Config.UBICACION,
            'voz_activa': db.obtener_configuracion('voz_activa') or Config.VOZ_ACTIVA,
            'modo_operacion': Config.MODO_OPERACION
        }
        
        return jsonify({'success': True, 'config': config})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check del sistema"""
    try:
        # Verificar MySQL
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INICIAR SERVIDOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == '__main__':
    print("="*70)
    print("🚀 KAIROS API REST")
    print("="*70)
    print(f"Puerto: {Config.API_PORT}")
    print(f"Debug: {Config.DEBUG}")
    print("="*70 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=Config.API_PORT,
        debug=Config.DEBUG
    )