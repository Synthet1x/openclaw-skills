#!/usr/bin/env python3
"""
Document Worker v5 - Поддержка нескольких PDF + объединение в один Excel
"""

import argparse
import base64
import json
import os
import requests
from pdf2image import convert_from_path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from pathlib import Path
from io import BytesIO
import glob

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-sonnet-4-6"


def pdf_to_images(pdf_path: str, dpi: int = 200):
    images = convert_from_path(pdf_path, dpi=dpi)
    encoded = []
    for img in images:
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        encoded.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))
    return encoded


def parse_with_claude(images: list, source_name: str):
    prompt = f"""Извлеки таблицу спецификации из изображений документа "{source_name}".

Верни JSON массив объектов со следующими полями:
- наименование
- артикул
- производитель
- марка
- ед.изм
- количество
- источник (название файла)

Если данных нет — верни []."""

    content = [{"type": "text", "text": prompt}]
    for img in images:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}})
    
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    data = {"model": MODEL, "messages": [{"role": "user", "content": content}], "temperature": 0.1, "max_tokens": 6000}
    
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=180)
    if response.status_code != 200:
        print(f"Ошибка: {response.text}")
        return []
    
    raw = response.json()["choices"][0]["message"]["content"].replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except:
        return []


def create_merged_excel(all_data: list, output_path: str, title: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "Объединённая спецификация"
    
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                         top=Side(style='thin'), bottom=Side(style='thin'))
    
    ws.merge_cells('A1:G1')
    ws['A1'] = title
    ws['A1'].font = Font(bold=True, size=16, color="1F4E79")
    
    headers = ["Наименование", "Артикул", "Производитель", "Марка", "Ед.изм", "Количество", "Источник"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
    
    for r, item in enumerate(all_data, 4):
        for c, key in enumerate(["наименование", "артикул", "производитель", "марка", "ед.изм", "количество", "источник"], 1):
            ws.cell(row=r, column=c, value=item.get(key, "")).border = thin_border
    
    for col in range(1, 8):
        ws.column_dimensions[get_column_letter(col)].width = 18
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return len(all_data)


def process_pdfs(pdf_paths: list, output_path: str, title: str):
    all_data = []
    
    for pdf_path in pdf_paths:
        print(f"🖼️  Обрабатываю: {Path(pdf_path).name}")
        images = pdf_to_images(pdf_path)
        print(f"   {len(images)} изображений")
        
        data = parse_with_claude(images, Path(pdf_path).name)
        for item in data:
            item["источник"] = Path(pdf_path).name
        all_data.extend(data)
        print(f"   Найдено {len(data)} позиций")
    
    print(f"\n📊 Всего позиций: {len(all_data)}")
    print("📊 Создаю объединённый Excel...")
    create_merged_excel(all_data, output_path, title)
    print(f"✅ Готово: {output_path}")
    return len(all_data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-folder", required=True, help="Папка с PDF файлами")
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="Объединённая спецификация")
    args = parser.parse_args()
    
    pdf_list = glob.glob(os.path.join(args.pdf_folder, "*.pdf"))
    
    if not pdf_list:
        print("PDF файлы не найдены в папке")
        return
    
    print(f"Найдено {len(pdf_list)} PDF файлов")
    process_pdfs(pdf_list, args.output, args.title)


if __name__ == "__main__":
    import glob
    main()
