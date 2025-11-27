#!/usr/bin/env python3
"""
Валидатор для файла translation_ru.tsv

Проверяет:
1. Корректность формата TSV (разделитель - табуляция)
2. Правильное количество столбцов (2: ID и OriginalText)
3. Формат ID (16 символов hex)
4. Отсутствие разорванных строк
"""

import sys
import re
from pathlib import Path


def validate_tsv(file_path: str) -> tuple[bool, list[str]]:
    """
    Валидирует TSV файл.
    
    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        errors.append(f"❌ Файл {file_path} не найден")
        return False, errors
    
    try:
        with open(file_path_obj, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        errors.append(f"❌ Ошибка при чтении файла: {e}")
        return False, errors
    
    if len(lines) == 0:
        errors.append("❌ Файл пуст")
        return False, errors
    
    # Проверка заголовка
    if len(lines) < 1:
        errors.append("❌ Файл должен содержать заголовок")
        return False, errors

    # Убираем возможный BOM (UTF-8 BOM: \ufeff) и переводы строк
    header = lines[0].lstrip('\ufeff').rstrip('\n\r')
    if not header.startswith('ID\tOriginalText'):
        errors.append(
            f"❌ Неверный заголовок. Ожидается: 'ID\\tOriginalText', получено: '{header[:50]}'"
        )
    
    # ID должен быть 16 символов hex
    id_pattern = re.compile(r'^[0-9a-fA-F]{16}$')
    
    # Проверка каждой строки
    current_entry_lines = []  # Для отслеживания многострочных записей
    entry_start_line = None
    current_id = None  # Для хранения ID текущей записи
    
    for line_num, line in enumerate(lines[1:], start=2):
        original_line = line
        line = line.rstrip('\n\r')
        
        # Пропускаем пустые строки
        if not line.strip():
            if current_entry_lines:
                # Пустая строка внутри записи - это ошибка
                id_info = f"ID: {current_id}, " if current_id else ""
                errors.append(
                    f"❌ Строка {line_num}: {id_info}Пустая строка внутри записи, начатой на строке {entry_start_line}. "
                    f"Возможно, запись разорвана."
                )
                current_entry_lines = []
                entry_start_line = None
                current_id = None
            continue
        
        # Проверяем, начинается ли строка с ID (16 hex символов + табуляция)
        is_new_entry = re.match(r'^[0-9a-fA-F]{16}\t', line)
        
        if is_new_entry:
            # Если это новая запись, обрабатываем предыдущую
            if current_entry_lines:
                # Валидируем предыдущую запись
                full_text = ''.join(current_entry_lines)
                if entry_start_line:
                    _validate_entry(errors, entry_start_line, full_text, id_pattern, current_id)
            
            # Начинаем новую запись
            current_entry_lines = [original_line]
            entry_start_line = line_num
            
            # Проверяем первую строку новой записи
            parts = line.split('\t', 1)  # Разделяем только на первую табуляцию
            if len(parts) != 2:
                # Пытаемся извлечь ID из начала строки
                potential_id = line[:16] if len(line) >= 16 else line
                errors.append(
                    f"❌ Строка {line_num}, ID: {potential_id}: Отсутствует разделитель табуляции после ID. "
                    f"Начало строки: '{line[:100]}'"
                )
                current_entry_lines = []
                entry_start_line = None
                current_id = None
            else:
                id_value = parts[0]
                current_id = id_value
                if not id_pattern.match(id_value):
                    errors.append(
                        f"❌ Строка {line_num}, ID: {id_value}: Неверный формат ID. "
                        f"Ожидается 16 hex символов, получено: '{id_value}'"
                    )
        else:
            # Это продолжение предыдущей записи (многострочное значение)
            if not current_entry_lines:
                # Строка не начинается с ID и нет активной записи - это ошибка
                errors.append(
                    f"❌ Строка {line_num}: Строка не начинается с корректного ID (16 hex символов + табуляция). "
                    f"Возможно, строка разорвана или предыдущая запись не завершена. "
                    f"Начало строки: '{line[:100]}'"
                )
            else:
                # Добавляем к текущей записи
                current_entry_lines.append(original_line)
    
    # Обрабатываем последнюю запись
    if current_entry_lines:
        full_text = ''.join(current_entry_lines)
        if entry_start_line:
            _validate_entry(errors, entry_start_line, full_text, id_pattern, current_id)
    
    # Фатальными считаем только сообщения, которые НЕ начинаются с ⚠ (предупреждения)
    has_fatal_errors = any(not err.lstrip().startswith('⚠') for err in errors)
    is_valid = not has_fatal_errors
    return is_valid, errors


def _validate_entry(errors: list, start_line: int, full_text: str, id_pattern: re.Pattern, current_id: str = None):
    """Валидирует одну запись TSV."""
    # Убираем последний перенос строки, если есть
    full_text = full_text.rstrip('\n\r')
    
    # Разделяем на ID и текст (только по первой табуляции)
    parts = full_text.split('\t', 1)
    
    if len(parts) != 2:
        id_info = f"ID: {current_id}, " if current_id else ""
        errors.append(
            f"❌ Строка {start_line}, {id_info}Неверный формат записи. "
            f"Ожидается ID и текст, разделённые табуляцией. "
            f"Начало: '{full_text[:100]}'"
        )
        return
    
    id_value, text = parts
    
    # Используем переданный ID или извлечённый
    display_id = current_id if current_id else id_value
    
    # Проверяем формат ID
    if not id_pattern.match(id_value):
        errors.append(
            f"❌ Строка {start_line}, ID: {display_id}: Неверный формат ID. "
            f"Ожидается 16 hex символов, получено: '{id_value}'"
        )
    
    # Проверяем, что в тексте нет дополнительных табуляций
    # (табуляция должна быть только разделителем между ID и текстом)
    if '\t' in text:
        errors.append(
            f"❌ Строка {start_line}, ID: {display_id}: В тексте найдены дополнительные табуляции. "
            f"Табуляция должна использоваться только как разделитель между ID и текстом. "
            f"Текст содержит {text.count(chr(9))} дополнительных табуляций. "
            f"Начало текста: '{text[:100]}'"
        )
    
    # Проверяем, что текст не пустой
    if not text.strip():
        errors.append(
            f"⚠️  Строка {start_line}, ID: {display_id}: Пустой текст"
        )

    # Проверяем корректность использования двойных кавычек.
    # Цель — ловить именно такие случаи, которые ломают TSV/CSV-парсеры,
    # а не запрещать любые сложные комбинации кавычек.
    # Правила:
    #   1) Если текст начинается с " и не заканчивается на "  -> фатальная ошибка.
    #   2) Если текст заканчивается на " и не начинается с "  -> фатальная ошибка.
    #   3) Если общее количество кавычек нечётное              -> предупреждение.
    if '"' in text:
        quote_count = text.count('"')

        starts_with_quote = text.startswith('"')
        ends_with_quote = text.endswith('"')

        # Открывающая без закрывающей
        if starts_with_quote and not ends_with_quote:
            errors.append(
                f"❌ Строка {start_line}, ID: {display_id}: Некорректное использование кавычек "
                f'(открывающая кавычка без закрывающей). Начало текста: "{text[:100]}"'
            )
        # Закрывающая без открывающей
        elif ends_with_quote and not starts_with_quote:
            errors.append(
                f"❌ Строка {start_line}, ID: {display_id}: Некорректное использование кавычек "
                f'(закрывающая кавычка без открывающей). Начало текста: "{text[:100]}"'
            )
        # Текст выглядит как полностью "заключённый в кавычки" (как CSV-поле).
        # В этом случае любое нечётное количество кавычек — гарантированно поломанное поле,
        # которое может склеить строки/столбцы при импорте → считаем фатальной ошибкой.
        elif starts_with_quote and ends_with_quote and quote_count % 2 != 0:
            errors.append(
                f"❌ Строка {start_line}, ID: {display_id}: Поломанные кавычки в кавычечной обёртке. "
                f"Поле начинается и заканчивается на \", но общее количество кавычек нечётное ({quote_count}), "
                f"что ломает CSV/TSV-парсеры. Начало текста: \"{text[:100]}\""
            )
        # Остальные случаи: кавычки где-то внутри, но не на границах поля.
        # Нечётное количество кавычек здесь подозрительно, но не всегда фатально → предупреждение.
        elif quote_count % 2 != 0:
            errors.append(
                f"⚠️ Строка {start_line}, ID: {display_id}: Нечётное количество двойных кавычек ({quote_count}). "
                f"Это может ломать TSV/CSV-конвертацию. Начало текста: \"{text[:100]}\""
            )


def main():
    # Настройка кодировки для Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    if len(sys.argv) != 2:
        print("Использование: python validate_tsv.py <путь_к_tsv_файлу>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    is_valid, errors = validate_tsv(file_path)
    
    fatal_errors = [e for e in errors if not e.lstrip().startswith('⚠')]
    warnings = [e for e in errors if e.lstrip().startswith('⚠')]

    if fatal_errors or warnings:
        print(f"\n🔍 Валидация файла {file_path}:\n")
        for error in errors:
            print(error)

    if fatal_errors:
        print(f"\n❌ Найдено ошибок: {len(fatal_errors)}")
        if warnings:
            print(f"⚠️ Найдено предупреждений: {len(warnings)}")
        sys.exit(1)
    elif warnings:
        print(f"\n⚠️ Найдено предупреждений: {len(warnings)}")
        sys.exit(0)
    else:
        print(f"✅ Файл {file_path} валиден!")
        sys.exit(0)


if __name__ == '__main__':
    main()

