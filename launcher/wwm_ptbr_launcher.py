#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WWM Tradutor PT-BR - Launcher
Instalador automático da tradução brasileira para Where Winds Meet

Autor: rodrigomiquilino
Projeto: https://github.com/rodrigomiquilino/wwm_brasileiro
Licença: MIT
"""

import os
import sys
import json
import shutil
import tempfile
import threading
import webbrowser
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests")
    import requests

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QPushButton, QLabel,
        QVBoxLayout, QHBoxLayout, QFileDialog, QProgressBar,
        QMessageBox, QFrame, QGraphicsDropShadowEffect
    )
    from PyQt5.QtGui import (
        QFont, QPalette, QColor, QLinearGradient, QPainter,
        QBrush, QPen, QPixmap, QIcon
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
except ImportError:
    os.system(f"{sys.executable} -m pip install PyQt5")
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

APP_NAME = "WWM Tradutor PT-BR"
APP_VERSION = "1.0.0"
GITHUB_REPO = "rodrigomiquilino/wwm_brasileiro"
GITHUB_API_RELEASES = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_PAGE = f"https://github.com/{GITHUB_REPO}/releases"

DEFAULT_STEAM_PATHS = [
    r"C:\Program Files (x86)\Steam\steamapps\common\Where Winds Meet",
    r"C:\Program Files\Steam\steamapps\common\Where Winds Meet",
    r"D:\Steam\steamapps\common\Where Winds Meet",
    r"D:\SteamLibrary\steamapps\common\Where Winds Meet",
    r"E:\Steam\steamapps\common\Where Winds Meet",
    r"E:\SteamLibrary\steamapps\common\Where Winds Meet",
]

GAME_EXE_RELATIVE = r"Engine\Binaries\Win64r\wwm.exe"
TRANSLATION_FILE_RELATIVE = r"Package\HD\oversea\locale\translate_words_map_en"
CONFIG_FILE = "wwm_ptbr_config.json"


# ============================================================================
# TEMA
# ============================================================================

class Theme:
    BACKGROUND_DARK = "#0a0a0f"
    BACKGROUND_MEDIUM = "#12121a"
    BACKGROUND_LIGHT = "#1a1a24"
    
    GOLD_PRIMARY = "#c9a227"
    GOLD_LIGHT = "#e6c355"
    GOLD_DARK = "#8b7019"
    
    RED_PRIMARY = "#8b2635"
    RED_LIGHT = "#a63446"
    RED_DARK = "#5c1a24"
    
    TEXT_PRIMARY = "#e8e6e3"
    TEXT_SECONDARY = "#9d9d9d"
    TEXT_MUTED = "#5a5a5a"
    
    SUCCESS = "#2e7d32"
    WARNING = "#f57c00"
    ERROR = "#c62828"
    INFO = "#1565c0"


# ============================================================================
# THREAD DE DOWNLOAD
# ============================================================================

class DownloadThread(QThread):
    """Thread para download de arquivos"""
    
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, url: str, dest_path: str):
        super().__init__()
        self.url = url
        self.dest_path = dest_path
    
    def run(self):
        try:
            self.status_signal.emit("Conectando ao servidor...")
            response = requests.get(self.url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            self.status_signal.emit("Baixando tradução...")
            
            with open(self.dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress_signal.emit(progress)
            
            self.finished_signal.emit(True, self.dest_path)
            
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class CheckUpdateThread(QThread):
    """Thread para verificar atualizações"""
    
    finished_signal = pyqtSignal(bool, str, str, str)  # success, version, download_url, message
    
    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
    
    def run(self):
        try:
            response = requests.get(GITHUB_API_RELEASES, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            latest_version = data.get('tag_name', '').lstrip('v')
            
            # Procura o arquivo de tradução nos assets
            download_url = None
            for asset in data.get('assets', []):
                if 'translate_words_map_en' in asset['name'].lower():
                    download_url = asset['browser_download_url']
                    break
            
            if not download_url:
                # Se não encontrou asset específico, usa o zipball
                download_url = data.get('zipball_url', '')
            
            # Compara versões
            if self._compare_versions(latest_version, self.current_version) > 0:
                self.finished_signal.emit(True, latest_version, download_url, "Nova versão disponível!")
            else:
                self.finished_signal.emit(True, latest_version, download_url, "Você já tem a versão mais recente!")
                
        except Exception as e:
            self.finished_signal.emit(False, "", "", f"Erro ao verificar: {str(e)}")
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compara duas versões. Retorna >0 se v1>v2, <0 se v1<v2, 0 se iguais"""
        try:
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]
            
            for i in range(max(len(parts1), len(parts2))):
                p1 = parts1[i] if i < len(parts1) else 0
                p2 = parts2[i] if i < len(parts2) else 0
                if p1 > p2:
                    return 1
                elif p1 < p2:
                    return -1
            return 0
        except:
            return 0


# ============================================================================
# WIDGETS CUSTOMIZADOS
# ============================================================================

class StyledButton(QPushButton):
    """Botão estilizado com tema oriental"""
    
    def __init__(self, text: str, primary: bool = False, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setMinimumHeight(45)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 11, QFont.Bold if primary else QFont.Normal))
        self._update_style()
    
    def _update_style(self):
        if self.primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {Theme.GOLD_PRIMARY}, stop:1 {Theme.GOLD_DARK});
                    color: {Theme.BACKGROUND_DARK};
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {Theme.GOLD_LIGHT}, stop:1 {Theme.GOLD_PRIMARY});
                }}
                QPushButton:pressed {{
                    background: {Theme.GOLD_DARK};
                }}
                QPushButton:disabled {{
                    background: {Theme.TEXT_MUTED};
                    color: {Theme.BACKGROUND_MEDIUM};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.BACKGROUND_LIGHT};
                    color: {Theme.TEXT_PRIMARY};
                    border: 1px solid {Theme.GOLD_DARK};
                    border-radius: 8px;
                    padding: 12px 24px;
                }}
                QPushButton:hover {{
                    background: {Theme.BACKGROUND_MEDIUM};
                    border-color: {Theme.GOLD_PRIMARY};
                }}
                QPushButton:pressed {{
                    background: {Theme.BACKGROUND_DARK};
                }}
                QPushButton:disabled {{
                    background: {Theme.BACKGROUND_DARK};
                    color: {Theme.TEXT_MUTED};
                    border-color: {Theme.TEXT_MUTED};
                }}
            """)


class StatusCard(QFrame):
    """Card de status estilizado"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BACKGROUND_LIGHT};
                border: 1px solid {Theme.GOLD_DARK}33;
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 10))
        self.title_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; border: none;")
        layout.addWidget(self.title_label)
        
        self.value_label = QLabel("—")
        self.value_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; border: none;")
        layout.addWidget(self.value_label)
    
    def set_value(self, value: str, color: str = None):
        self.value_label.setText(value)
        if color:
            self.value_label.setStyleSheet(f"color: {color}; border: none;")


# ============================================================================
# JANELA PRINCIPAL
# ============================================================================

class LauncherWindow(QMainWindow):
    """Janela principal do Launcher"""
    
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.game_path = self.config.get('game_path', '')
        self.installed_version = self.config.get('installed_version', '0.0.0')
        self.latest_version = None
        self.download_url = None
        
        self.init_ui()
        self.auto_detect_game()
        
        # Verifica atualizações automaticamente
        QTimer.singleShot(500, self.check_for_updates)
    
    def init_ui(self):
        """Inicializa a interface"""
        self.setWindowTitle(f"{APP_NAME}")
        self.setFixedSize(600, 700)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Widget central com fundo
        central = QWidget()
        self.setCentralWidget(central)
        
        # Layout principal
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container principal com bordas arredondadas
        self.container = QFrame()
        self.container.setObjectName("mainContainer")
        self.container.setStyleSheet(f"""
            QFrame#mainContainer {{
                background: {Theme.BACKGROUND_DARK};
                border: 1px solid {Theme.GOLD_DARK}66;
                border-radius: 16px;
            }}
        """)
        main_layout.addWidget(self.container)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(24, 24, 24, 24)
        container_layout.setSpacing(20)
        
        # Header
        self._create_header(container_layout)
        
        # Cards de status
        self._create_status_cards(container_layout)
        
        # Seleção do jogo
        self._create_game_selector(container_layout)
        
        # Barra de progresso
        self._create_progress_section(container_layout)
        
        # Botões de ação
        self._create_action_buttons(container_layout)
        
        # Footer
        self._create_footer(container_layout)
        
        # Aplicar sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)
    
    def _create_header(self, layout):
        """Cria o cabeçalho"""
        header = QFrame()
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(8)
        
        # Barra de título com botão fechar
        title_bar = QHBoxLayout()
        
        # Ícone/Logo (texto estilizado)
        logo = QLabel("⚔")
        logo.setFont(QFont("Segoe UI", 24))
        logo.setStyleSheet(f"color: {Theme.GOLD_PRIMARY};")
        title_bar.addWidget(logo)
        
        title_bar.addStretch()
        
        # Botão minimizar
        min_btn = QPushButton("─")
        min_btn.setFixedSize(30, 30)
        min_btn.setCursor(Qt.PointingHandCursor)
        min_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{
                color: {Theme.TEXT_PRIMARY};
                background: {Theme.BACKGROUND_LIGHT};
                border-radius: 4px;
            }}
        """)
        min_btn.clicked.connect(self.showMinimized)
        title_bar.addWidget(min_btn)
        
        # Botão fechar
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{
                color: white;
                background: {Theme.RED_PRIMARY};
                border-radius: 4px;
            }}
        """)
        close_btn.clicked.connect(self.close)
        title_bar.addWidget(close_btn)
        
        header_layout.addLayout(title_bar)
        
        # Título
        title = QLabel("Where Winds Meet")
        title.setFont(QFont("Segoe UI Light", 28))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel("Tradução Português Brasil")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet(f"color: {Theme.GOLD_PRIMARY};")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)
        
        # Linha decorativa
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, 
                stop:0.3 {Theme.GOLD_DARK},
                stop:0.5 {Theme.GOLD_PRIMARY},
                stop:0.7 {Theme.GOLD_DARK},
                stop:1 transparent);
        """)
        header_layout.addWidget(line)
        
        layout.addWidget(header)
    
    def _create_status_cards(self, layout):
        """Cria os cards de status"""
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        
        # Card versão instalada
        self.card_installed = StatusCard("Versão Instalada")
        self.card_installed.set_value(self.installed_version)
        cards_layout.addWidget(self.card_installed)
        
        # Card versão disponível
        self.card_available = StatusCard("Versão Disponível")
        self.card_available.set_value("Verificando...", Theme.TEXT_SECONDARY)
        cards_layout.addWidget(self.card_available)
        
        layout.addLayout(cards_layout)
    
    def _create_game_selector(self, layout):
        """Cria a seção de seleção do jogo"""
        selector = QFrame()
        selector.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BACKGROUND_MEDIUM};
                border: 1px solid {Theme.GOLD_DARK}33;
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        selector_layout = QVBoxLayout(selector)
        selector_layout.setSpacing(12)
        
        # Label
        label = QLabel("📂 Localização do Jogo")
        label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; border: none;")
        selector_layout.addWidget(label)
        
        # Caminho + botão
        path_layout = QHBoxLayout()
        
        self.path_label = QLabel("Nenhum jogo selecionado")
        self.path_label.setFont(QFont("Segoe UI", 9))
        self.path_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; border: none;")
        self.path_label.setWordWrap(True)
        path_layout.addWidget(self.path_label, 1)
        
        browse_btn = StyledButton("Procurar")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self.browse_game)
        path_layout.addWidget(browse_btn)
        
        selector_layout.addLayout(path_layout)
        
        # Status do jogo
        self.game_status = QLabel("")
        self.game_status.setFont(QFont("Segoe UI", 9))
        self.game_status.setStyleSheet(f"color: {Theme.TEXT_MUTED}; border: none;")
        selector_layout.addWidget(self.game_status)
        
        layout.addWidget(selector)
    
    def _create_progress_section(self, layout):
        """Cria a seção de progresso"""
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setSpacing(8)
        
        self.status_label = QLabel("Pronto")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        self.status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {Theme.BACKGROUND_LIGHT};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.GOLD_DARK}, stop:1 {Theme.GOLD_PRIMARY});
                border-radius: 4px;
            }}
        """)
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_frame)
    
    def _create_action_buttons(self, layout):
        """Cria os botões de ação"""
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(12)
        
        # Botão principal - Instalar/Atualizar
        self.install_btn = StyledButton("⬇ INSTALAR TRADUÇÃO", primary=True)
        self.install_btn.setMinimumHeight(55)
        self.install_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.install_btn.clicked.connect(self.install_translation)
        self.install_btn.setEnabled(False)
        buttons_layout.addWidget(self.install_btn)
        
        # Botões secundários
        secondary_layout = QHBoxLayout()
        secondary_layout.setSpacing(12)
        
        # Verificar atualizações
        self.check_btn = StyledButton("🔄 Verificar Atualizações")
        self.check_btn.clicked.connect(self.check_for_updates)
        secondary_layout.addWidget(self.check_btn)
        
        # Iniciar jogo
        self.play_btn = StyledButton("▶ Iniciar Jogo")
        self.play_btn.clicked.connect(self.launch_game)
        self.play_btn.setEnabled(False)
        secondary_layout.addWidget(self.play_btn)
        
        buttons_layout.addLayout(secondary_layout)
        
        layout.addLayout(buttons_layout)
    
    def _create_footer(self, layout):
        """Cria o rodapé"""
        layout.addStretch()
        
        footer = QFrame()
        footer_layout = QVBoxLayout(footer)
        footer_layout.setSpacing(4)
        
        # Links
        links_layout = QHBoxLayout()
        links_layout.setAlignment(Qt.AlignCenter)
        
        github_btn = QPushButton("GitHub")
        github_btn.setCursor(Qt.PointingHandCursor)
        github_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.GOLD_PRIMARY};
                border: none;
                font-size: 11px;
                text-decoration: underline;
            }}
            QPushButton:hover {{
                color: {Theme.GOLD_LIGHT};
            }}
        """)
        github_btn.clicked.connect(lambda: webbrowser.open(f"https://github.com/{GITHUB_REPO}"))
        links_layout.addWidget(github_btn)
        
        sep = QLabel("•")
        sep.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        links_layout.addWidget(sep)
        
        discord_btn = QPushButton("Discord")
        discord_btn.setCursor(Qt.PointingHandCursor)
        discord_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.GOLD_PRIMARY};
                border: none;
                font-size: 11px;
                text-decoration: underline;
            }}
            QPushButton:hover {{
                color: {Theme.GOLD_LIGHT};
            }}
        """)
        # discord_btn.clicked.connect(lambda: webbrowser.open("https://discord.gg/..."))
        links_layout.addWidget(discord_btn)
        
        footer_layout.addLayout(links_layout)
        
        # Créditos
        credits = QLabel(f"Comunidade WWM Brasil • v{APP_VERSION}")
        credits.setFont(QFont("Segoe UI", 9))
        credits.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        credits.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(credits)
        
        layout.addWidget(footer)
    
    # ========================================================================
    # LÓGICA DO APLICATIVO
    # ========================================================================
    
    def load_config(self) -> dict:
        """Carrega configurações salvas"""
        config_path = Path(__file__).parent / CONFIG_FILE
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_config(self):
        """Salva configurações"""
        config_path = Path(__file__).parent / CONFIG_FILE
        self.config['game_path'] = self.game_path
        self.config['installed_version'] = self.installed_version
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass
    
    def auto_detect_game(self):
        """Tenta detectar automaticamente o jogo"""
        if self.game_path and self.validate_game_path(self.game_path):
            self.update_game_path(self.game_path)
            return
        
        for path in DEFAULT_STEAM_PATHS:
            if self.validate_game_path(path):
                self.update_game_path(path)
                return
        
        self.game_status.setText("⚠ Jogo não encontrado automaticamente")
        self.game_status.setStyleSheet(f"color: {Theme.WARNING}; border: none;")
    
    def validate_game_path(self, path: str) -> bool:
        """Valida se o caminho do jogo é válido"""
        if not path:
            return False
        game_exe = Path(path) / GAME_EXE_RELATIVE
        return game_exe.exists()
    
    def update_game_path(self, path: str):
        """Atualiza o caminho do jogo"""
        self.game_path = path
        self.path_label.setText(path)
        self.path_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; border: none;")
        self.game_status.setText("✓ Jogo encontrado")
        self.game_status.setStyleSheet(f"color: {Theme.SUCCESS}; border: none;")
        self.play_btn.setEnabled(True)
        self.install_btn.setEnabled(True)
        self.save_config()
    
    def browse_game(self):
        """Abre diálogo para selecionar o executável do jogo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar WWM.exe",
            "",
            "Executável (wwm.exe)"
        )
        
        if file_path:
            # Extrai o caminho base do jogo
            # O executável está em: <game>/Engine/Binaries/Win64r/wwm.exe
            game_path = Path(file_path).parent.parent.parent.parent
            
            if self.validate_game_path(str(game_path)):
                self.update_game_path(str(game_path))
            else:
                QMessageBox.warning(
                    self,
                    "Caminho Inválido",
                    "O caminho selecionado não parece ser uma instalação válida do Where Winds Meet."
                )
    
    def check_for_updates(self):
        """Verifica se há atualizações disponíveis"""
        self.check_btn.setEnabled(False)
        self.card_available.set_value("Verificando...", Theme.TEXT_SECONDARY)
        self.status_label.setText("Verificando atualizações...")
        
        self.update_thread = CheckUpdateThread(self.installed_version)
        self.update_thread.finished_signal.connect(self.on_update_check_finished)
        self.update_thread.start()
    
    def on_update_check_finished(self, success: bool, version: str, url: str, message: str):
        """Callback quando a verificação de atualização termina"""
        self.check_btn.setEnabled(True)
        
        if success:
            self.latest_version = version
            self.download_url = url
            self.card_available.set_value(version, Theme.GOLD_PRIMARY)
            
            # Verifica se precisa atualizar
            if self._compare_versions(version, self.installed_version) > 0:
                self.status_label.setText(f"🎉 {message}")
                self.status_label.setStyleSheet(f"color: {Theme.SUCCESS};")
                self.install_btn.setText("⬆ ATUALIZAR TRADUÇÃO")
            else:
                self.status_label.setText(f"✓ {message}")
                self.status_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
                self.install_btn.setText("🔄 REINSTALAR TRADUÇÃO")
        else:
            self.card_available.set_value("Erro", Theme.ERROR)
            self.status_label.setText(f"❌ {message}")
            self.status_label.setStyleSheet(f"color: {Theme.ERROR};")
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compara duas versões"""
        try:
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]
            
            for i in range(max(len(parts1), len(parts2))):
                p1 = parts1[i] if i < len(parts1) else 0
                p2 = parts2[i] if i < len(parts2) else 0
                if p1 > p2:
                    return 1
                elif p1 < p2:
                    return -1
            return 0
        except:
            return 0
    
    def install_translation(self):
        """Instala ou atualiza a tradução"""
        if not self.game_path:
            QMessageBox.warning(self, "Erro", "Selecione o caminho do jogo primeiro!")
            return
        
        if not self.download_url:
            QMessageBox.warning(self, "Erro", "Verifique as atualizações primeiro!")
            return
        
        # Confirmação
        reply = QMessageBox.question(
            self,
            "Confirmar Instalação",
            f"Deseja instalar/atualizar a tradução para a versão {self.latest_version}?\n\n"
            "O arquivo original será substituído.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Inicia download
        self.install_btn.setEnabled(False)
        self.check_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Baixa para arquivo temporário
        temp_file = tempfile.mktemp(suffix='.tmp')
        
        self.download_thread = DownloadThread(self.download_url, temp_file)
        self.download_thread.progress_signal.connect(self.progress_bar.setValue)
        self.download_thread.status_signal.connect(self.status_label.setText)
        self.download_thread.finished_signal.connect(
            lambda ok, path: self.on_download_finished(ok, path)
        )
        self.download_thread.start()
    
    def on_download_finished(self, success: bool, result: str):
        """Callback quando o download termina"""
        if success:
            try:
                # Caminho de destino
                dest_path = Path(self.game_path) / TRANSLATION_FILE_RELATIVE
                
                # Backup do arquivo original (se existir)
                if dest_path.exists():
                    backup_path = dest_path.with_suffix('.backup')
                    shutil.copy2(dest_path, backup_path)
                
                # Copia o arquivo baixado
                shutil.copy2(result, dest_path)
                
                # Remove o temporário
                os.unlink(result)
                
                # Atualiza versão instalada
                self.installed_version = self.latest_version
                self.card_installed.set_value(self.installed_version, Theme.SUCCESS)
                self.save_config()
                
                self.status_label.setText("✓ Tradução instalada com sucesso!")
                self.status_label.setStyleSheet(f"color: {Theme.SUCCESS};")
                self.install_btn.setText("✓ INSTALADO")
                
                QMessageBox.information(
                    self,
                    "Sucesso!",
                    f"Tradução v{self.latest_version} instalada com sucesso!\n\n"
                    "Você já pode iniciar o jogo."
                )
                
            except Exception as e:
                self.status_label.setText(f"❌ Erro ao instalar: {str(e)}")
                self.status_label.setStyleSheet(f"color: {Theme.ERROR};")
                QMessageBox.critical(self, "Erro", f"Erro ao instalar tradução:\n{str(e)}")
        else:
            self.status_label.setText(f"❌ Erro no download: {result}")
            self.status_label.setStyleSheet(f"color: {Theme.ERROR};")
        
        self.install_btn.setEnabled(True)
        self.check_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def launch_game(self):
        """Inicia o jogo"""
        if not self.game_path:
            return
        
        game_exe = Path(self.game_path) / GAME_EXE_RELATIVE
        if game_exe.exists():
            os.startfile(str(game_exe))
            self.showMinimized()
        else:
            QMessageBox.warning(self, "Erro", "Executável do jogo não encontrado!")
    
    # ========================================================================
    # EVENTOS DE JANELA (arrastar janela sem bordas)
    # ========================================================================
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPos() - self.drag_position)
            event.accept()


# ============================================================================
# PONTO DE ENTRADA
# ============================================================================

def main():
    # Habilita DPI awareness para telas de alta resolução
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Configura paleta escura
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(Theme.BACKGROUND_DARK))
    palette.setColor(QPalette.WindowText, QColor(Theme.TEXT_PRIMARY))
    palette.setColor(QPalette.Base, QColor(Theme.BACKGROUND_MEDIUM))
    palette.setColor(QPalette.AlternateBase, QColor(Theme.BACKGROUND_LIGHT))
    palette.setColor(QPalette.Text, QColor(Theme.TEXT_PRIMARY))
    palette.setColor(QPalette.Button, QColor(Theme.BACKGROUND_LIGHT))
    palette.setColor(QPalette.ButtonText, QColor(Theme.TEXT_PRIMARY))
    palette.setColor(QPalette.Highlight, QColor(Theme.GOLD_PRIMARY))
    palette.setColor(QPalette.HighlightedText, QColor(Theme.BACKGROUND_DARK))
    app.setPalette(palette)
    
    window = LauncherWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
