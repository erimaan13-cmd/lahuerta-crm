"""Puerto LLM del clasificador híbrido (D-04). Desactivado en el MVP.

Contrato: recibe asunto/cuerpo y la lista de categorías; devuelve (categoría, confianza) o None si se abstiene.
Implementación real (P1): cliente de la API de Anthropic con clave en variable de entorno, sin enviar
datos de clientes reales sin acuerdo de tratamiento de datos (aviso de privacidad, E16).
"""
from typing import Protocol


class LLMClient(Protocol):
    def classify(self, subject: str, body: str, categories: list[str]) -> tuple[str, float] | None: ...


class NullLLMClient:
    """Se abstiene siempre: el correo queda en Needs Review."""

    def classify(self, subject, body, categories):
        return None


class MockLLMClient:
    """Para pruebas: devuelve una respuesta fija configurable."""

    def __init__(self, answer: tuple[str, float] | None):
        self.answer = answer
        self.calls = 0

    def classify(self, subject, body, categories):
        self.calls += 1
        return self.answer
