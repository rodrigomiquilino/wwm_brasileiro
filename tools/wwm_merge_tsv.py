#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WWM Merge TSV - Mesclador de Traduções
Ferramenta para mesclar arquivos TSV de tradução após atualizações do jogo

Autor: rodrigomiquilino
Projeto: https://github.com/rodrigomiquilino/wwm_brasileiro
Licença: MIT

IMPORTANTE: Este script mantém compatibilidade total com wwm_tradutor_ptbr.py
- Formato TSV: ID<tab>Texto (2 colunas, igual ao extraído)
- O arquivo .map NÃO é modificado (deve usar o .map do arquivo NOVO)

Uso:
    python wwm_merge_tsv.py --old traducao_antiga.tsv --new original_novo.tsv --output mesclado.tsv

Fluxo de trabalho após atualização do jogo:
    1. Extrair arquivos do jogo atualizado (gera novo.tsv + novo.map)
    2. Mesclar: traducao_atual.tsv + novo.tsv = mesclado.tsv
    3. Traduzir strings faltantes no mesclado.tsv
    4. Empacotar usando mesclado.tsv + novo.map (o .map do arquivo NOVO!)
"""

import os
import sys
import csv
import argparse
from datetime import datetime
from pathlib import Path
from collections import OrderedDict

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QPushButton, QTextEdit,
        QVBoxLayout, QHBoxLayout, QFileDialog, QLabel, QGroupBox,
        QGridLayout, QMessageBox, QProgressBar, QCheckBox, QLineEdit
    )
    from PyQt5.QtGui import QFont, QPalette, QColor
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    HAS_GUI = True
except ImportError:
    HAS_GUI = False


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

APP_NAME = "WWM Merge TSV"
APP_VERSION = "1.1.0"


# ============================================================================
# FUNÇÕES DE MERGE
# ============================================================================

def load_tsv_simple(filepath: str, log_callback=None) -> OrderedDict:
    """
    Carrega um arquivo TSV no formato do wwm_tradutor_ptbr.py
    Formato: ID<tab>Texto (2 colunas)
    
    Retorna: OrderedDict {id: texto} mantendo a ordem original
    """
    data = OrderedDict()
    
    if not os.path.exists(filepath):
        if log_callback:
            log_callback(f"❌ Arquivo não encontrado: {filepath}")
        return data
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            header = next(reader, None)
            
            if not header:
                if log_callback:
                    log_callback(f"❌ Arquivo vazio: {filepath}")
                return data
            
            for row in reader:
                if len(row) >= 2:
                    text_id = row[0].strip()
                    text = row[1]
                    data[text_id] = text
                elif len(row) == 1:
                    # Linha só com ID (sem texto)
                    text_id = row[0].strip()
                    data[text_id] = ""
        
        if log_callback:
            log_callback(f"✓ Carregado: {os.path.basename(filepath)} ({len(data):,} strings)")
        
    except Exception as e:
        if log_callback:
            log_callback(f"❌ Erro ao carregar {filepath}: {str(e)}")
    
    return data


def merge_translations(
    old_translated: OrderedDict,
    new_original: OrderedDict,
    log_callback=None
) -> tuple:
    """
    Mescla traduções antigas com o arquivo original novo.
    
    LÓGICA SIMPLES:
    - Usa a ORDEM e ESTRUTURA do arquivo NOVO (original atualizado)
    - Para cada ID do novo:
      - Se existe no antigo traduzido → usa o texto traduzido
      - Se não existe → mantém o texto original (precisa traduzir)
    
    Args:
        old_translated: Dict com traduções existentes {id: texto_traduzido}
        new_original: Dict com arquivo original novo {id: texto_original}
        log_callback: Função de callback para logs
    
    Returns:
        tuple: (merged_data, stats)
    """
    merged = OrderedDict()
    
    stats = {
        'total_old': len(old_translated),
        'total_new': len(new_original),
        'preserved': 0,      # Traduções reaproveitadas
        'new_strings': 0,    # Strings novas (sem tradução)
        'removed': 0,        # Strings que não existem mais
    }
    
    # IDs
    old_ids = set(old_translated.keys())
    new_ids = set(new_original.keys())
    
    # Strings removidas (estavam no antigo mas não no novo)
    stats['removed'] = len(old_ids - new_ids)
    
    # Processa na ordem do arquivo NOVO
    for text_id, original_text in new_original.items():
        if text_id in old_translated:
            # ID existe no traduzido - usa tradução existente
            translated_text = old_translated[text_id]
            
            # Se a tradução não está vazia, preserva
            if translated_text and translated_text.strip():
                merged[text_id] = translated_text
                stats['preserved'] += 1
            else:
                # Tradução vazia - usa original
                merged[text_id] = original_text
                stats['new_strings'] += 1
        else:
            # ID novo - não existe tradução, usa original
            merged[text_id] = original_text
            stats['new_strings'] += 1
    
    # Log de estatísticas
    if log_callback:
        log_callback("")
        log_callback("=" * 50)
        log_callback("📊 ESTATÍSTICAS DO MERGE")
        log_callback("=" * 50)
        log_callback(f"📁 Arquivo traduzido antigo: {stats['total_old']:,} strings")
        log_callback(f"📁 Arquivo original novo:    {stats['total_new']:,} strings")
        log_callback(f"📁 Diferença:                {stats['total_new'] - stats['total_old']:+,} strings")
        log_callback("-" * 50)
        log_callback(f"✅ Traduções preservadas:    {stats['preserved']:,}")
        log_callback(f"🆕 Strings a traduzir:       {stats['new_strings']:,}")
        log_callback(f"🗑️  Strings removidas:       {stats['removed']:,}")
        log_callback("=" * 50)
    
    return merged, stats


def save_merged_tsv(
    merged_data: OrderedDict,
    output_file: str,
    log_callback=None
) -> bool:
    """
    Salva o resultado do merge em arquivo TSV.
    Formato compatível com wwm_tradutor_ptbr.py: ID<tab>Texto (2 colunas)
    """
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['ID', 'OriginalText'])
            
            for text_id, text in merged_data.items():
                writer.writerow([text_id, text])
        
        if log_callback:
            log_callback(f"✅ Arquivo salvo: {output_file}")
            log_callback(f"   Total: {len(merged_data):,} strings")
        
        return True
        
    except Exception as e:
        if log_callback:
            log_callback(f"❌ Erro ao salvar: {str(e)}")
        return False


def save_untranslated_list(
    old_translated: OrderedDict,
    new_original: OrderedDict,
    output_file: str,
    log_callback=None
) -> bool:
    """
    Salva lista de strings que precisam ser traduzidas (novas ou sem tradução)
    """
    try:
        list_file = output_file.replace('.tsv', '_faltando.tsv')
        
        old_ids = set(old_translated.keys())
        count = 0
        
        with open(list_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['ID', 'OriginalText'])
            
            for text_id, original_text in new_original.items():
                needs_translation = False
                
                if text_id not in old_ids:
                    # String nova
                    needs_translation = True
                elif not old_translated[text_id] or not old_translated[text_id].strip():
                    # Tradução vazia
                    needs_translation = True
                
                if needs_translation:
                    writer.writerow([text_id, original_text])
                    count += 1
        
        if log_callback:
            log_callback(f"📝 Lista de faltantes: {list_file} ({count:,} strings)")
        
        return True
        
    except Exception as e:
        if log_callback:
            log_callback(f"❌ Erro ao salvar lista: {str(e)}")
        return False


def save_report(
    stats: dict,
    old_translated: OrderedDict,
    new_original: OrderedDict,
    output_file: str,
    log_callback=None
) -> bool:
    """
    Salva um relatório das mudanças
    """
    try:
        report_file = output_file.replace('.tsv', '_relatorio.txt')
        
        old_ids = set(old_translated.keys())
        new_ids = set(new_original.keys())
        
        added_ids = new_ids - old_ids
        removed_ids = old_ids - new_ids
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("WWM MERGE TSV - RELATÓRIO\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("ESTATÍSTICAS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Arquivo traduzido antigo: {stats['total_old']:,} strings\n")
            f.write(f"Arquivo original novo:    {stats['total_new']:,} strings\n")
            f.write(f"Diferença:                {stats['total_new'] - stats['total_old']:+,} strings\n\n")
            
            f.write(f"Traduções preservadas:    {stats['preserved']:,}\n")
            f.write(f"Strings a traduzir:       {stats['new_strings']:,}\n")
            f.write(f"Strings removidas:        {stats['removed']:,}\n\n")
            
            # Lista strings novas (primeiras 50)
            if added_ids:
                f.write(f"STRINGS NOVAS ({len(added_ids)} total, mostrando 50)\n")
                f.write("-" * 40 + "\n")
                for text_id in list(added_ids)[:50]:
                    text = new_original[text_id][:60].replace('\n', ' ')
                    f.write(f"{text_id}: {text}...\n")
                f.write("\n")
            
            # Lista strings removidas (primeiras 50)
            if removed_ids:
                f.write(f"STRINGS REMOVIDAS ({len(removed_ids)} total, mostrando 50)\n")
                f.write("-" * 40 + "\n")
                for text_id in list(removed_ids)[:50]:
                    text = old_translated[text_id][:60].replace('\n', ' ') if old_translated[text_id] else "(vazio)"
                    f.write(f"{text_id}: {text}...\n")
                f.write("\n")
            
            f.write("=" * 60 + "\n")
            f.write("IMPORTANTE: Use o arquivo .map do NOVO original para empacotar!\n")
            f.write("=" * 60 + "\n")
        
        if log_callback:
            log_callback(f"📄 Relatório: {report_file}")
        
        return True
        
    except Exception as e:
        if log_callback:
            log_callback(f"❌ Erro ao salvar relatório: {str(e)}")
        return False


# ============================================================================
# INTERFACE GRÁFICA
# ============================================================================

if HAS_GUI:
    class MergeThread(QThread):
        """Thread para executar o merge"""
        
        log_signal = pyqtSignal(str)
        finished_signal = pyqtSignal(bool, dict)
        
        def __init__(self, old_file, new_file, output_file, options):
            super().__init__()
            self.old_file = old_file
            self.new_file = new_file
            self.output_file = output_file
            self.options = options
        
        def run(self):
            try:
                self.log_signal.emit("🔄 Iniciando merge...")
                self.log_signal.emit("")
                
                # Carrega arquivos
                old_data = load_tsv_simple(self.old_file, self.log_signal.emit)
                new_data = load_tsv_simple(self.new_file, self.log_signal.emit)
                
                if not new_data:
                    self.log_signal.emit("❌ Arquivo novo está vazio!")
                    self.finished_signal.emit(False, {})
                    return
                
                # Executa merge
                merged_data, stats = merge_translations(
                    old_data,
                    new_data,
                    log_callback=self.log_signal.emit
                )
                
                # Salva resultado
                save_merged_tsv(merged_data, self.output_file, self.log_signal.emit)
                
                # Salva lista de faltantes
                if self.options.get('save_missing', True):
                    save_untranslated_list(old_data, new_data, self.output_file, self.log_signal.emit)
                
                # Salva relatório
                if self.options.get('save_report', True):
                    save_report(stats, old_data, new_data, self.output_file, self.log_signal.emit)
                
                self.log_signal.emit("")
                self.log_signal.emit("=" * 50)
                self.log_signal.emit("✅ MERGE CONCLUÍDO!")
                self.log_signal.emit("")
                self.log_signal.emit("⚠️  LEMBRE-SE: Para empacotar, use o arquivo .map")
                self.log_signal.emit("   do original NOVO, não do antigo!")
                self.log_signal.emit("=" * 50)
                
                self.finished_signal.emit(True, stats)
                
            except Exception as e:
                self.log_signal.emit(f"❌ Erro: {str(e)}")
                self.finished_signal.emit(False, {})
    
    
    class MergeWindow(QMainWindow):
        """Janela principal"""
        
        def __init__(self):
            super().__init__()
            self.init_ui()
        
        def init_ui(self):
            self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
            self.setMinimumSize(750, 650)
            
            central = QWidget()
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            layout.setSpacing(10)
            
            # Título
            title = QLabel(f"⚔️ {APP_NAME}")
            title.setFont(QFont("Segoe UI", 16, QFont.Bold))
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            
            subtitle = QLabel("Mescla traduções após atualizações do jogo")
            subtitle.setAlignment(Qt.AlignCenter)
            subtitle.setStyleSheet("color: #888;")
            layout.addWidget(subtitle)
            
            # Instruções
            instructions = QLabel(
                "📌 COMO USAR:\n"
                "1. Tradução Atual = seu arquivo .tsv traduzido\n"
                "2. Original Novo = .tsv extraído do jogo atualizado\n"
                "3. O resultado terá traduções antigas + textos originais novos"
            )
            instructions.setStyleSheet("background: #1a2a1a; padding: 10px; border-radius: 6px; color: #8f8;")
            layout.addWidget(instructions)
            
            # Arquivos de entrada
            input_group = QGroupBox("📂 Arquivos de Entrada")
            input_layout = QGridLayout()
            
            input_layout.addWidget(QLabel("Tradução Atual (.tsv):"), 0, 0)
            self.old_file_input = QLineEdit()
            self.old_file_input.setPlaceholderText("Arquivo TSV com suas traduções existentes...")
            input_layout.addWidget(self.old_file_input, 0, 1)
            old_btn = QPushButton("📁")
            old_btn.setFixedWidth(40)
            old_btn.clicked.connect(lambda: self.browse_file(self.old_file_input))
            input_layout.addWidget(old_btn, 0, 2)
            
            input_layout.addWidget(QLabel("Original Novo (.tsv):"), 1, 0)
            self.new_file_input = QLineEdit()
            self.new_file_input.setPlaceholderText("TSV extraído do jogo ATUALIZADO...")
            input_layout.addWidget(self.new_file_input, 1, 1)
            new_btn = QPushButton("📁")
            new_btn.setFixedWidth(40)
            new_btn.clicked.connect(lambda: self.browse_file(self.new_file_input))
            input_layout.addWidget(new_btn, 1, 2)
            
            input_group.setLayout(input_layout)
            layout.addWidget(input_group)
            
            # Arquivo de saída
            output_group = QGroupBox("💾 Arquivo de Saída")
            output_layout = QHBoxLayout()
            
            self.output_file_input = QLineEdit()
            self.output_file_input.setPlaceholderText("Nome do arquivo mesclado...")
            self.output_file_input.setText("translation_merged.tsv")
            output_layout.addWidget(self.output_file_input)
            output_btn = QPushButton("📁")
            output_btn.setFixedWidth(40)
            output_btn.clicked.connect(self.browse_output)
            output_layout.addWidget(output_btn)
            
            output_group.setLayout(output_layout)
            layout.addWidget(output_group)
            
            # Opções
            options_group = QGroupBox("⚙️ Opções")
            options_layout = QVBoxLayout()
            
            self.save_missing_cb = QCheckBox("Gerar arquivo com strings faltando (_faltando.tsv)")
            self.save_missing_cb.setChecked(True)
            options_layout.addWidget(self.save_missing_cb)
            
            self.save_report_cb = QCheckBox("Gerar relatório de mudanças (_relatorio.txt)")
            self.save_report_cb.setChecked(True)
            options_layout.addWidget(self.save_report_cb)
            
            options_group.setLayout(options_layout)
            layout.addWidget(options_group)
            
            # Botão de merge
            self.merge_btn = QPushButton("🔄 MESCLAR TRADUÇÕES")
            self.merge_btn.setFixedHeight(50)
            self.merge_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
            self.merge_btn.setStyleSheet("""
                QPushButton {
                    background: #c9a227;
                    color: #0a0a0f;
                    border: none;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background: #e6c355;
                }
                QPushButton:disabled {
                    background: #555;
                    color: #888;
                }
            """)
            self.merge_btn.clicked.connect(self.start_merge)
            layout.addWidget(self.merge_btn)
            
            # Log
            log_group = QGroupBox("📋 Log")
            log_layout = QVBoxLayout()
            
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setFont(QFont("Consolas", 9))
            log_layout.addWidget(self.log_text)
            
            log_group.setLayout(log_layout)
            layout.addWidget(log_group)
            
            # Estilo escuro
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background: #1a1a24;
                    color: #e8e6e3;
                }
                QGroupBox {
                    border: 1px solid #333;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
                QLineEdit {
                    background: #12121a;
                    border: 1px solid #333;
                    border-radius: 4px;
                    padding: 8px;
                    color: #e8e6e3;
                }
                QPushButton {
                    background: #2a2a3a;
                    border: 1px solid #444;
                    border-radius: 4px;
                    padding: 8px 12px;
                    color: #e8e6e3;
                }
                QPushButton:hover {
                    background: #3a3a4a;
                    border-color: #c9a227;
                }
                QTextEdit {
                    background: #0a0a0f;
                    border: 1px solid #333;
                    border-radius: 4px;
                    color: #e8e6e3;
                }
                QCheckBox {
                    spacing: 8px;
                }
            """)
        
        def browse_file(self, line_edit):
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Selecionar TSV", "",
                "Arquivos TSV (*.tsv);;Todos (*.*)"
            )
            if filepath:
                line_edit.setText(filepath)
        
        def browse_output(self):
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Salvar Como", "translation_merged.tsv",
                "Arquivos TSV (*.tsv)"
            )
            if filepath:
                self.output_file_input.setText(filepath)
        
        def log(self, message):
            self.log_text.append(message)
        
        def start_merge(self):
            old_file = self.old_file_input.text().strip()
            new_file = self.new_file_input.text().strip()
            output_file = self.output_file_input.text().strip()
            
            if not old_file or not new_file:
                QMessageBox.warning(self, "Aviso", "Selecione os dois arquivos de entrada!")
                return
            
            if not output_file:
                output_file = "translation_merged.tsv"
            
            self.merge_btn.setEnabled(False)
            self.log_text.clear()
            
            options = {
                'save_missing': self.save_missing_cb.isChecked(),
                'save_report': self.save_report_cb.isChecked(),
            }
            
            self.merge_thread = MergeThread(old_file, new_file, output_file, options)
            self.merge_thread.log_signal.connect(self.log)
            self.merge_thread.finished_signal.connect(self.on_finished)
            self.merge_thread.start()
        
        def on_finished(self, success, stats):
            self.merge_btn.setEnabled(True)
            
            if success:
                QMessageBox.information(
                    self, "Sucesso",
                    f"Merge concluído!\n\n"
                    f"✅ Traduções preservadas: {stats.get('preserved', 0):,}\n"
                    f"🆕 Strings a traduzir: {stats.get('new_strings', 0):,}\n"
                    f"🗑️ Removidas: {stats.get('removed', 0):,}\n\n"
                    f"⚠️ Use o .map do original NOVO para empacotar!"
                )


# ============================================================================
# LINHA DE COMANDO
# ============================================================================

def main_cli():
    parser = argparse.ArgumentParser(
        description="WWM Merge TSV - Mescla traduções com arquivo original atualizado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplo:
  python wwm_merge_tsv.py --old traducao.tsv --new original_novo.tsv --output mesclado.tsv

IMPORTANTE: Para empacotar o resultado, use o arquivo .map do NOVO, não do antigo!
        """
    )
    
    parser.add_argument('--old', '-o', required=True, help='TSV com traduções existentes')
    parser.add_argument('--new', '-n', required=True, help='TSV original do jogo atualizado')
    parser.add_argument('--output', '-out', default='translation_merged.tsv', help='Arquivo de saída')
    parser.add_argument('--no-report', action='store_true', help='Não gerar relatório')
    parser.add_argument('--gui', action='store_true', help='Abrir interface gráfica')
    
    args = parser.parse_args()
    
    if args.gui and HAS_GUI:
        app = QApplication(sys.argv)
        window = MergeWindow()
        window.show()
        sys.exit(app.exec_())
    
    print(f"\n⚔️ {APP_NAME} v{APP_VERSION}")
    print("=" * 50)
    
    old_data = load_tsv_simple(args.old, print)
    new_data = load_tsv_simple(args.new, print)
    
    if not new_data:
        print("❌ Arquivo novo está vazio!")
        sys.exit(1)
    
    merged_data, stats = merge_translations(old_data, new_data, print)
    
    save_merged_tsv(merged_data, args.output, print)
    save_untranslated_list(old_data, new_data, args.output, print)
    
    if not args.no_report:
        save_report(stats, old_data, new_data, args.output, print)
    
    print("\n✅ Processo concluído!")
    print("\n⚠️  IMPORTANTE: Para empacotar, use o arquivo .map do NOVO!")


def main():
    if len(sys.argv) == 1 and HAS_GUI:
        app = QApplication(sys.argv)
        window = MergeWindow()
        window.show()
        sys.exit(app.exec_())
    else:
        main_cli()


if __name__ == "__main__":
    main()
