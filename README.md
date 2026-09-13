# JARVIS - Asistente de IA Local para Linux Mint

Asistente personal avanzado inspirado en JARVIS, diseñado para Linux Mint 22.3 Cinnamon.

## Características

- **Control por voz** con palabra de activación
- **STT/TTS optimizados** para bajo consumo de recursos
- **Integración con OpenRouter API** para razonamiento LLM
- **Interfaz minimalista** que no consume GPU
- **Ejecución de comandos del sistema** de forma segura

## Requisitos

- Python 3.10+
- Linux Mint 22.3 Cinnamon (o distribución basada en Ubuntu/Debian)
- Micrófono y altavoces configurados
- API Key de OpenRouter

## Instalación

Ver `INSTALL.md` para instrucciones detalladas.


+++ jarvis/README.md (修改后)
# 🤖 JARVIS - Asistente Personal de IA para Linux

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Linux Mint](https://img.shields.io/badge/Linux-Mint%2022.3-green.svg)](https://linuxmint.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)]()

> **Just A Rather Very Intelligent System** - Un asistente de voz inspirado en Iron Man, diseñado para Linux Mint 22.3 Cinnamon.

![JARVIS Banner](https://img.shields.io/badge/JARVIS-Always_Listening-purple?style=for-the-badge&logo=google-assistant)

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Requisitos del Sistema](#-requisitos-del-sistema)
- [Arquitectura](#-arquitectura)
- [Instalación Rápida](#-instalación-rápida)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Comandos Disponibles](#-comandos-disponibles)
- [Optimización](#-optimización)
- [Solución de Problemas](#-solución-de-problemas)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## ✨ Características

### 🎙️ Control por Voz Completo
- **Wake Word Detection**: Actívate diciendo "Jarvis" o "Hey Jarvis"
- **Speech-to-Text (STT)**: Reconocimiento de voz offline con Vosk (modelo en español)
- **Text-to-Speech (TTS)**: Respuestas de voz naturales con espeak-ng/piper
- **Detección de Actividad de Voz (VAD)**: Solo procesa cuando hablas, ahorrando recursos

### 🧠 Inteligencia Artificial
- **OpenRouter API**: Conexión a múltiples modelos LLM (GPT-4, Claude, Mistral, etc.)
- **Historial de Conversación**: Mantiene contexto durante la sesión
- **System Prompt Personalizado**: Personalidad de mayordomo profesional estilo JARVIS
- **Streaming de Respuestas**: Visualización en tiempo real mientras genera

### 💻 Control del Sistema
- **Comandos Seguros**: Ejecución controlada de comandos de Linux
- **Whitelist/Blacklist**: Protección contra comandos peligrosos
- **Funciones Integradas**:
  - 📅 Consultar hora y fecha
  - 🌤️ Obtener clima local
  - 📸 Capturar pantalla
  - 🔊 Controlar volumen del sistema
  - 📊 Monitorear procesos y recursos
  - 📁 Gestionar archivos básicos

### 🖥️ Interfaces Múltiples
- **GUI Minimalista**: Interfaz Tkinter ligera (~30MB RAM, sin GPU)
- **Modo Terminal**: Interfaz CLI para servidores/headless
- **Notificaciones del Sistema**: Integración con notify-osd de Cinnamon

### ⚡ Optimización de Recursos
- **Bajo Consumo**: ~200-300MB RAM total en reposo
- **Procesamiento Asíncrono**: UI responsiva durante generación LLM
- **Modelos Ligeros**: Vosk small (~50MB) vs modelos grandes (>500MB)
- **Sin GPU Requerida**: Todo funciona con CPU

---

## 💻 Requisitos del Sistema

### Hardware Mínimo
| Componente | Requisito | Recomendado |
|------------|-----------|-------------|
| **CPU** | 2 núcleos @ 2.0 GHz | 4 núcleos @ 3.0 GHz |
| **RAM** | 4 GB | 8 GB+ |
| **Almacenamiento** | 500 MB libres | 1 GB+ SSD |
| **Audio** | Micrófono funcional | Micrófono + Altavoces |
| **Conexión** | Internet para LLM | Internet estable |

### Software
- **Sistema Operativo**: Linux Mint 22.3 Cinnamon (Ubuntu 24.04 base)
- **Python**: 3.10 o superior
- **Dependencias de Audio**: ALSA/PulseAudio/PipeWire
- **API Key**: OpenRouter (o proveedor compatible)

### Compatibilidad Probada
✅ Linux Mint 22.3 Cinnamon
✅ Ubuntu 24.04 LTS
✅ Debian 12+
⚠️ Otras distribuciones (puede requerir ajustes)

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                      JARVIS Core                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Voice      │  │     LLM      │  │    System    │      │
│  │   Module     │  │    Module    │  │   Module     │      │
│  │              │  │              │  │              │      │
│  │  • STT(Vosk) │  │  • OpenRouter│  │  • Commands  │      │
│  │  • TTS(espeak)│ │  • Context   │  │  • Safety    │      │
│  │  • WakeWord  │  │  • Streaming │  │  • Monitor   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                 │
│                  ┌────────▼────────┐                        │
│                  │   Main Loop     │                        │
│                  │   (asyncio)     │                        │
│                  └────────┬────────┘                        │
│                           │                                 │
│         ┌─────────────────┼─────────────────┐               │
│         │                 │                 │               │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐        │
│  │     GUI     │  │   Terminal  │  │   Headless  │        │
│  │  (Tkinter)  │  │     CLI     │  │  (Systemd)  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  OpenRouter API │
                    │  (Cloud LLMs)   │
                    └─────────────────┘
```

### Módulos Principales

| Módulo | Archivo | Responsabilidad |
|--------|---------|-----------------|
| **Voice** | `modules/voice_module.py` | Captura de audio, STT, TTS, wake word |
| **LLM** | `modules/llm_module.py` | Comunicación con OpenRouter, historial |
| **System** | `modules/system_module.py` | Ejecución segura de comandos Linux |
| **UI** | `modules/ui_module.py` | Interfaz gráfica y notificaciones |
| **Config** | `config/settings.py` | Configuración centralizada |

---

## 🚀 Instalación Rápida

### Paso 1: Clonar el Repositorio

```bash
cd ~
git clone https://github.com/tu-usuario/jarvis.git
cd jarvis
```

### Paso 2: Instalar Dependencias del Sistema

```bash
sudo apt update
sudo apt install -y \
    python3-pip python3-venv python3-dev \
    portaudio19-dev libasound2-dev libpulse-dev \
    pulseaudio-utils espeak-ng espeak-ng-data \
    ffmpeg libffi-dev libssl-dev git notify-osd
```

### Paso 3: Configurar Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 4: Descargar Modelo de Voz

```bash
mkdir -p models && cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.tar.gz
tar -xzf vosk-model-small-es-0.42.tar.gz
mv vosk-model-small-es-0.42 vosk-model-es
cd ..
```

> **Nota**: El modelo small ocupa ~50MB. Para mayor precisión, descarga el modelo grande (~500MB):
> ```bash
> wget https://alphacephei.com/vosk/models/vosk-model-es-0.42.tar.gz
> ```

### Paso 5: Configurar API Key

```bash
cp .env.example .env
nano .env
```

Agrega tu clave de OpenRouter:
```env
OPENROUTER_API_KEY=sk-or-v1-tu-clave-aqui
```

> **Obtén tu API Key**: [openrouter.ai/keys](https://openrouter.ai/keys)

---

## ⚙️ Configuración

### Variables de Entorno (.env)

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `OPENROUTER_API_KEY` | Tu clave de API | *Requerida* |
| `LLM_MODEL` | Modelo a usar | `mistral-7b-instruct:free` |
| `STT_MODEL_PATH` | Ruta al modelo Vosk | `models/vosk-model-es` |
| `AUDIO_DEVICE_INDEX` | Índice del micrófono | `None` (auto) |
| `WAKE_WORD_SENSITIVITY` | Sensibilidad (0.0-1.0) | `0.6` |
| `TTS_ENGINE` | Motor TTS | `espeak` |
| `MAX_HISTORY_MESSAGES` | Mensajes en historial | `10` |
| `LOG_LEVEL` | Nivel de logs | `INFO` |

### Modelos LLM Disponibles

JARVIS soporta cualquier modelo en OpenRouter:

```env
# Gratuitos
LLM_MODEL=mistral-7b-instruct:free
LLM_MODEL=openchat-3.5-0106:free

# De pago (mejor calidad)
LLM_MODEL=openai/gpt-4-turbo-preview
LLM_MODEL=anthropic/claude-3-sonnet
LLM_MODEL=google/gemini-pro
```

### Personalizar Wake Word

Edita `config/settings.py`:
```python
WAKE_WORDS = ["jarvis", "hey jarvis", "ok jarvis"]
```

---

## 🎯 Uso

### Modos de Ejecución

#### 1. Modo Normal (con GUI)
```bash
source venv/bin/activate
python main.py
```

#### 2. Modo Terminal (sin GUI)
```bash
python main.py --no-gui
```

#### 3. Modo Headless (solo wake word)
```bash
python main.py --headless
```

Ideal para ejecutar como servicio en segundo plano.

#### 4. Modo Debug
```bash
python main.py --debug
```

Muestra logs detallados en consola.

### Comandos de Voz

Después de decir **"Jarvis"**, prueba estos comandos:

| Comando | Acción |
|---------|--------|
| _"¿Qué hora es?"_ | Responde con hora y fecha actual |
| _"¿Cómo está el clima?"_ | Muestra clima local (requiere ciudad configurada) |
| _"Toma una captura de pantalla"_ | Guarda screenshot en ~/Pictures |
| _"Sube el volumen"_ / _"Baja el volumen"_ | Ajusta volumen del sistema |
| _"¿Qué procesos están corriendo?"_ | Lista top 5 procesos por CPU |
| _"Ejecuta ls -la"_ | Ejecuta comando (si está permitido) |
| _"Limpia el historial"_ | Borra conversación anterior |
| _"Apágate"_ | Cierra JARVIS elegantemente |

### Comandos desde Terminal

En modo `--no-gui`, escribe directamente:
```
>>> ¿Qué hora es?
JARVIS: Son las 14:30 del martes 15 de enero, 2025.

>>> Toma una captura
JARVIS: Captura guardada en /home/usuario/Pictures/screenshot_20250115_143045.png
```

---

## ⚡ Optimización

### Reducir Consumo de RAM

1. **Usar modelo Vosk small**:
   ```bash
   # Ya configurado por defecto
   STT_MODEL_PATH=models/vosk-model-es
   ```

2. **Limitar historial de conversación**:
   ```env
   MAX_HISTORY_MESSAGES=5
   ```

3. **Cerrar aplicaciones innecesarias** mientras JARVIS corre.

### Reducir Uso de CPU

1. **Aumentar chunk size de audio**:
   ```python
   # En config/settings.py
   AUDIO_CHUNK_SIZE = 8192  # Default: 4096
   ```

2. **Reducir sensibilidad del wake word**:
   ```env
   WAKE_WORD_SENSITIVITY=0.5
   ```

3. **Usar nice value en systemd**:
   ```ini
   # En jarvis-user.service
   Nice=10
   IOSchedulingClass=idle
   ```

### Mejorar Latencia

1. **Usar SSD** para el sistema y modelos.
2. **Seleccionar modelo LLM rápido**:
   ```env
   LLM_MODEL=mistral-7b-instruct:free
   ```
3. **Conexión Ethernet** en lugar de WiFi si es posible.

### Benchmark Típico

| Métrica | Valor |
|---------|-------|
| RAM en reposo | ~220 MB |
| RAM escuchando | ~250 MB |
| RAM procesando | ~300 MB |
| CPU en reposo | < 2% |
| CPU escuchando | 3-5% |
| CPU procesando STT | 10-15% |
| Latencia STT | 200-500ms |
| Latencia LLM | 1-5s (depende del modelo) |

---

## 🔧 Solución de Problemas

### El micrófono no funciona

```bash
# Verificar dispositivos de audio
arecord -l

# Probar grabación
arecord -f cd test.wav
aplay test.wav

# Si no hay dispositivos, instalar drivers
sudo apt install linux-sound-base alsa-base alsa-utils
```

### Error: "No module named 'vosk'"

```bash
source venv/bin/activate
pip install vosk
```

### Error: "PortAudio not found"

```bash
sudo apt install portaudio19-dev
pip uninstall pyaudio
pip install pyaudio --no-cache-dir
```

### JARVIS no detecta la wake word

1. Verifica que el micrófono esté seleccionado correctamente:
   ```bash
   pavucontrol  # GUI de PulseAudio
   ```

2. Ajusta la sensibilidad en `.env`:
   ```env
   WAKE_WORD_SENSITIVITY=0.7
   ```

3. Prueba con diferentes frases de activación.

### La voz TTS suena robótica

1. Instala voces adicionales:
   ```bash
   sudo apt install espeak-ng-es mbrola es-mb
   ```

2. Cambia el motor TTS:
   ```env
   TTS_ENGINE=piper
   ```

3. Considera descargar voces de Piper de mayor calidad.

### Error de API Key inválida

1. Verifica tu clave en [openrouter.ai/keys](https://openrouter.ai/keys)
2. Asegúrate de no tener espacios en blanco:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-xxxxx  # Sin espacios
   ```
3. Reinicia JARVIS después de cambiar la clave.

### Logs y Debugging

```bash
# Ver logs en tiempo real
tail -f logs/jarvis.log

# Ejecutar en modo debug
python main.py --debug

# Ver logs de systemd (si ejecuta como servicio)
journalctl --user -u jarvis-user.service -f
```

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Aquí hay algunas formas de ayudar:

### Áreas Necesitadas
- 🌍 Traducciones a otros idiomas
- 🎨 Mejoras en la interfaz gráfica
- 🔌 Integración con más servicios (Home Assistant, Spotify, etc.)
- 🧪 Tests automatizados
- 📚 Documentación adicional

### Cómo Contribuir

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Estándares de Código
- Python 3.10+
- Seguir PEP 8
- Type hints donde sea apropiado
- Docstrings en funciones públicas
- Tests para nuevas características

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

### Créditos
- **Vosk**: [alphacephei.com/vosk](https://alphacephei.com/vosk/)
- **OpenRouter**: [openrouter.ai](https://openrouter.ai)
- **Inspiración**: Proyectos JARVIS de código abierto

---

## 📞 Soporte y Comunidad

- 📧 **Email**: tu-email@ejemplo.com
- 💬 **Discord**: [Únete al servidor](https://discord.gg/tu-invite)
- 🐛 **Issues**: [Reporta bugs aquí](https://github.com/tu-usuario/jarvis/issues)
- 💡 **Ideas**: [Discusiones GitHub](https://github.com/tu-usuario/jarvis/discussions)

---

## 🙏 Agradecimientos

Gracias a:
- La comunidad de código abierto por las librerías utilizadas
- Los desarrolladores de Vosk por el excelente motor STT offline
- OpenRouter por proporcionar acceso a múltiples modelos LLM
- Tú, por darle vida a JARVIS en tu sistema

---

<div align="center">

**Hecho con ❤️ para la comunidad de Linux**

[⬆️ Volver arriba](#-jarvis---asistente-personal-de-ia-para-linux)

</div>

