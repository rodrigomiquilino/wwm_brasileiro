import re
import os
import struct
import pyzstd
import sys
import csv
import configparser
import random
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QFileDialog, QLabel, QGroupBox, QGridLayout, QMessageBox, QComboBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal

def extract_file(input_file, output_dir, log_callback):
    try:
        base_name = os.path.splitext(os.path.basename(input_file))[0]

        with open(input_file, 'rb') as f:
            if f.read(4) != b'\xEF\xBE\xAD\xDE':
                return False

            f.read(4)
            offset_count_bytes = f.read(4)
            offset_count = struct.unpack('<I', offset_count_bytes)[0] + 1

            if offset_count == 1:
                comp_block_len = struct.unpack('<I', f.read(4))[0]
                comp_block = f.read(comp_block_len)

                if len(comp_block) < comp_block_len:
                    return False

                header = comp_block[:9]
                comp_data_part = comp_block[9:]

                if len(header) < 9:
                    return False
                    
                comp_type, comp_size, decomp_size = struct.unpack('<BII', header)

                if comp_type == 0x04:
                    try:
                        decomp_data = pyzstd.decompress(comp_data_part)
                        output_path = os.path.join(output_subdir, f"{base_name}_0.dat")
                        with open(output_path, 'wb') as out_f:
                            out_f.write(decomp_data)
                        log_callback(f"{base_name}_0.dat {comp_block_len} {decomp_size}")
                    except Exception:
                        pass
            else:
                offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(offset_count)]
                data_start = f.tell()
                for i in range(offset_count):
                    current_offset = offsets[i]
                    if i == (offset_count - 1):
                       continue
                    else:
                        next_offset = offsets[i + 1]
                    block_len = next_offset - current_offset

                    f.seek(data_start + current_offset)
                    comp_block = f.read(block_len)

                    if len(comp_block) < block_len:
                        continue

                    if len(comp_block) < 9:
                        continue

                    header = comp_block[:9]
                    comp_data_part = comp_block[9:]
                    comp_type, comp_size, decomp_size = struct.unpack('<BII', header)
                    if comp_type == 0x04:
                        try:
                            decomp_data = pyzstd.decompress(comp_data_part)
                            output_path = os.path.join(output_dir, f"{base_name}_{i}.dat")
                            with open(output_path, 'wb') as out_f:
                                out_f.write(decomp_data)
                            log_callback(f"{os.path.basename(output_path)} {current_offset} {decomp_size}")
                        except Exception:
                            pass

            return True

    except Exception:
        return False

def pak_file(input_file, output_dir, log_callback):
    try:
        files = [f for f in os.listdir(input_file) if f.endswith('.dat')]
    
        def extract_number(filename):
            match = re.search(r'(\d+)\.dat$', filename)
            return int(match.group(1)) if match else float('inf')
        files.sort(key=extract_number)
    
        output_file = os.path.join(output_dir, "output_file_for_game.bin")
        with open(output_file, 'wb') as outfile:
            outfile.write(b'\xEF\xBE\xAD\xDE\x01\x00\x00\x00')
            count_files = struct.pack('<I', len(files))
            outfile.write(count_files)
            archive = b''
            for filename in files:
                file_path = os.path.join(input_file, filename)
                file_size = os.path.getsize(file_path)
                with open(file_path, 'rb') as infile:
                    comp_data = pyzstd.compress(infile.read())
                    header = struct.pack('<BII', 4, len(comp_data), file_size)
                    len_arch = struct.pack('<I', len(archive))
                    outfile.write(len_arch)
                    archive += header + comp_data
                log_callback(f"Обработан: {filename}")
                
            len_arch = struct.pack('<I', len(archive))
            outfile.write(len_arch)
            outfile.write(archive)
    
        log_callback(f"✅ Сборка завершена. Файл сохранен как: {output_file}")
    except Exception as e:
        log_callback(f"❌ Ошибка сборки файла: {str(e)}")

def extract_text(input_path, output_dir, log_callback):
    try:
        if os.path.isdir(input_path):
            y = 0
            k = 0
            for filename in os.listdir(input_path):
                if filename.endswith('.dat'):
                    full_path = os.path.join(input_path, filename)
                    if os.path.isfile(full_path):
                        base_name = os.path.splitext(os.path.basename(full_path))[0]
                        with open(full_path, 'rb') as f:
                            f.seek(16)
                            code = b''
                            if f.read(4) == b'\xDC\x96\x58\x59':
                                y += 1
                                if y == 1:
                                    form = 'w'
                                else:
                                    form = 'a'
                                output_path = os.path.join(output_dir, f"TextExtractor.csv")
                                file_name = os.path.basename(full_path)
                                f.seek(0)
                                count_full = struct.unpack('<I', f.read(4))[0]
                                f.read(4)
                                count_text = struct.unpack('<I', f.read(4))[0]
                                f.read(12)
                                code = f.read(count_full).hex()
                                f.read(17)
                                data_start = f.tell()
                                with open(output_path, form, newline='', encoding="utf-8") as out_f:
                                    writer = csv.writer(out_f, delimiter=';')
                                    if form == 'w':
                                        writer.writerow(['Number','File','All Blocks','Work Blocks','Current Block','Unknown','ID','OriginalText'])
                                    for i in range(count_full):
                                        f.seek(data_start + (i * 16))
                                        id = f.read(8).hex()
                                        start_text_offset = f.tell()
                                        offset_text = struct.unpack('<I', f.read(4))[0]
                                        lenght = struct.unpack('<I', f.read(4))[0]
                                        f.seek(start_text_offset + offset_text)
                                        text = f.read(lenght).decode('utf-8', errors='ignore')
                                        text = text.replace('\n', '\\n')
                                        text = text.replace('\r', '\\r')
                                        k += 1
                                        writer.writerow([str(k), file_name, count_full, count_text, str(i), code[i*2:(i+1)*2], id, text])
                                log_callback(f"Обработан - {base_name}.txt - {count_text}")
        log_callback(f"✅ Распаковка текста завершена в {output_path}")   
        return True
    except Exception as e:
        log_callback(f"❌ Ошибка распаковки: {str(e)}")
        return False

def pak_text(input_file, output_dir, log_callback):
    try:
        base_name = ''
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            k = 0
            start_unk = 0
            start_id = 0
            curr_text = 0
            all_blocks = b''
            work_blocks = b''
            filled_bytes_unk = b''
            filled_bytes_id = b''
            filled_bytes_text = b''
            for row in reader:
                if row[0] == "Number" or row[1] == 'File':
                    continue
                    
                if row[1] != base_name:
                    form = 'wb'
                    if base_name != '':
                        output_path = os.path.join(output_dir, base_name)
                        with open(output_path, form) as out_f:
                            out_f.write(all_blocks)
                            out_f.write(work_blocks)
                            out_f.write(file_bytes)
                            out_f.write(filled_bytes_unk)
                            out_f.write(filled_bytes_id)
                            out_f.write(filled_bytes_text)
                    base_name = str(row[1])
                else:
                    form = 'ab'
                    
                if form == 'wb':
                    all_blocks = struct.pack('<II', int(row[2]), 0)
                    work_blocks = struct.pack('<II', int(row[3]), 0)
                    file_bytes = b'\xDC\x96\x58\x59\x00\x00\x00\x00'
                    filled_bytes_unk = b''
                    filled_bytes_id = b''
                    filled_bytes_text = b''
                    start_unk = len(all_blocks) + len(work_blocks) + len(file_bytes)
                    start_id = start_unk + int(row[2]) + 17
                    curr_text = start_id + int(row[2]) * 16
                
                text = row[7].replace('\\n', '\x0A').encode('utf-8')
                unk_byte = bytes.fromhex(row[5])
                filled_bytes_unk += unk_byte
                start_unk += 1
                if start_unk >= int(row[2]) + 24:
                    if len(filled_bytes_unk) >= 16:
                        filled_bytes_unk += b'\xFF' + filled_bytes_unk[:16]
                    else:
                        filled_bytes_unk += b'\xFF' + filled_bytes_unk + b'\x80' * (16 - len(filled_bytes_unk))
                id_byte = bytes.fromhex(row[6])
                filled_bytes_id += id_byte
                start_id += 8
                offset_len = struct.pack('<II', (curr_text - start_id), len(text))
                filled_bytes_id += offset_len
                start_id += 8
                filled_bytes_text += text
                curr_text += len(text)
            output_path = os.path.join(output_dir, base_name)
            with open(output_path, form) as out_f:
                out_f.write(all_blocks)
                out_f.write(work_blocks)
                out_f.write(file_bytes)
                out_f.write(filled_bytes_unk)
                out_f.write(filled_bytes_id)
                out_f.write(filled_bytes_text)
        log_callback(f"✅ Запаковка завершена")            
        return True

    except Exception as e:
        log_callback(f"❌ Ошибка запаковки: {str(e)}")
        return False
                            
class WorkerThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, input_path, output_dir, func):
        super().__init__()
        self.input_path = input_path
        self.output_dir = output_dir
        self.func = func

    def run(self):
        if self.func == 1:
            extract_file(self.input_path, self.output_dir, self.log_signal.emit)
        elif self.func == 2:
            pak_file(self.input_path, self.output_dir, self.log_signal.emit)
        elif self.func == 3:
            extract_text(self.input_path, self.output_dir, self.log_signal.emit)
        elif self.func == 4:
            pak_text(self.input_path, self.output_dir, self.log_signal.emit)

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
        self.initUI()

    def initUI(self):
        # Основной вертикальный layout
        main_layout = QVBoxLayout()

        # Создаем 4 QGroupBox
        group_box_extr_files = QGroupBox(f'📦 Распаковка файлов')
        group_box_pack_files = QGroupBox(f'📦 Запаковка файлов')
        group_box_extr_texts = QGroupBox(f'📦 Распаковка текста')
        group_box_pack_texts = QGroupBox(f'📦 Запаковка текста')
        group_box_translate = QGroupBox(f'📑 Перевод по ID')

        # Создаем QPushButton's в "Распаковка файлов"
        group_layout = QGridLayout()
        group_layout.setColumnMinimumWidth(0, 250)
        group_layout.setColumnStretch(0, 0)
        group_layout.setColumnStretch(1, 1)

        buttonEF_select_file = QPushButton(f'📄 Выберите файл')
        self.labelEF_select_file = QLabel('Файл не выбран')
        self.labelEF_select_file.setWordWrap(True)
        buttonEF_select_file.clicked.connect(self.selectEF_input_file)
        group_layout.addWidget(buttonEF_select_file, 0, 0)
        group_layout.addWidget(self.labelEF_select_file, 0, 1)
        
        buttonEF_output_folder = QPushButton(f'📂 Папка сохранения')
        self.labelEF_output_folder = QLabel('Папка не выбрана')
        self.labelEF_output_folder.setWordWrap(True)
        buttonEF_output_folder.clicked.connect(self.selectEF_output_dir)
        group_layout.addWidget(buttonEF_output_folder, 1, 0)
        group_layout.addWidget(self.labelEF_output_folder, 1, 1)

        buttonEF_run = QPushButton(f'Распаковать')
        buttonEF_run.setStyleSheet("background: #2196F3; color: white; font-weight: bold;")
        buttonEF_run.clicked.connect(self.start_processing1)
        group_layout.addWidget(buttonEF_run, 2, 0, 1, 0)
        group_box_extr_files.setLayout(group_layout)

        # Создаем QPushButton's в "Запаковка файлов"
        group_layout = QGridLayout()
        group_layout.setColumnMinimumWidth(0, 250)
        group_layout.setColumnStretch(0, 0)
        group_layout.setColumnStretch(1, 1)

        buttonPF_select_folder = QPushButton(f'📂 Выберите папку')
        self.labelPF_select_folder = QLabel('Папка не выбрана')
        self.labelPF_select_folder.setWordWrap(True)
        buttonPF_select_folder.clicked.connect(self.selectPF_input_dir)
        group_layout.addWidget(buttonPF_select_folder, 0, 0)
        group_layout.addWidget(self.labelPF_select_folder, 0, 1)
        
        buttonPF_output_folder = QPushButton(f'📂 Папка сохранения')
        self.labelPF_output_folder = QLabel('Папка не выбрана')
        self.labelPF_output_folder.setWordWrap(True)
        buttonPF_output_folder.clicked.connect(self.selectPF_output_dir)
        group_layout.addWidget(buttonPF_output_folder, 1, 0)
        group_layout.addWidget(self.labelPF_output_folder, 1, 1)

        buttonPF_run = QPushButton(f'Запаковать')
        buttonPF_run.setStyleSheet("background: #4CAF50; color: white; font-weight: bold;")
        buttonPF_run.clicked.connect(self.start_processing2)
        group_layout.addWidget(buttonPF_run, 2, 0, 1, 0)
        group_box_pack_files.setLayout(group_layout)

        # Создаем QPushButton's в "Распаковка текста"
        group_layout = QGridLayout()
        group_layout.setColumnMinimumWidth(0, 250)
        group_layout.setColumnStretch(0, 0)
        group_layout.setColumnStretch(1, 1)

        buttonET_select_folder = QPushButton(f'📂 Выберите папку')
        self.labelET_select_folder = QLabel('Папка не выбрана')
        self.labelET_select_folder.setWordWrap(True)
        buttonET_select_folder.clicked.connect(self.selectET_input_dir)
        group_layout.addWidget(buttonET_select_folder, 0, 0)
        group_layout.addWidget(self.labelET_select_folder, 0, 1)
        
        buttonET_output_folder = QPushButton(f'📂 Папка сохранения')
        self.labelET_output_folder = QLabel('Папка не выбрана')
        self.labelET_output_folder.setWordWrap(True)
        buttonET_output_folder.clicked.connect(self.selectET_output_dir)
        group_layout.addWidget(buttonET_output_folder, 1, 0)
        group_layout.addWidget(self.labelET_output_folder, 1, 1)

        buttonET_run = QPushButton(f'Распаковать')
        buttonET_run.setStyleSheet("background: #2196F3; color: white; font-weight: bold;")
        buttonET_run.clicked.connect(self.start_processing3)
        group_layout.addWidget(buttonET_run, 2, 0, 1, 0)
        group_box_extr_texts.setLayout(group_layout)

        # Создаем QPushButton's в "Запаковка текста"
        group_layout = QGridLayout()
        group_layout.setColumnMinimumWidth(0, 250)
        group_layout.setColumnStretch(0, 0)
        group_layout.setColumnStretch(1, 1)

        buttonPT_select_file = QPushButton(f'📄 Выберите файл')
        self.labelPT_select_file = QLabel('Файл не выбран')
        self.labelPT_select_file.setWordWrap(True)
        buttonPT_select_file.clicked.connect(self.selectPT_input_file)
        group_layout.addWidget(buttonPT_select_file, 0, 0)
        group_layout.addWidget(self.labelPT_select_file, 0, 1)
        
        buttonPT_output_folder = QPushButton(f'📂 Папка сохранения')
        self.labelPT_output_folder = QLabel('Папка не выбрана')
        self.labelPT_output_folder.setWordWrap(True)
        buttonPT_output_folder.clicked.connect(self.selectPT_output_dir)
        group_layout.addWidget(buttonPT_output_folder, 1, 0)
        group_layout.addWidget(self.labelPT_output_folder, 1, 1)

        buttonPT_run = QPushButton(f'Запаковать')
        buttonPT_run.setStyleSheet("background: #4CAF50; color: white; font-weight: bold;")
        buttonPT_run.clicked.connect(self.start_processing4)
        group_layout.addWidget(buttonPT_run, 2, 0, 1, 0)
        group_box_pack_texts.setLayout(group_layout)

        # Создаем QPushButton's в "Перевод по ID"
        group_layout = QGridLayout()
        group_layout.setColumnMinimumWidth(0, 250)
        group_layout.setColumnStretch(0, 0)
        group_layout.setColumnStretch(1, 1)

        buttonTR_select_file = QPushButton(f'📄 Выберите TextExtractor.csv')
        self.labelTR_select_file = QLabel('Файл не выбран')
        self.labelTR_select_file.setWordWrap(True)
        buttonTR_select_file.clicked.connect(self.selectTR_input_file)
        group_layout.addWidget(buttonTR_select_file, 0, 0)
        group_layout.addWidget(self.labelTR_select_file, 0, 1)

        labelTR_format = QLabel('Формат файла перевода')
        self.comboTR_format = QComboBox()
        self.comboTR_format.addItem("CSV (; разделитель)", ";")
        self.comboTR_format.addItem("TSV (табуляция)", "\t")
        group_layout.addWidget(labelTR_format, 1, 0)
        group_layout.addWidget(self.comboTR_format, 1, 1)

        buttonTR_export = QPushButton(f'Создать CSV/TSV: ID,OriginalText')
        buttonTR_export.setStyleSheet("background: #2196F3; color: white; font-weight: bold;")
        buttonTR_export.clicked.connect(self.export_translation_csv)
        group_layout.addWidget(buttonTR_export, 2, 0, 1, 0)

        buttonTR_apply = QPushButton(f'Применить переводы из CSV/TSV')
        buttonTR_apply.setStyleSheet("background: #4CAF50; color: white; font-weight: bold;")
        buttonTR_apply.clicked.connect(self.apply_translation_csv)
        group_layout.addWidget(buttonTR_apply, 3, 0, 1, 0)

        buttonTR_debug = QPushButton(f'Создать debug TextExtractor.csv (теги)')
        buttonTR_debug.setStyleSheet("background: #FF9800; color: white; font-weight: bold;")
        buttonTR_debug.clicked.connect(self.create_debug_csv)
        group_layout.addWidget(buttonTR_debug, 4, 0, 1, 0)

        group_box_translate.setLayout(group_layout)
        
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        main_layout.addWidget(group_box_extr_files)
        main_layout.addWidget(group_box_pack_files)
        main_layout.addWidget(group_box_extr_texts)
        main_layout.addWidget(group_box_pack_texts)
        main_layout.addWidget(group_box_translate)
        main_layout.addWidget(self.log_box)

        self.setLayout(main_layout)

        self.EFinput_path = None
        self.EFoutput_dir = None
        self.ETinput_path = None
        self.EToutput_dir = None
        self.PFinput_path = None
        self.PFoutput_dir = None
        self.PTinput_path = None
        self.PToutput_dir = None
        self.TRinput_path = None

        # Загружаем сохранённые пути, если есть
        self.load_paths_config()

        self.setWindowTitle("WWM Распаковка/Запаковка файлов и текста")
        self.setGeometry(100, 100, 800, 600)
        self.show()

    def load_paths_config(self):
        """Загрузка путей из config.ini и установка лейблов, если файлы/папки существуют."""
        config = configparser.ConfigParser()
        if not os.path.isfile(self.config_path):
            return

        try:
            config.read(self.config_path, encoding="utf-8")
        except Exception:
            return

        if "paths" not in config:
            return

        paths = config["paths"]

        def _set_path(attr_name, label, key, is_dir):
            value = paths.get(key, "").strip()
            if not value:
                return
            if is_dir and not os.path.isdir(value):
                return
            if not is_dir and not os.path.isfile(value):
                return
            setattr(self, attr_name, value)
            if label is not None:
                label.setText(value)

        _set_path("EFinput_path", self.labelEF_select_file, "EFinput_path", False)
        _set_path("EFoutput_dir", self.labelEF_output_folder, "EFoutput_dir", True)
        _set_path("ETinput_path", self.labelET_select_folder, "ETinput_path", True)
        _set_path("EToutput_dir", self.labelET_output_folder, "EToutput_dir", True)
        _set_path("PFinput_path", self.labelPF_select_folder, "PFinput_path", True)
        _set_path("PFoutput_dir", self.labelPF_output_folder, "PFoutput_dir", True)
        _set_path("PTinput_path", self.labelPT_select_file, "PTinput_path", False)
        _set_path("PToutput_dir", self.labelPT_output_folder, "PToutput_dir", True)
        _set_path("TRinput_path", self.labelTR_select_file, "TRinput_path", False)

    def save_paths_config(self):
        """Сохранение текущих путей в config.ini."""
        config = configparser.ConfigParser()
        if os.path.isfile(self.config_path):
            try:
                config.read(self.config_path, encoding="utf-8")
            except Exception:
                config = configparser.ConfigParser()

        if "paths" not in config:
            config["paths"] = {}

        paths = config["paths"]
        for key in [
            "EFinput_path", "EFoutput_dir",
            "ETinput_path", "EToutput_dir",
            "PFinput_path", "PFoutput_dir",
            "PTinput_path", "PToutput_dir",
            "TRinput_path",
        ]:
            value = getattr(self, key, None)
            if value:
                paths[key] = value

        try:
            with open(self.config_path, "w", encoding="utf-8") as cfg:
                config.write(cfg)
        except Exception:
            pass

    # Функция записи в лог
    def log(self, message):
        self.log_box.append(message)

    # Функция открытия файла для распаковки файла
    def selectEF_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл для распаковки файла")
        if file_path:
            self.EFinput_path = file_path
            self.log(f"Для распаковки файла выбран файл: {file_path}")
            self.labelEF_select_file.setText(f"{file_path}")
            self.save_paths_config()
            
    # Функция открытия папки сохранения для распаковки файла
    def selectEF_output_dir(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку сохранения для распаковки файла")
        if folder_path:
            self.EFoutput_dir = folder_path
            self.log(f"Для распаковки файла выбрана папка сохранения: {folder_path}")
            self.labelEF_output_folder.setText(f"{folder_path}")
            self.save_paths_config()

    # Функция открытия папки с *.dat файлами для запаковки файла
    def selectPF_input_dir(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку с *.dat файлами для запаковки файла")
        if folder_path:
            self.PFinput_path = folder_path
            self.log(f"Для запаковки файла выбрана папка с dat: {folder_path}")
            self.labelPF_select_folder.setText(f"{folder_path}")
            self.save_paths_config()
            
    # Функция открытия папки сохранения для запаковки файла
    def selectPF_output_dir(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку сохранения для запаковки файла")
        if folder_path:
            self.PFoutput_dir = folder_path
            self.log(f"Для запаковки файла выбрана папка сохранения: {folder_path}")
            self.labelPF_output_folder.setText(f"{folder_path}")
            self.save_paths_config()
            
    # Функция открытия папки с *.dat файлами для распаковки текста
    def selectET_input_dir(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку с *.dat файлами для распаковки текста")
        if folder_path:
            self.ETinput_path = folder_path
            self.log(f"Для распаковки текста выбрана папка с *.dat: {folder_path}")
            self.labelET_select_folder.setText(f"{folder_path}")
            self.save_paths_config()
            
    # Функция открытия папки сохранения для распаковки текста
    def selectET_output_dir(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку сохранения для распаковки текста")
        if folder_path:
            self.EToutput_dir = folder_path
            self.log(f"Для распаковки текста выбрана папка сохранения: {folder_path}")
            self.labelET_output_folder.setText(f"{folder_path}")
            self.save_paths_config()

    # Функция выбора TextExtractor.csv для работы с переводом
    def selectTR_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите TextExtractor.csv", filter='*.csv')
        if file_path:
            self.TRinput_path = file_path
            self.log(f"Для перевода выбран файл: {file_path}")
            self.labelTR_select_file.setText(f"{file_path}")
            self.save_paths_config()
            
    # Функция открытия файла CSV для запаковки текста
    def selectPT_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл CSV для запаковки текста", filter='*.csv')
        if file_path:
            self.PTinput_path = file_path
            self.log(f"Для запаковки текста выбран файл: {file_path}")
            self.labelPT_select_file.setText(f"{file_path}")
            self.save_paths_config()
            
    # Функция открытия папки сохранения для запаковки текста
    def selectPT_output_dir(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку сохранения для запаковки текста")
        if folder_path:
            self.PToutput_dir = folder_path
            self.log(f"Для запаковки текста выбрана папка сохранения: {folder_path}")
            self.labelPT_output_folder.setText(f"{folder_path}")
            self.save_paths_config()

    # Создать CSV ID,OriginalText из TextExtractor.csv
    def export_translation_csv(self):
        if not self.TRinput_path:
            self.log("Пожалуйста, выберите TextExtractor.csv для экспорта перевода")
            return

        # Определяем формат (CSV или TSV) и разделитель
        sep = ";"
        default_name = "translation.csv"
        file_filter = "CSV Files (*.csv);;TSV Files (*.tsv)"
        if hasattr(self, "comboTR_format"):
            fmt_sep = self.comboTR_format.currentData()
            if fmt_sep == "\t":
                sep = "\t"
                default_name = "translation.tsv"
                file_filter = "TSV Files (*.tsv);;CSV Files (*.csv)"
            else:
                sep = ";"

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить файл для перевода (ID,OriginalText)",
            default_name,
            file_filter
        )
        if not output_path:
            return

        try:
            with open(self.TRinput_path, 'r', encoding='utf-8', newline='') as src_f:
                reader = csv.reader(src_f, delimiter=';')
                header = next(reader, None)
                if not header:
                    self.log("❌ В исходном CSV нет заголовка")
                    return

                try:
                    id_idx = header.index('ID')
                    text_idx = header.index('OriginalText')
                except ValueError:
                    self.log("❌ В исходном CSV не найдены колонки 'ID' и 'OriginalText'")
                    return

                with open(output_path, 'w', encoding='utf-8', newline='') as out_f:
                    writer = csv.writer(out_f, delimiter=sep)
                    writer.writerow(['ID', 'OriginalText'])
                    count = 0
                    for row in reader:
                        if len(row) <= max(id_idx, text_idx):
                            continue
                        text = row[text_idx]
                        if sep == '\t' and text:
                            text = text.replace('\t', ' \\t ')
                        if text and text.strip():
                            writer.writerow([row[id_idx], text])
                            count += 1

            self.log(f"✅ Создан файл перевода: {output_path} (строк: {count})")
        except Exception as e:
            self.log(f"❌ Ошибка при создании файла перевода: {str(e)}")

    # Применить переводы из CSV обратно в TextExtractor.csv
    def apply_translation_csv(self):
        if not self.TRinput_path:
            self.log("Пожалуйста, выберите TextExtractor.csv для применения перевода")
            return

        trans_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите CSV/TSV с переводом (ID,OriginalText)",
            filter='CSV/TSV Files (*.csv *.tsv)'
        )
        if not trans_path:
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить обновлённый TextExtractor.csv",
            "TextExtractor_translated.csv",
            "CSV Files (*.csv)"
        )
        if not output_path:
            return

        try:
            # Определяем разделитель в файле перевода:
            ext = os.path.splitext(trans_path)[1].lower()
            if ext == '.tsv':
                delim = '\t'
            else:
                delim = ';'

            translations = {}
            with open(trans_path, 'r', encoding='utf-8', newline='') as tf:
                reader = csv.reader(tf, delimiter=delim)
                header = next(reader, None)
                if header:
                    try:
                        id_idx = header.index('ID')
                        text_idx = header.index('OriginalText')
                    except ValueError:
                        # Если нет заголовков, считаем, что первые две колонки — ID и текст
                        id_idx = 0
                        text_idx = 1
                        # обработаем первую строку как данные
                        if len(header) > 1 and header[0].strip():
                            translations[header[0].strip()] = header[1]
                for row in reader:
                    if len(row) <= max(id_idx, text_idx):
                        continue
                    key = row[id_idx].strip()
                    if not key:
                        continue
                    text = row[text_idx]
                    # Преобразуем реальные переводчикиные переносы в \n и \r для совместимости с pak_text
                    text = text.replace('\n', '\\n').replace('\r', '\\r')
                    translations[key] = text

            if not translations:
                self.log("❌ В файле перевода не найдено ни одной строки с ID")
                return

            replaced = 0
            total = 0
            with open(self.TRinput_path, 'r', encoding='utf-8', newline='') as src_f, \
                 open(output_path, 'w', encoding='utf-8', newline='') as out_f:

                reader = csv.reader(src_f, delimiter=';')
                writer = csv.writer(out_f, delimiter=';')

                header = next(reader, None)
                if not header:
                    self.log("❌ В исходном TextExtractor.csv нет заголовка")
                    return

                writer.writerow(header)

                try:
                    id_idx_csv = header.index('ID')
                    text_idx_csv = header.index('OriginalText')
                except ValueError:
                    self.log("❌ В исходном TextExtractor.csv не найдены колонки 'ID' и 'OriginalText'")
                    return

                for row in reader:
                    if len(row) <= max(id_idx_csv, text_idx_csv):
                        writer.writerow(row)
                        continue
                    total += 1
                    key = row[id_idx_csv]
                    if key in translations:
                        row[text_idx_csv] = translations[key]
                        replaced += 1
                    writer.writerow(row)

            self.log(f"✅ Применён перевод к файлу: {output_path} (заменено строк: {replaced} из {total})")
        except Exception as e:
            self.log(f"❌ Ошибка при применении файла перевода: {str(e)}")

    # Создать debug-версию TextExtractor.csv с тегами [xxxx] в начале текста
    def create_debug_csv(self):
        if not self.TRinput_path:
            self.log("Пожалуйста, выберите TextExtractor.csv для создания debug файла")
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить debug TextExtractor.csv",
            "TextExtractor_debug.csv",
            "CSV Files (*.csv)"
        )
        if not output_path:
            return

        allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz123456789"
        used_tags = set()

        def gen_tag():
            # Генерация уникального 4-символьного тега
            while True:
                t = "".join(random.choice(allowed_chars) for _ in range(4))
                if t not in used_tags:
                    used_tags.add(t)
                    return t

        try:
            with open(self.TRinput_path, 'r', encoding='utf-8', newline='') as src_f, \
                 open(output_path, 'w', encoding='utf-8', newline='') as out_f:

                reader = csv.reader(src_f, delimiter=';')
                writer = csv.writer(out_f, delimiter=';')

                header = next(reader, None)
                if not header:
                    self.log("❌ В исходном TextExtractor.csv нет заголовка")
                    return

                writer.writerow(header)

                try:
                    text_idx = header.index('OriginalText')
                except ValueError:
                    self.log("❌ В исходном TextExtractor.csv не найдена колонка 'OriginalText'")
                    return

                count = 0
                for row in reader:
                    if len(row) <= text_idx:
                        writer.writerow(row)
                        continue
                    text = row[text_idx]
                    if text and text.strip():
                        tag = gen_tag()
                        row[text_idx] = f"[{tag}]{text}"
                        count += 1
                    writer.writerow(row)

            self.log(f"✅ Создан debug файл: {output_path} (строк с тегами: {count})")
        except Exception as e:
            self.log(f"❌ Ошибка при создании debug файла: {str(e)}")
    
    # Функция запуска скрипта распаковки файла
    def start_processing1(self):
        if not self.EFinput_path:
            self.log("Пожалуйста, выберите файл для распаковки файла")
            return
        if not self.EFoutput_dir:
            self.log("Пожалуйста, выберите папку сохранения для распаковки файла")
            return

        self.worker = WorkerThread(self.EFinput_path, self.EFoutput_dir, 1)
        self.worker.log_signal.connect(self.log)
        self.worker.start()
        
    # Функция запуска скрипта запаковки файла
    def start_processing2(self):
        if not self.PFinput_path:
            self.log("Пожалуйста, выберите папку c *.dat для запаковки файла")
            return
        if not self.PFoutput_dir:
            self.log("Пожалуйста, выберите папку сохранения для запаковки файла")
            return

        self.worker = WorkerThread(self.PFinput_path, self.PFoutput_dir, 2)
        self.worker.log_signal.connect(self.log)
        self.worker.start()
        
    # Функция запуска скрипта распаковки текста
    def start_processing3(self):
        if not self.ETinput_path:
            self.log("Пожалуйста, выберите папку c *.dat для распаковки текста")
            return
        if not self.EToutput_dir:
            self.log("Пожалуйста, выберите папку сохранения для распаковки текста")
            return

        self.worker = WorkerThread(self.ETinput_path, self.EToutput_dir, 3)
        self.worker.log_signal.connect(self.log)
        self.worker.start()
        
    # Функция запуска скрипта распаковки текста
    def start_processing4(self):
        if not self.PTinput_path:
            self.log("Пожалуйста, выберите файл CSV для запаковки текста")
            return
        if not self.PToutput_dir:
            self.log("Пожалуйста, выберите папку сохранения для запаковки текста")
            return

        self.worker = WorkerThread(self.PTinput_path, self.PToutput_dir, 4)
        self.worker.log_signal.connect(self.log)
        self.worker.start()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app_font = QFont("Verdana", 10)
    app.setFont(app_font)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())
