/**
 * Sistema de Voz de Kairos - Mejorado
 * Voz natural en español latino sin emojis
 */

class KairosVoice {
    constructor() {
        this.reconocimiento = null;
        this.sintesis = window.speechSynthesis;
        this.escuchando = false;
        this.vozActiva = KairosConfig.VOZ.ACTIVA;
        this.vozSeleccionada = null;
        
        this.inicializarReconocimiento();
        this.inicializarVozLatina();
    }

    /**
     * Inicializar voz latina natural
     */
    inicializarVozLatina() {
        // Esperar a que se carguen las voces
        if (this.sintesis.getVoices().length === 0) {
            this.sintesis.addEventListener('voiceschanged', () => {
                this.seleccionarMejorVoz();
            });
        } else {
            this.seleccionarMejorVoz();
        }
    }

    /**
     * Seleccionar la mejor voz en español latino
     */
    seleccionarMejorVoz() {
        const voces = this.sintesis.getVoices();
        
        // Prioridad de voces (de mejor a peor calidad)
        const prioridades = [
            // Voces de alta calidad
            'es-MX', 'es-AR', 'es-CO', 'es-CL', 'es-PE', 'es-VE',
            // Voces alternativas
            'es-ES', 'es-US',
            // Fallback
            'es'
        ];

        // Palabras clave para voces femeninas naturales
        const palabrasClaveNaturales = [
            'premium', 'natural', 'enhanced', 'neural', 'paulina', 'monica', 
            'sabina', 'lupe', 'female', 'mujer', 'woman'
        ];

        // Buscar voz por prioridad
        for (const lang of prioridades) {
            // Primero buscar voces naturales
            const vozNatural = voces.find(voz => 
                voz.lang.startsWith(lang) && 
                palabrasClaveNaturales.some(palabra => 
                    voz.name.toLowerCase().includes(palabra)
                )
            );
            
            if (vozNatural) {
                this.vozSeleccionada = vozNatural;
                console.log('🎙️ Voz seleccionada (Premium):', vozNatural.name, vozNatural.lang);
                return;
            }

            // Si no hay natural, buscar cualquier voz femenina del idioma
            const vozFemenina = voces.find(voz => 
                voz.lang.startsWith(lang) && 
                (voz.name.toLowerCase().includes('female') || 
                 voz.name.toLowerCase().includes('woman') ||
                 voz.name.toLowerCase().includes('mujer'))
            );
            
            if (vozFemenina) {
                this.vozSeleccionada = vozFemenina;
                console.log('🎙️ Voz seleccionada (Femenina):', vozFemenina.name, vozFemenina.lang);
                return;
            }

            // Última opción: cualquier voz del idioma
            const vozIdioma = voces.find(voz => voz.lang.startsWith(lang));
            if (vozIdioma) {
                this.vozSeleccionada = vozIdioma;
                console.log('🎙️ Voz seleccionada:', vozIdioma.name, vozIdioma.lang);
                return;
            }
        }

        console.warn('⚠️ No se encontró voz en español latino, usando predeterminada');
    }

    /**
     * Limpiar texto de emojis y símbolos
     */
    limpiarTexto(texto) {
        // Eliminar emojis y símbolos
        let textoLimpio = texto
            // Remover emojis Unicode
            .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
            .replace(/[\u{2600}-\u{26FF}]/gu, '')
            .replace(/[\u{2700}-\u{27BF}]/gu, '')
            // Remover símbolos especiales comunes
            .replace(/[✓✅❌⚠️💚🎯🔊📋🎤📤➤→←]/g, '')
            // Remover caracteres especiales de markdown
            .replace(/[*_~`#]/g, '')
            // Limpiar espacios múltiples
            .replace(/\s+/g, ' ')
            .trim();

        // Reemplazar abreviaturas comunes
        const reemplazos = {
            'Kairos': 'Caíros',  // Pronunciación correcta
            'KAIROS': 'Caíros',
            'kairos': 'Caíros',
            'Dr.': 'Doctor',
            'Dra.': 'Doctora',
            'Sr.': 'Señor',
            'Sra.': 'Señora',
            'Ud.': 'Usted',
            'Uds.': 'Ustedes',
            'etc.': 'etcétera',
            'ej.': 'ejemplo',
            'p.ej.': 'por ejemplo',
            'DNI': 'D N I',
            'IA': 'Inteligencia Artificial',
            'AI': 'Inteligencia Artificial'
        };

        for (const [abrev, completo] of Object.entries(reemplazos)) {
            textoLimpio = textoLimpio.replace(new RegExp(abrev, 'g'), completo);
        }

        return textoLimpio;
    }

    /**
     * Inicializar reconocimiento de voz
     */
    inicializarReconocimiento() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('⚠️ Reconocimiento de voz no disponible');
            this.vozActiva = false;
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.reconocimiento = new SpeechRecognition();
        
        // Configurar para español latino
        this.reconocimiento.lang = 'es-MX'; // Español mexicano (latino)
        this.reconocimiento.continuous = false;
        this.reconocimiento.interimResults = false;
        this.reconocimiento.maxAlternatives = 1;

        this.reconocimiento.onstart = () => {
            console.log('🎤 Escuchando...');
            this.escuchando = true;
        };

        this.reconocimiento.onend = () => {
            console.log('🎤 Detenido');
            this.escuchando = false;
        };

        this.reconocimiento.onerror = (event) => {
            console.error('❌ Error reconocimiento:', event.error);
            this.escuchando = false;
        };
    }

    /**
     * Iniciar escucha
     */
    async escuchar() {
        if (!this.vozActiva || !this.reconocimiento) {
            throw new Error('Voz no disponible');
        }

        return new Promise((resolve, reject) => {
            this.reconocimiento.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                console.log('📝 Reconocido:', transcript);
                resolve(transcript);
            };

            this.reconocimiento.onerror = (event) => {
                reject(event.error);
            };

            try {
                this.reconocimiento.start();
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Detener escucha
     */
    detener() {
        if (this.reconocimiento && this.escuchando) {
            this.reconocimiento.stop();
        }
    }

    /**
     * Hablar (síntesis mejorada)
     */
    hablar(texto) {
        if (!this.vozActiva) return;

        // Limpiar texto de emojis
        const textoLimpio = this.limpiarTexto(texto);
        
        if (!textoLimpio) {
            console.log('🔇 Texto vacío después de limpiar, no se reproduce');
            return;
        }

        // Cancelar cualquier habla anterior
        this.sintesis.cancel();

        const utterance = new SpeechSynthesisUtterance(textoLimpio);
        
        // Configurar voz seleccionada
        if (this.vozSeleccionada) {
            utterance.voice = this.vozSeleccionada;
        }
        
        // Parámetros para voz más natural
        utterance.lang = 'es-MX'; // Español latino
        utterance.rate = 0.95;    // Velocidad natural (ni rápido ni lento)
        utterance.pitch = 1.0;    // Tono natural
        utterance.volume = 1.0;   // Volumen máximo

        utterance.onstart = () => {
            console.log('🔊 Hablando:', textoLimpio);
        };

        utterance.onerror = (event) => {
            console.error('❌ Error síntesis:', event.error);
        };

        // Pequeño delay para evitar problemas en algunos navegadores
        setTimeout(() => {
            this.sintesis.speak(utterance);
        }, 100);
    }

    /**
     * Cancelar habla
     */
    cancelarHabla() {
        this.sintesis.cancel();
    }

    /**
     * Toggle voz
     */
    toggle() {
        this.vozActiva = !this.vozActiva;
        console.log(`🔊 Voz: ${this.vozActiva ? 'ON' : 'OFF'}`);
        
        if (!this.vozActiva) {
            this.cancelarHabla();
        }
        
        return this.vozActiva;
    }

    /**
     * Listar voces disponibles (para debugging)
     */
    listarVoces() {
        const voces = this.sintesis.getVoices();
        console.log('🎙️ Voces disponibles en español:');
        voces
            .filter(voz => voz.lang.startsWith('es'))
            .forEach(voz => {
                console.log(`- ${voz.name} (${voz.lang}) ${voz.localService ? '[Local]' : '[Online]'}`);
            });
    }
}

// Instancia global
const voz = new KairosVoice();

// Para debugging en consola
window.listarVoces = () => voz.listarVoces();