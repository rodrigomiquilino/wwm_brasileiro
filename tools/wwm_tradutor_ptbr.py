#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WWM Tradutor PT-BR
Ferramenta de extraÃ§Ã£o e empacotamento para traduÃ§Ã£o de Where Winds Meet

Autor: rodrigomiquilino
Projeto: https://github.com/rodrigomiquilino/wwm_brasileiro
LicenÃ§a: MIT
"""

import re
import os
import sys
import struct
import csv
import configparser
from datetime import datetime
from pathlib import Path

try:
    import pyzstd
except ImportError:
    print("Erro: pyzstd nÃ£o encontrado. Instale com: pip install pyzstd")
    sys.exit(1)

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QPushButton, QTextEdit, 
        QVBoxLayout, QHBoxLayout, QFileDialog, QLabel, QGroupBox, 
        QGridLayout, QMessageBox, QProgressBar, QTabWidget, QLineEdit,
        QComboBox, QListWidget, QListWidgetItem
    )
    from PyQt5.QtGui import QFont, QPalette, QColor
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
except ImportError:
    print("Erro: PyQt5 nÃ£o encontrado. Instale com: pip install PyQt5")
    sys.exit(1)



# CONFIGURAÃ‡ÃƒO


APP_NAME = "WWM Tradutor PT-BR"
APP_VERSION = "2.1.0"
CONFIG_FILE = "config_ptbr.ini"

GAME_FILE_SIGNATURE = b'\xEF\xBE\xAD\xDE'
TEXT_BLOCK_SIGNATURE = b'\xDC\x96\x58\x59'
OUTPUT_FOLDER = "output"



# FUNÃ‡Ã•ES DE EXTRAÃ‡ÃƒO E EMPACOTAMENTO


def get_project_root() -> Path:
    """Retorna o diretÃ³rio raiz do projeto"""
    return Path(__file__).parent.parent


def get_output_folder() -> Path:
    """Retorna a pasta output do projeto"""
    return get_project_root() / OUTPUT_FOLDER


def create_session_folder() -> Path:
    """Cria uma pasta de sessÃ£o com timestamp"""
    timestamp = datetime.now().strftime("%d%m%Y%H%M%S")
    session_path = get_output_folder() / timestamp
    
    # Cria subpastas
    (session_path / "dat").mkdir(parents=True, exist_ok=True)
    (session_path / "tsv").mkdir(parents=True, exist_ok=True)
    (session_path / "bin").mkdir(parents=True, exist_ok=True)
    
    return session_path


def list_existing_sessions() -> list:
    """Lista sessÃµes existentes na pasta output"""
    output_folder = get_output_folder()
    sessions = []
    
    if output_folder.exists():
        for item in output_folder.iterdir():
            if item.is_dir() and (item / "dat").exists():
                sessions.append(item.name)
    
    return sorted(sessions, reverse=True)  # Mais recente primeiro


def extract_game_file(input_file: str, output_dir: str, log_callback=None) -> bool:
    """
    Extrai um arquivo binÃ¡rio do jogo para mÃºltiplos arquivos .dat
    Suporta arquivos normais e arquivos _diff
    """
    try:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        
        with open(input_file, 'rb') as f:
            # Verifica assinatura do arquivo
            if f.read(4) != GAME_FILE_SIGNATURE:
                if log_callback:
                    log_callback(f"âŒ Arquivo invÃ¡lido: assinatura nÃ£o reconhecida")
                return False
            
            f.read(4)  # Pula 4 bytes
            offset_count = struct.unpack('<I', f.read(4))[0] + 1
            
            if offset_count == 1:
                # Arquivo com bloco Ãºnico
                comp_block_len = struct.unpack('<I', f.read(4))[0]
                comp_block = f.read(comp_block_len)
                
                if len(comp_block) < 9:
                    return False
                
                header = comp_block[:9]
                comp_data = comp_block[9:]
                comp_type, comp_size, decomp_size = struct.unpack('<BII', header)
                
                if comp_type == 0x04:
                    try:
                        decomp_data = pyzstd.decompress(comp_data)
                        output_path = os.path.join(output_dir, f"{base_name}_0.dat")
                        with open(output_path, 'wb') as out_f:
                            out_f.write(decomp_data)
                        if log_callback:
                            log_callback(f"âœ… {base_name}_0.dat ({decomp_size} bytes)")
                    except Exception as e:
                        if log_callback:
                            log_callback(f"âŒ Erro ao descompactar: {e}")
                        return False
            else:
                # Arquivo com mÃºltiplos blocos
                offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(offset_count)]
                data_start = f.tell()
                
                # Calcula o tamanho total dos dados disponÃ­veis
                file_size = os.path.getsize(input_file)
                data_available = file_size - data_start
                
                extracted_count = 0
                for i in range(offset_count - 1):
                    current_offset = offsets[i]
                    next_offset = offsets[i + 1]
                    block_len = next_offset - current_offset
                    
                    # Verifica se block_len Ã© vÃ¡lido (proteÃ§Ã£o para arquivos _diff)
                    if block_len <= 0:
                        # Tenta calcular o tamanho restante
                        block_len = data_available - current_offset
                        if block_len <= 0:
                            continue
                    
                    f.seek(data_start + current_offset)
                    comp_block = f.read(block_len)
                    
                    if len(comp_block) < 9:
                        continue
                    
                    header = comp_block[:9]
                    comp_data = comp_block[9:]
                    comp_type, comp_size, decomp_size = struct.unpack('<BII', header)
                    
                    if comp_type == 0x04:
                        try:
                            decomp_data = pyzstd.decompress(comp_data)
                            output_path = os.path.join(output_dir, f"{base_name}_{i}.dat")
                            with open(output_path, 'wb') as out_f:
                                out_f.write(decomp_data)
                            extracted_count += 1
                            if log_callback and extracted_count % 100 == 0:
                                log_callback(f"ðŸ“¦ ExtraÃ­dos {extracted_count} arquivos...")
                        except Exception:
                            pass
                
                if log_callback:
                    log_callback(f"âœ… ExtraÃ§Ã£o completa: {extracted_count} arquivos .dat")
            
            return True
    
    except Exception as e:
        if log_callback:
            log_callback(f"âŒ Erro na extraÃ§Ã£o: {str(e)}")
        return False


def extract_texts_to_tsv(input_dir: str, output_file: str, log_callback=None) -> bool:
    """
    Extrai textos dos arquivos .dat para um arquivo TSV
    Formato: ID + OriginalText (igual ao translation_en.tsv)
    O mapeamento interno completo Ã© salvo em arquivo separado (.map) com todos os dados necessÃ¡rios
    """
    try:
        text_files_count = 0
        total_strings = 0
        
        # Arquivo de mapeamento (interno, para empacotar de volta)
        map_file = output_file.replace('.tsv', '.map')
        
        with open(output_file, 'w', newline='', encoding='utf-8') as out_f, \
             open(map_file, 'w', newline='', encoding='utf-8') as map_f:
            
            # TSV simples: apenas ID e OriginalText
            writer = csv.writer(out_f, delimiter='\t')
            writer.writerow(['ID', 'OriginalText'])
            
            # Mapeamento interno completo (igual ao CSV russo)
            # File, AllBlocks, WorkBlocks, Block, Unknown, ID
            map_writer = csv.writer(map_f, delimiter='\t')
            map_writer.writerow(['File', 'AllBlocks', 'WorkBlocks', 'Block', 'Unknown', 'ID'])
            
            dat_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.dat')])
            
            for filename in dat_files:
                full_path = os.path.join(input_dir, filename)
                
                with open(full_path, 'rb') as f:
                    f.seek(16)
                    if f.read(4) != TEXT_BLOCK_SIGNATURE:
                        continue
                    
                    text_files_count += 1
                    f.seek(0)
                    
                    count_full = struct.unpack('<I', f.read(4))[0]
                    f.read(4)
                    count_text = struct.unpack('<I', f.read(4))[0]
                    f.read(12)
                    # LÃª os bytes "unknown" (cÃ³digos) - importante para reconstruir!
                    unknown_codes = f.read(count_full).hex()
                    f.read(17)
                    data_start = f.tell()
                    
                    for i in range(count_full):
                        f.seek(data_start + (i * 16))
                        text_id = f.read(8).hex()
                        start_text_offset = f.tell()
                        offset_text = struct.unpack('<I', f.read(4))[0]
                        length = struct.unpack('<I', f.read(4))[0]
                        
                        f.seek(start_text_offset + offset_text)
                        text = f.read(length).decode('utf-8', errors='ignore')
                        text = text.replace('\n', '\\n').replace('\r', '\\r')
                        
                        # CÃ³digo unknown deste bloco (2 caracteres hex por bloco)
                        unknown_byte = unknown_codes[i*2:(i+1)*2]
                        
                        # Escreve no TSV simples
                        writer.writerow([text_id, text])
                        # Escreve no mapeamento completo
                        map_writer.writerow([filename, str(count_full), str(count_text), str(i), unknown_byte, text_id])
                        total_strings += 1
                
                if log_callback and text_files_count % 10 == 0:
                    log_callback(f"ðŸ“ Processados {text_files_count} arquivos de texto...")
        
        if log_callback:
            log_callback(f"âœ… ExtraÃ§Ã£o completa: {total_strings} strings de {text_files_count} arquivos")
            log_callback(f"ðŸ“„ TSV para traduÃ§Ã£o: {os.path.basename(output_file)}")
            log_callback(f"ðŸ“„ Mapeamento interno: {os.path.basename(map_file)}")
        return True
    
    except Exception as e:
        if log_callback:
            log_callback(f"âŒ Erro na extraÃ§Ã£o de textos: {str(e)}")
        return False


def pack_game_file(input_dir: str, output_file: str, log_callback=None) -> bool:
    """
    Empacota arquivos .dat de volta para o formato do jogo
    """
    try:
        files = [f for f in os.listdir(input_dir) if f.endswith('.dat')]
        
        def extract_number(filename):
            match = re.search(r'(\d+)\.dat$', filename)
            return int(match.group(1)) if match else float('inf')
        
        files.sort(key=extract_number)
        
        if not files:
            if log_callback:
                log_callback("âŒ Nenhum arquivo .dat encontrado na pasta")
            return False
        
        with open(output_file, 'wb') as outfile:
            # Escreve cabeÃ§alho
            outfile.write(GAME_FILE_SIGNATURE + b'\x01\x00\x00\x00')
            outfile.write(struct.pack('<I', len(files)))
            
            archive = b''
            for i, filename in enumerate(files):
                file_path = os.path.join(input_dir, filename)
                file_size = os.path.getsize(file_path)
                
                with open(file_path, 'rb') as infile:
                    comp_data = pyzstd.compress(infile.read())
                    header = struct.pack('<BII', 4, len(comp_data), file_size)
                    outfile.write(struct.pack('<I', len(archive)))
                    archive += header + comp_data
                
                if log_callback and (i + 1) % 100 == 0:
                    log_callback(f"ðŸ“¦ Empacotados {i + 1}/{len(files)} arquivos...")
            
            outfile.write(struct.pack('<I', len(archive)))
            outfile.write(archive)
        
        if log_callback:
            log_callback(f"âœ… Empacotamento completo: {output_file}")
        return True
    
    except Exception as e:
        if log_callback:
            log_callback(f"âŒ Erro no empacotamento: {str(e)}")
        return False


def pack_texts_to_dat(tsv_file: str, dat_dir: str, log_callback=None) -> bool:
    """
    Empacota textos traduzidos de volta nos arquivos .dat
    ReconstrÃ³i os arquivos .dat do zero usando o mapeamento completo
    """
    try:
        # Arquivo de mapeamento
        map_file = tsv_file.replace('.tsv', '.map')
        
        if not os.path.exists(map_file):
            if log_callback:
                log_callback(f"âŒ Arquivo de mapeamento nÃ£o encontrado: {map_file}")
            return False
        
        # Carrega traduÃ§Ãµes do TSV (ID -> texto)
        translations = {}
        with open(tsv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader, None)  # Pula header
            for row in reader:
                if len(row) >= 2:
                    text_id = row[0]
                    text = row[1]
                    translations[text_id] = text
        
        if log_callback:
            log_callback(f"ðŸ“š Carregadas {len(translations)} traduÃ§Ãµes")
        
        # Carrega mapeamento e agrupa por arquivo
        # Formato: File, AllBlocks, WorkBlocks, Block, Unknown, ID
        file_data = {}  # filename -> lista de (block, unknown, id, text)
        
        with open(map_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader, None)  # Pula header
            for row in reader:
                if len(row) >= 6:
                    filename = row[0]
                    all_blocks = int(row[1])
                    work_blocks = int(row[2])
                    block = int(row[3])
                    unknown = row[4]
                    text_id = row[5]
                    
                    # Pega texto traduzido ou original
                    text = translations.get(text_id, '')
                    
                    if filename not in file_data:
                        file_data[filename] = {
                            'all_blocks': all_blocks,
                            'work_blocks': work_blocks,
                            'entries': []
                        }
                    file_data[filename]['entries'].append({
                        'block': block,
                        'unknown': unknown,
                        'id': text_id,
                        'text': text
                    })
        
        if log_callback:
            log_callback(f"ðŸ“š Carregado mapeamento para {len(file_data)} arquivos")
        
        # ReconstrÃ³i cada arquivo .dat
        processed = 0
        for filename, data in file_data.items():
            output_path = os.path.join(dat_dir, filename)
            
            all_blocks = data['all_blocks']
            work_blocks = data['work_blocks']
            entries = sorted(data['entries'], key=lambda x: x['block'])
            
            # ConstrÃ³i o arquivo .dat do zero (igual ao script russo pak_text)
            # Header: all_blocks(4) + 0(4) + work_blocks(4) + 0(4) + signature(4) + 0(4)
            all_blocks_bytes = struct.pack('<II', all_blocks, 0)
            work_blocks_bytes = struct.pack('<II', work_blocks, 0)
            file_bytes = TEXT_BLOCK_SIGNATURE + b'\x00\x00\x00\x00'
            
            # Bytes unknown (cÃ³digos)
            filled_bytes_unk = b''
            # Bytes ID + offset + length
            filled_bytes_id = b''
            # Bytes texto
            filled_bytes_text = b''
            
            # Calcula posiÃ§Ãµes iniciais
            start_unk = len(all_blocks_bytes) + len(work_blocks_bytes) + len(file_bytes)
            start_id = start_unk + all_blocks + 17
            curr_text = start_id + all_blocks * 16
            
            for i, entry in enumerate(entries):
                # Converte texto
                text = entry['text'].replace('\\n', '\n').replace('\\r', '\r').encode('utf-8')
                
                # Unknown byte
                unk_byte = bytes.fromhex(entry['unknown']) if entry['unknown'] else b'\x00'
                filled_bytes_unk += unk_byte
                
                # ID bytes (8 bytes)
                id_bytes = bytes.fromhex(entry['id'])
                filled_bytes_id += id_bytes
                
                # Offset e length (cada um 4 bytes)
                # Offset Ã© relativo Ã  posiÃ§Ã£o atual do ID (apÃ³s os 8 bytes do ID)
                current_id_pos = start_id + (i * 16) + 8
                offset = curr_text - current_id_pos
                filled_bytes_id += struct.pack('<II', offset, len(text))
                
                # Texto
                filled_bytes_text += text
                curr_text += len(text)
            
            # Adiciona padding apÃ³s os unknown bytes (17 bytes extras)
            # O formato original tem: unknown_codes + \xFF + primeiros 16 bytes dos unknown_codes (ou padding)
            if len(filled_bytes_unk) >= 16:
                padding = b'\xFF' + filled_bytes_unk[:16]
            else:
                padding = b'\xFF' + filled_bytes_unk + b'\x80' * (16 - len(filled_bytes_unk))
            filled_bytes_unk += padding
            
            # Escreve arquivo completo
            with open(output_path, 'wb') as f:
                f.write(all_blocks_bytes)
                f.write(work_blocks_bytes)
                f.write(file_bytes)
                f.write(filled_bytes_unk)
                f.write(filled_bytes_id)
                f.write(filled_bytes_text)
            
            processed += 1
            if log_callback and processed % 50 == 0:
                log_callback(f"ðŸ“¦ Processados {processed} arquivos...")
        
        if log_callback:
            log_callback(f"âœ… Empacotamento de textos completo: {processed} arquivos reconstruÃ­dos")
        return True
    
    except Exception as e:
        if log_callback:
            log_callback(f"âŒ Erro ao empacotar textos: {str(e)}")
        import traceback
        traceback.print_exc()
        return False






class WorkerThread(QThread):
    """Thread para executar operaÃ§Ãµes em background"""
    
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
        self.result_data = None
    
    def run(self):
        try:
            result = self.task_func(*self.args, log_callback=self.log, **self.kwargs)
            self.finished_signal.emit(result, "")
        except Exception as e:
            self.log(f"âŒ Erro: {str(e)}")
            self.finished_signal.emit(False, str(e))
    
    def log(self, message):
        self.log_signal.emit(message)



# INTERFACE GRÃFICA


class WWMTradutorGUI(QMainWindow):
    """Janela principal do WWM Tradutor PT-BR"""
    
    def __init__(self):
        super().__init__()
        self.config = configparser.ConfigParser()
        self.load_config()
        self.current_session = None
        self.init_ui()
    
    def init_ui(self):
        """Inicializa a interface grÃ¡fica"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # TÃ­tulo
        title_label = QLabel(f"ðŸŽ® {APP_NAME}")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Ferramenta de traduÃ§Ã£o EN â†’ PT-BR para Where Winds Meet")
        subtitle_label.setFont(QFont("Segoe UI", 10))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        main_layout.addWidget(subtitle_label)
        
        # Abas (apenas 2)
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 10))
        main_layout.addWidget(self.tabs)
        
        # Aba 1: Extrair (bin â†’ dat â†’ tsv)
        self.tabs.addTab(self.create_extract_tab(), "ðŸ“¦ 1. Extrair do Jogo")
        
        # Aba 2: Empacotar (tsv â†’ dat â†’ bin)
        self.tabs.addTab(self.create_pack_tab(), "ðŸ“¦ 2. Empacotar para o Jogo")
        
        # Log
        log_group = QGroupBox("ðŸ“‹ Log de OperaÃ§Ãµes")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMinimumHeight(150)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        # BotÃµes do log
        log_btn_layout = QHBoxLayout()
        clear_btn = QPushButton("ðŸ—‘ï¸ Limpar Log")
        clear_btn.clicked.connect(lambda: self.log_text.clear())
        log_btn_layout.addWidget(clear_btn)
        
        open_output_btn = QPushButton("ðŸ“‚ Abrir Pasta Output")
        open_output_btn.clicked.connect(self.open_output_folder)
        log_btn_layout.addWidget(open_output_btn)
        
        log_layout.addLayout(log_btn_layout)
        main_layout.addWidget(log_group)
        
        # Barra de status
        self.statusBar().showMessage("Pronto")
        
        # Log inicial
        self.log(f"ðŸš€ {APP_NAME} v{APP_VERSION} iniciado")
        self.log(f"ðŸ“ Pasta do projeto: {get_project_root()}")
        self.log(f"ðŸ“ Pasta output: {get_output_folder()}")
    
    def create_extract_tab(self) -> QWidget:
        """Cria aba de extraÃ§Ã£o (bin â†’ dat â†’ tsv)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # InformaÃ§Ãµes
        info_label = QLabel("""
        <h3>ðŸ“¦ Extrair Arquivos do Jogo</h3>
        <p>Este processo irÃ¡:</p>
        <ol>
            <li>Extrair o arquivo <b>.bin</b> do jogo para arquivos <b>.dat</b></li>
            <li>Extrair os textos dos <b>.dat</b> para um arquivo <b>.tsv</b> editÃ¡vel</li>
        </ol>
        <p>Uma nova pasta serÃ¡ criada em <code>output/</code> com a data e hora atual.</p>
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Grupo: Selecionar arquivo do jogo
        file_group = QGroupBox("ðŸ“„ Arquivo do Jogo (.bin)")
        file_layout = QVBoxLayout(file_group)
        
        file_row = QHBoxLayout()
        self.extract_file_edit = QLineEdit()
        self.extract_file_edit.setPlaceholderText("Selecione o arquivo .bin do jogo...")
        self.extract_file_edit.setMinimumHeight(35)
        file_row.addWidget(self.extract_file_edit)
        
        browse_btn = QPushButton("ðŸ“‚ Procurar")
        browse_btn.setMinimumHeight(35)
        browse_btn.clicked.connect(self.browse_game_file)
        file_row.addWidget(browse_btn)
        
        file_layout.addLayout(file_row)
        layout.addWidget(file_group)
        
        # BotÃ£o de execuÃ§Ã£o
        extract_btn = QPushButton("ðŸš€ EXTRAIR TUDO")
        extract_btn.setMinimumHeight(50)
        extract_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        extract_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #006CBD;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
        """)
        extract_btn.clicked.connect(self.run_full_extract)
        layout.addWidget(extract_btn)
        
        layout.addStretch()
        return widget
    
    def create_pack_tab(self) -> QWidget:
        """Cria aba de empacotamento (tsv â†’ dat â†’ bin)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # InformaÃ§Ãµes
        info_label = QLabel("""
        <h3>ðŸ“¦ Empacotar de Volta para o Jogo</h3>
        <p>Este processo irÃ¡:</p>
        <ol>
            <li>Ler o arquivo <b>.tsv</b> com suas traduÃ§Ãµes</li>
            <li>Atualizar os arquivos <b>.dat</b> com os textos traduzidos</li>
            <li>Criar o arquivo <b>.bin</b> final para substituir no jogo</li>
        </ol>
        <p>Selecione uma sessÃ£o existente da lista abaixo.</p>
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Grupo: Selecionar sessÃ£o
        session_group = QGroupBox("ðŸ“‚ Selecionar SessÃ£o de TraduÃ§Ã£o")
        session_layout = QVBoxLayout(session_group)
        
        # Lista de sessÃµes
        self.session_list = QListWidget()
        self.session_list.setMinimumHeight(150)
        self.session_list.itemClicked.connect(self.on_session_selected)
        session_layout.addWidget(self.session_list)
        
        # BotÃ£o atualizar lista
        refresh_btn = QPushButton("ðŸ”„ Atualizar Lista")
        refresh_btn.clicked.connect(self.refresh_session_list)
        session_layout.addWidget(refresh_btn)
        
        layout.addWidget(session_group)
        
        # Info da sessÃ£o selecionada
        self.session_info_label = QLabel("Nenhuma sessÃ£o selecionada")
        self.session_info_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(self.session_info_label)
        
        # BotÃ£o de execuÃ§Ã£o
        pack_btn = QPushButton("ðŸ“¦ EMPACOTAR TUDO")
        pack_btn.setMinimumHeight(50)
        pack_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        pack_btn.setStyleSheet("""
            QPushButton {
                background-color: #107C10;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0E6B0E;
            }
            QPushButton:pressed {
                background-color: #0C5A0C;
            }
        """)
        pack_btn.clicked.connect(self.run_full_pack)
        layout.addWidget(pack_btn)
        
        layout.addStretch()
        
        # Carregar lista de sessÃµes
        self.refresh_session_list()
        
        return widget
    
    
    # MÃ‰TODOS AUXILIARES
    
    
    def log(self, message: str):
        """Adiciona mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        QApplication.processEvents()
    
    def browse_game_file(self):
        """Abre diÃ¡logo para selecionar arquivo do jogo"""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Selecionar Arquivo do Jogo", 
            "", 
            "Arquivos do jogo (*.bin);;Todos (*.*)"
        )
        if path:
            self.extract_file_edit.setText(path)
    
    def open_output_folder(self):
        """Abre a pasta output no explorador"""
        output_path = get_output_folder()
        output_path.mkdir(parents=True, exist_ok=True)
        os.startfile(str(output_path))
    
    def refresh_session_list(self):
        """Atualiza a lista de sessÃµes"""
        self.session_list.clear()
        sessions = list_existing_sessions()
        
        for session in sessions:
            session_path = get_output_folder() / session
            
            # Contar arquivos
            dat_count = len(list((session_path / "dat").glob("*.dat"))) if (session_path / "dat").exists() else 0
            tsv_count = len(list((session_path / "tsv").glob("*.tsv"))) if (session_path / "tsv").exists() else 0
            # Conta arquivos na pasta bin (sem extensÃ£o)
            bin_count = len([f for f in (session_path / "bin").iterdir() if f.is_file()]) if (session_path / "bin").exists() else 0
            
            # Formatar data
            try:
                dt = datetime.strptime(session, "%d%m%Y%H%M%S")
                date_str = dt.strftime("%d/%m/%Y %H:%M:%S")
            except:
                date_str = session
            
            item_text = f"ðŸ“ {session} ({date_str})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, session)
            self.session_list.addItem(item)
        
        if not sessions:
            self.session_list.addItem("Nenhuma sessÃ£o encontrada")
    
    def on_session_selected(self, item):
        """Callback quando uma sessÃ£o Ã© selecionada"""
        session = item.data(Qt.UserRole)
        if not session:
            return
        
        self.current_session = session
        session_path = get_output_folder() / session
        
        # Contar arquivos
        dat_count = len(list((session_path / "dat").glob("*.dat"))) if (session_path / "dat").exists() else 0
        tsv_files = list((session_path / "tsv").glob("*.tsv")) if (session_path / "tsv").exists() else []
        # Conta arquivos na pasta bin (sem extensÃ£o)
        bin_count = len([f for f in (session_path / "bin").iterdir() if f.is_file()]) if (session_path / "bin").exists() else 0
        
        info = f"""
        <b>SessÃ£o:</b> {session}<br>
        <b>Arquivos .dat:</b> {dat_count}<br>
        <b>Arquivos .tsv:</b> {len(tsv_files)}<br>
        <b>Arquivos .bin:</b> {bin_count}<br>
        <b>Caminho:</b> <code>{session_path}</code>
        """
        self.session_info_label.setText(info)
    
    def load_config(self):
        """Carrega configuraÃ§Ãµes do arquivo"""
        config_path = Path(__file__).parent / CONFIG_FILE
        if config_path.exists():
            self.config.read(config_path, encoding='utf-8')
    
    def save_config(self):
        """Salva configuraÃ§Ãµes no arquivo"""
        config_path = Path(__file__).parent / CONFIG_FILE
        with open(config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    
    # MÃ‰TODOS DE EXECUÃ‡ÃƒO
    
    
    def run_full_extract(self):
        """Executa extraÃ§Ã£o completa: bin â†’ dat â†’ tsv"""
        input_file = self.extract_file_edit.text()
        
        if not input_file:
            QMessageBox.warning(self, "Aviso", "Selecione o arquivo .bin do jogo!")
            return
        
        if not os.path.exists(input_file):
            QMessageBox.warning(self, "Aviso", "Arquivo nÃ£o encontrado!")
            return
        
        # Criar pasta de sessÃ£o
        session_path = create_session_folder()
        dat_folder = session_path / "dat"
        tsv_folder = session_path / "tsv"
        
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        tsv_file = tsv_folder / f"{base_name}.tsv"
        
        self.log(f"ðŸš€ Iniciando extraÃ§Ã£o completa...")
        self.log(f"ðŸ“ SessÃ£o criada: {session_path.name}")
        self.log(f"ðŸ“„ Arquivo: {input_file}")
        self.statusBar().showMessage("Extraindo...")
        
        # Desabilitar botÃµes
        self.setEnabled(False)
        
        # Etapa 1: Extrair bin â†’ dat
        self.log(f"ðŸ“¦ Etapa 1: Extraindo .bin para .dat...")
        result1 = extract_game_file(input_file, str(dat_folder), log_callback=self.log)
        
        if not result1:
            self.log("âŒ Falha na extraÃ§Ã£o dos arquivos .dat")
            self.setEnabled(True)
            self.statusBar().showMessage("Falhou!")
            return
        
        # Etapa 2: Extrair dat â†’ tsv
        self.log(f"ðŸ“ Etapa 2: Extraindo textos para .tsv...")
        result2 = extract_texts_to_tsv(str(dat_folder), str(tsv_file), log_callback=self.log)
        
        if not result2:
            self.log("âŒ Falha na extraÃ§Ã£o dos textos")
            self.setEnabled(True)
            self.statusBar().showMessage("Falhou!")
            return
        
        self.log(f"âœ… ExtraÃ§Ã£o completa!")
        self.log(f"ðŸ“ Pasta: {session_path}")
        self.log(f"ðŸ“„ TSV para traduÃ§Ã£o: {tsv_file}")
        
        self.setEnabled(True)
        self.statusBar().showMessage("ExtraÃ§Ã£o concluÃ­da!")
        
        # Atualizar lista de sessÃµes
        self.refresh_session_list()
        
        # Perguntar se quer abrir pasta
        reply = QMessageBox.question(
            self, 
            "ExtraÃ§Ã£o ConcluÃ­da", 
            f"ExtraÃ§Ã£o concluÃ­da com sucesso!\n\nDeseja abrir a pasta {session_path.name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            os.startfile(str(session_path))
    
    def run_full_pack(self):
        """Executa empacotamento completo: tsv â†’ dat â†’ bin"""
        if not self.current_session:
            QMessageBox.warning(self, "Aviso", "Selecione uma sessÃ£o da lista!")
            return
        
        session_path = get_output_folder() / self.current_session
        dat_folder = session_path / "dat"
        tsv_folder = session_path / "tsv"
        bin_folder = session_path / "bin"
        
        # Encontrar arquivo TSV
        tsv_files = list(tsv_folder.glob("*.tsv"))
        if not tsv_files:
            QMessageBox.warning(self, "Aviso", "Nenhum arquivo .tsv encontrado na sessÃ£o!")
            return
        
        tsv_file = tsv_files[0]  # Usar o primeiro TSV encontrado
        
        # Nome do arquivo de saÃ­da (sem extensÃ£o, igual ao jogo original)
        base_name = tsv_file.stem
        output_bin = bin_folder / base_name  # Sem extensÃ£o .bin
        
        self.log(f"ðŸš€ Iniciando empacotamento completo...")
        self.log(f"ðŸ“ SessÃ£o: {self.current_session}")
        self.log(f"ðŸ“„ TSV: {tsv_file.name}")
        self.statusBar().showMessage("Empacotando...")
        
        # Desabilitar botÃµes
        self.setEnabled(False)
        
        # Etapa 1: Aplicar traduÃ§Ãµes do TSV nos DAT
        self.log(f"ðŸ“ Etapa 1: Aplicando traduÃ§Ãµes nos .dat...")
        result1 = pack_texts_to_dat(str(tsv_file), str(dat_folder), log_callback=self.log)
        
        if not result1:
            self.log("âŒ Falha ao aplicar traduÃ§Ãµes")
            self.setEnabled(True)
            self.statusBar().showMessage("Falhou!")
            return
        
        # Etapa 2: Empacotar dat â†’ bin
        self.log(f"ðŸ“¦ Etapa 2: Empacotando .dat para .bin...")
        result2 = pack_game_file(str(dat_folder), str(output_bin), log_callback=self.log)
        
        if not result2:
            self.log("âŒ Falha no empacotamento")
            self.setEnabled(True)
            self.statusBar().showMessage("Falhou!")
            return
        
        self.log(f"âœ… Empacotamento completo!")
        self.log(f"ðŸ“¦ Arquivo para o jogo: {output_bin}")
        
        self.setEnabled(True)
        self.statusBar().showMessage("Empacotamento concluÃ­do!")
        
        # Atualizar lista de sessÃµes
        self.refresh_session_list()
        
        # Perguntar se quer abrir pasta
        reply = QMessageBox.question(
            self, 
            "Empacotamento ConcluÃ­do", 
            f"Empacotamento concluÃ­do com sucesso!\n\nArquivo criado: {output_bin.name}\n\nDeseja abrir a pasta bin?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            os.startfile(str(bin_folder))






def main():
    """FunÃ§Ã£o principal"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Paleta de cores moderna
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(250, 250, 250))
    palette.setColor(QPalette.WindowText, QColor(33, 33, 33))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(33, 33, 33))
    palette.setColor(QPalette.Text, QColor(33, 33, 33))
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, QColor(33, 33, 33))
    palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    window = WWMTradutorGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
