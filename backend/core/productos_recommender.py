"""
Productos Recommender - Sistema Inteligente de Recomendación
Asegura que Kairos SOLO recete productos que existen en inventario
"""

import sys
import os
from typing import Dict, List, Optional
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

from backend.database.productos_manager import ProductosManager
from backend.core.ia_config_manager import IAConfigManager

class ProductosRecommender:
    """
    Recomendador Inteligente de Productos
    
    Asegura que:
    - Solo recomienda productos en inventario
    - Matchea síntomas con productos adecuados
    - Considera stock disponible
    - Explica por qué recomienda cada producto
    """
    
    def __init__(self):
        """Inicializar recomendador"""
        
        self.productos = ProductosManager()
        self.ia_config = IAConfigManager()
        
        # Cargar catálogo
        self.catalogo = self._cargar_catalogo()
        
        print("💊 Productos Recommender inicializado")
        print(f"   Productos en catálogo: {len(self.catalogo)}")
    
    def _cargar_catalogo(self) -> List[Dict]:
        """Cargar catálogo completo de productos desde BD"""
        
        query = """
        SELECT 
            id,
            nombre,
            categoria,
            presentacion,
            para_que_sirve,
            beneficios_principales,
            sintomas_que_trata,
            perfil_paciente_ideal,
            dosis_recomendada,
            mejor_momento_tomar,
            duracion_tratamiento,
            precio,
            precio_oferta,
            stock
        FROM productos_naturales
        WHERE stock > 0
        ORDER BY nombre
        """
        
        from backend.database.db_manager import DatabaseManager
        db = DatabaseManager()
        
        try:
            productos_bd = db.ejecutar_query(query)
            
            catalogo = []
            for p in productos_bd:
                catalogo.append({
                    'id': p['id'],
                    'nombre': p['nombre'],
                    'categoria': p['categoria'],
                    'presentacion': p['presentacion'],
                    'para_que_sirve': p['para_que_sirve'],
                    'beneficios': p['beneficios_principales'],
                    'sintomas_que_trata': p['sintomas_que_trata'],
                    'perfil_paciente': p['perfil_paciente_ideal'],
                    'precio': float(p['precio']),
                    'precio_oferta': float(p['precio_oferta']) if p['precio_oferta'] else None,
                    'stock': p['stock'],
                    'dosis': p['dosis_recomendada'],
                    'momento': p['mejor_momento_tomar'],
                    'duracion': p['duracion_tratamiento']
                })
            
            return catalogo
            
        except Exception as e:
            print(f"   ⚠️ Error cargando catálogo: {e}")
            return []
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # RECOMENDACIÓN INTELIGENTE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def recomendar_productos(self, contexto_medico: Dict) -> List[Dict]:
        """
        Recomendar productos basándose en el contexto médico
        
        Args:
            contexto_medico: Información del paciente (síntomas, diagnóstico)
            
        Returns:
            Lista de productos recomendados con explicación
        """
        
        sintoma_principal = contexto_medico.get('sintoma_principal', '')
        sintomas_adicionales = contexto_medico.get('sintomas_adicionales', [])
        
        print(f"   🔍 Analizando: {sintoma_principal}")
        
        # Método 1: Reglas basadas en síntomas (rápido, sin GPT)
        productos_reglas = self._recomendar_por_reglas(
            sintoma_principal,
            sintomas_adicionales
        )
        
        if productos_reglas:
            print(f"   ✅ Recomendación por reglas: {len(productos_reglas)} productos")
            return productos_reglas
        
        # Método 2: GPT con catálogo limitado (inteligente)
        if self.ia_config.esta_activo():
            productos_gpt = self._recomendar_con_gpt(contexto_medico)
            
            if productos_gpt:
                print(f"   ✅ Recomendación por GPT: {len(productos_gpt)} productos")
                return productos_gpt
        
        # Fallback: Producto más vendido o general
        print(f"   ⚠️ Usando recomendación fallback")
        return self._recomendar_fallback()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MÉTODO 1: REGLAS BASADAS EN SÍNTOMAS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _recomendar_por_reglas(self, 
                               sintoma_principal: str,
                               sintomas_adicionales: List[str]) -> List[Dict]:
        """
        Recomendación basada en el campo sintomas_que_trata de la BD
        (Rápido, sin costo, siempre disponible)
        """
        
        sintoma_lower = sintoma_principal.lower()
        todos_sintomas = [sintoma_lower] + [s.lower() for s in sintomas_adicionales]
        
        recomendaciones = []
        
        # Buscar productos que traten estos síntomas
        for producto in self.catalogo:
            sintomas_que_trata = (producto.get('sintomas_que_trata') or '').lower()
            perfil_paciente = (producto.get('perfil_paciente') or '').lower()
            
            # Calcular score de match
            score = 0
            razon_match = []
            
            # Verificar cada síntoma
            for sintoma in todos_sintomas:
                if sintoma in sintomas_que_trata:
                    score += 2
                    razon_match.append(sintoma)
                
                if sintoma in perfil_paciente:
                    score += 1
            
            # Si hay match, agregar recomendación
            if score > 0:
                # Construir razón
                if razon_match:
                    razon = f"Indicado para {', '.join(razon_match)}. {producto['para_que_sirve'][:100]}..."
                else:
                    razon = producto['para_que_sirve'][:150]
                
                recomendaciones.append({
                    'producto': producto,
                    'razon': razon,
                    'prioridad': score,
                    'score': score
                })
        
        # Ordenar por score (mayor primero)
        recomendaciones.sort(key=lambda x: x['score'], reverse=True)
        
        # Retornar top 2
        return recomendaciones[:2]
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MÉTODO 2: RECOMENDACIÓN CON GPT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _recomendar_con_gpt(self, contexto_medico: Dict) -> List[Dict]:
        """
        Recomendar productos usando GPT
        GPT solo puede elegir de nuestro catálogo
        """
        
        # Construir descripción del catálogo
        catalogo_str = self._formatear_catalogo_para_gpt()
        
        # Contexto del paciente
        sintoma = contexto_medico.get('sintoma_principal', '')
        duracion = contexto_medico.get('duracion', '')
        intensidad = contexto_medico.get('intensidad', '')
        
        prompt = f"""Eres médico especializado en medicina natural.

CATÁLOGO DE PRODUCTOS DISPONIBLES:
{catalogo_str}

CASO DEL PACIENTE:
- Síntoma principal: {sintoma}
- Duración: {duracion}
- Intensidad: {intensidad}

INSTRUCCIONES:
1. Analiza el caso del paciente
2. Recomienda SOLO productos del catálogo disponible
3. Máximo 2 productos
4. Explica brevemente por qué cada uno

FORMATO DE RESPUESTA (JSON):
{{
    "productos": [
        {{
            "nombre": "Moringa",
            "razon": "porque ayuda con..."
        }}
    ]
}}

RESPUESTA:"""
        
        try:
            config = self.ia_config.obtener_config()
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f"Bearer {config['api_key']}",
                    'Content-Type': 'application/json'
                },
                json={
                    'model': config['modelo'],
                    'messages': [
                        {'role': 'system', 'content': 'Eres médico experto en medicina natural.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.5,
                    'max_tokens': 300
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                respuesta_texto = data['choices'][0]['message']['content'].strip()
                
                # Limpiar JSON
                respuesta_texto = respuesta_texto.replace('```json', '').replace('```', '')
                
                import json
                respuesta_json = json.loads(respuesta_texto)
                
                # Convertir a formato interno
                recomendaciones = []
                for item in respuesta_json.get('productos', []):
                    producto = self._buscar_producto_por_nombre(item['nombre'])
                    if producto:
                        recomendaciones.append({
                            'producto': producto,
                            'razon': item['razon'],
                            'prioridad': 1
                        })
                
                self.ia_config.incrementar_consulta(0.005)
                
                return recomendaciones
            
        except Exception as e:
            print(f"   ❌ Error GPT: {e}")
        
        return []
    
    def _formatear_catalogo_para_gpt(self) -> str:
        """Formatear catálogo para enviar a GPT"""
        
        lineas = []
        for i, p in enumerate(self.catalogo, 1):
            lineas.append(f"{i}. {p['nombre']}")
            lineas.append(f"   Para qué sirve: {p['para_que_sirve']}")
            lineas.append(f"   Beneficios: {p['beneficios']}")
            lineas.append(f"   Precio: S/. {p['precio']:.2f}")
            lineas.append("")
        
        return '\n'.join(lineas)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MÉTODO 3: FALLBACK
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _recomendar_fallback(self) -> List[Dict]:
        """Recomendación cuando todo falla"""
        
        # Recomendar el producto más popular o Moringa
        moringa = self._buscar_producto_por_nombre('Moringa')
        
        if moringa:
            return [{
                'producto': moringa,
                'razon': 'Es nuestro producto más completo para bienestar general.',
                'prioridad': 1
            }]
        
        # Si no hay Moringa, el primer producto disponible
        if self.catalogo:
            return [{
                'producto': self.catalogo[0],
                'razon': 'Producto recomendado para bienestar general.',
                'prioridad': 1
            }]
        
        return []
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UTILIDADES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _buscar_producto_por_nombre(self, nombre: str) -> Optional[Dict]:
        """Buscar producto en catálogo por nombre"""
        
        nombre_lower = nombre.lower()
        
        for producto in self.catalogo:
            if nombre_lower in producto['nombre'].lower():
                return producto
        
        return None
    
    def formatear_receta(self, recomendaciones: List[Dict]) -> str:
        """
        Formatear recomendaciones como receta legible
        Usa información real de productos_naturales
        """
        
        if not recomendaciones:
            return "No hay productos disponibles en este momento."
        
        receta = "📋 **RECETA NATURAL:**\n\n"
        
        for i, rec in enumerate(recomendaciones, 1):
            p = rec['producto']
            
            receta += f"{i}. **{p['nombre']}** ({p['categoria'].replace('_', ' ').title()})\n"
            receta += f"   💊 {p['presentacion']}\n"
            
            # Precio (con oferta si existe)
            if p.get('precio_oferta'):
                receta += f"   💰 ~~S/. {p['precio']:.2f}~~ → **S/. {p['precio_oferta']:.2f}**\n"
            else:
                receta += f"   💰 S/. {p['precio']:.2f}\n"
            
            receta += f"   \n   **¿Por qué este producto?**\n   {rec['razon']}\n"
            
            # Dosificación
            if p.get('dosis'):
                receta += f"   \n   **Dosis:** {p['dosis']}\n"
            
            if p.get('momento'):
                receta += f"   **Momento ideal:** {p['momento']}\n"
            
            if p.get('duracion'):
                receta += f"   **Duración:** {p['duracion']}\n"
            
            receta += "\n"
        
        return receta


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("="*70)
    print("🧪 TEST PRODUCTOS RECOMMENDER")
    print("="*70)
    
    recommender = ProductosRecommender()
    
    # Test casos
    casos = [
        {
            'sintoma_principal': 'cansancio',
            'duracion': '1 mes',
            'intensidad': 8
        },
        {
            'sintoma_principal': 'estrés',
            'duracion': '2 semanas',
            'intensidad': 9
        }
    ]
    
    for caso in casos:
        print(f"\n📋 CASO: {caso['sintoma_principal']}")
        recomendaciones = recommender.recomendar_productos(caso)
        
        if recomendaciones:
            print(recommender.formatear_receta(recomendaciones))
        else:
            print("   ❌ Sin recomendaciones")
    
    print("="*70)