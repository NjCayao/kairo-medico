/**
 * Configuración dinámica de Kairos
 * Lee desde variables o usa defaults
 */

const KairosConfig = {
    // API Base URL (detecta automáticamente)
    API_BASE_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:5000'
        : `http://${window.location.hostname}:5000`,
    
    // Endpoints
    API: {
        NUEVA_SESION: '/api/sesion/nueva',
        CAPTURAR_DATOS: '/api/sesion/capturar-datos',
        MENSAJE: '/api/sesion/mensaje',
        FINALIZAR: '/api/sesion/finalizar',
        ESTADO: '/api/sesion/estado',
        ESTADISTICAS: '/api/estadisticas',
        CONFIG: '/api/config',
        HEALTH: '/api/health'
    },
    
    // Configuración de voz
    VOZ: {
        ACTIVA: true,
        IDIOMA: 'es-ES',
        VELOCIDAD: 1.0,
        TONO: 1.0
    },
    
    // Tiempos (milisegundos)
    TIEMPOS: {
        TIMEOUT_INACTIVIDAD: 300000, // 5 minutos
        TIMEOUT_VOZ: 10000,           // 10 segundos
        DESPEDIDA: 5000,              // 5 segundos
        TYPING_DELAY: 1000            // 1 segundo
    },
    
    // Modo debug
    DEBUG: window.location.hostname === 'localhost'
};

// Log si está en debug
if (KairosConfig.DEBUG) {
    console.log('🔧 Kairos Config:', KairosConfig);
}