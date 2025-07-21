

import requests
import json
import re
import ssl
import urllib3

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 설정 ---
NOTION_API_KEY = "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"
PAGE_ID = "23731382e0a28084b958f0551643d8a5"
MARKDOWN_FILE = 'HANDOVER_DOCUMENTATION.md'

# --- Notion API 헤더 ---
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def parse_rich_text(text):
    """마크다운 형식의 문자열을 Notion rich_text 배열로 변환합니다."""
    text = text.strip()
    text = text.replace('<br>', '\n')

    parts = re.split(r'(\*\*.*?\*\*)', text)
    if len(parts) == 1:
        return [{"type": "text", "text": {"content": text}}] if text else []

    rich_text_objects = []
    for part in parts:
        if not part:
            continue
        if part.startswith('**') and part.endswith('**'):
            rich_text_objects.append({
                "type": "text",
                "text": {"content": part[2:-2]},
                "annotations": {"bold": True}
            })
        else:
            rich_text_objects.append({
                "type": "text",
                "text": {"content": part}
            })
    return rich_text_objects

def create_table_block(rows):
    """테이블 데이터로 Notion 테이블 블록을 생성합니다."""
    if not rows:
        return None

    table_width = len(rows[0])
    
    if len(rows) > 1 and '---' in "".join(rows[1]):
        header_row = rows[0]
        data_rows = rows[2:]
        has_header = True
    else:
        header_row = None
        data_rows = rows
        has_header = False

    table_children = []
    if has_header:
        table_children.append({
            "type": "table_row",
            "table_row": {"cells": [parse_rich_text(cell) for cell in header_row]}
        })

    for row_data in data_rows:
        while len(row_data) < table_width:
            row_data.append("")
        table_children.append({
            "type": "table_row",
            "table_row": {"cells": [parse_rich_text(cell) for cell in row_data]}
        })

    if not table_children:
        return None

    return {
        "type": "table",
        "table": {
            "table_width": table_width,
            "has_column_header": has_header,
            "has_row_header": False,
            "children": table_children
        }
    }

def parse_markdown_to_notion_blocks(markdown_content):
    """마크다운 콘텐츠를 Notion 블록 리스트로 변환합니다."""
    blocks = []
    lines = markdown_content.splitlines()
    
    in_table = False
    table_rows = []

    for line in lines:
        stripped_line = line.strip()
        
        if in_table and not stripped_line.startswith('|'):
            if table_rows:
                table_block = create_table_block(table_rows)
                if table_block:
                    blocks.append(table_block)
                table_rows = []
            in_table = False

        if not stripped_line:
            blocks.append({"type": "paragraph", "paragraph": {"rich_text": []}})
        elif stripped_line.startswith('# '):
            blocks.append({"type": "heading_1", "heading_1": {"rich_text": parse_rich_text(stripped_line[2:])}})
        elif stripped_line.startswith('## '):
            blocks.append({"type": "heading_2", "heading_2": {"rich_text": parse_rich_text(stripped_line[3:])}})
        elif stripped_line.startswith('### '):
            blocks.append({"type": "heading_3", "heading_3": {"rich_text": parse_rich_text(stripped_line[4:])}})
        elif stripped_line.startswith('> '):
            blocks.append({"type": "quote", "quote": {"rich_text": parse_rich_text(stripped_line[2:])}})
        elif stripped_line.startswith(('* ', '- ')):
            blocks.append({"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": parse_rich_text(stripped_line[2:])}})
        elif stripped_line.startswith('|') and stripped_line.endswith('|'):
            in_table = True
            row_cells = [cell.strip() for cell in stripped_line.split('|')][1:-1]
            table_rows.append(row_cells)
        else:
            blocks.append({"type": "paragraph", "paragraph": {"rich_text": parse_rich_text(stripped_line)}})

    if table_rows:
        table_block = create_table_block(table_rows)
        if table_block:
            blocks.append(table_block)

    return blocks

def clear_page_content(page_id):
    """페이지의 모든 블록을 삭제합니다."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    try:
        while True:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
            data = response.json()
            blocks = data.get('results', [])
            if not blocks:
                break
            for block in blocks:
                delete_url = f"https://api.notion.com/v1/blocks/{block['id']}"
                del_response = requests.delete(delete_url, headers=headers, verify=False)
                del_response.raise_for_status()
            if not data.get('has_more'):
                break
            url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100&start_cursor={data.get('next_cursor')}"
        print("기존 페이지 콘텐츠를 모두 삭제했습니다.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"페이지 삭제 중 오류 발생: {e}")
        return False

def update_notion_page(page_id, blocks):
    """Notion 페이지에 새로운 블록들을 추가합니다."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    for i in range(0, len(blocks), 100):
        chunk = blocks[i:i+100]
        data = {"children": chunk}
        try:
            response = requests.patch(url, headers=headers, data=json.dumps(data), verify=False)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Notion 페이지 업데이트 실패: {e}")
            print(f"응답 내용: {response.text}")
            return False
    print(f"Notion 페이지가 성공적으로 업데이트되었습니다. 총 {len(blocks)}개의 블록이 추가되었습니다.")
    return True

def main():
    try:
        with open(MARKDOWN_FILE, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        print(f"오류: '{MARKDOWN_FILE}' 파일을 찾을 수 없습니다.")
        return

    notion_blocks = parse_markdown_to_notion_blocks(markdown_content)
    
    if not notion_blocks:
        print("변환할 콘텐츠가 없습니다.")
        return

    if not clear_page_content(PAGE_ID):
        print("페이지 삭제 중 오류가 발생하여 업데이트를 중단합니다.")
        return
        
    update_notion_page(PAGE_ID, notion_blocks)

if __name__ == "__main__":
    main()
