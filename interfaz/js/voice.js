/**
 * Sistema de Voz de Kairos
 * Reconocimiento y síntesis de voz
 */

class KairosVoice {
    constructor() {
        this.reconocimiento = null;
        this.sintesis = window.speechSynthesis;
        this.escuchando = false;
        this.vozActiva = KairosConfig.VOZ.ACTIVA;
        
        this.inicializarReconocimiento();
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
        
        this.reconocimiento.lang = KairosConfig.VOZ.IDIOMA;
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
     * Hablar (síntesis)
     */
    hablar(texto) {
        if (!this.vozActiva) return;

        // Cancelar cualquier habla anterior
        this.sintesis.cancel();

        const utterance = new SpeechSynthesisUtterance(texto);
        utterance.lang = KairosConfig.VOZ.IDIOMA;
        utterance.rate = KairosConfig.VOZ.VELOCIDAD;
        utterance.pitch = KairosConfig.VOZ.TONO;

        utterance.onstart = () => {
            console.log('🔊 Hablando:', texto);
        };

        utterance.onerror = (event) => {
            console.error('❌ Error síntesis:', event.error);
        };

        this.sintesis.speak(utterance);
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
        return this.vozActiva;
    }
}

// Instancia global
const voz = new KairosVoice();