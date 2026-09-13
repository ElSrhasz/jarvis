# Guía de Instalación para JARVIS en Linux Mint 22.3

## 1. Preparación del Sistema

### Instalar dependencias del sistema

```bash
sudo apt update
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
    git
```

### Configurar audio (opcional pero recomendado)

Verificar que el micrófono y altavoces funcionan:

```bash
# Listar dispositivos de captura
arecord -l

# Listar dispositivos de reproducción
aplay -l

# Probar grabación
arecord -d 5 test.wav
aplay test.wav
rm test.wav
```

## 2. Configuración del Entorno Python

```bash
cd ~/jarvis

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip
```

## 3. Instalar Dependencias de Python

```bash
pip install -r requirements.txt
```

## 4. Configurar API Key

```bash
cp .env.example .env
nano .env
```

Editar `.env` y agregar tu API key de OpenRouter:
```
OPENROUTER_API_KEY=tu_api_key_aqui
```

## 5. Descargar Modelos (Opcional)

### Vosk (STT offline - recomendado para español)

```bash
mkdir -p models
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.tar.gz
tar -xzf vosk-model-small-es-0.42.tar.gz
mv vosk-model-small-es-0.42 vosk-model-es
cd ..
```

### Piper TTS (voz más natural)

```bash
# Descargar Piper
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_linux_x86_64.tar.gz
tar -xzf piper_linux_x86_64.tar.gz

# Descargar voz en español
mkdir -p piper/voices
cd piper/voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/speaker_0/es_MX-speaker_0-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/speaker_0/es_MX-speaker_0-medium.onnx.json
cd ../..
```

## 6. Configurar Inicio Automático

### Opción A: Script systemd (recomendado)

```bash
sudo cp jarvis.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable jarvis.service
sudo systemctl start jarvis.service
```

Para modo usuario (sin sudo):
```bash
mkdir -p ~/.config/systemd/user
cp jarvis-user.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable jarvis-user.service
systemctl --user start jarvis-user.service
```

### Opción B: Archivo .desktop para inicio de sesión

```bash
cp jarvis.desktop ~/.config/autostart/
```

Editar `~/.config/autostart/jarvis.desktop` y actualizar la ruta:
```ini
Exec=/home/tu_usuario/jarvis/venv/bin/python /home/tu_usuario/jarvis/main.py
```

## 7. Verificar Instalación

```bash
source venv/bin/activate
python -c "import vosk, pyaudio, asyncio; print('Todas las librerías instaladas correctamente')"
```

## 8. Ejecutar JARVIS

```bash
source venv/bin/activate
python main.py
```

## Solución de Problemas

### Error de audio (PulseAudio/PipeWire)

```bash
# Reiniciar PulseAudio
pulseaudio -k
pulseaudio --start

# Verificar configuración
pavucontrol
```

### Error de permisos de micrófono

```bash
# Agregar usuario al grupo audio
sudo usermod -aG audio $USER
# Cerrar sesión y volver a entrar
```

### Alto consumo de CPU

- Usar modelo Vosk "small" en lugar del completo
- Reducir frecuencia de muestreo a 16000 Hz
- Desactivar la interfaz gráfica si no es necesaria
- Usar `nice` para priorizar el proceso:
  ```bash
  nice -n 10 python main.py
  ```
