#!/usr/bin/env python3
"""
DocumentAgent - Финальная версия (Claude Sonnet 4.6)
Готов к интеграции с Max
"""

import json
import os
import requests
import subprocess
from pathlib import Path
from datetime import datetime

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-sonnet-4-6"
WORKER_PATH = "~/openclaw-skills/document-worker/document_worker.py"


class DocumentAgent:
    def __init__(self, session_id: str = "main"):
        self.session_id = session_id
        self.state_file = Path(f"~/.openclaw/sessions/{session_id}_state.json").expanduser()
        self.state = self._load_state()
    
    def _load_state(self):
        if self.state_file.exists():
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        return {
            "created_at": datetime.now().isoformat(),
            "pdfs": {},
            "current_excel": None,
            "history": []
        }
    
    def _save_state(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")
    
    def load_pdf(self, pdf_path: str):
        filename = Path(pdf_path).name
        self.state["pdfs"][filename] = {
            "path": pdf_path,
            "loaded_at": datetime.now().isoformat(),
            "positions": 0,
            "status": "loaded"
        }
        self.state["history"].append({"role": "system", "content": f"Загружен PDF: {filename}"})
        self._save_state()
        return f"✅ PDF загружен: {filename}"
    
    def parse_pdf(self, filename: str = None):
        if not filename and self.state["pdfs"]:
            filename = list(self.state["pdfs"].keys())[-1]
        if not filename or filename not in self.state["pdfs"]:
            return "PDF не найден"
        
        pdf_path = self.state["pdfs"][filename]["path"]
        output_path = str(Path(pdf_path).parent / f"{Path(filename).stem}_результат.xlsx")
        
        try:
            result = subprocess.run(
                ["python3", WORKER_PATH, "--pdf", pdf_path, "--output", output_path, "--title", filename],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                self.state["pdfs"][filename]["status"] = "parsed"
                self.state["current_excel"] = output_path
                self.state["history"].append({"role": "system", "content": f"Распарсен: {filename}"})
                self._save_state()
                return f"✅ Готово! Файл: {output_path}"
            return f"Ошибка парсинга: {result.stderr}"
        except Exception as e:
            return f"Ошибка: {str(e)}"
    
    def call_model(self, user_message: str):
        messages = [
            {"role": "system", "content": "Ты — DocumentAgent. Помогаешь работать с PDF и Excel. У тебя есть инструменты: load_pdf, parse_pdf. Отвечай кратко."}
        ]
        for msg in self.state["history"][-12:]:
            messages.append(msg)
        messages.append({"role": "user", "content": user_message})
        
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        data = {"model": MODEL, "messages": messages, "temperature": 0.3, "max_tokens": 2000}
        
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=60)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            return f"Ошибка модели: {response.text}"
        except Exception as e:
            return f"Ошибка: {str(e)}"
    
    def chat(self, message: str):
        self.state["history"].append({"role": "user", "content": message})
        
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["распарси", "обработай", "извлеки"]):
            response = self.parse_pdf()
        elif "статус" in msg_lower or "что загружено" in msg_lower:
            response = self.get_status_text()
        else:
            response = self.call_model(message)
        
        self.state["history"].append({"role": "assistant", "content": response})
        self._save_state()
        return response
    
    def get_status_text(self):
        if not self.state["pdfs"]:
            return "PDF не загружены"
        lines = ["📁 Загруженные PDF:"]
        for name, info in self.state["pdfs"].items():
            lines.append(f"  • {name} ({info['status']})")
        if self.state.get("current_excel"):
            lines.append(f"\n📄 Последний Excel: {self.state['current_excel']}")
        return "\n".join(lines)


# ==================== ИНТЕГРАЦИЯ С MAX ====================

def handle_max_message(agent: DocumentAgent, message: str, attachments: list = None):
    """
    Основная функция для обработки сообщений из Max
    """
    # Если прислали файл
    if attachments:
        for att in attachments:
            if att.get("type") == "file" and att.get("name", "").endswith(".pdf"):
                result = agent.load_pdf(att["path"])
                return result
    
    # Обычное сообщение
    return agent.chat(message)


if __name__ == "__main__":
    print("DocumentAgent готов (Claude Sonnet 4.6)")
    print("Используй handle_max_message() для интеграции с Max")
