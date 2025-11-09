"""
Gestor de Plantas Medicinales - BASADO EN BD REAL
Estructura: plantas_medicinales
"""

import sys
import os
from typing import List, Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.database.database_manager import DatabaseManager

class PlantasMedicinalesManager:
    """Gestor de plantas medicinales desde BD"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.catalogo = None
        self._cargar_desde_bd()
    
    def _cargar_desde_bd(self):
        """Cargar plantas desde BD"""
        try:
            query = """
            SELECT 
                id,
                nombre_comun,
                nombre_cientifico,
                categoria,
                descripcion,
                propiedades_curativas,
                sintomas_que_trata,
                formas_preparacion,
                dosis_recomendada,
                frecuencia_uso,
                duracion_tratamiento,
                mejor_momento_tomar,
                contraindicaciones,
                efectos_secundarios,
                advertencias,
                veces_recomendado,
                activo
            FROM plantas_medicinales 
            WHERE activo = TRUE 
            ORDER BY veces_recomendado DESC
            """
            
            plantas = self.db.ejecutar_query(query)
            
            if plantas:
                self.catalogo = plantas
                print(f"🌿 Plantas Medicinales Manager inicializado ({len(plantas)} plantas)")
            else:
                self.catalogo = []
        
        except Exception as e:
            print(f"❌ Error cargando plantas: {e}")
            self.catalogo = []
    
    def obtener_todas(self) -> List[Dict]:
        """Obtener todas las plantas activas"""
        return self.catalogo if self.catalogo else []
    
    def obtener_por_id(self, planta_id: int) -> Optional[Dict]:
        """Obtener planta por ID"""
        if not self.catalogo:
            return None
        
        for planta in self.catalogo:
            if planta['id'] == planta_id:
                return planta
        
        return None
    
    def buscar_por_sintoma(self, sintoma: str) -> List[Dict]:
        """Buscar plantas por síntoma"""
        if not self.catalogo:
            return []
        
        sintoma_lower = sintoma.lower()
        resultados = []
        
        for planta in self.catalogo:
            sintomas = (planta.get('sintomas_que_trata') or '').lower()
            propiedades = (planta.get('propiedades_curativas') or '').lower()
            
            if sintoma_lower in sintomas or sintoma_lower in propiedades:
                resultados.append(planta)
        
        return resultados
    
    def incrementar_uso(self, planta_id: int):
        """Incrementar contador de uso"""
        query = """
        UPDATE plantas_medicinales 
        SET veces_recomendado = veces_recomendado + 1 
        WHERE id = %s
        """
        self.db.ejecutar_comando(query, (planta_id,))


if __name__ == "__main__":
    print("="*60)
    print("TEST PLANTAS MEDICINALES MANAGER")
    print("="*60)
    
    pm = PlantasMedicinalesManager()
    
    print(f"\nTotal plantas: {len(pm.obtener_todas())}")
    
    if pm.catalogo:
        print("\nPrimeras 3 plantas:")
        for p in pm.obtener_todas()[:3]:
            print(f"  • {p['nombre_comun']}")
    
    print("\n" + "="*60)