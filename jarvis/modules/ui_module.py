"""
Interfaz gráfica minimalista para JARVIS.
Usa Tkinter para una UI ligera que no consume GPU.
"""

import asyncio
import logging
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, Callable
import threading
from datetime import datetime

from config.settings import Config

logger = logging.getLogger(__name__)


class JarvisUI:
    """Interfaz gráfica minimalista para JARVIS."""
    
    def __init__(self, on_command_callback: Optional[Callable] = None):
        self.on_command = on_command_callback
        self.root = None
        self.status_var = None
        self.transcript_text = None
        self.response_label = None
        self.command_entry = None
        self.is_running = False
        
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Configurar la interfaz gráfica."""
        self.root = tk.Tk()
        self.root.title("JARVIS - Asistente Personal")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')  # Tema moderno y ligero
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Header con estado
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(0, weight=1)
        
        # Título
        title_label = ttk.Label(
            header_frame, 
            text="🤖 JARVIS", 
            font=('Helvetica', 16, 'bold')
        )
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Indicador de estado
        self.status_var = tk.StringVar(value="⚪ Inactivo")
        status_label = ttk.Label(
            header_frame,
            textvariable=self.status_var,
            font=('Helvetica', 10)
        )
        status_label.grid(row=0, column=1, sticky=tk.E)
        
        # Área de transcripción (historial)
        transcript_frame = ttk.LabelFrame(main_frame, text="Transcripción", padding="5")
        transcript_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, S), pady=(0, 10))
        transcript_frame.columnconfigure(0, weight=1)
        transcript_frame.rowconfigure(0, weight=1)
        
        self.transcript_text = scrolledtext.ScrolledText(
            transcript_frame,
            height=12,
            width=60,
            wrap=tk.WORD,
            state='disabled',
            font=('Consolas', 9)
        )
        self.transcript_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar tags para colores
        self.transcript_text.tag_configure('user', foreground='blue')
        self.transcript_text.tag_configure('assistant', foreground='green')
        self.transcript_text.tag_configure('system', foreground='gray')
        self.transcript_text.tag_configure('error', foreground='red')
        
        # Área de respuesta actual
        response_frame = ttk.LabelFrame(main_frame, text="Respuesta Actual", padding="5")
        response_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.response_label = ttk.Label(
            response_frame,
            text="",
            wraplength=550,
            justify=tk.LEFT,
            font=('Helvetica', 10)
        )
        self.response_label.grid(row=0, column=0, sticky=tk.W)
        
        # Entrada de comandos por texto
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)
        
        self.command_entry = ttk.Entry(input_frame, font=('Helvetica', 10))
        self.command_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.command_entry.bind('<Return>', lambda e: self._send_text_command())
        
        send_button = ttk.Button(
            input_frame,
            text="Enviar",
            command=self._send_text_command
        )
        send_button.grid(row=0, column=1)
        
        # Botones de control
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        start_button = ttk.Button(
            button_frame,
            text="▶ Iniciar Voz",
            command=self._start_voice_mode
        )
        start_button.grid(row=0, column=0, padx=(0, 5))
        
        stop_button = ttk.Button(
            button_frame,
            text="⏹ Detener",
            command=self._stop_voice_mode
        )
        stop_button.grid(row=0, column=1, padx=(0, 5))
        
        clear_button = ttk.Button(
            button_frame,
            text="🗑 Limpiar",
            command=self._clear_transcript
        )
        clear_button.grid(row=0, column=2, padx=(0, 5))
        
        # Barra de progreso (para indicar procesamiento)
        self.progress_bar = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=580
        )
        self.progress_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Footer con info
        footer_label = ttk.Label(
            main_frame,
            text=f"Modelo: {Config.OPENROUTER_MODEL[:30]}...",
            font=('Helvetica', 8),
            foreground='gray'
        )
        footer_label.grid(row=6, column=0, sticky=tk.W, pady=(5, 0))
        
    def _send_text_command(self) -> None:
        """Enviar comando desde la entrada de texto."""
        command = self.command_entry.get().strip()
        if command and self.on_command:
            self.add_to_transcript(command, 'user')
            self.command_entry.delete(0, tk.END)
            self.on_command(command)
    
    def _start_voice_mode(self) -> None:
        """Iniciar modo de voz."""
        self.set_status("🟡 Escuchando...")
        self.show_progress(True)
        if self.on_command:
            self.on_command("__VOICE_MODE__")
    
    def _stop_voice_mode(self) -> None:
        """Detener modo de voz."""
        self.set_status("⚪ Inactivo")
        self.show_progress(False)
    
    def _clear_transcript(self) -> None:
        """Limpiar transcripción."""
        self.transcript_text.config(state='normal')
        self.transcript_text.delete('1.0', tk.END)
        self.transcript_text.config(state='disabled')
        self.response_label.config(text="")
    
    def set_status(self, status: str) -> None:
        """Actualizar estado."""
        self.status_var.set(status)
    
    def show_progress(self, show: bool) -> None:
        """Mostrar/ocultar barra de progreso."""
        if show:
            self.progress_bar.start(10)
        else:
            self.progress_bar.stop()
    
    def add_to_transcript(self, text: str, role: str = 'system') -> None:
        """Agregar texto a la transcripción."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.transcript_text.config(state='normal')
        
        if role == 'user':
            self.transcript_text.insert(tk.END, f"[{timestamp}] Usted: {text}\n\n", 'user')
        elif role == 'assistant':
            self.transcript_text.insert(tk.END, f"[{timestamp}] JARVIS: {text}\n\n", 'assistant')
        elif role == 'error':
            self.transcript_text.insert(tk.END, f"[{timestamp}] Error: {text}\n\n", 'error')
        else:
            self.transcript_text.insert(tk.END, f"[{timestamp}] {text}\n\n", 'system')
        
        self.transcript_text.see(tk.END)
        self.transcript_text.config(state='disabled')
    
    def update_response(self, text: str) -> None:
        """Actualizar etiqueta de respuesta."""
        self.response_label.config(text=text[:200])  # Limitar longitud
    
    def run_async(self, coro):
        """Ejecutar corutina en el loop de eventos."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if not loop.is_running():
            # Ejecutar en hilo separado
            def run_loop():
                asyncio.set_event_loop(loop)
                loop.run_forever()
            
            thread = threading.Thread(target=run_loop, daemon=True)
            thread.start()
        
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future
    
    def run(self) -> None:
        """Iniciar la interfaz gráfica."""
        logger.info("Iniciando interfaz gráfica")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()
    
    def _on_close(self) -> None:
        """Manejar cierre de ventana."""
        logger.info("Cerrando interfaz gráfica")
        self.is_running = False
        self.root.destroy()
    
    def schedule(self, callback: Callable, delay_ms: int = 0) -> None:
        """Programar ejecución de callback en el hilo principal."""
        if self.root:
            self.root.after(delay_ms, callback)


class MinimalUI:
    """Interfaz aún más minimalista (solo terminal con notificaciones)."""
    
    def __init__(self):
        self.status = "inicializando"
        
    def update_status(self, status: str) -> None:
        """Actualizar estado (para usar con notificaciones del sistema)."""
        self.status = status
        logger.info(f"Estado: {status}")
        
        # Notificación del sistema (si disponible)
        try:
            import subprocess
            subprocess.run([
                'notify-send', '-u', 'low', '-t', '2000',
                'JARVIS', status
            ], capture_output=True)
        except Exception:
            pass
    
    def show_error(self, message: str) -> None:
        """Mostrar error."""
        logger.error(message)
        try:
            import subprocess
            subprocess.run([
                'notify-send', '-u', 'critical', '-t', '5000',
                'JARVIS - Error', message
            ], capture_output=True)
        except Exception:
            pass


def create_ui(use_gui: bool = True, on_command: Optional[Callable] = None):
    """
    Fábrica para crear la interfaz apropiada.
    
    Args:
        use_gui: Si True, usa interfaz gráfica. Si False, usa minimalista.
        on_command: Callback para comandos
        
    Returns:
        Instancia de UI
    """
    if use_gui:
        try:
            return JarvisUI(on_command_callback=on_command)
        except Exception as e:
            logger.warning(f"No se pudo crear GUI: {e}. Usando interfaz minimalista.")
            return MinimalUI()
    else:
        return MinimalUI()
