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
import webbrowser
import zipfile
import hashlib
import ctypes
import re
from pathlib import Path
from datetime import datetime

# Configuração de DPI para Windows ANTES de importar Qt
if sys.platform == 'win32':
    try:
        # Torna o processo DPI-aware (Per-Monitor DPI Aware V2)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:
        try:
            # Fallback para versões mais antigas do Windows
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

# Variáveis de ambiente para Qt
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
os.environ['QT_SCALE_FACTOR_ROUNDING_POLICY'] = 'PassThrough'


def is_admin() -> bool:
    """Verifica se o programa está rodando como administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def run_as_admin():
    """Reinicia o programa como administrador"""
    try:
        if sys.platform == 'win32':
            if getattr(sys, 'frozen', False):
                # Executando como .exe compilado
                executable = sys.executable
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", executable, None, None, 1
                )
            else:
                # Executando como script Python
                executable = sys.executable
                script = os.path.abspath(__file__)
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", executable, f'"{script}"', None, 1
                )
            sys.exit(0)
    except Exception as e:
        return False
    return True

try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests")
    import requests

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QPushButton, QLabel,
        QVBoxLayout, QHBoxLayout, QFileDialog, QProgressBar,
        QMessageBox, QFrame, QGraphicsDropShadowEffect, QSizePolicy,
        QScrollArea
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
APP_VERSION = "2.2.0"
GITHUB_REPO = "rodrigomiquilino/wwm_brasileiro"
GITHUB_API_RELEASES = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
GITHUB_RELEASES_PAGE = f"https://github.com/{GITHUB_REPO}/releases"

# Arquivo de configuração local (na pasta do launcher)
LOCAL_CONFIG_FILE = "wwm_ptbr_launcher.json"

# Arquivo de configuração da tradução (na pasta de tradução do jogo)
TRANSLATION_CONFIG_FILE = ".wwm_ptbr_config"

# Arquivos de tradução
TRANSLATION_FILES = [
    "translate_words_map_en",
    "translate_words_map_en_diff"
]

# Plataformas suportadas
class Platform:
    STEAM = "steam"
    EPIC = "epic"
    STANDALONE = "standalone"
    UNKNOWN = "unknown"


# Caminhos relativos por plataforma
PLATFORM_CONFIG = {
    Platform.STEAM: {
        "name": "Steam",
        "translation_path": r"Package\HD\oversea\locale",
        "exe_pattern": r"Engine\Binaries\Win64r\wwm.exe",
        "launch_command": "steam://rungameid/3564740",
        "icon": "🎮"
    },
    Platform.EPIC: {
        "name": "Epic Games",
        "translation_path": r"Package\HD\oversea\locale",
        "exe_pattern": r"Engine\Binaries\Win64r\wwm.exe",
        "launch_command": "com.epicgames.launcher://apps/4806012311744989a5f96d97a42f7829%3Ad53f8dc5825748849ca0890279c3dad7%3Aa7d28f0e0935490b9d6f92dda1a7a75b?action=launch&silent=true",
        "icon": "🎯"
    },
    Platform.STANDALONE: {
        "name": "Standalone",
        "translation_path": r"LocalData\Patch\HD\oversea\locale",
        "exe_pattern": r"wwm_(standard|lite)\Engine\Binaries\Win64r\wwm.exe",
        "variants": ["wwm_standard", "wwm_lite"],  # Variantes suportadas
        "launcher_exe": "launcher.exe",  # Executável para iniciar o jogo
        "launch_command": None,
        "icon": "💻"
    }
}


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
# UTILITÁRIOS
# ============================================================================

def get_file_hash(filepath: str) -> str:
    """Calcula o hash MD5 de um arquivo"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return ""


def get_file_modified_time(filepath: str) -> str:
    """Retorna a data de modificação do arquivo no formato ISO"""
    try:
        mtime = os.path.getmtime(filepath)
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ""


# ============================================================================
# GERENCIADOR DE CONFIGURAÇÃO DA TRADUÇÃO
# ============================================================================

class TranslationConfig:
    """Gerencia o arquivo de configuração na pasta de tradução"""
    
    def __init__(self, translation_path: str):
        self.config_path = Path(translation_path) / TRANSLATION_CONFIG_FILE
        self.data = self._load()
    
    def _load(self) -> dict:
        """Carrega a configuração"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save(self):
        """Salva a configuração"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def is_translation_installed(self) -> bool:
        """Verifica se a tradução foi instalada por nós"""
        return self.data.get('installed', False)
    
    def get_installed_version(self) -> str:
        """Retorna a versão instalada"""
        return self.data.get('version', '')
    
    def get_installed_timestamp(self) -> str:
        """Retorna o timestamp da instalação"""
        return self.data.get('timestamp', '')
    
    def get_file_hashes(self) -> dict:
        """Retorna os hashes dos arquivos instalados"""
        return self.data.get('file_hashes', {})
    
    def set_installed(self, version: str, timestamp: str, file_hashes: dict):
        """Marca a tradução como instalada"""
        self.data['installed'] = True
        self.data['version'] = version
        self.data['timestamp'] = timestamp
        self.data['file_hashes'] = file_hashes
        self.save()
    
    def clear(self):
        """Limpa a configuração (tradução removida)"""
        self.data = {}
        if self.config_path.exists():
            try:
                self.config_path.unlink()
            except:
                pass


# ============================================================================
# DETECTOR DE PLATAFORMA
# ============================================================================

class PlatformDetector:
    """Detecta a plataforma baseado no executável selecionado"""
    
    @staticmethod
    def detect(exe_path: str) -> tuple:
        """
        Detecta a plataforma e retorna (platform, game_root, translation_path)
        """
        exe_path = Path(exe_path)
        exe_name = exe_path.name.lower()
        exe_str = str(exe_path).lower()
        
        # wwm.exe - detecta qual plataforma
        if exe_name == "wwm.exe":
            # Standalone: wwm_standard/Engine/Binaries/Win64r/wwm.exe
            #         ou wwm_lite/Engine/Binaries/Win64r/wwm.exe
            if "wwm_standard" in exe_str or "wwm_lite" in exe_str:
                # wwm/wwm_standard/Engine/Binaries/Win64r/wwm.exe → wwm/wwm_standard/
                # wwm/wwm_lite/Engine/Binaries/Win64r/wwm.exe → wwm/wwm_lite/
                game_root = exe_path.parent.parent.parent.parent  # wwm_standard ou wwm_lite
                translation_path = game_root / PLATFORM_CONFIG[Platform.STANDALONE]["translation_path"]
                return Platform.STANDALONE, game_root, translation_path
            
            # Steam ou Epic: Engine/Binaries/Win64r/wwm.exe → raiz do jogo
            game_root = exe_path.parent.parent.parent.parent
            
            # Detecta se é Epic ou Steam pelo caminho
            if "epic games" in exe_str:
                platform = Platform.EPIC
            elif "steam" in exe_str:
                platform = Platform.STEAM
            else:
                # Verifica pela estrutura de pastas
                if (game_root / "Package").exists():
                    # Pode ser Steam ou Epic, vamos verificar mais
                    if (game_root.parent / "steamapps").exists():
                        platform = Platform.STEAM
                    else:
                        platform = Platform.EPIC
                else:
                    platform = Platform.UNKNOWN
            
            if platform in [Platform.STEAM, Platform.EPIC]:
                translation_path = game_root / PLATFORM_CONFIG[platform]["translation_path"]
                return platform, game_root, translation_path
        
        return Platform.UNKNOWN, None, None
    
    @staticmethod
    def get_launch_command(platform: str, exe_path: str) -> str:
        """Retorna o comando para iniciar o jogo"""
        if platform == Platform.STANDALONE:
            return str(exe_path)  # Executa o launcher.exe diretamente
        elif platform in PLATFORM_CONFIG:
            return PLATFORM_CONFIG[platform]["launch_command"]
        return None


# ============================================================================
# VERIFICADOR DE STATUS DA TRADUÇÃO
# ============================================================================

class TranslationStatus:
    """Status possíveis da tradução"""
    NOT_INSTALLED = "not_installed"      # Nunca instalou (versão original)
    INSTALLED = "installed"              # Tradução instalada e ativa
    OUTDATED = "outdated"                # Tradução desatualizada (tem update)
    OVERWRITTEN = "overwritten"          # Jogo atualizou e sobrescreveu nossa tradução
    BACKUP_AVAILABLE = "backup_available" # Backup disponível para restaurar


class TranslationChecker:
    """Verifica o status da tradução instalada"""
    
    def __init__(self, translation_path: str):
        self.translation_path = Path(translation_path)
        self.config = TranslationConfig(translation_path)
    
    def get_status(self) -> dict:
        """
        Retorna o status completo da tradução
        """
        result = {
            'status': TranslationStatus.NOT_INSTALLED,
            'installed_version': None,
            'installed_timestamp': None,
            'has_backup': False,
            'files_intact': True,
            'message': ''
        }
        
        # Verifica se existe backup
        for tf in TRANSLATION_FILES:
            backup_file = self.translation_path / f"{tf}.backup"
            if backup_file.exists():
                result['has_backup'] = True
                break
        
        # Verifica se a tradução foi instalada por nós
        if not self.config.is_translation_installed():
            result['status'] = TranslationStatus.NOT_INSTALLED
            result['message'] = "Versão original do jogo"
            return result
        
        # Tradução foi instalada - verifica integridade
        result['installed_version'] = self.config.get_installed_version()
        result['installed_timestamp'] = self.config.get_installed_timestamp()
        
        # Verifica se os arquivos ainda são os mesmos (não foram sobrescritos)
        saved_hashes = self.config.get_file_hashes()
        for tf in TRANSLATION_FILES:
            file_path = self.translation_path / tf
            if file_path.exists():
                current_hash = get_file_hash(str(file_path))
                saved_hash = saved_hashes.get(tf, '')
                
                if saved_hash and current_hash != saved_hash:
                    result['files_intact'] = False
                    break
        
        if not result['files_intact']:
            result['status'] = TranslationStatus.OVERWRITTEN
            result['message'] = "Tradução foi sobrescrita (possível atualização do jogo)"
        else:
            result['status'] = TranslationStatus.INSTALLED
            result['message'] = "Tradução PT-BR ativa"
        
        return result


# ============================================================================
# THREAD DE DOWNLOAD
# ============================================================================

class DownloadThread(QThread):
    """Thread para download de arquivos com retry automático"""
    
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    MAX_RETRIES = 3
    TIMEOUT = 60  # segundos
    
    def __init__(self, url: str, dest_path: str):
        super().__init__()
        self.url = url
        self.dest_path = dest_path
    
    def run(self):
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                if attempt > 0:
                    self.status_signal.emit(f"Tentativa {attempt + 1}/{self.MAX_RETRIES}...")
                else:
                    self.status_signal.emit("Conectando ao servidor...")
                
                response = requests.get(self.url, stream=True, timeout=self.TIMEOUT)
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
                return
                
            except requests.exceptions.Timeout:
                last_error = "Tempo limite excedido. Verifique sua conexão."
            except requests.exceptions.ConnectionError:
                last_error = "Erro de conexão. Verifique sua internet."
            except Exception as e:
                last_error = str(e)
            
            # Aguarda antes de tentar novamente
            if attempt < self.MAX_RETRIES - 1:
                import time
                time.sleep(2)
        
        self.finished_signal.emit(False, f"Falha após {self.MAX_RETRIES} tentativas: {last_error}")


class CheckUpdateThread(QThread):
    """Thread para verificar atualizações da tradução
    
    Busca releases com tag no formato "x.x.x" ou "vx.x.x" (sem prefixo "launcher-")
    """
    
    # success, translation_version, timestamp, download_url, message
    finished_signal = pyqtSignal(bool, str, str, str, str)
    
    def __init__(self):
        super().__init__()
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compara duas versões. Retorna 1 se v1 > v2, -1 se v1 < v2, 0 se iguais"""
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
    
    def run(self):
        try:
            response = requests.get(GITHUB_API_RELEASES, timeout=10)
            response.raise_for_status()
            
            releases = response.json()
            
            # Procura o release de tradução mais recente
            # Tags de tradução: "x.x.x" ou "vx.x.x" (NÃO começam com "launcher-")
            best_version = None
            best_release = None
            
            for release in releases:
                tag = release.get('tag_name', '')
                
                # Ignora releases do launcher
                if tag.lower().startswith('launcher'):
                    continue
                
                # Extrai versão da tag
                version_match = re.search(r'v?(\d+\.\d+\.\d+)', tag)
                if version_match:
                    version = version_match.group(1)
                    
                    # Verifica se é a versão mais recente
                    if best_version is None or self._compare_versions(version, best_version) > 0:
                        best_version = version
                        best_release = release
            
            if best_release:
                published_at = best_release.get('published_at', '')
                
                # Procura o ZIP de tradução nos assets
                download_url = None
                for asset in best_release.get('assets', []):
                    if asset['name'].lower().endswith('.zip'):
                        download_url = asset['browser_download_url']
                        break
                
                # Fallback: zipball
                if not download_url:
                    download_url = best_release.get('zipball_url', '')
                
                self.finished_signal.emit(True, best_version, published_at, download_url, "Verificação concluída!")
            else:
                self.finished_signal.emit(False, "", "", "", "Nenhuma tradução encontrada")
            
        except Exception as e:
            self.finished_signal.emit(False, "", "", "", f"Erro: {str(e)}")


class CheckLauncherUpdateThread(QThread):
    """Thread para verificar atualizações do launcher
    
    Busca releases com tag no formato "launcher-x.x.x"
    """
    
    finished_signal = pyqtSignal(bool, str, str, str)  # success, version, download_url, message
    
    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compara duas versões. Retorna 1 se v1 > v2, -1 se v1 < v2, 0 se iguais"""
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
    
    def run(self):
        try:
            response = requests.get(GITHUB_API_RELEASES, timeout=10)
            response.raise_for_status()
            
            releases = response.json()
            
            # Procura o release do launcher mais recente
            # Tags de launcher: "launcher-x.x.x"
            best_version = None
            best_release = None
            
            for release in releases:
                tag = release.get('tag_name', '')
                
                # Só considera releases do launcher
                if not tag.lower().startswith('launcher'):
                    continue
                
                # Extrai versão da tag (launcher-x.x.x -> x.x.x)
                version_match = re.search(r'launcher-v?(\d+\.\d+\.\d+)', tag, re.IGNORECASE)
                if version_match:
                    version = version_match.group(1)
                    
                    # Verifica se é a versão mais recente
                    if best_version is None or self._compare_versions(version, best_version) > 0:
                        best_version = version
                        best_release = release
            
            if best_release and best_version:
                # Procura o .exe nos assets
                download_url = ""
                for asset in best_release.get('assets', []):
                    if asset['name'].lower().endswith('.exe'):
                        download_url = asset['browser_download_url']
                        break
                
                if self._compare_versions(best_version, self.current_version) > 0:
                    self.finished_signal.emit(True, best_version, download_url, "Nova versão do launcher disponível!")
                else:
                    self.finished_signal.emit(True, best_version, "", "Launcher atualizado!")
            else:
                # Não encontrou release do launcher, está atualizado
                self.finished_signal.emit(True, self.current_version, "", "Launcher atualizado!")
                
        except Exception as e:
            self.finished_signal.emit(False, "", "", f"Erro: {str(e)}")


# ============================================================================
# WIDGETS CUSTOMIZADOS
# ============================================================================

class StyledButton(QPushButton):
    """Botão estilizado com tema oriental"""
    
    def __init__(self, text: str, primary: bool = False, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 10, QFont.Bold if primary else QFont.Normal))
        self._update_style()
    
    def _update_style(self):
        if self.primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {Theme.GOLD_PRIMARY}, stop:1 {Theme.GOLD_DARK});
                    color: {Theme.BACKGROUND_DARK};
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
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
                    border-radius: 6px;
                    padding: 8px 16px;
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
        self.setFixedHeight(70)
        self.setMinimumWidth(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BACKGROUND_LIGHT};
                border: 1px solid {Theme.GOLD_DARK}33;
                border-radius: 10px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(10, 8, 10, 8)
        
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 8))
        self.title_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; border: none;")
        self.title_label.setFixedHeight(16)
        self.title_label.setWordWrap(False)
        layout.addWidget(self.title_label)
        
        self.value_label = QLabel("—")
        self.value_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; border: none;")
        self.value_label.setFixedHeight(20)
        self.value_label.setWordWrap(False)
        layout.addWidget(self.value_label)
        
        layout.addStretch()
    
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
        
        # Estado do aplicativo
        self.config = self._load_local_config()
        self.exe_path = self.config.get('exe_path', '')
        self.platform = Platform.UNKNOWN
        self.game_root = None
        self.translation_path = None
        
        # Versões
        self.latest_version = None
        self.latest_timestamp = None
        self.download_url = None
        
        self.init_ui()
        
        # Se já tem executável salvo, tenta detectar
        if self.exe_path and Path(self.exe_path).exists():
            self._detect_platform(self.exe_path)
        
        # Verifica atualizações automaticamente
        QTimer.singleShot(500, self.check_for_updates)
        QTimer.singleShot(1000, self.check_launcher_update)
    
    def _get_app_dir(self) -> Path:
        """Retorna o diretório do aplicativo (funciona tanto como .py quanto como .exe)"""
        if getattr(sys, 'frozen', False):
            # Executando como .exe compilado
            return Path(sys.executable).parent
        else:
            # Executando como script Python
            return Path(__file__).parent
    
    def _load_local_config(self) -> dict:
        """Carrega configuração local do launcher"""
        config_path = self._get_app_dir() / LOCAL_CONFIG_FILE
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_local_config(self):
        """Salva configuração local"""
        config_path = self._get_app_dir() / LOCAL_CONFIG_FILE
        self.config['exe_path'] = self.exe_path
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass
    
    def init_ui(self):
        """Inicializa a interface"""
        self.setWindowTitle(f"{APP_NAME}")
        self.setMinimumSize(550, 700)  # Tamanho mínimo que cabe tudo
        self.resize(600, 750)  # Tamanho inicial
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container principal com scroll
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
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(12)
        
        # Seções da UI
        self._create_header(container_layout)
        self._create_status_cards(container_layout)
        self._create_game_selector(container_layout)
        self._create_progress_section(container_layout)
        self._create_action_buttons(container_layout)
        self._create_footer(container_layout)
        
        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)
    
    def _create_header(self, layout):
        """Cria o cabeçalho"""
        header = QFrame()
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(4)
        header_layout.setContentsMargins(0, 0, 0, 8)
        
        # Barra de título
        title_bar = QHBoxLayout()
        
        logo = QLabel("⚔")
        logo.setFont(QFont("Segoe UI", 20))
        logo.setFixedSize(30, 30)
        logo.setStyleSheet(f"color: {Theme.GOLD_PRIMARY};")
        title_bar.addWidget(logo)
        
        title_bar.addStretch()
        
        # Minimizar
        min_btn = QPushButton("─")
        min_btn.setFixedSize(28, 28)
        min_btn.setCursor(Qt.PointingHandCursor)
        min_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {Theme.TEXT_PRIMARY};
                background: {Theme.BACKGROUND_LIGHT};
                border-radius: 4px;
            }}
        """)
        min_btn.clicked.connect(self.showMinimized)
        title_bar.addWidget(min_btn)
        
        # Fechar
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: none;
                font-size: 12px;
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
        title.setFont(QFont("Segoe UI Light", 24))
        title.setFixedHeight(32)
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel("Tradução Português Brasil")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setFixedHeight(18)
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
        # Container para todos os cards com altura fixa
        cards_container = QWidget()
        cards_container.setFixedHeight(160)
        cards_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        cards_container_layout = QVBoxLayout(cards_container)
        cards_container_layout.setSpacing(10)
        cards_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Primeira linha de cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        
        # Card plataforma
        self.card_platform = StatusCard("Plataforma")
        self.card_platform.set_value("Não detectada", Theme.TEXT_MUTED)
        cards_layout.addWidget(self.card_platform)
        
        # Card status tradução
        self.card_status = StatusCard("Status")
        self.card_status.set_value("—", Theme.TEXT_MUTED)
        cards_layout.addWidget(self.card_status)
        
        cards_container_layout.addLayout(cards_layout)
        
        # Segunda linha de cards
        cards_layout2 = QHBoxLayout()
        cards_layout2.setSpacing(12)
        
        # Card versão instalada
        self.card_installed = StatusCard("Versão Instalada")
        self.card_installed.set_value("—")
        cards_layout2.addWidget(self.card_installed)
        
        # Card versão disponível
        self.card_available = StatusCard("Versão Disponível")
        self.card_available.set_value("Verificando...", Theme.TEXT_SECONDARY)
        cards_layout2.addWidget(self.card_available)
        
        cards_container_layout.addLayout(cards_layout2)
        
        layout.addWidget(cards_container)
    
    def _create_game_selector(self, layout):
        """Cria a seção de seleção do jogo"""
        selector = QFrame()
        selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        selector.setMinimumHeight(140)
        selector.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BACKGROUND_MEDIUM};
                border: 1px solid {Theme.GOLD_DARK}33;
                border-radius: 10px;
            }}
        """)
        
        selector_layout = QVBoxLayout(selector)
        selector_layout.setSpacing(8)
        selector_layout.setContentsMargins(14, 12, 14, 12)
        
        # Título
        label = QLabel("📂 Localização do Jogo")
        label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        label.setFixedHeight(20)
        label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; border: none;")
        selector_layout.addWidget(label)
        
        # Caminho do executável
        self.path_label = QLabel("Localize o arquivo wwm.exe do jogo")
        self.path_label.setFont(QFont("Segoe UI", 8))
        self.path_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; border: none;")
        self.path_label.setWordWrap(True)
        self.path_label.setMinimumHeight(16)
        selector_layout.addWidget(self.path_label)
        
        # Status do jogo
        self.game_status = QLabel("")
        self.game_status.setFont(QFont("Segoe UI", 8))
        self.game_status.setStyleSheet(f"color: {Theme.TEXT_MUTED}; border: none;")
        self.game_status.setWordWrap(True)
        self.game_status.setMinimumHeight(16)
        selector_layout.addWidget(self.game_status)
        
        # Botão embaixo (largura total)
        browse_btn = StyledButton("📁 Procurar wwm.exe")
        browse_btn.setFixedHeight(36)
        browse_btn.clicked.connect(self.browse_game)
        selector_layout.addWidget(browse_btn)
        
        layout.addWidget(selector)
    
    def _create_progress_section(self, layout):
        """Cria a seção de progresso"""
        progress_frame = QFrame()
        progress_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        progress_frame.setFixedHeight(50)
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setSpacing(6)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("Localize o wwm.exe para começar")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setFixedHeight(20)
        self.status_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        self.status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {Theme.BACKGROUND_LIGHT};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.GOLD_DARK}, stop:1 {Theme.GOLD_PRIMARY});
                border-radius: 3px;
            }}
        """)
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_frame)
    
    def _create_action_buttons(self, layout):
        """Cria os botões de ação"""
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        
        # Botão principal - Instalar/Atualizar
        self.install_btn = StyledButton("⬇ INSTALAR TRADUÇÃO", primary=True)
        self.install_btn.setFixedHeight(48)
        self.install_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.install_btn.clicked.connect(self.install_translation)
        self.install_btn.setEnabled(False)
        self.install_btn.setToolTip("Baixa e instala a tradução PT-BR do GitHub")
        buttons_layout.addWidget(self.install_btn)
        
        # Botão de restaurar original (inicialmente oculto)
        self.restore_btn = StyledButton("🔙 RESTAURAR ORIGINAL (Remover Tradução)")
        self.restore_btn.setFixedHeight(40)
        self.restore_btn.clicked.connect(self.restore_backup)
        self.restore_btn.setVisible(False)
        self.restore_btn.setToolTip("Restaura os arquivos originais do jogo (remove a tradução)")
        buttons_layout.addWidget(self.restore_btn)
        
        # Botões secundários
        secondary_layout = QHBoxLayout()
        secondary_layout.setSpacing(10)
        
        # Verificar atualizações
        self.check_btn = StyledButton("🔄 Verificar")
        self.check_btn.setFixedHeight(38)
        self.check_btn.clicked.connect(self.check_for_updates)
        self.check_btn.setToolTip("Verifica se há nova versão da tradução disponível")
        secondary_layout.addWidget(self.check_btn)
        
        # Iniciar jogo
        self.play_btn = StyledButton("▶ Iniciar Jogo")
        self.play_btn.setFixedHeight(38)
        self.play_btn.clicked.connect(self.launch_game)
        self.play_btn.setEnabled(False)
        self.play_btn.setToolTip("Inicia o jogo pela plataforma detectada")
        secondary_layout.addWidget(self.play_btn)
        
        buttons_layout.addLayout(secondary_layout)
        
        layout.addLayout(buttons_layout)
    
    def _create_footer(self, layout):
        """Cria o rodapé"""
        layout.addStretch()
        
        footer = QFrame()
        footer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        footer.setFixedHeight(70)
        footer_layout = QVBoxLayout(footer)
        footer_layout.setSpacing(4)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        
        # Links
        links_layout = QHBoxLayout()
        links_layout.setAlignment(Qt.AlignCenter)
        
        github_btn = QPushButton("GitHub")
        github_btn.setFixedHeight(20)
        github_btn.setCursor(Qt.PointingHandCursor)
        github_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.GOLD_PRIMARY};
                border: none;
                font-size: 10px;
                text-decoration: underline;
            }}
            QPushButton:hover {{
                color: {Theme.GOLD_LIGHT};
            }}
        """)
        github_btn.clicked.connect(lambda: webbrowser.open(f"https://github.com/{GITHUB_REPO}"))
        links_layout.addWidget(github_btn)
        
        sep = QLabel("•")
        sep.setFixedHeight(20)
        sep.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        links_layout.addWidget(sep)
        
        discord_btn = QPushButton("Discord")
        discord_btn.setFixedHeight(20)
        discord_btn.setCursor(Qt.PointingHandCursor)
        discord_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.GOLD_PRIMARY};
                border: none;
                font-size: 10px;
                text-decoration: underline;
            }}
            QPushButton:hover {{
                color: {Theme.GOLD_LIGHT};
            }}
        """)
        discord_btn.clicked.connect(lambda: webbrowser.open("https://discordapp.com/users/rodrigo.dev"))
        links_layout.addWidget(discord_btn)
        
        footer_layout.addLayout(links_layout)
        
        # Botão de nova versão do launcher
        self.launcher_update_btn = QPushButton("⬆ Nova versão disponível - Clique para baixar")
        self.launcher_update_btn.setFixedHeight(22)
        self.launcher_update_btn.setCursor(Qt.PointingHandCursor)
        self.launcher_update_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.INFO};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 10px;
                font-size: 9px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #1976d2;
            }}
        """)
        self.launcher_update_btn.clicked.connect(lambda: webbrowser.open(GITHUB_RELEASES_PAGE))
        self.launcher_update_btn.setVisible(False)
        footer_layout.addWidget(self.launcher_update_btn, alignment=Qt.AlignCenter)
        
        # Créditos
        credits = QLabel(f"Comunidade WWM Brasil • v{APP_VERSION}")
        credits.setFont(QFont("Segoe UI", 8))
        credits.setFixedHeight(16)
        credits.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        credits.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(credits)
        
        layout.addWidget(footer)
    
    # ========================================================================
    # LÓGICA DO APLICATIVO
    # ========================================================================
    
    def browse_game(self):
        """Abre diálogo para selecionar o executável do jogo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar executável do jogo (wwm.exe)",
            "",
            "Executável do jogo (wwm.exe)"
        )
        
        if file_path:
            self._detect_platform(file_path)
    
    def _detect_platform(self, exe_path: str):
        """Detecta a plataforma e configura os caminhos"""
        platform, game_root, translation_path = PlatformDetector.detect(exe_path)
        
        if platform == Platform.UNKNOWN:
            QMessageBox.warning(
                self,
                "Executável Inválido",
                "Não foi possível identificar a plataforma.\n\n"
                "Selecione o executável wwm.exe do jogo:\n"
                "• Steam: [Steam]\\steamapps\\common\\...\\Engine\\Binaries\\Win64r\\wwm.exe\n"
                "• Epic: [Epic Games]\\...\\Engine\\Binaries\\Win64r\\wwm.exe\n"
                "• Standalone: [wwm]\\wwm_standard\\Engine\\Binaries\\Win64r\\wwm.exe\n"
                "• Standalone Lite: [wwm]\\wwm_lite\\Engine\\Binaries\\Win64r\\wwm.exe"
            )
            return
        
        # Verifica se a pasta de tradução existe
        if not translation_path.exists():
            QMessageBox.warning(
                self,
                "Pasta não encontrada",
                f"A pasta de tradução não foi encontrada:\n{translation_path}\n\n"
                "Verifique se o jogo está instalado corretamente."
            )
            return
        
        # Salva configuração
        self.exe_path = exe_path
        self.platform = platform
        self.game_root = game_root
        self.translation_path = translation_path
        self._save_local_config()
        
        # Atualiza UI
        platform_config = PLATFORM_CONFIG[platform]
        platform_name = platform_config['name']
        
        # Para Standalone, mostra a variante (Standard ou Lite)
        if platform == Platform.STANDALONE:
            exe_str = str(exe_path).lower()
            if "wwm_lite" in exe_str:
                platform_name = "Standalone (Lite)"
            elif "wwm_standard" in exe_str:
                platform_name = "Standalone (Standard)"
        
        self.card_platform.set_value(f"{platform_config['icon']} {platform_name}", Theme.GOLD_PRIMARY)
        self.path_label.setText(str(exe_path))
        self.path_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; border: none;")
        self.game_status.setText(f"✓ Pasta de tradução: {translation_path}")
        self.game_status.setStyleSheet(f"color: {Theme.SUCCESS}; border: none;")
        
        self.play_btn.setEnabled(True)
        self.install_btn.setEnabled(True)
        
        # Verifica status da tradução local
        self._update_translation_status()
        
        # Verifica automaticamente se há atualizações online
        self.check_for_updates()
    
    def _update_translation_status(self):
        """Atualiza o status da tradução instalada"""
        if not self.translation_path:
            return
        
        checker = TranslationChecker(str(self.translation_path))
        status = checker.get_status()
        
        # Atualiza cards
        if status['status'] == TranslationStatus.NOT_INSTALLED:
            self.card_status.set_value("Original", Theme.TEXT_SECONDARY)
            self.card_installed.set_value("Não instalada")
            self.install_btn.setText("⬇ INSTALAR TRADUÇÃO")
            self.install_btn.setVisible(True)
            self.restore_btn.setVisible(False)
            self.status_label.setText("Pronto para instalar a tradução PT-BR")
            self.status_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
            
        elif status['status'] == TranslationStatus.INSTALLED:
            self.card_status.set_value("✓ PT-BR Ativo", Theme.SUCCESS)
            self.card_installed.set_value(status['installed_version'] or "Instalada", Theme.SUCCESS)
            # Botão de instalar fica oculto até verificar se há atualização
            self.install_btn.setVisible(False)
            self.restore_btn.setVisible(status['has_backup'])
            self.status_label.setText(status['message'])
            self.status_label.setStyleSheet(f"color: {Theme.SUCCESS};")
            
        elif status['status'] == TranslationStatus.OVERWRITTEN:
            self.card_status.set_value("⚠ Sobrescrita", Theme.WARNING)
            self.card_installed.set_value("Necessita reinstalar", Theme.WARNING)
            self.install_btn.setText("🔄 REINSTALAR TRADUÇÃO")
            self.install_btn.setVisible(True)
            self.restore_btn.setVisible(status['has_backup'])
            self.status_label.setText("⚠ " + status['message'])
            self.status_label.setStyleSheet(f"color: {Theme.WARNING};")
    
    def check_for_updates(self):
        """Verifica atualizações da tradução"""
        self.check_btn.setEnabled(False)
        self.check_btn.setText("⏳ Verificando...")
        self.card_available.set_value("🔍 Buscando...", Theme.TEXT_SECONDARY)
        self.status_label.setText("Conectando ao GitHub...")
        self.status_label.setStyleSheet(f"color: {Theme.INFO};")
        
        self.update_thread = CheckUpdateThread()
        self.update_thread.finished_signal.connect(self.on_update_check_finished)
        self.update_thread.start()
    
    def on_update_check_finished(self, success: bool, version: str, timestamp: str, url: str, message: str):
        """Callback da verificação de atualização"""
        self.check_btn.setEnabled(True)
        self.check_btn.setText("🔄 Verificar")
        
        if success:
            self.latest_version = version
            self.latest_timestamp = timestamp
            self.download_url = url
            self.card_available.set_value(version, Theme.GOLD_PRIMARY)
            
            # Atualiza status se tiver plataforma detectada
            if self.translation_path:
                # Verifica se precisa atualizar baseado na versão
                checker = TranslationChecker(str(self.translation_path))
                config = checker.config
                installed_version = config.get_installed_version()
                
                if not config.is_translation_installed():
                    # Tradução não instalada - mostra botão de instalar
                    self.install_btn.setText("⬇ INSTALAR TRADUÇÃO")
                    self.install_btn.setVisible(True)
                    self.status_label.setText("Pronto para instalar a tradução PT-BR")
                    self.status_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
                elif installed_version and version:
                    comparison = self._compare_versions(version, installed_version)
                    if comparison > 0:
                        # Há atualização disponível - mostra botão
                        self.status_label.setText(f"🎉 Nova versão disponível: v{version}")
                        self.status_label.setStyleSheet(f"color: {Theme.GOLD_PRIMARY};")
                        self.install_btn.setText("⬆ ATUALIZAR TRADUÇÃO")
                        self.install_btn.setVisible(True)
                    elif comparison < 0:
                        # Versão instalada é MAIOR que a disponível (release apagada)
                        # Oferece reinstalar para a versão estável
                        self.status_label.setText(f"⚠ Versão instalada ({installed_version}) não encontrada online")
                        self.status_label.setStyleSheet(f"color: {Theme.WARNING};")
                        self.install_btn.setText("🔄 REINSTALAR v" + version)
                        self.install_btn.setVisible(True)
                        self.card_installed.set_value(installed_version, Theme.WARNING)
                    else:
                        # Tradução está atualizada - oculta botão
                        self.status_label.setText("✓ Tradução está atualizada")
                        self.status_label.setStyleSheet(f"color: {Theme.SUCCESS};")
                        self.install_btn.setVisible(False)
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
        if not self.translation_path:
            QMessageBox.warning(self, "Erro", "Selecione o executável do jogo primeiro!")
            return
        
        if not self.download_url:
            QMessageBox.warning(self, "Erro", "Verifique as atualizações primeiro!")
            return
        
        # Verifica permissão de escrita
        if not self._check_write_permission():
            return
        
        # Confirmação
        reply = QMessageBox.question(
            self,
            "Confirmar Instalação",
            f"Deseja instalar a tradução PT-BR v{self.latest_version}?\n\n"
            "📁 O backup dos arquivos originais será preservado.\n"
            "(Atualizações não sobrescrevem o backup original)",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Inicia download
        self.install_btn.setEnabled(False)
        self.check_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        temp_file = tempfile.mktemp(suffix='.zip')
        
        self.download_thread = DownloadThread(self.download_url, temp_file)
        self.download_thread.progress_signal.connect(self.progress_bar.setValue)
        self.download_thread.status_signal.connect(self.status_label.setText)
        self.download_thread.finished_signal.connect(self.on_download_finished)
        self.download_thread.start()
    
    def on_download_finished(self, success: bool, result: str):
        """Callback do download"""
        if success:
            try:
                self.status_label.setText("Extraindo arquivos...")
                
                locale_path = self.translation_path
                temp_extract_dir = tempfile.mkdtemp(prefix='wwm_translation_')
                
                files_installed = []
                files_backed_up = []
                file_hashes = {}
                
                try:
                    with zipfile.ZipFile(result, 'r') as zip_ref:
                        zip_ref.extractall(temp_extract_dir)
                    
                    for translation_file in TRANSLATION_FILES:
                        source_file = self._find_file_in_directory(temp_extract_dir, translation_file)
                        
                        if source_file:
                            dest_file = locale_path / translation_file
                            
                            # Backup do arquivo original
                            if dest_file.exists():
                                backup_file = dest_file.with_suffix('.backup')
                                # Só faz backup se não existir (preserva o original real)
                                if not backup_file.exists():
                                    shutil.copy2(dest_file, backup_file)
                                    files_backed_up.append(translation_file)
                            
                            # Copia o novo arquivo
                            shutil.copy2(source_file, dest_file)
                            files_installed.append(translation_file)
                            
                            # Calcula hash
                            file_hashes[translation_file] = get_file_hash(str(dest_file))
                    
                    shutil.rmtree(temp_extract_dir, ignore_errors=True)
                    
                except zipfile.BadZipFile:
                    shutil.rmtree(temp_extract_dir, ignore_errors=True)
                    raise Exception("Arquivo ZIP inválido")
                
                os.unlink(result)
                
                if files_installed:
                    # Salva configuração da tradução
                    config = TranslationConfig(str(locale_path))
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    config.set_installed(self.latest_version, timestamp, file_hashes)
                    
                    self._update_translation_status()
                    
                    self.status_label.setText("✓ Tradução instalada com sucesso!")
                    self.status_label.setStyleSheet(f"color: {Theme.SUCCESS};")
                    
                    msg = f"Tradução v{self.latest_version} instalada com sucesso!\n\n"
                    msg += f"📦 Arquivos instalados:\n"
                    for f in files_installed:
                        msg += f"   • {f}\n"
                    
                    if files_backed_up:
                        msg += f"\n💾 Backups criados:\n"
                        for f in files_backed_up:
                            msg += f"   • {f}.backup\n"
                    
                    QMessageBox.information(self, "Sucesso!", msg)
                else:
                    raise Exception("Nenhum arquivo de tradução encontrado no pacote.")
                
            except Exception as e:
                self.status_label.setText(f"❌ Erro: {str(e)}")
                self.status_label.setStyleSheet(f"color: {Theme.ERROR};")
                QMessageBox.critical(self, "Erro", f"Erro ao instalar:\n{str(e)}")
        else:
            self.status_label.setText(f"❌ Erro no download: {result}")
            self.status_label.setStyleSheet(f"color: {Theme.ERROR};")
        
        self.install_btn.setEnabled(True)
        self.check_btn.setEnabled(True)
        self.restore_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def _check_write_permission(self) -> bool:
        """Verifica se tem permissão de escrita na pasta de tradução"""
        try:
            # Tenta criar um arquivo temporário na pasta
            test_file = self.translation_path / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except PermissionError:
            reply = QMessageBox.question(
                self,
                "Permissão Necessária",
                "A pasta do jogo requer permissão de administrador para modificar.\n\n"
                f"Pasta: {self.translation_path}\n\n"
                "Deseja reiniciar o launcher como Administrador?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                run_as_admin()
            return False
        except Exception as e:
            QMessageBox.warning(
                self,
                "Erro de Permissão",
                f"Não foi possível acessar a pasta:\n{self.translation_path}\n\n"
                f"Erro: {str(e)}"
            )
            return False
    
    def _find_file_in_directory(self, directory: str, filename: str) -> str:
        """Procura um arquivo recursivamente"""
        for root, dirs, files in os.walk(directory):
            if filename in files:
                return os.path.join(root, filename)
        return None
    
    def restore_backup(self):
        """Restaura os arquivos originais"""
        if not self.translation_path:
            return
        
        # Verifica permissão de escrita
        if not self._check_write_permission():
            return
        
        reply = QMessageBox.question(
            self,
            "Restaurar Original",
            "Deseja restaurar os arquivos originais do jogo?\n\n"
            "Isso irá REMOVER a tradução PT-BR.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            locale_path = self.translation_path
            files_restored = []
            
            for translation_file in TRANSLATION_FILES:
                backup_file = locale_path / f"{translation_file}.backup"
                original_file = locale_path / translation_file
                
                if backup_file.exists():
                    if original_file.exists():
                        original_file.unlink()
                    
                    shutil.move(str(backup_file), str(original_file))
                    files_restored.append(translation_file)
            
            if files_restored:
                # Remove configuração
                config = TranslationConfig(str(locale_path))
                config.clear()
                
                self._update_translation_status()
                
                self.status_label.setText("✓ Arquivos originais restaurados!")
                self.status_label.setStyleSheet(f"color: {Theme.SUCCESS};")
                
                msg = "Arquivos originais restaurados!\n\n"
                msg += "📦 Arquivos restaurados:\n"
                for f in files_restored:
                    msg += f"   • {f}\n"
                
                QMessageBox.information(self, "Sucesso!", msg)
            else:
                QMessageBox.warning(self, "Aviso", "Nenhum backup encontrado.")
                self.restore_btn.setVisible(False)
                
        except Exception as e:
            self.status_label.setText(f"❌ Erro: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao restaurar:\n{str(e)}")
    
    def launch_game(self):
        """Inicia o jogo"""
        if not self.exe_path or not self.platform:
            return
        
        if self.platform == Platform.STANDALONE:
            # Standalone: executa o launcher.exe relativo ao game_root
            # game_root: [pasta]/wwm_standard/
            # launcher: [pasta]/Win32/deploy/launcher.exe
            # Então: game_root.parent / Win32 / deploy / launcher.exe
            launcher_exe = self.game_root.parent / "Win32" / "deploy" / "launcher.exe"
            
            if launcher_exe.exists():
                os.startfile(str(launcher_exe))
            else:
                QMessageBox.warning(
                    self,
                    "Launcher não encontrado",
                    f"O launcher.exe não foi encontrado em:\n{launcher_exe}\n\n"
                    "Verifique se o jogo está instalado corretamente."
                )
                return
        elif self.platform == Platform.STEAM:
            webbrowser.open(PLATFORM_CONFIG[Platform.STEAM]["launch_command"])
        elif self.platform == Platform.EPIC:
            webbrowser.open(PLATFORM_CONFIG[Platform.EPIC]["launch_command"])
        
        self.showMinimized()
    
    def check_launcher_update(self):
        """Verifica nova versão do launcher"""
        self.launcher_check_thread = CheckLauncherUpdateThread(APP_VERSION)
        self.launcher_check_thread.finished_signal.connect(self.on_launcher_update_check)
        self.launcher_check_thread.start()
    
    def on_launcher_update_check(self, success: bool, version: str, download_url: str, message: str):
        """Callback da verificação do launcher"""
        if success and version:
            if self._compare_versions(version, APP_VERSION) > 0:
                self.launcher_update_btn.setText(f"⬆ Nova versão v{version} disponível - Clique para baixar")
                self.launcher_update_btn.setVisible(True)
    
    # ========================================================================
    # EVENTOS DE JANELA
    # ========================================================================
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Verifica se está no canto inferior direito para redimensionar
            margin = 20
            rect = self.rect()
            if (event.pos().x() >= rect.width() - margin and 
                event.pos().y() >= rect.height() - margin):
                self.resizing = True
                self.resize_start = event.globalPos()
                self.resize_size = self.size()
            else:
                self.resizing = False
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if hasattr(self, 'resizing') and self.resizing:
                # Redimensionando
                delta = event.globalPos() - self.resize_start
                new_width = max(self.minimumWidth(), self.resize_size.width() + delta.x())
                new_height = max(self.minimumHeight(), self.resize_size.height() + delta.y())
                self.resize(new_width, new_height)
            elif hasattr(self, 'drag_position'):
                # Arrastando
                self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            # Muda cursor no canto inferior direito
            margin = 20
            rect = self.rect()
            if (event.pos().x() >= rect.width() - margin and 
                event.pos().y() >= rect.height() - margin):
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
    
    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.setCursor(Qt.ArrowCursor)
        event.accept()


# ============================================================================
# PONTO DE ENTRADA
# ============================================================================

def main():
    # Configurações de High DPI - devem vir ANTES de criar QApplication
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
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
