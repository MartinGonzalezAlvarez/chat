import asyncio
import json
import os
import uuid

import httpx
import reflex as rx

class SettingsState(rx.State):
    color: str = "violet"
    font_family: str = "Poppins"

class State(rx.State):
    question: str = ""
    processing: bool = False
    chat_history: list[tuple[str, str]] = []
    user_id: str = str(uuid.uuid4())
    max_history_length: int = 20  # Límite de historial

    def sanitize_input(self, text: str) -> str:
        """Sanitiza la entrada del usuario"""
        return text.strip()[:500]  # Limita longitud y elimina espacios

    async def answer(self):
        # Validación de entrada
        if not self.question.strip():
            return

        sanitized_question = self.sanitize_input(self.question)

        self.processing = True
        yield

        self.chat_history.append((sanitized_question, ""))

        # Truncar historial si es necesario
        if len(self.chat_history) > self.max_history_length:
            self.chat_history = self.chat_history[-self.max_history_length:]

        self.question = ""
        yield

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=30.0)) as client:
            input_payload = {
                "prompt": sanitized_question,
                "model": "mistral:7b",
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40
                }
            }

            apiserver_url = os.environ.get("APISERVER_URL", "http://localhost:3335")

            try:
                async with client.stream(
                    'POST',
                    f"{apiserver_url}/api/generate",
                    json=input_payload
                ) as response:
                    full_response = ""
                    async for chunk in response.aiter_text():
                        json_chunk = json.loads(chunk)  # Parsear como JSON
                        fragment = json_chunk['response']  # Acceder al campo 'response'
                        full_response += fragment  # Acumular la respuesta
                        yield  # Actualizar la UI

                    # Actualizar el historial de chat al final del streaming
                    self.chat_history[-1] = (
                        self.chat_history[-1][0],
                        full_response
                    )

            except (httpx.RequestError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.HTTPStatusError) as e:
                print(f"Error de comunicación: {e}")
                self.chat_history[-1] = (self.chat_history[-1][0], "Error de comunicación.")
            except asyncio.CancelledError:
                print("La solicitud fue cancelada.")
                self.chat_history[-1] = (self.chat_history[-1][0], "La solicitud fue cancelada.")
            finally:
                self.processing = False
                yield

    async def handle_key_down(self, key: str):
        if key == "Enter" and not self.processing:
            await self.answer()

    def clear_chat(self):
        self.chat_history = []
        self.processing = False


