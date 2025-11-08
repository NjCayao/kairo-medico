"""
Learning Manager - Sistema de Aprendizaje Automático
Kairos aprende de cada conversación
"""

import sys
import os
from typing import Dict, List
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

from backend.database.db_manager import DatabaseManager

class LearningManager:
    """
    Sistema de Aprendizaje Automático
    
    Funciones:
    - Analizar conversaciones exitosas
    - Identificar patrones comunes
    - Mejorar respuestas automáticamente
    - Estadísticas de desempeño
    """
    
    def __init__(self):
        """Inicializar learning manager"""
        
        self.db = DatabaseManager()
        print("📚 Learning Manager inicializado")
    
    def registrar_conversacion(self, 
                               paciente_nombre: str,
                               mensajes: List[Dict],
                               exitosa: bool = True,
                               calificacion: float = None):
        """Registrar conversación completa para análisis"""
        
        query = """
        INSERT INTO conversaciones_aprendizaje
        (paciente_nombre, total_mensajes, exitosa, calificacion, fecha)
        VALUES (%s, %s, %s, %s, NOW())
        """
        
        try:
            self.db.ejecutar_query(
                query,
                (paciente_nombre, len(mensajes), exitosa, calificacion)
            )
            print(f"   📝 Conversación registrada para aprendizaje")
        except:
            pass
    
    def obtener_estadisticas_aprendizaje(self) -> Dict:
        """Obtener estadísticas del sistema de aprendizaje"""
        
        query = """
        SELECT 
            COUNT(*) as total_conversaciones,
            SUM(CASE WHEN exitosa = TRUE THEN 1 ELSE 0 END) as exitosas,
            AVG(total_mensajes) as promedio_mensajes,
            AVG(calificacion) as calificacion_promedio
        FROM conversaciones_aprendizaje
        WHERE fecha >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """
        
        try:
            resultado = self.db.ejecutar_query(query)
            if resultado:
                return {
                    'conversaciones_ultimo_mes': resultado[0]['total_conversaciones'] or 0,
                    'tasa_exito': (resultado[0]['exitosas'] or 0) / max(resultado[0]['total_conversaciones'], 1) * 100,
                    'mensajes_promedio': float(resultado[0]['promedio_mensajes'] or 0),
                    'calificacion': float(resultado[0]['calificacion_promedio'] or 0)
                }
        except:
            pass
        
        return {
            'conversaciones_ultimo_mes': 0,
            'tasa_exito': 0,
            'mensajes_promedio': 0,
            'calificacion': 0
        }
    
    def obtener_patrones_comunes(self) -> List[Dict]:
        """Obtener patrones comunes de conversación"""
        
        query = """
        SELECT patron_mensaje, COUNT(*) as frecuencia
        FROM respuestas_aprendidas
        WHERE activo = TRUE
        GROUP BY patron_mensaje
        ORDER BY frecuencia DESC
        LIMIT 10
        """
        
        try:
            return self.db.ejecutar_query(query) or []
        except:
            return []


if __name__ == "__main__":
    print("🧪 TEST LEARNING MANAGER")
    learning = LearningManager()
    stats = learning.obtener_estadisticas_aprendizaje()
    print(f"Estadísticas: {stats}")