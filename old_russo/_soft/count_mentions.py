#!/usr/bin/env python3
"""
Скрипт для подсчета упоминаний имен из dictionary.tsv в translation_en.tsv
и добавления результатов в третий столбец dictionary.tsv
"""

import re
import sys
from pathlib import Path
from collections import defaultdict


def load_names_from_dictionary(dict_path: str) -> list[tuple[str, int]]:
    """Загружает имена из dictionary.tsv и возвращает список (имя, номер_строки)."""
    names = []
    with open(dict_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # Пропускаем заголовок
        for i, line in enumerate(lines[1:], start=2):
            line = line.rstrip('\n\r')
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 1:
                original_name = parts[0].strip()
                if original_name:
                    names.append((original_name, i))
    return names


def load_texts_from_translation(translation_path: str) -> str:
    """Загружает все тексты из translation_en.tsv и объединяет в одну строку для поиска."""
    all_text_parts = []
    id_pattern = re.compile(r'^[0-9a-f]{16}$')
    
    with open(translation_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        current_entry = []
        
        for line in lines[1:]:  # Пропускаем заголовок
            line = line.rstrip('\n\r')
            if not line:
                continue
            
            # Проверяем, начинается ли строка с ID (16 hex символов)
            parts = line.split('\t', 1)
            if len(parts) >= 1 and id_pattern.match(parts[0]):
                # Новая запись - сохраняем предыдущую
                if current_entry:
                    entry_text = ' '.join(current_entry)
                    all_text_parts.append(entry_text)
                # Начинаем новую запись
                if len(parts) >= 2:
                    current_entry = [parts[1]]
                else:
                    current_entry = []
            else:
                # Продолжение предыдущей записи
                if current_entry:
                    current_entry.append(line)
        
        # Сохраняем последнюю запись
        if current_entry:
            entry_text = ' '.join(current_entry)
            all_text_parts.append(entry_text)
    
    # Объединяем все тексты в одну строку для более эффективного поиска
    return ' '.join(all_text_parts)


def count_mentions(name: str, all_text: str) -> int:
    """
    Подсчитывает количество упоминаний имени в тексте.
    Использует поиск с учетом границ слов, чтобы не находить части слов.
    Учитывает апострофы и дефисы как часть имени.
    """
    # Быстрая проверка - если имя не найдено в тексте вообще, возвращаем 0
    if name.lower() not in all_text.lower():
        return 0
    
    # Экранируем специальные символы для regex
    escaped_name = re.escape(name)
    
    # Создаем паттерн, который ищет имя как отдельное слово
    # Учитываем, что перед и после имени могут быть:
    # - границы слов (\b)
    # - апострофы (для случаев типа "Sun Mengliang's")
    # - дефисы (для составных имен)
    # Используем негативный lookbehind и lookahead для более точного поиска
    # Ищем имя, которое не является частью другого слова
    
    # Если имя содержит апостроф или дефис, используем более гибкий паттерн
    if "'" in name or "-" in name:
        # Для имен с апострофами/дефисами ищем точное совпадение с границами
        # но разрешаем апострофы и дефисы как часть имени
        pattern = r'(?<![A-Za-z])' + escaped_name + r'(?![A-Za-z])'
    else:
        # Для обычных имен используем стандартные границы слов
        pattern = r'\b' + escaped_name + r'\b'
    
    # Находим все вхождения (без учета регистра)
    matches = re.findall(pattern, all_text, re.IGNORECASE)
    return len(matches)


def update_dictionary_with_counts(dict_path: str, name_counts: dict[str, int], name_lines: dict[str, int]) -> None:
    """Обновляет dictionary.tsv, добавляя количество упоминаний в третий столбец."""
    # Читаем все строки
    with open(dict_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Обновляем строки
    updated_lines = []
    for i, line in enumerate(lines):
        line = line.rstrip('\n\r')
        if i == 0:
            # Заголовок - проверяем, есть ли уже третий столбец
            parts = line.split('\t')
            if len(parts) < 3 or not parts[2].strip():
                # Добавляем или обновляем заголовок третьего столбца
                if len(parts) >= 2:
                    updated_lines.append(f"{parts[0]}\t{parts[1]}\tУпоминания\n")
                else:
                    updated_lines.append(f"{parts[0]}\t\tУпоминания\n")
            else:
                # Заголовок уже есть
                updated_lines.append(line + '\n')
        else:
            parts = line.split('\t')
            if len(parts) >= 1:
                original_name = parts[0].strip()
                # Получаем количество упоминаний
                count = name_counts.get(original_name, 0)
                
                # Формируем новую строку
                if len(parts) >= 2:
                    # Есть перевод
                    translation = parts[1]
                    # Если уже есть третий столбец, заменяем его
                    if len(parts) >= 3:
                        new_line = f"{original_name}\t{translation}\t{count}\n"
                    else:
                        new_line = f"{original_name}\t{translation}\t{count}\n"
                else:
                    # Нет перевода
                    new_line = f"{original_name}\t\t{count}\n"
                
                updated_lines.append(new_line)
            else:
                # Пустая строка или некорректная
                updated_lines.append(line + '\n')
    
    # Записываем обратно
    with open(dict_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)


def main():
    dict_path = 'docs/dictionary.tsv'
    translation_path = 'translation_en.tsv'
    
    print("📖 Загрузка имен из dictionary.tsv...")
    names_with_lines = load_names_from_dictionary(dict_path)
    print(f"   Найдено имен: {len(names_with_lines)}")
    
    print("📄 Загрузка текстов из translation_en.tsv...")
    all_text = load_texts_from_translation(translation_path)
    print(f"   Загружено текста: {len(all_text)} символов")
    
    print("🔍 Подсчет упоминаний...")
    name_counts = {}
    name_lines = {}
    found_count = 0
    total_names = len(names_with_lines)
    
    for idx, (name, line_num) in enumerate(names_with_lines, 1):
        name_lines[name] = line_num
        count = count_mentions(name, all_text)
        name_counts[name] = count
        if count > 0:
            found_count += 1
            if found_count <= 20:  # Показываем первые 20 для примера
                print(f"   {name}: {count} упоминаний", flush=True)
        
        # Показываем прогресс каждые 100 имен
        if idx % 100 == 0 or idx == total_names:
            print(f"   Обработано: {idx}/{total_names} имен ({idx*100//total_names}%)", flush=True)
    
    if found_count > 20:
        print(f"   ... и еще {found_count - 20} имен с упоминаниями")
    
    print(f"\n✅ Найдено упоминаний для {found_count} имен")
    print(f"   Всего упоминаний: {sum(name_counts.values())}")
    
    print(f"\n💾 Обновление {dict_path}...")
    update_dictionary_with_counts(dict_path, name_counts, name_lines)
    print("✅ Готово!")


if __name__ == '__main__':
    main()

