# Documentación de Arquitectura JARVIS

## 1. Resumen de Arquitectura

### Librerías Elegidas y Justificación

#### STT (Speech-to-Text): **Vosk**
- **Por qué**: Modelo offline ligero (~50MB para el modelo small en español)
- **Ventajas**: 
  - No requiere conexión a internet para reconocimiento de voz
  - Bajo consumo de CPU comparado con Whisper
  - Soporte nativo para Linux
  - Reconocimiento en tiempo real con partial results
- **Alternativa considerada**: faster-whisper (más preciso pero requiere ~500MB y más CPU)

#### TTS (Text-to-Speech): **espeak-ng + pyttsx3**
- **Por qué**: espeak-ng está disponible en repositorios oficiales de Linux Mint
- **Ventajas**:
  - Instalación simple vía apt
  - Mínimo consumo de recursos
  - Sin dependencias externas pesadas
- **Alternativa premium**: Piper TTS (voz más natural pero requiere descarga manual de modelos ONNX)

#### Wake Word Detection: **Implementación ligera basada en Vosk**
- **Por qué**: Evita cargar motores adicionales como Porcupine o OpenWakeWord
- **Ventajas**:
  - Reutiliza el mismo modelo STT
  - Sin servicios externos de pago
  - Configuración simple de sensibilidad
- **Nota**: Se usa VAD (Voice Activity Detection) para reducir procesamiento en silencio

#### LLM: **OpenRouter API**
- **Por qué**: Delega el razonamiento pesado a la nube, manteniendo local solo lo esencial
- **Ventajas**:
  - Acceso a múltiples modelos (GPT-4, Claude, Mistral, etc.)
  - Sin necesidad de GPU local
  - Pago por uso (no suscripción mensual obligatoria)
  - Historial de conversación en memoria local

#### GUI: **Tkinter**
- **Por qué**: Viene incluido con Python, no consume GPU
- **Ventajas**:
  - Cero dependencias adicionales
  - Nativo en Linux
  - Suficiente para mostrar estado y transcripción
- **Alternativa**: Interfaz minimalista con notificaciones del sistema (notify-send)

#### Procesamiento Asíncrono: **asyncio**
- **Por qué**: Permite que la UI no se congele mientras el LLM genera respuesta
- **Implementación**:
  - Todas las operaciones I/O son asíncronas
  - La grabación de audio corre en hilo separado
  - El TTS se ejecuta en background para no bloquear

---

## 2. Preparación del Entorno (Linux Mint 22.3)

### Comandos de Instalación

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    portaudio19-dev \
    libasound2-dev \
    libpulse-dev \
    pulseaudio-utils \
    espeak-ng \
    espeak-ng-data \
    ffmpeg \
    libffi-dev \
    libssl-dev \
    git \
    notify-osd

# Crear directorio del proyecto
mkdir -p ~/jarvis
cd ~/jarvis

# Clonar o copiar archivos del proyecto
# (si estás usando este código directamente)
git clone <repository-url> .  # O copiar archivos manualmente

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias de Python
pip install -r requirements.txt
```

### Descargar Modelo Vosk (STT)

```bash
cd ~/jarvis
mkdir -p models
cd models

# Modelo pequeño en español (~50MB) - recomendado
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.tar.gz
tar -xzf vosk-model-small-es-0.42.tar.gz
mv vosk-model-small-es-0.42 vosk-model-es

# Opcional: Modelo completo en español (~800MB) - más preciso
# wget https://alphacephei.com/vosk/models/vosk-model-es-0.42.tar.gz
# tar -xzf vosk-model-es-0.42.tar.gz

cd ..
```

### Configurar API Key

```bash
cd ~/jarvis
cp .env.example .env
nano .env
```

Editar `.env` y agregar tu clave de OpenRouter:
```
OPENROUTER_API_KEY=sk-or-v1-tu_clave_aqui
```

Obtén tu API key en: https://openrouter.ai/keys

---

## 3. Estructura de Directorios

```
jarvis/
├── main.py                 # Punto de entrada principal
├── requirements.txt        # Dependencias de Python
├── .env.example           # Plantilla de variables de entorno
├── .env                   # Variables de entorno (NO commitear)
├── .gitignore             # Archivos ignorados por git
├── README.md              # Documentación general
├── INSTALL.md             # Guía de instalación detallada
├── ARCHITECTURE.md        # Este archivo
├── jarvis.service         # Systemd service (root)
├── jarvis-user.service    # Systemd service (usuario)
├── jarvis.desktop         # Autoinicio en sesión gráfica
│
├── config/
│   ├── __init__.py
│   └── settings.py        # Configuración centralizada
│
├── modules/
│   ├── __init__.py
│   ├── voice_module.py    # STT, TTS, Wake Word
│   ├── llm_module.py      # OpenRouter API, historial
│   ├── system_module.py   # Comandos de Linux
│   └── ui_module.py       # Interfaz gráfica Tkinter
│
├── models/                # Modelos de ML (descargar por separado)
│   └── vosk-model-es/     # Modelo Vosk en español
│
├── logs/                  # Logs de ejecución
│   └── jarvis.log
│
├── data/                  # Datos persistentes (recordatorios, etc.)
│
└── venv/                  # Entorno virtual Python (no commitear)
```

---

## 4. Código Fuente Principal

Los archivos principales ya están creados:

- `main.py`: Orquestador principal con tres modos (GUI, terminal, headless)
- `modules/voice_module.py`: Todo el procesamiento de audio
- `modules/llm_module.py`: Comunicación con OpenRouter y gestión de contexto
- `modules/system_module.py`: Ejecución segura de comandos Linux
- `modules/ui_module.py`: Interfaz gráfica minimalista
- `config/settings.py`: Configuración centralizada

---

## 5. Configuración del System Prompt

El System Prompt está definido en `config/settings.py`:

```python
SYSTEM_PROMPT = """Eres JARVIS, un asistente de inteligencia artificial altamente avanzado, 
creado para asistir de manera eficiente y leal. Tu tono es profesional, cortés y ligeramente 
formal, similar a un mayordomo británico de alta clase. 

Características de tu personalidad:
- Eres extremadamente competente y eficiente
- Hablas de manera concisa pero completa
- Muestras lealtad absoluta a tu usuario
- Tienes un toque de humor seco e ingenioso cuando es apropiado
- Nunca eres arrogante, pero sí confiado en tus capacidades
- Te refieres al usuario como "señor" o "señora" según corresponda
- Siempre buscas la solución más óptima a los problemas

Cuando ejecutes comandos del sistema:
- Verifica que sean seguros antes de sugerirlos
- Explica brevemente qué hará el comando
- Advierte sobre posibles riesgos

Tu objetivo principal es hacer la vida de tu usuario más fácil y productiva."""
```

### Headers para OpenRouter API

```python
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/jarvis-assistant",
    "X-Title": "JARVIS Assistant"
}
```

---

## 6. Instrucciones de Ejecución

### Modo Normal (con GUI)

```bash
cd ~/jarvis
source venv/bin/activate
python main.py
```

### Modo Terminal (sin GUI)

```bash
cd ~/jarvis
source venv/bin/activate
python main.py --no-gui
```

### Modo Headless (solo wake word, sin interacción)

```bash
cd ~/jarvis
source venv/bin/activate
python main.py --headless
```

### Modo Debug

```bash
cd ~/jarvis
source venv/bin/activate
python main.py --debug
```

---

## 7. Configuración de Inicio Automático

### Opción A: Systemd (Recomendado para servidor/headless)

```bash
# Editar el archivo de servicio
nano ~/jarvis/jarvis-user.service

# Reemplazar %USER% con tu nombre de usuario
# Copiar a systemd
cp ~/jarvis/jarvis-user.service ~/.config/systemd/user/

# Recargar y habilitar
systemctl --user daemon-reload
systemctl --user enable jarvis-user.service
systemctl --user start jarvis-user.service

# Verificar estado
systemctl --user status jarvis-user.service

# Ver logs
journalctl --user -u jarvis-user.service -f
```

### Opción B: Inicio con Sesión Gráfica

```bash
# Editar archivo desktop
nano ~/jarvis/jarvis.desktop

# Reemplazar REPLACE_WITH_USERNAME con tu usuario
# Copiar a autostart
cp ~/jarvis/jarvis.desktop ~/.config/autostart/
```

---

## 8. Optimización de Recursos

### Consejos para Bajo Consumo

1. **Usar modelo Vosk "small"**: El modelo completo usa ~4x más RAM
   ```bash
   # En .env
   STT_MODEL_PATH=models/vosk-model-es  # Usa el small
   ```

2. **Reducir frecuencia de muestreo**: 16000 Hz es suficiente para voz
   ```bash
   # En .env
   AUDIO_SAMPLE_RATE=16000
   ```

3. **Prioridad de proceso baja**: Ya configurado en systemd
   ```ini
   Nice=10
   CPUSchedulingPolicy=idle
   ```

4. **Desactivar GUI si no es necesaria**:
   ```bash
   python main.py --headless
   ```

5. **Ajustar chunk size de audio**: Chunk más grande = menos CPU pero más latencia
   ```bash
   # En .env
   AUDIO_CHUNK_SIZE=8192  # Default: 4096
   ```

6. **Usar modelos LLM económicos en OpenRouter**:
   ```bash
   # En .env - modelos gratuitos o baratos
   OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
   ```

7. **Limitar historial de conversación**:
   ```python
   # En llm_module.py
   self.history = ConversationHistory(max_messages=10)  # Default: 20
   ```

### Monitoreo de Recursos

```bash
# Ver consumo de JARVIS
ps aux | grep jarvis

# Ver uso de memoria
smem -tk | grep jarvis

# Ver uso de CPU en tiempo real
top -p $(pgrep -f "python.*jarvis")
```

---

## 9. Solución de Problemas Comunes

### Error: "No module named 'pyaudio'"
```bash
sudo apt install portaudio19-dev python3-dev
pip install pyaudio
```

### Error: "Modelo Vosk no encontrado"
```bash
cd ~/jarvis/models
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.tar.gz
tar -xzf vosk-model-small-es-0.42.tar.gz
```

### Error: "espeak-ng no encontrado"
```bash
sudo apt install espeak-ng espeak-ng-data
```

### Error: "OPENROUTER_API_KEY no configurada"
```bash
cp ~/jarvis/.env.example ~/jarvis/.env
nano ~/jarvis/.env
# Agregar tu API key
```

### Audio no se escucha o graba mal
```bash
# Verificar dispositivos
arecord -l  # Dispositivos de captura
aplay -l    # Dispositivos de reproducción

# Probar micrófono
arecord -d 5 test.wav
aplay test.wav

# Ver configuración PulseAudio
pavucontrol
```

### Alto consumo de CPU
1. Usar modelo Vosk small
2. Reducir sample rate a 16000
3. Aumentar chunk size
4. Ejecutar en modo headless

---

## 10. Comandos de Voz Recomendados

### Comandos Integrados
- "JARVIS, ¿qué hora es?" → Responde con la hora actual
- "JARVIS, información del sistema" → Muestra estado del sistema
- "JARVIS, limpia el historial" → Borra la memoria de conversación
- "JARVIS, apágate" → Cierra el asistente

### Comandos vía LLM (ejemplos)
- "¿Cuál es el clima en Madrid?"
- "Busca archivos PDF en mi carpeta Documentos"
- "¿Cuánta memoria RAM tengo libre?"
- "Abre la calculadora"
- "Toma una captura de pantalla"
- "Sube el volumen al 80%"

---

## 11. Seguridad

### Comandos Bloqueados por Defecto

El sistema bloquea automáticamente comandos peligrosos:
- `rm -rf /` y variantes
- `mkfs` (formateo de discos)
- `dd if=` (escritura directa a disco)
- Fork bombs
- `chmod 777 /`
- `shutdown`, `reboot`, `poweroff` sin confirmación

### Whitelist de Comandos

Solo se permiten comandos específicos (ver `system_module.py`):
- Información del sistema (uname, hostname, ps, etc.)
- Archivos (ls, cp, mv, cat, grep, etc.)
- Red (ping, curl, wget, ssh, etc.)
- Paquetes (apt, dpkg - solo consulta)

---

## 12. Extensibilidad

### Agregar Nuevo Comando Especial

En `main.py`, método `_handle_special_commands`:

```python
elif 'tu_comando' in command_lower:
    response = "Respuesta personalizada"
    self.voice.speak(response)
    return True
```

### Agregar Nuevo Motor TTS

En `modules/voice_module.py`, clase `TextToSpeech`:

```python
def _speak_nuevo_engine(self, text: str) -> None:
    # Implementación del nuevo engine
    pass

# En _init_engine
elif self.engine == "nuevo_engine":
    self._speak_nuevo_engine(text)
```

### Cambiar Modelo LLM

En `.env`:
```
OPENROUTER_MODEL=anthropic/claude-3-haiku
# o
OPENROUTER_MODEL=google/gemini-pro
# o  
OPENROUTER_MODEL=meta-llama/llama-3-70b-instruct
```

Ver modelos disponibles en: https://openrouter.ai/models
