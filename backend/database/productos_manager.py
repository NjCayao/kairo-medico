"""
Gestor de Productos Naturales - VERSIÓN BD FINAL
✅ Carga desde MySQL (productos_naturales)
✅ Excel SOLO para importar/exportar
✅ GPT puede enriquecer info faltante
"""

import sys
import os
from typing import List, Dict, Optional
import json
import requests

# Agregar path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database.database_manager import DatabaseManager
from backend.core.ia_config_manager import IAConfigManager

class ProductosManager:
    """Gestor de productos desde BD MySQL"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.ia_config = IAConfigManager()
        self.catalogo = None
        self.productos_dict = {}
        
        # Cargar desde BD
        self._cargar_desde_bd()
    
    def _cargar_desde_bd(self):
        """Cargar productos desde MySQL"""
        try:
            query = """
            SELECT * FROM productos_naturales 
            WHERE activo = TRUE 
            ORDER BY nivel_prioridad DESC, veces_recomendado DESC
            """
            
            productos = self.db.ejecutar_query(query)
            
            if productos:
                self.catalogo = productos
                self.productos_dict = {p['id']: p for p in productos}
                
                print(f"📦 Productos cargados desde BD: {len(productos)} activos")
                for p in productos:
                    print(f"   - {p['nombre']} (S/. {float(p['precio']):.0f})")
            else:
                print("⚠️ No hay productos en BD")
                self.catalogo = []
        
        except Exception as e:
            print(f"❌ Error: {e}")
            self.catalogo = []
    
    def obtener_todos(self) -> List[Dict]:
        """Todos los productos activos"""
        return self.catalogo if self.catalogo else []
    
    def obtener_por_id(self, producto_id: int) -> Optional[Dict]:
        """Producto por ID"""
        return self.productos_dict.get(producto_id)
    
    def buscar_por_sintoma(self, sintoma: str) -> List[Dict]:
        """Buscar por síntoma"""
        if not self.catalogo:
            return []
        
        sintoma_lower = sintoma.lower()
        resultados = []
        
        for p in self.catalogo:
            sintomas = (p.get('sintomas_que_trata') or '').lower()
            para_que = (p.get('para_que_sirve') or '').lower()
            
            if sintoma_lower in sintomas or sintoma_lower in para_que:
                resultados.append(p)
        
        return resultados
    
    def incrementar_recomendacion(self, producto_id: int):
        """Incrementar recomendaciones"""
        query = "UPDATE productos_naturales SET veces_recomendado = veces_recomendado + 1 WHERE id = %s"
        self.db.ejecutar_comando(query, (producto_id,))
    
    def enriquecer_producto_con_gpt(self, producto_id: int) -> bool:
        """Enriquecer info con GPT"""
        if not self.ia_config.esta_activo():
            return False
        
        producto = self.obtener_por_id(producto_id)
        if not producto or (producto.get('para_que_sirve') and producto.get('sintomas_que_trata')):
            return True
        
        print(f"🔍 Buscando info: {producto['nombre']}")
        
        prompt = f"""Información sobre: {producto['nombre']}

SOLO JSON:
{{
  "para_que_sirve": "Descripción",
  "beneficios_principales": "Lista separada por comas",
  "sintomas_que_trata": "síntomas separados por comas",
  "dosis_recomendada": "Dosis típica",
  "contraindicaciones": "Contraindicaciones"
}}"""

        try:
            config = self.ia_config.obtener_config()
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={'Authorization': f"Bearer {config['api_key']}", 'Content-Type': 'application/json'},
                json={
                    'model': config['modelo'],
                    'messages': [
                        {'role': 'system', 'content': 'Eres experto en medicina natural. SOLO JSON.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 600
                },
                timeout=25
            )
            
            if response.status_code == 200:
                data = response.json()
                contenido = data['choices'][0]['message']['content'].strip()
                contenido = contenido.replace('```json', '').replace('```', '').strip()
                
                info = json.loads(contenido)
                
                query = """
                UPDATE productos_naturales 
                SET para_que_sirve = COALESCE(para_que_sirve, %s),
                    beneficios_principales = COALESCE(beneficios_principales, %s),
                    sintomas_que_trata = COALESCE(sintomas_que_trata, %s),
                    dosis_recomendada = COALESCE(dosis_recomendada, %s),
                    contraindicaciones = COALESCE(contraindicaciones, %s)
                WHERE id = %s
                """
                
                self.db.ejecutar_comando(query, (
                    info.get('para_que_sirve'),
                    info.get('beneficios_principales'),
                    info.get('sintomas_que_trata'),
                    info.get('dosis_recomendada'),
                    info.get('contraindicaciones'),
                    producto_id
                ))
                
                print(f"✅ Enriquecido: {producto['nombre']}")
                self._cargar_desde_bd()
                return True
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return False


# Test
if __name__ == "__main__":
    print("="*60)
    print("TEST PRODUCTOS MANAGER - BD")
    print("="*60)
    
    pm = ProductosManager()
    
    print(f"\n📊 Total: {len(pm.obtener_todos())}")
    
    if pm.catalogo:
        print(f"\n🔍 Test búsqueda 'dolor':")
        resultados = pm.buscar_por_sintoma("dolor")
        for p in resultados:
            print(f"   • {p['nombre']}")
    
    print("\n" + "="*60)