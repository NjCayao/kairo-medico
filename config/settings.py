"""
Configuración general de Kairos
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración general"""
    
    # ━━━ BASE DE DATOS ━━━
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'kairos_medico')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    # ━━━ SEGURIDAD ━━━
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    
    # ━━━ MODO OPERACIÓN ━━━
    MODO_OPERACION = os.getenv('MODO_OPERACION', 'feria')
    
    # ━━━ RUTAS ━━━
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'backend', 'data')
    MODELS_DIR = os.path.join(DATA_DIR, 'models')
    LOGS_DIR = os.path.join(BASE_DIR, 'backend', 'logs')
    
    # ━━━ ML ━━━
    MODELO_CLASIFICADOR = os.path.join(MODELS_DIR, 'classifier.pkl')
    EXCEL_ENTRENAMIENTO = os.path.join(DATA_DIR, 'kairos_entrenamiento.xlsx')
    EXCEL_PRODUCTOS = os.path.join(DATA_DIR, 'catalogo_productos.xlsx')
    
    # ━━━ IMPRESORA ━━━
    IMPRESORA_MODELO = os.getenv('IMPRESORA_MODELO', 'Xprinter XP-58IIH')
    PAPEL_ANCHO = int(os.getenv('PAPEL_ANCHO', 58))
    
    # ━━━ VOZ ━━━
    VOZ_ACTIVA = os.getenv('VOZ_ACTIVA', 'True') == 'True'
    VOZ_IDIOMA = os.getenv('VOZ_IDIOMA', 'es-PE')
    VOZ_VELOCIDAD = int(os.getenv('VOZ_VELOCIDAD', 140))
    
    # ━━━ EVENTO ━━━
    EVENTO_NOMBRE = os.getenv('EVENTO_NOMBRE', 'Feria Salud')
    EVENTO_UBICACION = os.getenv('EVENTO_UBICACION', '')
    STAND_NUMERO = os.getenv('STAND_NUMERO', '')
    
    # ━━━ CONSULTA ━━━
    MODO_DIAGNOSTICO = 'express'  # express, normal, profundo
    PREGUNTAS_MAXIMAS = 8
    DURACION_MAXIMA_MIN = 12
    
    # ━━━ INTERFACE ━━━
    TIEMPO_DESPEDIDA = 5  # segundos
    TIEMPO_RESET = 300     # 5 minutos inactividad

# Crear directorios si no existen
os.makedirs(Config.MODELS_DIR, exist_ok=True)
os.makedirs(Config.LOGS_DIR, exist_ok=True)

if __name__ == "__main__":
    # Test de configuración
    print("="*60)
    print("CONFIGURACIÓN KAIROS FERIA")
    print("="*60)
    print(f"Base de datos: {Config.DB_NAME}@{Config.DB_HOST}")
    print(f"Modo: {Config.MODO_OPERACION}")
    print(f"Debug: {Config.DEBUG}")
    print(f"Data dir: {Config.DATA_DIR}")
    print(f"Evento: {Config.EVENTO_NOMBRE}")
    print("="*60)