"""
Gestor de Remedios Caseros - BASADO EN BD REAL
Estructura: remedios_caseros
"""

import sys
import os
from typing import List, Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.database.database_manager import DatabaseManager

class RemediosCaserosManager:
    """Gestor de remedios caseros desde BD"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.catalogo = None
        self._cargar_desde_bd()
    
    def _cargar_desde_bd(self):
        """Cargar remedios desde BD"""
        try:
            query = """
            SELECT 
                id,
                nombre,
                categoria,
                descripcion,
                ingredientes_json,
                ingredientes_texto,
                sintomas_que_trata,
                propiedades,
                preparacion_paso_a_paso,
                como_aplicar,
                frecuencia,
                duracion_tratamiento,
                mejor_momento,
                contraindicaciones,
                advertencias,
                temperatura,
                veces_recomendado,
                activo
            FROM remedios_caseros 
            WHERE activo = TRUE 
            ORDER BY veces_recomendado DESC
            """
            
            remedios = self.db.ejecutar_query(query)
            
            if remedios:
                self.catalogo = remedios
                print(f"🍯 Remedios Caseros Manager inicializado ({len(remedios)} remedios)")
            else:
                self.catalogo = []
        
        except Exception as e:
            print(f"❌ Error cargando remedios: {e}")
            self.catalogo = []
    
    def obtener_todos(self) -> List[Dict]:
        """Obtener todos los remedios activos"""
        return self.catalogo if self.catalogo else []
    
    def obtener_por_id(self, remedio_id: int) -> Optional[Dict]:
        """Obtener remedio por ID"""
        if not self.catalogo:
            return None
        
        for remedio in self.catalogo:
            if remedio['id'] == remedio_id:
                return remedio
        
        return None
    
    def buscar_por_sintoma(self, sintoma: str) -> List[Dict]:
        """Buscar remedios por síntoma"""
        if not self.catalogo:
            return []
        
        sintoma_lower = sintoma.lower()
        resultados = []
        
        for remedio in self.catalogo:
            sintomas = (remedio.get('sintomas_que_trata') or '').lower()
            descripcion = (remedio.get('descripcion') or '').lower()
            
            if sintoma_lower in sintomas or sintoma_lower in descripcion:
                resultados.append(remedio)
        
        return resultados
    
    def incrementar_uso(self, remedio_id: int):
        """Incrementar contador de uso"""
        query = """
        UPDATE remedios_caseros 
        SET veces_recomendado = veces_recomendado + 1 
        WHERE id = %s
        """
        self.db.ejecutar_comando(query, (remedio_id,))


if __name__ == "__main__":
    print("="*60)
    print("TEST REMEDIOS CASEROS MANAGER")
    print("="*60)
    
    rm = RemediosCaserosManager()
    
    print(f"\nTotal remedios: {len(rm.obtener_todos())}")
    
    if rm.catalogo:
        print("\nPrimeros 3 remedios:")
        for r in rm.obtener_todos()[:3]:
            print(f"  • {r['nombre']}")
    
    print("\n" + "="*60)