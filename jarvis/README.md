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

## Descarga e instalación (.deb para Linux Mint)

Puedes descargar el paquete `.deb` ya compilado desde la sección **Releases**
de este repositorio:

📦 **[Descargar jarvis-assistant_1.0.0_all.deb](https://github.com/jarvis-assistant/jarvis/releases/download/v1.0.0/jarvis-assistant_1.0.0_all.deb)**

### Instalar el .deb

Opción A — doble clic: abre el archivo `.deb` con el Gestor de Paquetes de Linux Mint y pulsa **Instalar**.

Opción B — terminal (recomendada, instala dependencias automáticamente):

```bash
cd ~/Descargas   # o donde hayas descargado el archivo
sudo apt install ./jarvis-assistant_1.0.0_all.deb
```

Después de instalar:

```bash
# 1. Configura tu API key de OpenRouter
sudo nano /opt/jarvis/.env      # edita OPENROUTER_API_KEY=...

# 2. Ejecuta JARVIS
jarvis                          # o "jarvis --no-gui" sin interfaz gráfica
```

El instalador crea automáticamente el entorno virtual en `/opt/jarvis/venv`,
instala las librerías Python y añade JARVIS al arranque automático de tu sesión.

### Compilar tu propio .deb

Si prefieres generar el paquete tú mismo desde el código fuente:

```bash
cd jarvis
./build_deb.sh
# Resultado: dist/jarvis-assistant_1.0.0_all.deb
```

Solo necesitas `dpkg-deb` (incluido por defecto en Linux Mint).

## Instalación

Ver `INSTALL.md` para instrucciones detalladas.
