"""
Módulo LLM para JARVIS.
Maneja la comunicación con OpenRouter API y el historial de conversación.
"""

import asyncio
import logging
from typing import List, Dict, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime

import aiohttp
from config.settings import Config

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Mensaje individual en el historial de conversación."""
    role: str  # "system", "user", o "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convertir a formato para API."""
        return {
            "role": self.role,
            "content": self.content
        }


class ConversationHistory:
    """Gestión del historial de conversación en memoria."""
    
    def __init__(self, max_messages: int = 20):
        """
        Inicializar historial.
        
        Args:
            max_messages: Número máximo de mensajes a mantener (excluyendo system prompt)
        """
        self.max_messages = max_messages
        self.messages: List[Message] = []
        self.system_prompt = Config.SYSTEM_PROMPT
        
    def add_message(self, role: str, content: str) -> None:
        """Agregar mensaje al historial."""
        message = Message(role=role, content=content)
        self.messages.append(message)
        
        # Mantener solo los últimos max_messages mensajes del usuario/asistente
        user_assistant_messages = [
            m for m in self.messages if m.role in ("user", "assistant")
        ]
        
        if len(user_assistant_messages) > self.max_messages:
            # Eliminar los mensajes más antiguos
            messages_to_remove = len(user_assistant_messages) - self.max_messages
            removed = 0
            new_messages = []
            for msg in self.messages:
                if msg.role in ("user", "assistant") and removed < messages_to_remove:
                    removed += 1
                else:
                    new_messages.append(msg)
            self.messages = new_messages
        
        logger.debug(f"Historial: {len(self.messages)} mensajes")
    
    def get_full_history(self) -> List[dict]:
        """Obtener historial completo con system prompt."""
        full_history = [
            {"role": "system", "content": self.system_prompt}
        ]
        full_history.extend([msg.to_dict() for msg in self.messages])
        return full_history
    
    def clear(self) -> None:
        """Limpiar historial (manteniendo system prompt implícito)."""
        self.messages = []
        logger.info("Historial de conversación limpiado")
    
    def get_summary(self) -> str:
        """Obtener resumen del contexto actual."""
        if not self.messages:
            return "Sin contexto previo"
        
        last_few = self.messages[-min(4, len(self.messages)):]
        summary_parts = []
        for msg in last_few:
            preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            summary_parts.append(f"{msg.role}: {preview}")
        
        return "\n".join(summary_parts)


class OpenRouterClient:
    """Cliente asíncrono para OpenRouter API."""
    
    def __init__(self):
        self.api_url = Config.OPENROUTER_URL
        self.headers = Config.get_headers()
        self.model = Config.OPENROUTER_MODEL
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtener o crear sesión aiohttp."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self) -> None:
        """Cerrar sesión."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def chat_completion(
        self, 
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 500,
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Enviar mensajes y obtener respuesta del LLM.
        
        Args:
            messages: Lista de mensajes en formato [{"role": "...", "content": "..."}]
            temperature: Temperatura para la generación (0-1)
            max_tokens: Máximo de tokens en la respuesta
            stream: Si True, generar respuesta en streaming
            
        Yields:
            Fragmentos de la respuesta (si stream=True) o respuesta completa
        """
        session = await self._get_session()
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if stream:
            payload["stream"] = True
        
        try:
            logger.debug(f"Enviando request a OpenRouter (modelo: {self.model})")
            
            async with session.post(
                self.api_url,
                headers=self.headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error API: {response.status} - {error_text}")
                    yield f"[Error: API retornó {response.status}]"
                    return
                
                if stream:
                    # Procesar streaming
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            try:
                                import json
                                chunk = json.loads(data)
                                delta = chunk.get('choices', [{}])[0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                else:
                    # Respuesta completa
                    result = await response.json()
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    yield content
                    
        except aiohttp.ClientError as e:
            logger.error(f"Error de conexión: {e}")
            yield f"[Error de conexión: {str(e)}]"
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            yield f"[Error: {str(e)}]"
    
    async def send_message(
        self, 
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Enviar mensajes y obtener respuesta completa.
        
        Args:
            messages: Lista de mensajes
            temperature: Temperatura para la generación
            max_tokens: Máximo de tokens
            
        Returns:
            Respuesta completa del LLM
        """
        response_parts = []
        async for part in self.chat_completion(messages, temperature, max_tokens, stream=False):
            response_parts.append(part)
        return "".join(response_parts)


class LLMModule:
    """Módulo principal de LLM que integra cliente y historial."""
    
    def __init__(self):
        self.client = OpenRouterClient()
        self.history = ConversationHistory(max_messages=20)
        self._is_processing = False
        
    async def process_query(self, query: str) -> str:
        """
        Procesar consulta del usuario y obtener respuesta.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Respuesta del asistente
        """
        if self._is_processing:
            return "Estoy procesando otra solicitud, señor. Un momento por favor."
        
        self._is_processing = True
        
        try:
            # Agregar consulta al historial
            self.history.add_message("user", query)
            
            # Obtener historial completo
            messages = self.history.get_full_history()
            
            logger.info(f"Procesando consulta: {query[:50]}...")
            
            # Obtener respuesta del LLM
            response = await self.client.send_message(
                messages,
                temperature=0.7,
                max_tokens=500
            )
            
            if response:
                # Agregar respuesta al historial
                self.history.add_message("assistant", response)
                logger.info(f"Respuesta obtenida ({len(response)} chars)")
                return response
            else:
                error_msg = "Lo siento, no pude obtener una respuesta en este momento."
                self.history.add_message("assistant", error_msg)
                return error_msg
                
        except Exception as e:
            logger.error(f"Error procesando consulta: {e}")
            error_msg = "Ha ocurrido un error técnico. ¿Podría repetir, señor?"
            return error_msg
        finally:
            self._is_processing = False
    
    async def process_query_streaming(
        self, 
        query: str
    ) -> AsyncGenerator[str, None]:
        """
        Procesar consulta con respuesta en streaming.
        
        Args:
            query: Consulta del usuario
            
        Yields:
            Fragmentos de la respuesta
        """
        if self._is_processing:
            yield "Estoy procesando otra solicitud, señor."
            return
        
        self._is_processing = True
        
        try:
            # Agregar consulta al historial
            self.history.add_message("user", query)
            
            # Obtener historial completo
            messages = self.history.get_full_history()
            
            logger.info(f"Procesando consulta (streaming): {query[:50]}...")
            
            # Acumular respuesta completa
            full_response = []
            
            async for chunk in self.client.chat_completion(
                messages,
                temperature=0.7,
                max_tokens=500,
                stream=True
            ):
                full_response.append(chunk)
                yield chunk
            
            # Agregar respuesta completa al historial
            if full_response:
                response_text = "".join(full_response)
                self.history.add_message("assistant", response_text)
                
        except Exception as e:
            logger.error(f"Error en streaming: {e}")
            yield "[Error en la respuesta]"
        finally:
            self._is_processing = False
    
    def get_context_summary(self) -> str:
        """Obtener resumen del contexto actual."""
        return self.history.get_summary()
    
    def clear_history(self) -> None:
        """Limpiar historial de conversación."""
        self.history.clear()
        logger.info("Historial limpiado por comando del usuario")
    
    async def execute_command(self, command_description: str) -> tuple[bool, str]:
        """
        Ejecutar comando del sistema basado en descripción natural.
        
        Args:
            command_description: Descripción del comando en lenguaje natural
            
        Returns:
            Tuple (éxito, resultado/error)
        """
        # Pedir al LLM que genere el comando específico
        prompt = f"""Basado en esta solicitud: "{command_description}"
        
Genera ÚNICAMENTE el comando de bash exacto que ejecutarías para cumplir esta solicitud.
No incluyas explicaciones, solo el comando. Si la solicitud es peligrosa o ambigua, responde "RECHAZADO".

Comando:"""
        
        self.history.add_message("user", command_description)
        messages = self.history.get_full_history()
        
        # Mensaje temporal para obtener el comando
        temp_messages = messages + [{"role": "user", "content": prompt}]
        
        command = await self.client.send_message(temp_messages, temperature=0.3, max_tokens=100)
        command = command.strip().strip('`').strip()
        
        # Eliminar el prompt temporal del historial
        self.history.messages = self.history.messages[:-1]
        
        if "RECHAZADO" in command.upper():
            return False, "Prefiero no ejecutar ese comando por seguridad, señor."
        
        # Validar comando básico (evitar comandos peligrosos)
        dangerous_patterns = ['rm -rf /', 'mkfs', 'dd if=', ':(){:|:&};:', '> /dev/sda']
        for pattern in dangerous_patterns:
            if pattern in command:
                return False, "Ese comando podría ser peligroso, señor. ¿Podemos buscar una alternativa?"
        
        # Ejecutar comando
        try:
            logger.info(f"Ejecutando comando: {command}")
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            if process.returncode == 0:
                result = stdout.decode('utf-8').strip() or "Comando ejecutado exitosamente."
                return True, result
            else:
                error = stderr.decode('utf-8').strip()
                return False, f"Error al ejecutar: {error}"
                
        except asyncio.TimeoutError:
            return False, "El comando tardó demasiado. Lo he interrumpido por seguridad."
        except Exception as e:
            return False, f"Error técnico: {str(e)}"
    
    async def cleanup(self) -> None:
        """Liberar recursos."""
        await self.client.close()
