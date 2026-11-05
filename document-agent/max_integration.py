#!/usr/bin/env python3
"""
Интеграция DocumentAgent с Max
"""

from document_agent import DocumentAgent, handle_max_message

# Создаём одного агента на всю сессию (сохраняет контекст)
agent = DocumentAgent("main")


def on_max_message(message: str, attachments: list = None, chat_id: str = None):
    """
    Эта функция будет вызываться при каждом сообщении из Max
    """
    try:
        response = handle_max_message(agent, message, attachments)
        return response
    except Exception as e:
        return f"Ошибка: {str(e)}"


# Пример использования (для теста)
if __name__ == "__main__":
    # Тестовое сообщение
    result = on_max_message("статус")
    print("Ответ агента:", result)
