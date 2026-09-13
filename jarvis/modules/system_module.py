"""
Módulo de control del sistema para JARVIS.
Ejecuta comandos de Linux de forma segura y gestiona operaciones del sistema.
"""

import asyncio
import logging
import subprocess
import re
from typing import Optional, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)


class SystemCommand:
    """Ejecución segura de comandos del sistema."""
    
    # Comandos permitidos (whitelist)
    ALLOWED_COMMANDS = {
        # Información del sistema
        'uname', 'hostname', 'whoami', 'pwd', 'date', 'cal', 'uptime',
        'df', 'du', 'free', 'top', 'htop', 'ps', 'pgrep', 'pidof',
        
        # Archivos y directorios
        'ls', 'cd', 'mkdir', 'rmdir', 'touch', 'cp', 'mv', 'rm',
        'cat', 'head', 'tail', 'less', 'more', 'wc', 'grep', 'find',
        'chmod', 'chown', 'ln', 'readlink',
        
        # Red
        'ping', 'curl', 'wget', 'ssh', 'scp', 'rsync',
        'ip', 'ifconfig', 'netstat', 'ss', 'dig', 'nslookup', 'host',
        
        # Paquetes (solo consulta)
        'apt', 'dpkg', 'snap', 'flatpak',
        
        # Procesos
        'kill', 'killall', 'pkill', 'nice', 'renice', 'nohup',
        
        # Utilidades
        'echo', 'printf', 'sleep', 'timeout', 'watch',
        'zip', 'unzip', 'tar', 'gzip', 'gunzip',
        'sort', 'uniq', 'cut', 'awk', 'sed', 'xargs',
        
        # Específicos de Linux Mint
        'mintupdate', 'mintinstall', 'cinnamon-settings',
    }
    
    # Comandos explícitamente prohibidos
    FORBIDDEN_PATTERNS = [
        r'rm\s+(-[rf]+\s+)?/$',  # rm en raíz
        r'mkfs',  # Formatear
        r'dd\s+if=',  # dd escritura directa
        r'>\s*/dev/sd',  # Escritura directa a disco
        r':\(\)\{:\|\:&\};:',  # Fork bomb
        r'chmod\s+777\s+/',  # Permisos peligrosos
        r'sudo\s+rm',  # sudo rm
        r'reboot',  # Reboot sin confirmación
        r'poweroff',  # Apagado sin confirmación
        r'shutdown',  # Shutdown sin confirmación
    ]
    
    def __init__(self):
        self.timeout = 30  # segundos
    
    def is_command_allowed(self, command: str) -> Tuple[bool, str]:
        """
        Verificar si un comando es seguro de ejecutar.
        
        Args:
            command: Comando a verificar
            
        Returns:
            Tuple (es_seguro, mensaje)
        """
        # Extraer el comando base
        parts = command.strip().split()
        if not parts:
            return False, "Comando vacío"
        
        base_command = parts[0]
        
        # Verificar contra patrones prohibidos
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Comando potencialmente peligroso detectado"
        
        # Verificar whitelist
        if base_command not in self.ALLOWED_COMMANDS:
            # Permitir rutas absolutas comunes
            allowed_paths = ['/usr/bin/', '/bin/', '/usr/local/bin/']
            is_absolute_allowed = any(
                command.startswith(path) and base_command.split('/')[-1] in self.ALLOWED_COMMANDS
                for path in allowed_paths
            )
            
            if not is_absolute_allowed:
                return False, f"Comando '{base_command}' no está en la lista permitida"
        
        return True, "Comando permitido"
    
    async def execute(
        self, 
        command: str, 
        timeout: Optional[int] = None,
        capture_output: bool = True
    ) -> Tuple[bool, str, str]:
        """
        Ejecutar comando del sistema.
        
        Args:
            command: Comando a ejecutar
            timeout: Timeout en segundos
            capture_output: Si True, captura stdout/stderr
            
        Returns:
            Tuple (éxito, stdout, stderr)
        """
        # Verificar seguridad
        is_safe, message = self.is_command_allowed(command)
        if not is_safe:
            logger.warning(f"Comando bloqueado por seguridad: {command}")
            return False, "", message
        
        timeout = timeout or self.timeout
        
        try:
            logger.info(f"Ejecutando: {command}")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
                stdin=asyncio.subprocess.DEVNULL
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                stdout_str = stdout.decode('utf-8', errors='replace').strip() if stdout else ""
                stderr_str = stderr.decode('utf-8', errors='replace').strip() if stderr else ""
                
                success = process.returncode == 0
                
                if success:
                    logger.debug(f"Comando exitoso: {command[:50]}...")
                else:
                    logger.warning(f"Comando falló (código {process.returncode}): {command}")
                
                return success, stdout_str, stderr_str
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                logger.error(f"Timeout ejecutando comando: {command}")
                return False, "", f"Timeout después de {timeout} segundos"
                
        except Exception as e:
            logger.error(f"Error ejecutando comando: {e}")
            return False, "", f"Error: {str(e)}"
    
    async def execute_safe(
        self, 
        command: str,
        timeout: Optional[int] = None
    ) -> str:
        """
        Ejecutar comando y devolver resultado combinado.
        
        Args:
            command: Comando a ejecutar
            timeout: Timeout en segundos
            
        Returns:
            Resultado o mensaje de error
        """
        success, stdout, stderr = await self.execute(command, timeout)
        
        if success:
            return stdout if stdout else "Comando ejecutado exitosamente."
        else:
            return stderr if stderr else "Error al ejecutar el comando."


class SystemController:
    """Controlador de alto nivel para operaciones del sistema."""
    
    def __init__(self):
        self.cmd = SystemCommand()
    
    async def get_system_info(self) -> dict:
        """Obtener información del sistema."""
        info = {}
        
        # Hostname
        _, stdout, _ = await self.cmd.execute("hostname")
        info['hostname'] = stdout
        
        # Usuario
        _, stdout, _ = await self.cmd.execute("whoami")
        info['user'] = stdout
        
        # Directorio actual
        _, stdout, _ = await self.cmd.execute("pwd")
        info['cwd'] = stdout
        
        # Uso de disco
        _, stdout, _ = await self.cmd.execute("df -h / | tail -1 | awk '{print $5}'")
        info['disk_usage'] = stdout.replace('%', '') if stdout else "N/A"
        
        # Memoria libre
        _, stdout, _ = await self.cmd.execute("free -m | awk 'NR==2{printf \"%.0f\", $7}'")
        info['free_memory_mb'] = int(stdout) if stdout.isdigit() else 0
        
        # Uptime
        _, stdout, _ = await self.cmd.execute("uptime -p")
        info['uptime'] = stdout
        
        return info
    
    async def search_files(
        self, 
        pattern: str, 
        path: str = "~",
        max_results: int = 20
    ) -> List[str]:
        """
        Buscar archivos por patrón.
        
        Args:
            pattern: Patrón de búsqueda
            path: Directorio donde buscar
            max_results: Máximo de resultados
            
        Returns:
            Lista de rutas encontradas
        """
        command = f"find {path} -name '*{pattern}*' -type f 2>/dev/null | head -{max_results}"
        _, stdout, _ = await self.cmd.execute(command)
        
        if stdout:
            return stdout.split('\n')
        return []
    
    async def get_process_info(self, process_name: str) -> str:
        """
        Obtener información de un proceso.
        
        Args:
            process_name: Nombre del proceso
            
        Returns:
            Información del proceso
        """
        command = f"ps aux | grep -i {process_name} | grep -v grep"
        _, stdout, _ = await self.cmd.execute(command)
        return stdout if stdout else f"No se encontró el proceso '{process_name}'"
    
    async def kill_process(self, process_name: str) -> str:
        """
        Terminar un proceso por nombre.
        
        Args:
            process_name: Nombre del proceso
            
        Returns:
            Resultado de la operación
        """
        command = f"pkill -f {process_name}"
        return await self.cmd.execute_safe(command)
    
    async def check_service_status(self, service_name: str) -> str:
        """
        Verificar estado de un servicio systemd.
        
        Args:
            service_name: Nombre del servicio
            
        Returns:
            Estado del servicio
        """
        command = f"systemctl is-active {service_name}"
        _, stdout, _ = await self.cmd.execute(command)
        
        if stdout == "active":
            return f"El servicio {service_name} está activo"
        elif stdout == "inactive":
            return f"El servicio {service_name} está inactivo"
        else:
            return f"Estado de {service_name}: {stdout}"
    
    async def manage_service(
        self, 
        service_name: str, 
        action: str
    ) -> str:
        """
        Gestionar servicio systemd.
        
        Args:
            service_name: Nombre del servicio
            action: start, stop, restart, status
            
        Returns:
            Resultado de la operación
        """
        if action not in ['start', 'stop', 'restart', 'status']:
            return f"Acción '{action}' no válida"
        
        # Requiere sudo para start/stop/restart
        if action in ['start', 'stop', 'restart']:
            command = f"sudo systemctl {action} {service_name}"
            return await self.cmd.execute_safe(command)
        else:
            return await self.check_service_status(service_name)
    
    async def get_weather(self, city: str) -> str:
        """
        Obtener clima usando wttr.in.
        
        Args:
            city: Ciudad
            
        Returns:
            Reporte del clima
        """
        command = f"curl -s wttr.in/{city}?format=3"
        return await self.cmd.execute_safe(command)
    
    async def take_screenshot(self, output_path: Optional[str] = None) -> str:
        """
        Tomar captura de pantalla.
        
        Args:
            output_path: Ruta de salida (opcional)
            
        Returns:
            Ruta de la captura o error
        """
        if output_path is None:
            timestamp = asyncio.get_event_loop().time()
            output_path = f"/tmp/screenshot_{int(timestamp)}.png"
        
        # Intentar con gnome-screenshot primero
        _, stdout, stderr = await self.cmd.execute(
            f"gnome-screenshot -f {output_path}"
        )
        
        if not stdout and not stderr:
            return f"Captura guardada en: {output_path}"
        
        # Fallback a import (ImageMagick)
        _, stdout, stderr = await self.cmd.execute(
            f"import -window root {output_path}"
        )
        
        if not stderr:
            return f"Captura guardada en: {output_path}"
        
        return "No se pudo tomar la captura. ¿Está instalado gnome-screenshot o ImageMagick?"
    
    async def set_volume(self, level: int) -> str:
        """
        Ajustar volumen del sistema.
        
        Args:
            level: Nivel de volumen (0-100)
            
        Returns:
            Resultado de la operación
        """
        level = max(0, min(100, level))
        command = f"pactl set-sink-volume @DEFAULT_SINK@ {level}%"
        return await self.cmd.execute_safe(command)
    
    async def get_volume(self) -> str:
        """Obtener volumen actual."""
        command = "pactl get-sink-volume @DEFAULT_SINK@ | awk -F'/' '{print $2}' | tr -d ' %'"
        _, stdout, _ = await self.cmd.execute(command)
        return f"Volumen actual: {stdout}%" if stdout else "No se pudo obtener el volumen"
    
    async def open_application(self, app_name: str) -> str:
        """
        Abrir aplicación.
        
        Args:
            app_name: Nombre de la aplicación
            
        Returns:
            Resultado de la operación
        """
        command = f"nohup {app_name} > /dev/null 2>&1 &"
        await self.cmd.execute(command, capture_output=False)
        return f"Abriendo {app_name}..."
    
    async def create_reminder(self, text: str, minutes: int) -> str:
        """
        Crear recordatorio (simulado con notificación).
        
        Args:
            text: Texto del recordatorio
            minutes: Minutos hasta el recordatorio
            
        Returns:
            Confirmación
        """
        # Esto sería mejor implementado con un sistema de persistencia
        # Por ahora, solo mostramos un mensaje
        return f"Recordatorio configurado: '{text}' en {minutes} minutos (nota: requiere implementación persistente)"
    
    async def shutdown(self, delay: int = 0) -> str:
        """
        Apagar el sistema (requiere confirmación).
        
        Args:
            delay: Segundos de espera antes de apagar
            
        Returns:
            Mensaje de confirmación o error
        """
        if delay > 0:
            command = f"sudo shutdown -P +{delay//60}"
        else:
            command = "sudo shutdown -P now"
        
        # Nota: Esto requiere contraseña sudo
        return "¿Confirmar apagado del sistema? Este comando requiere privilegios de administrador."
    
    async def reboot(self, delay: int = 0) -> str:
        """
        Reiniciar el sistema (requiere confirmación).
        
        Args:
            delay: Segundos de espera antes de reiniciar
            
        Returns:
            Mensaje de confirmación o error
        """
        if delay > 0:
            command = f"sudo shutdown -r +{delay//60}"
        else:
            command = "sudo shutdown -r now"
        
        return "¿Confirmar reinicio del sistema? Este comando requiere privilegios de administrador."


# Singleton para acceso global
_system_controller = None

def get_system_controller() -> SystemController:
    """Obtener instancia singleton del controlador."""
    global _system_controller
    if _system_controller is None:
        _system_controller = SystemController()
    return _system_controller
