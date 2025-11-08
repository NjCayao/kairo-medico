"""
Configuración del sistema - TODO desde variables de entorno
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Base de datos
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'kairos_medico')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    # API
    API_PORT = int(os.getenv('API_PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Operación
    MODO_OPERACION = os.getenv('MODO_OPERACION', 'feria')
    EVENTO_NOMBRE = os.getenv('EVENTO_NOMBRE', 'Feria Salud')
    UBICACION = os.getenv('UBICACION', 'Stand Principal')
    
    # Voz
    VOZ_ACTIVA = os.getenv('VOZ_ACTIVA', 'True').lower() == 'true'
    VOZ_IDIOMA = os.getenv('VOZ_IDIOMA', 'es-PE')
    
    # Excel
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    EXCEL_PRODUCTOS = os.path.join(BASE_DIR, 'backend', 'data', 'catalogo_productos.xlsx')
    EXCEL_ENTRENAMIENTO = os.path.join(BASE_DIR, 'backend', 'data', 'kairos_entrenamiento.xlsx')