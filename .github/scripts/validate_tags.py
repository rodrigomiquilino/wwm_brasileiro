#!/usr/bin/env python3
"""
Валидатор игровых тегов для файла translation_ru.tsv

Проверяет:
1. Корректность тегов цветового оформления (#G...#E)
2. Отсутствие русских букв после символа # (код 01)
3. Закрывающий тег #E без открывающего (код 02)
4. Открывающий тег без закрывающего #E (код 03)
5. Корректность тегов-ссылок (<...|...|...|...>) (код 04)
6. Несбалансированные фигурные скобки в переменных (код 05)
7. Закрывающая скобка } без открывающей { (код 06)
8. Открывающая скобка { без закрывающей } (код 07)
"""

import sys
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, Tuple, List


# Коды ошибок
ERROR_CODE_RUSSIAN_AFTER_HASH = "01"
ERROR_CODE_CLOSING_TAG_WITHOUT_OPENING = "02"
ERROR_CODE_OPENING_TAG_WITHOUT_CLOSING = "03"
ERROR_CODE_LINK_TAG_INVALID = "04"
ERROR_CODE_UNBALANCED_BRACES = "05"
ERROR_CODE_CLOSING_BRACE_WITHOUT_OPENING = "06"
ERROR_CODE_OPENING_BRACE_WITHOUT_CLOSING = "07"


def validate_tags(file_path: str) -> Dict[str, Set[str]]:
    """
    Валидирует игровые теги в TSV файле.
    
    Returns:
        dict: {id: set of error codes}
    """
    errors_by_id: Dict[str, Set[str]] = defaultdict(set)
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        print(f"❌ Файл {file_path} не найден")
        return errors_by_id
    
    try:
        with open(file_path_obj, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")
        return errors_by_id
    
    if len(lines) == 0:
        return errors_by_id
    
    # Паттерны для проверки
    id_pattern = re.compile(r'^[0-9a-fA-F]{16}$')
    
    # Проверка каждой строки
    current_entry_lines = []
    entry_start_line = None
    current_id = None
    
    for line_num, line in enumerate(lines[1:], start=2):
        original_line = line
        line = line.rstrip('\n\r')
        
        # Пропускаем пустые строки
        if not line.strip():
            continue
        
        # Проверяем, начинается ли строка с ID
        is_new_entry = re.match(r'^[0-9a-fA-F]{16}\t', line)
        
        if is_new_entry:
            # Если это новая запись, обрабатываем предыдущую
            if current_entry_lines:
                full_text = ''.join(current_entry_lines)
                if entry_start_line and current_id:
                    _validate_entry_tags(
                        errors_by_id, entry_start_line, full_text, id_pattern,
                        current_id
                    )
            
            # Начинаем новую запись
            current_entry_lines = [original_line]
            entry_start_line = line_num
            
            parts = line.split('\t', 1)
            if len(parts) == 2:
                current_id = parts[0]
        else:
            # Продолжение предыдущей записи
            if current_entry_lines:
                current_entry_lines.append(original_line)
    
    # Обрабатываем последнюю запись
    if current_entry_lines:
        full_text = ''.join(current_entry_lines)
        if entry_start_line and current_id:
            _validate_entry_tags(
                errors_by_id, entry_start_line, full_text, id_pattern,
                current_id
            )
    
    return errors_by_id


def _validate_entry_tags(
    errors_by_id: Dict[str, Set[str]], start_line: int, full_text: str,
    id_pattern: re.Pattern, current_id: str
):
    """Валидирует теги в одной записи TSV."""
    full_text = full_text.rstrip('\n\r')
    
    # Разделяем на ID и текст
    parts = full_text.split('\t', 1)
    if len(parts) != 2:
        return
    
    id_value, text = parts
    
    # 1. Проверка тегов цветового оформления #G...#E и русских букв после #
    # Сначала находим все теги-ссылки, чтобы пропустить теги внутри них
    link_ranges = []
    for link_match in re.finditer(r'<([^>]*)>', text):
        link_ranges.append((link_match.start(), link_match.end()))
    
    def is_inside_link_tag(pos):
        """Проверяет, находится ли позиция внутри тега-ссылки."""
        for start, end in link_ranges:
            if start <= pos < end:
                return True
        return False
    
    # Проходим по тексту и проверяем парность тегов
    tag_stack = []
    i = 0
    while i < len(text):
        # Пропускаем теги внутри тегов-ссылок
        if is_inside_link_tag(i):
            i += 1
            continue
        
        # Проверяем, не начинается ли здесь открывающий тег
        if text[i] == '#' and i + 1 < len(text):
            # Сначала проверяем закрывающий тег #E
            if text[i:i+2] == '#E':
                if tag_stack:
                    tag_stack.pop()
                else:
                    errors_by_id[current_id].add(ERROR_CODE_CLOSING_TAG_WITHOUT_OPENING)
                i += 2
                continue
            
            # Проверяем hex код цвета (#000, #FFFFFF, #ffc89c10 и т.д.)
            hex_match = re.match(r'#([0-9A-Fa-f]{3,})(?![0-9A-Fa-f])', text[i:])
            if hex_match:
                hex_code = hex_match.group(0)
                hex_code_len = len(hex_code)
                
                # Проверяем, используется ли hex код как открывающий тег с закрывающим #E
                if i + hex_code_len < len(text) and text[i + hex_code_len:i + hex_code_len + 2] != '#E':
                    # После hex кода идет текст - это может быть открывающий тег с закрывающим #E
                    tag_stack.append((i, hex_code))
                
                i += hex_code_len
                continue
            
            # Проверяем буквенный тег (#G, #R, #Y и т.д.)
            letter_match = re.match(r'#([A-Za-z][A-Za-z0-9]*)', text[i:])
            if letter_match:
                tag = letter_match.group(0)
                if tag != '#E':
                    tag_stack.append((i, tag))
                i += len(tag)
                continue
            
            # Проверяем на русскую букву после #
            if i + 1 < len(text) and '\u0400' <= text[i+1] <= '\u04FF':
                errors_by_id[current_id].add(ERROR_CODE_RUSSIAN_AFTER_HASH)
                i += 1
                continue
        
        i += 1
    
    # Проверяем незакрытые открывающие теги
    if tag_stack:
        errors_by_id[current_id].add(ERROR_CODE_OPENING_TAG_WITHOUT_CLOSING)
    
    # 3. Проверка тегов-ссылок <...|...|...|...>
    # Проверяем только теги, которые содержат символ | (теги-ссылки)
    # Если в <> просто текст без |, то это не ошибка (например, <Water Loong Army>)
    for link_match in re.finditer(r'<([^>]*)>', text):
        link_content = link_match.group(1)
        # Игнорируем HTML-подобные теги (например, <TEXT>, </TEXT>, <IMAGE>)
        if re.match(r'^[A-Z/]', link_content.strip()):
            continue
        
        # Проверяем только если есть символ | (это тег-ссылка)
        if '|' in link_content:
            parts = link_content.split('|')
            if len(parts) != 3 and len(parts) != 4 and len(parts) != 5:
                errors_by_id[current_id].add(ERROR_CODE_LINK_TAG_INVALID)
        # Если нет |, то это просто текст в угловых скобках - не ошибка
    
    # 4. Проверка переменных {...}
    open_braces = text.count('{')
    close_braces = text.count('}')
    if open_braces != close_braces:
        errors_by_id[current_id].add(ERROR_CODE_UNBALANCED_BRACES)
    
    # Проверяем, что все переменные правильно закрыты
    brace_stack = []
    for i, char in enumerate(text):
        if char == '{':
            brace_stack.append(i)
        elif char == '}':
            if not brace_stack:
                errors_by_id[current_id].add(ERROR_CODE_CLOSING_BRACE_WITHOUT_OPENING)
            else:
                brace_stack.pop()
    
    # Проверяем незакрытые переменные
    if brace_stack:
        errors_by_id[current_id].add(ERROR_CODE_OPENING_BRACE_WITHOUT_CLOSING)


def _get_error_message(error_code: str, start_line: int, display_id: str, context: str) -> str:
    """Формирует сообщение об ошибке по коду."""
    messages = {
        ERROR_CODE_RUSSIAN_AFTER_HASH: f"Строка {start_line}, ID: {display_id} [Код {error_code}]: Найдена русская буква после символа #. После # должны быть только английские буквы или hex символы (0-9, A-F). Контекст: '{context[:100]}'",
        ERROR_CODE_CLOSING_TAG_WITHOUT_OPENING: f"Строка {start_line}, ID: {display_id} [Код {error_code}]: Найден закрывающий тег #E без соответствующего открывающего тега. Контекст: '{context[:100]}'",
        ERROR_CODE_OPENING_TAG_WITHOUT_CLOSING: f"Строка {start_line}, ID: {display_id} [Код {error_code}]: Открывающий тег не имеет закрывающего тега #E. Контекст: '{context[:100]}'",
        ERROR_CODE_LINK_TAG_INVALID: f"Строка {start_line}, ID: {display_id} [Код {error_code}]: Тег-ссылка должен содержать 4 или 5 частей, разделённых символом |. Контекст: '{context[:100]}'",
        ERROR_CODE_UNBALANCED_BRACES: f"Строка {start_line}, ID: {display_id} [Код {error_code}]: Несбалансированные фигурные скобки в переменных. Контекст: '{context[:100]}'",
        ERROR_CODE_CLOSING_BRACE_WITHOUT_OPENING: f"Строка {start_line}, ID: {display_id} [Код {error_code}]: Найдена закрывающая скобка }} без соответствующей открывающей {{. Контекст: '{context[:100]}'",
        ERROR_CODE_OPENING_BRACE_WITHOUT_CLOSING: f"Строка {start_line}, ID: {display_id} [Код {error_code}]: Найдена открывающая скобка {{ без соответствующей закрывающей }}. Контекст: '{context[:100]}'",
    }
    return messages.get(error_code, f"Строка {start_line}, ID: {display_id} [Код {error_code}]: Неизвестная ошибка. Контекст: '{context[:100]}'")


def _get_context(text: str, search_str: str, context_len: int = 30, pos: int = None) -> str:
    """Получает контекст вокруг найденной строки."""
    if pos is None:
        pos = text.find(search_str)
        if pos == -1:
            return text[:context_len]
    
    start = max(0, pos - context_len)
    end = min(len(text), pos + len(search_str) + context_len)
    context = text[start:end]
    
    # Заменяем переносы строк для читаемости
    context = context.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    
    return context


def _get_entry_text_by_id(file_path: str, target_id: str) -> Tuple[int, str]:
    """Получает текст записи по ID и номер строки."""
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        return 0, ""
    
    try:
        with open(file_path_obj, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        return 0, ""
    
    current_entry_lines = []
    entry_start_line = None
    current_id = None
    
    for line_num, line in enumerate(lines[1:], start=2):
        original_line = line
        line = line.rstrip('\n\r')
        
        if not line.strip():
            continue
        
        is_new_entry = re.match(r'^[0-9a-fA-F]{16}\t', line)
        
        if is_new_entry:
            if current_entry_lines and current_id == target_id:
                return entry_start_line or 0, ''.join(current_entry_lines)
            
            current_entry_lines = [original_line]
            entry_start_line = line_num
            
            parts = line.split('\t', 1)
            if len(parts) == 2:
                current_id = parts[0]
        else:
            if current_entry_lines:
                current_entry_lines.append(original_line)
    
    if current_entry_lines and current_id == target_id:
        return entry_start_line or 0, ''.join(current_entry_lines)
    
    return 0, ""


def main():
    # Настройка кодировки для Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # Определяем пути к файлам
    script_dir = Path(__file__).parent.parent.parent
    ru_file = script_dir / "translation_ru.tsv"
    en_file = script_dir / "translation_en.tsv"
    
    if not ru_file.exists():
        print(f"❌ Файл {ru_file} не найден")
        sys.exit(1)
    
    # Сначала проверяем RU файл
    print("🔍 Проверка translation_ru.tsv...")
    ru_errors = validate_tags(str(ru_file))
    
    # Затем проверяем EN файл
    en_errors = {}
    if en_file.exists():
        print("🔍 Проверка translation_en.tsv...")
        en_errors = validate_tags(str(en_file))
    else:
        print(f"⚠️  Файл {en_file} не найден, проверяется только RU файл")
    
    # Собираем все уникальные ID с ошибками
    all_ids = set(ru_errors.keys()) | set(en_errors.keys())
    
    if not all_ids:
        print(f"✅ Все теги в файлах валидны!")
        sys.exit(0)
    
    print(f"\n🔍 Валидация тегов:\n")
    
    # Отслеживаем, есть ли ошибки только в RU (блокирующие)
    has_ru_only_errors = False
    
    # Для каждого ID проверяем ошибки
    for entry_id in sorted(all_ids):
        ru_error_codes = ru_errors.get(entry_id, set())
        en_error_codes = en_errors.get(entry_id, set())
        
        # Определяем метку
        if ru_error_codes and en_error_codes:
            label = "[RU\\EN]"
            prefix = "⚠️"
        elif en_error_codes:
            label = "[EN]"
            prefix = "⚠️"
        else:  # только в RU - это ошибка!
            label = "[RU]"
            prefix = "❌"
            has_ru_only_errors = True
        
        # Получаем текст записи для контекста
        start_line, entry_text = _get_entry_text_by_id(str(ru_file), entry_id)
        if not entry_text:
            start_line, entry_text = _get_entry_text_by_id(str(en_file), entry_id)
        
        parts = entry_text.split('\t', 1)
        text = parts[1] if len(parts) > 1 else ""
        
        # Выводим ошибки
        all_error_codes = ru_error_codes | en_error_codes
        for error_code in sorted(all_error_codes):
            # Используем начало текста как контекст
            context = text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t') if text else ""
            message = _get_error_message(error_code, start_line, entry_id, context)
            print(f"{prefix} {label} {message}")
    
    total_ru = sum(len(codes) for codes in ru_errors.values())
    total_en = sum(len(codes) for codes in en_errors.values())
    total_unique = len(all_ids)
    
    ru_only_count = sum(1 for entry_id in all_ids if entry_id in ru_errors and entry_id not in en_errors)
    
    if has_ru_only_errors:
        print(f"\n❌ Найдено ошибок только в RU: {ru_only_count} записей (блокирующие)")
        print(f"⚠️  Найдено предупреждений: {total_unique - ru_only_count} записей (RU\\EN: {total_ru - ru_only_count}, EN: {total_en})")
        print("❌ Ошибки только в RU файле требуют исправления. Коммит будет заблокирован.")
        sys.exit(1)
    else:
        print(f"\n⚠️  Найдено предупреждений: {total_unique} записей (RU\\EN: {total_ru}, EN: {total_en})")
        print("ℹ️  Это предупреждения, а не критичные ошибки. Коммит не будет заблокирован.")
        sys.exit(0)


if __name__ == '__main__':
    main()
