"""
Gestor de Configuración de IA
Lee configuración desde BD (panel admin)
"""

import sys
import os
from typing import Dict, Optional
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database.database_manager import DatabaseManager

class IAConfigManager:
    """
    Gestor de configuración de IA
    """
    
    def __init__(self):
        """Inicializar gestor"""
        self.db = DatabaseManager()
        self.config = None
        self.cargar_configuracion()
    
    def cargar_configuracion(self) -> bool:
        """
        Cargar configuración desde BD
        """
        try:
            query = """
            SELECT * FROM configuracion_ia 
            WHERE activo = TRUE 
            ORDER BY id DESC 
            LIMIT 1
            """
            
            resultado = self.db.ejecutar_query(query)
            
            if resultado and len(resultado) > 0:
                self.config = resultado[0]
                print(f"✅ Config IA cargada: {self.config['proveedor']} ({self.config['modelo_gpt']})")
                return True
            else:
                print("⚠️ No hay configuración de IA activa")
                self.config = None
                return False
                
        except Exception as e:
            print(f"❌ Error cargando config IA: {e}")
            self.config = None
            return False
    
    def esta_activo(self) -> bool:
        """Verificar si IA está activa"""
        return self.config is not None and self.config['activo']
    
    def tiene_api_key(self) -> bool:
        """Verificar si tiene API key configurada"""
        if not self.config:
            return False
        
        api_key = self.config.get('api_key', '')
        return api_key and api_key != 'TU_API_KEY_AQUI' and len(api_key) > 20
    
    def puede_hacer_consulta(self) -> tuple[bool, str]:
        """
        Verificar si puede hacer consulta IA
        
        Returns:
            (puede, razon)
        """
        if not self.esta_activo():
            return False, "IA no está activa en configuración"
        
        if not self.tiene_api_key():
            return False, "No hay API key configurada"
        
        # Verificar límite diario
        if self.config['consultas_realizadas_hoy'] >= self.config['limite_diario_consultas']:
            return False, f"Límite diario alcanzado ({self.config['limite_diario_consultas']})"
        
        # Verificar presupuesto mensual
        if self.config['gasto_mes_actual'] >= self.config['presupuesto_mensual']:
            return False, f"Presupuesto mensual agotado (S/. {self.config['presupuesto_mensual']})"
        
        return True, "OK"
    
    def obtener_config(self) -> Dict:
        """Obtener configuración completa"""
        if not self.config:
            return {}
        
        return {
            'proveedor': self.config['proveedor'],
            'modelo': self.config['modelo_gpt'] if self.config['proveedor'] == 'openai' else self.config['modelo_claude'],
            'api_key': self.config['api_key'],
            'temperatura': float(self.config['temperatura']),
            'max_tokens': self.config['max_tokens'],
            'guardar_respuestas': self.config['guardar_respuestas_ia'],
            'confianza_minima': float(self.config['confianza_minima_guardar'])
        }
    
    def incrementar_consulta(self, costo: float = 0.02):
        """
        Registrar consulta realizada
        """
        if not self.config:
            return
        
        query = """
        UPDATE configuracion_ia 
        SET consultas_realizadas_hoy = consultas_realizadas_hoy + 1,
            gasto_mes_actual = gasto_mes_actual + %s
        WHERE id = %s
        """
        
        self.db.ejecutar_comando(query, (costo, self.config['id']))
    
    def resetear_contador_diario(self):
        """
        Resetear contador diario (cron job)
        """
        query = "UPDATE configuracion_ia SET consultas_realizadas_hoy = 0"
        self.db.ejecutar_comando(query)
        print("✅ Contador diario de consultas reseteado")
    
    def resetear_gasto_mensual(self):
        """
        Resetear gasto mensual (cron job)
        """
        query = "UPDATE configuracion_ia SET gasto_mes_actual = 0"
        self.db.ejecutar_comando(query)
        print("✅ Gasto mensual reseteado")
    
    def registrar_consulta_log(self, datos: Dict) -> int:
        """
        Registrar consulta en log
        """
        query = """
        INSERT INTO log_consultas_ia (
            sesion_id, usuario_id, sintoma, contexto_enviado, prompt_usado,
            respuesta_ia, tokens_usados, tiempo_respuesta_ms,
            proveedor, modelo, costo_estimado,
            diagnostico_generado, confianza, guardado_en_bd,
            exitosa, error_mensaje
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        parametros = (
            datos.get('sesion_id'),
            datos.get('usuario_id'),
            datos.get('sintoma'),
            datos.get('contexto_enviado'),
            datos.get('prompt_usado'),
            datos.get('respuesta_ia'),
            datos.get('tokens_usados', 0),
            datos.get('tiempo_respuesta_ms', 0),
            datos.get('proveedor'),
            datos.get('modelo'),
            datos.get('costo_estimado', 0.02),
            datos.get('diagnostico_generado'),
            datos.get('confianza', 0.0),
            datos.get('guardado_en_bd', False),
            datos.get('exitosa', True),
            datos.get('error_mensaje')
        )
        
        if self.db.ejecutar_comando(query, parametros):
            return self.db.obtener_ultimo_id()
        
        return 0
    
    def obtener_estadisticas_hoy(self) -> Dict:
        """
        Obtener estadísticas del día
        """
        query = """
        SELECT 
            COUNT(*) as total,
            SUM(tokens_usados) as tokens,
            SUM(costo_estimado) as costo,
            AVG(tiempo_respuesta_ms) as tiempo_promedio
        FROM log_consultas_ia
        WHERE DATE(fecha_consulta) = CURDATE()
        """
        
        resultado = self.db.ejecutar_query(query)
        
        if resultado:
            return resultado[0]
        
        return {'total': 0, 'tokens': 0, 'costo': 0, 'tiempo_promedio': 0}
    
    def obtener_estadisticas_mes(self) -> Dict:
        """
        Obtener estadísticas del mes
        """
        query = """
        SELECT 
            COUNT(*) as total,
            SUM(tokens_usados) as tokens,
            SUM(costo_estimado) as costo,
            SUM(CASE WHEN guardado_en_bd = 1 THEN 1 ELSE 0 END) as guardados
        FROM log_consultas_ia
        WHERE MONTH(fecha_consulta) = MONTH(CURDATE())
        AND YEAR(fecha_consulta) = YEAR(CURDATE())
        """
        
        resultado = self.db.ejecutar_query(query)
        
        if resultado:
            stats = resultado[0]
            stats['presupuesto'] = self.config['presupuesto_mensual'] if self.config else 0
            stats['porcentaje_usado'] = (stats['costo'] / stats['presupuesto'] * 100) if stats['presupuesto'] > 0 else 0
            return stats
        
        return {'total': 0, 'tokens': 0, 'costo': 0, 'guardados': 0}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRUEBAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("="*70)
    print("🧪 TEST CONFIG MANAGER IA")
    print("="*70)
    
    manager = IAConfigManager()
    
    print(f"\n¿IA activa?: {manager.esta_activo()}")
    print(f"¿Tiene API key?: {manager.tiene_api_key()}")
    
    puede, razon = manager.puede_hacer_consulta()
    print(f"¿Puede consultar?: {puede}")
    if not puede:
        print(f"Razón: {razon}")
    
    if manager.config:
        config = manager.obtener_config()
        print(f"\nConfiguración:")
        print(f"  Proveedor: {config.get('proveedor')}")
        print(f"  Modelo: {config.get('modelo')}")
        print(f"  Temperatura: {config.get('temperatura')}")
        print(f"  Max tokens: {config.get('max_tokens')}")
    
    stats_hoy = manager.obtener_estadisticas_hoy()
    print(f"\nEstadísticas hoy:")
    print(f"  Consultas: {stats_hoy['total']}")
    print(f"  Costo: S/. {stats_hoy['costo']:.4f}")
    
    stats_mes = manager.obtener_estadisticas_mes()
    print(f"\nEstadísticas mes:")
    print(f"  Consultas: {stats_mes['total']}")
    print(f"  Costo: S/. {stats_mes['costo']:.2f}")
    print(f"  Guardados: {stats_mes['guardados']}")
    
    print("\n" + "="*70)