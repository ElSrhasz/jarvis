#!/usr/bin/env python3
"""
JARVIS - Asistente Personal de IA para Linux Mint

Un asistente de voz inspirado en JARVIS de Iron Man, diseñado para ser
eficiente, profesional y útil. Utiliza OpenRouter API para el razonamiento
y modelos locales ligeros para STT/TTS.

Autor: Desarrollador Senior de Sistemas de IA
Licencia: MIT
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from colorama import init as colorama_init, Fore, Style

from config.settings import Config
from modules.voice_module import VoiceModule
from modules.llm_module import LLMModule
from modules.system_module import get_system_controller
from modules.ui_module import create_ui, JarvisUI

# Inicializar colorama para logs con colores
colorama_init()


class JARVIS:
    """Clase principal del asistente JARVIS."""
    
    def __init__(self, use_gui: bool = True, headless: bool = False):
        """
        Inicializar JARVIS.
        
        Args:
            use_gui: Si True, muestra interfaz gráfica
            headless: Si True, ejecuta sin interacción (solo escucha wake word)
        """
        self.use_gui = use_gui and not headless
        self.headless = headless
        
        # Configurar logging
        self._setup_logging()
        
        # Componentes principales
        self.voice = None
        self.llm = None
        self.system = None
        self.ui = None
        
        # Estado
        self.is_running = False
        self.current_task = None
        
        logger.info(f"{Fore.CYAN}╔════════════════════════════════════════╗{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}║{Style.BRIGHT}  JARVIS - Asistente Personal IA    {Style.RESET_ALL}{Fore.CYAN}║{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}╚════════════════════════════════════════╝{Style.RESET_ALL}")
        
    def _setup_logging(self) -> None:
        """Configurar sistema de logging."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Crear handler para archivo
        file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
        file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Crear handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
        console_formatter = logging.Formatter(
            f'{Fore.GREEN}%(asctime)s{Style.RESET_ALL} - '
            f'{Fore.YELLOW}%(name)s{Style.RESET_ALL} - '
            f'%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Configurar logger root
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        global logger
        logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """
        Inicializar todos los componentes.
        
        Returns:
            True si todo se inicializó correctamente
        """
        try:
            logger.info("Inicializando componentes...")
            
            # Inicializar módulo de voz
            logger.info("Cargando módulo de voz...")
            self.voice = VoiceModule()
            
            # Inicializar módulo LLM
            logger.info("Conectando con OpenRouter API...")
            self.llm = LLMModule()
            
            # Inicializar control del sistema
            logger.info("Inicializando control del sistema...")
            self.system = get_system_controller()
            
            # Inicializar UI si corresponde
            if self.use_gui:
                logger.info("Creando interfaz gráfica...")
                self.ui = create_ui(use_gui=True, on_command=self._handle_ui_command)
            else:
                self.ui = create_ui(use_gui=False)
            
            logger.info(f"{Fore.GREEN}✓ Todos los componentes inicializados{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            logger.error(f"{Fore.RED}Error durante la inicialización: {e}{Style.RESET_ALL}")
            return False
    
    def _handle_ui_command(self, command: str) -> None:
        """Manejar comando desde la UI."""
        if command == "__VOICE_MODE__":
            # Iniciar escucha de voz desde la UI
            asyncio.create_task(self.process_voice_command())
        else:
            # Comando de texto
            asyncio.create_task(self.process_text_command(command))
    
    async def process_text_command(self, command: str) -> None:
        """
        Procesar comando ingresado por texto.
        
        Args:
            command: Comando del usuario
        """
        if not command.strip():
            return
        
        logger.info(f"Comando recibido: {command}")
        
        if self.ui and isinstance(self.ui, JarvisUI):
            self.ui.show_progress(True)
        
        # Procesar con LLM
        response = await self.llm.process_query(command)
        
        # Hablar respuesta
        self.voice.speak(response)
        
        if self.ui and isinstance(self.ui, JarvisUI):
            self.ui.show_progress(False)
            self.ui.add_to_transcript(response, 'assistant')
            self.ui.update_response(response)
    
    async def process_voice_command(self) -> Optional[str]:
        """
        Escuchar y procesar comando de voz.
        
        Returns:
            Comando reconocido o None
        """
        try:
            if self.ui and isinstance(self.ui, JarvisUI):
                self.ui.set_status("🎤 Escuchando...")
            
            # Anunciar que está escuchando
            self.voice.speak("¿Sí, señor?")
            
            # Escuchar comando
            command = await self.voice.listen_for_command(timeout=15.0)
            
            if not command:
                logger.debug("No se reconoció ningún comando")
                if self.ui and isinstance(self.ui, JarvisUI):
                    self.ui.set_status("⚪ Inactivo")
                return None
            
            logger.info(f"Comando de voz reconocido: {command}")
            
            if self.ui and isinstance(self.ui, JarvisUI):
                self.ui.add_to_transcript(command, 'user')
                self.ui.set_status("⚙️ Procesando...")
            
            # Verificar comandos especiales
            if await self._handle_special_commands(command):
                if self.ui and isinstance(self.ui, JarvisUI):
                    self.ui.set_status("⚪ Inactivo")
                return command
            
            # Procesar con LLM
            response = await self.llm.process_query(command)
            
            # Hablar respuesta
            self.voice.speak(response)
            
            if self.ui and isinstance(self.ui, JarvisUI):
                self.ui.add_to_transcript(response, 'assistant')
                self.ui.update_response(response)
                self.ui.set_status("⚪ Inactivo")
            
            return command
            
        except Exception as e:
            logger.error(f"Error procesando comando de voz: {e}")
            if self.ui and isinstance(self.ui, JarvisUI):
                self.ui.set_status("⚪ Inactivo")
            return None
    
    async def _handle_special_commands(self, command: str) -> bool:
        """
        Manejar comandos especiales del sistema.
        
        Args:
            command: Comando del usuario
            
        Returns:
            True si se manejó un comando especial
        """
        command_lower = command.lower()
        
        # Comandos especiales
        if any(word in command_lower for word in ['apágate', 'apagar', 'cierra sesión']):
            self.voice.speak("Como ordene, señor. Cerrando sesión.")
            self.is_running = False
            return True
        
        elif any(word in command_lower for word in ['limpia historial', 'borra memoria', 'reinicia conversación']):
            self.llm.clear_history()
            response = "Historial de conversación limpiado, señor."
            self.voice.speak(response)
            if self.ui and isinstance(self.ui, JarvisUI):
                self.ui.add_to_transcript(response, 'system')
            return True
        
        elif 'información del sistema' in command_lower or 'estado del sistema' in command_lower:
            info = await self.system.get_system_info()
            response = (
                f"Sistema: {info.get('hostname', 'N/A')}, "
                f"Usuario: {info.get('user', 'N/A')}, "
                f"Disco: {info.get('disk_usage', 'N/A')}%, "
                f"Memoria libre: {info.get('free_memory_mb', 0)}MB"
            )
            self.voice.speak(response)
            if self.ui and isinstance(self.ui, JarvisUI):
                self.ui.add_to_transcript(response, 'assistant')
            return True
        
        elif 'qué hora' in command_lower or 'dime la hora' in command_lower:
            from datetime import datetime
            now = datetime.now().strftime("%H:%M")
            response = f"Son las {now}, señor."
            self.voice.speak(response)
            if self.ui and isinstance(self.ui, JarvisUI):
                self.ui.add_to_transcript(response, 'assistant')
            return True
        
        return False
    
    async def run_wake_word_loop(self) -> None:
        """Ejecutar bucle de escucha de wake word."""
        logger.info(f"Escuchando palabra de activación: '{Config.WAKE_WORD}'")
        
        def on_wake_word_detected():
            """Callback cuando se detecta wake word."""
            logger.info(f"{Fore.MAGENTA}¡Wake word detectada!{Style.RESET_ALL}")
            
            if self.ui and isinstance(self.ui, JarvisUI):
                self.ui.schedule(lambda: self.ui.set_status("🎤 Activado"))
            
            # Programar procesamiento del comando
            asyncio.create_task(self.process_voice_command())
        
        # Ejecutar en hilo separado para no bloquear
        import threading
        thread = threading.Thread(
            target=lambda: self.voice.wake_word_detector.listen_loop(on_wake_word_detected),
            daemon=True
        )
        thread.start()
    
    async def run_interactive_mode(self) -> None:
        """Ejecutar modo interactivo (texto + voz bajo demanda)."""
        print(f"\n{Fore.CYAN}╔════════════════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.BRIGHT}  JARVIS listo. Escribe 'ayuda' para opciones.  {Style.RESET_ALL}{Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╚════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
        
        self.is_running = True
        
        while self.is_running:
            try:
                # Leer input del usuario
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: input(f"{Fore.BLUE}Usted:{Style.RESET_ALL} ")
                )
                
                command = user_input.strip()
                
                if not command:
                    continue
                
                # Comandos especiales de terminal
                if command.lower() in ['salir', 'quit', 'exit']:
                    self.voice.speak("Hasta luego, señor.")
                    break
                
                elif command.lower() == 'ayuda':
                    print(f"\n{Fore.GREEN}Comandos disponibles:{Style.RESET_ALL}")
                    print("  voice      - Activar modo de voz")
                    print("  limpiar    - Limpiar historial")
                    print("  estado     - Información del sistema")
                    print("  salir      - Cerrar JARVIS")
                    print("  ayuda      - Mostrar esta ayuda\n")
                    continue
                
                elif command.lower() == 'voice':
                    await self.process_voice_command()
                    continue
                
                elif command.lower() == 'limpiar':
                    self.llm.clear_history()
                    print(f"{Fore.GREEN}Historial limpiado.{Style.RESET_ALL}")
                    continue
                
                elif command.lower() == 'estado':
                    info = await self.system.get_system_info()
                    print(f"\n{Fore.GREEN}Estado del sistema:{Style.RESET_ALL}")
                    for key, value in info.items():
                        print(f"  {key}: {value}")
                    print()
                    continue
                
                # Procesar comando normal
                await self.process_text_command(command)
                
            except KeyboardInterrupt:
                break
            except EOFError:
                break
    
    async def run(self) -> None:
        """Ejecutar JARVIS según el modo configurado."""
        if not await self.initialize():
            logger.error("Fallo en la inicialización. Saliendo.")
            return
        
        self.is_running = True
        
        # Configurar manejo de señales
        def signal_handler(sig, frame):
            logger.info("Señal de terminación recibida")
            self.is_running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            if self.headless:
                # Modo solo wake word (sin interacción)
                await self.run_wake_word_loop()
                
                # Mantener ejecutando
                while self.is_running:
                    await asyncio.sleep(1)
                    
            elif self.use_gui and self.ui:
                # Modo GUI
                logger.info("Iniciando interfaz gráfica...")
                
                # Iniciar loop de wake word en background
                await self.run_wake_word_loop()
                
                # Ejecutar GUI en hilo principal
                self.ui.run()
                
            else:
                # Modo terminal interactivo
                await self.run_interactive_mode()
                
        except Exception as e:
            logger.error(f"Error durante la ejecución: {e}", exc_info=True)
        finally:
            await self.cleanup()
    
    async def cleanup(self) -> None:
        """Limpiar recursos antes de salir."""
        logger.info("Cerrando JARVIS...")
        
        self.is_running = False
        
        # Limpiar componentes
        if self.voice:
            self.voice.cleanup()
        
        if self.llm:
            await self.llm.cleanup()
        
        logger.info(f"{Fore.YELLOW}JARVIS cerrado. Hasta luego, señor.{Style.RESET_ALL}")


async def main_async():
    """Función principal asíncrona."""
    import argparse
    
    parser = argparse.ArgumentParser(description='JARVIS - Asistente Personal IA')
    parser.add_argument('--no-gui', action='store_true', help='Ejecutar sin interfaz gráfica')
    parser.add_argument('--headless', action='store_true', help='Modo sin interacción (solo wake word)')
    parser.add_argument('--debug', action='store_true', help='Habilitar modo debug')
    args = parser.parse_args()
    
    if args.debug:
        Config.LOG_LEVEL = "DEBUG"
    
    jarvis = JARVIS(
        use_gui=not args.no_gui,
        headless=args.headless
    )
    
    await jarvis.run()


def main():
    """Función principal."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrumpido por el usuario.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error fatal: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
