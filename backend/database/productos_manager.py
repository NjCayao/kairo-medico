"""
Gestor de Productos Naturales
Lee catálogo desde Excel
"""

import pandas as pd
import os
import sys
from typing import List, Dict, Optional

# Agregar path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import Config

class ProductosManager:
    """
    Gestor de catálogo de productos naturales
    """
    
    def __init__(self, excel_path: str = None):
        """
        Inicializar gestor
        
        Args:
            excel_path: Ruta al archivo Excel (opcional)
        """
        self.excel_path = excel_path or Config.EXCEL_PRODUCTOS
        self.catalogo = None
        self.productos_dict = {}
        
        # Cargar catálogo al iniciar
        self.cargar_catalogo()
    
    def cargar_catalogo(self) -> bool:
        """
        Cargar catálogo desde Excel
        
        Returns:
            bool: True si cargó exitosamente
        """
        try:
            print(f"📂 Cargando catálogo desde: {self.excel_path}")
            
            # Verificar que existe
            if not os.path.exists(self.excel_path):
                print(f"❌ No se encuentra el archivo: {self.excel_path}")
                return False
            
            # Leer Excel
            self.catalogo = pd.read_excel(self.excel_path)
            
            # Normalizar nombres de columnas (minúsculas, sin espacios)
            self.catalogo.columns = [col.lower().strip().replace(' ', '_') 
                                    for col in self.catalogo.columns]
            
            # Filtrar solo productos activos
            self.catalogo = self.catalogo[self.catalogo['activo'] == True]
            
            # Crear diccionario por ID para búsqueda rápida
            self.productos_dict = {
                row['id']: row.to_dict() 
                for _, row in self.catalogo.iterrows()
            }
            
            print(f"✅ Catálogo cargado: {len(self.catalogo)} productos activos")
            
            # Mostrar productos cargados
            for _, producto in self.catalogo.iterrows():
                print(f"   - {producto['nombre']} (S/. {producto['precio']})")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar catálogo: {e}")
            return False
    
    def obtener_todos(self) -> List[Dict]:
        """
        Obtener todos los productos activos
        
        Returns:
            Lista de diccionarios con productos
        """
        if self.catalogo is None:
            return []
        
        return self.catalogo.to_dict('records')
    
    def obtener_por_id(self, producto_id: int) -> Optional[Dict]:
        """
        Obtener producto por ID
        
        Args:
            producto_id: ID del producto
            
        Returns:
            Dict con datos del producto o None
        """
        return self.productos_dict.get(producto_id)
    
    def buscar_por_categoria(self, categoria: str) -> List[Dict]:
        """
        Buscar productos por categoría
        
        Args:
            categoria: moringa_capsulas, ganoderma_te, etc
            
        Returns:
            Lista de productos de esa categoría
        """
        if self.catalogo is None:
            return []
        
        resultados = self.catalogo[
            self.catalogo['categoria'].str.lower() == categoria.lower()
        ]
        
        return resultados.to_dict('records')
    
    def buscar_por_sintoma(self, sintoma: str) -> List[Dict]:
        """
        Buscar productos que traten un síntoma específico
        
        Args:
            sintoma: síntoma a buscar (ej: "dolor de cabeza", "fatiga")
            
        Returns:
            Lista de productos que tratan ese síntoma
        """
        if self.catalogo is None:
            return []
        
        # Normalizar búsqueda
        sintoma_lower = sintoma.lower().strip()
        
        # Buscar en columna sintomas_que_trata
        resultados = self.catalogo[
            self.catalogo['sintomas_que_trata'].str.lower().str.contains(
                sintoma_lower, 
                na=False, 
                regex=False
            )
        ]
        
        productos = resultados.to_dict('records')
        
        print(f"🔍 Búsqueda '{sintoma}': {len(productos)} productos encontrados")
        
        return productos
    
    def buscar_por_multiples_sintomas(self, sintomas: List[str]) -> List[Dict]:
        """
        Buscar productos que traten varios síntomas
        Prioriza productos que tratan más síntomas
        
        Args:
            sintomas: Lista de síntomas
            
        Returns:
            Lista de productos ordenados por relevancia
        """
        if self.catalogo is None or not sintomas:
            return []
        
        productos_score = {}
        
        # Por cada producto, contar cuántos síntomas trata
        for _, producto in self.catalogo.iterrows():
            sintomas_producto = producto['sintomas_que_trata'].lower()
            score = 0
            
            for sintoma in sintomas:
                if sintoma.lower() in sintomas_producto:
                    score += 1
            
            if score > 0:
                producto_dict = producto.to_dict()
                producto_dict['score_relevancia'] = score
                productos_score[producto['id']] = producto_dict
        
        # Ordenar por score (mayor a menor)
        productos_ordenados = sorted(
            productos_score.values(),
            key=lambda x: x['score_relevancia'],
            reverse=True
        )
        
        print(f"🔍 Búsqueda múltiple: {len(productos_ordenados)} productos encontrados")
        for prod in productos_ordenados[:3]:  # Top 3
            print(f"   - {prod['nombre']} (match: {prod['score_relevancia']} síntomas)")
        
        return productos_ordenados
    
    def buscar_texto_libre(self, texto: str) -> List[Dict]:
        """
        Búsqueda de texto libre en nombre, descripción y síntomas
        
        Args:
            texto: Texto a buscar
            
        Returns:
            Lista de productos que contienen el texto
        """
        if self.catalogo is None:
            return []
        
        texto_lower = texto.lower().strip()
        
        # Buscar en múltiples columnas
        mascara = (
            self.catalogo['nombre'].str.lower().str.contains(texto_lower, na=False) |
            self.catalogo['descripcion_corta'].str.lower().str.contains(texto_lower, na=False) |
            self.catalogo['sintomas_que_trata'].str.lower().str.contains(texto_lower, na=False)
        )
        
        resultados = self.catalogo[mascara]
        
        return resultados.to_dict('records')
    
    def obtener_por_precio(self, precio_min: float = 0, 
                          precio_max: float = 1000) -> List[Dict]:
        """
        Filtrar productos por rango de precio
        
        Args:
            precio_min: Precio mínimo
            precio_max: Precio máximo
            
        Returns:
            Lista de productos en ese rango
        """
        if self.catalogo is None:
            return []
        
        resultados = self.catalogo[
            (self.catalogo['precio'] >= precio_min) &
            (self.catalogo['precio'] <= precio_max)
        ]
        
        return resultados.to_dict('records')
    
    def obtener_info_completa(self, producto_id: int) -> str:
        """
        Obtener información completa de un producto
        Formateada para mostrar a usuario
        
        Args:
            producto_id: ID del producto
            
        Returns:
            str: Información formateada
        """
        producto = self.obtener_por_id(producto_id)
        
        if not producto:
            return "Producto no encontrado"
        
        info = f"""
╔══════════════════════════════════════════════════════════╗
  {producto['nombre'].upper()}
╚══════════════════════════════════════════════════════════╝

📦 PRESENTACIÓN:
   {producto['presentacion']}

💊 PARA QUÉ SIRVE:
   {producto['para_que_sirve']}

✅ BENEFICIOS PRINCIPALES:
   {producto['beneficios']}

📋 CÓMO USAR:
   • Dosis: {producto['dosis']}
   • Momento: {producto['momento_tomar']}
   • Preparación: {producto['como_preparar']}

🔄 COMBINACIONES:
   • Combina bien con: {producto['combinar_con']}
   • Evitar con: {producto['evitar_con']}

⚠️ IMPORTANTE:
   • Contraindicaciones: {producto['contraindicaciones']}
   • Efectos secundarios: {producto['efectos_secundarios']}

⏱️ RESULTADOS:
   {producto['cuando_hace_efecto']}

💰 PRECIO: S/. {producto['precio']:.2f}

⭐ DIFERENCIADOR:
   {producto['diferenciador']}
"""
        return info
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtener estadísticas del catálogo
        
        Returns:
            Dict con estadísticas
        """
        if self.catalogo is None:
            return {}
        
        stats = {
            'total_productos': len(self.catalogo),
            'por_categoria': self.catalogo['categoria'].value_counts().to_dict(),
            'precio_promedio': float(self.catalogo['precio'].mean()),
            'precio_min': float(self.catalogo['precio'].min()),
            'precio_max': float(self.catalogo['precio'].max()),
        }
        
        return stats

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRUEBAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("="*60)
    print("PROBANDO PRODUCTOS MANAGER")
    print("="*60)
    
    # Crear instancia
    pm = ProductosManager()
    
    if pm.catalogo is not None:
        print("\n✅ Catálogo cargado correctamente\n")
        
        # Test 1: Buscar por síntoma
        print("━"*60)
        print("TEST 1: Buscar por síntoma 'fatiga'")
        print("━"*60)
        productos = pm.buscar_por_sintoma('fatiga')
        for prod in productos:
            print(f"  • {prod['nombre']} - S/. {prod['precio']}")
        
        # Test 2: Buscar por categoría
        print("\n" + "━"*60)
        print("TEST 2: Buscar categoría 'moringa_capsulas'")
        print("━"*60)
        productos = pm.buscar_por_categoria('moringa_capsulas')
        for prod in productos:
            print(f"  • {prod['nombre']}")
        
        # Test 3: Buscar múltiples síntomas
        print("\n" + "━"*60)
        print("TEST 3: Buscar múltiples síntomas")
        print("━"*60)
        sintomas = ['fatiga', 'estrés', 'dolor de cabeza']
        productos = pm.buscar_por_multiples_sintomas(sintomas)
        for prod in productos[:2]:  # Top 2
            print(f"  • {prod['nombre']} (relevancia: {prod['score_relevancia']})")
        
        # Test 4: Obtener producto específico
        print("\n" + "━"*60)
        print("TEST 4: Información completa producto ID=1")
        print("━"*60)
        info = pm.obtener_info_completa(1)
        print(info)
        
        # Test 5: Estadísticas
        print("\n" + "━"*60)
        print("TEST 5: Estadísticas del catálogo")
        print("━"*60)
        stats = pm.obtener_estadisticas()
        print(f"  Total productos: {stats['total_productos']}")
        print(f"  Precio promedio: S/. {stats['precio_promedio']:.2f}")
        print(f"  Rango precios: S/. {stats['precio_min']:.2f} - S/. {stats['precio_max']:.2f}")
        print(f"  Por categoría: {stats['por_categoria']}")
        
    else:
        print("\n❌ No se pudo cargar el catálogo")
        print("   Verifica que el archivo Excel existe en:")
        print(f"   {Config.EXCEL_PRODUCTOS}")
    
    print("\n" + "="*60)