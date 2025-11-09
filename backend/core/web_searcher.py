"""
Web Search Module V2
Busca en MÚLTIPLES FUENTES GRATIS:
1. Wikipedia (enciclopedia médica gratis)
2. DuckDuckGo (búsqueda general gratis)
3. Bing (backup, 1000/mes gratis)
"""

import os
import requests
from typing import List, Dict, Optional

class WebSearcher:
    """Buscador multi-fuente para investigación médica"""
    
    def __init__(self):
        self.bing_key = os.getenv('BING_SEARCH_KEY', '')
        
    def buscar(self, query: str, num_resultados: int = 5) -> str:
        """Buscar en múltiples fuentes y combinar"""
        
        print(f"   🔍 Buscando: {query}")
        
        resultados_totales = []
        
        # 1. WIKIPEDIA (Enciclopedia médica)
        wiki_info = self._buscar_wikipedia(query)
        if wiki_info:
            resultados_totales.append("📚 WIKIPEDIA:\n" + wiki_info)
        
        # 2. DUCKDUCKGO (Búsqueda general)
        ddg_info = self._buscar_duckduckgo(query, num_resultados)
        if ddg_info:
            resultados_totales.append("🔍 BÚSQUEDA WEB:\n" + ddg_info)
        
        # 3. BING (Backup si las anteriores fallan)
        if not resultados_totales and self.bing_key:
            bing_info = self._buscar_bing(query, num_resultados)
            if bing_info:
                resultados_totales.append("🔍 BING:\n" + bing_info)
        
        # Combinar resultados
        if resultados_totales:
            return "\n\n".join(resultados_totales)
        
        # Si todo falla, GPT investiga
        return self._simulacion_sin_api(query)
    
    def _buscar_wikipedia(self, query: str) -> str:
        """Buscar en Wikipedia (GRATIS, ILIMITADO)"""
        try:
            import wikipediaapi
            
            wiki = wikipediaapi.Wikipedia(
                language='es',
                user_agent='KairosBot/1.0'
            )
            
            # Buscar página
            page = wiki.page(query)
            
            if page.exists():
                # Extraer resumen (primeros 500 caracteres)
                resumen = page.summary[:500] + "..."
                print(f"   ✅ Wikipedia encontró: {page.title}")
                return f"• {page.title}\n  {resumen}"
            
        except ImportError:
            print(f"   ⚠️ Instala: pip install wikipedia-api")
        except Exception as e:
            print(f"   ⚠️ Wikipedia: {e}")
        
        return ""
    
    def _buscar_duckduckgo(self, query: str, num: int) -> str:
        """Buscar con DuckDuckGo (GRATIS, ILIMITADO)"""
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                resultados = []
                
                for result in ddgs.text(query, max_results=num):
                    titulo = result.get('title', '')
                    snippet = result.get('body', '')
                    resultados.append(f"• {titulo}\n  {snippet}")
                
                if resultados:
                    texto = "\n\n".join(resultados)
                    print(f"   ✅ DuckDuckGo: {len(resultados)} resultados")
                    return texto
        
        except ImportError:
            print(f"   ⚠️ Instala: pip install duckduckgo-search")
        except Exception as e:
            print(f"   ⚠️ DuckDuckGo: {e}")
        
        return ""
    
    def _buscar_bing(self, query: str, num: int) -> str:
        """Buscar con Bing (1000/mes GRATIS)"""
        try:
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {"Ocp-Apim-Subscription-Key": self.bing_key}
            params = {
                "q": query,
                "count": num,
                "mkt": "es-PE",
                "responseFilter": "Webpages"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                resultados = []
                for result in data.get('webPages', {}).get('value', [])[:num]:
                    titulo = result.get('name', '')
                    snippet = result.get('snippet', '')
                    resultados.append(f"• {titulo}\n  {snippet}")
                
                if resultados:
                    texto = "\n\n".join(resultados)
                    print(f"   ✅ Bing: {len(resultados)} resultados")
                    return texto
            
        except Exception as e:
            print(f"   ⚠️ Bing: {e}")
        
        return ""
    
    def _simulacion_sin_api(self, query: str) -> str:
        """Sin APIs - GPT investiga libremente"""
        print(f"   ⚠️ Sin búsqueda web - GPT investiga")
        
        return f"""Investiga en tu conocimiento médico sobre: {query}

Enfócate en:
- Plantas/remedios COMUNES en Perú
- Con respaldo tradicional o científico
- Seguros y accesibles
- Disponibles en mercados/farmacias

Información verificada y práctica."""


# Singleton
_web_searcher = None

def obtener_buscador() -> WebSearcher:
    """Obtener instancia del buscador"""
    global _web_searcher
    if _web_searcher is None:
        _web_searcher = WebSearcher()
    return _web_searcher