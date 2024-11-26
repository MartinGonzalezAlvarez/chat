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

        async with httpx.AsyncClient() as client:
            input_payload = {
                "prompt": sanitized_question,
                "model": "mistral",
                "stream": True
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
                        try:
                            # Intenta parsear como JSON
                            json_chunk = json.loads(chunk)
                            if isinstance(json_chunk, dict) and 'response' in json_chunk:
                                fragment = json_chunk['response']
                            else:
                                fragment = chunk
                        except json.JSONDecodeError:
                            # Si no es JSON, usa el chunk directo
                            fragment = chunk

                        # Acumula el fragmento sin añadir espacios extra
                        full_response += fragment

                        # Actualiza el historial de chat
                        self.chat_history[-1] = (
                            self.chat_history[-1][0],
                            full_response
                        )
                        yield

            except httpx.RequestError as e:
                print(f"Error de comunicación: {e}")
                self.chat_history[-1] = (self.chat_history[-1][0], "Error de comunicación.")
            finally:
                self.processing = False
                yield

    async def handle_key_down(self, key: str):
        if key == "Enter" and not self.processing:
            await self.answer()

    def clear_chat(self):
        self.chat_history = []
        self.processing = False