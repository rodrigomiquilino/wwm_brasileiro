# WWM Tradutor PT-BR - Launcher

Launcher para instalação e atualização automática da tradução brasileira de **Where Winds Meet**.

## 🎮 Funcionalidades

- **Detecção automática** do jogo instalado
- **Verificação de atualizações** diretamente do GitHub
- **Download e instalação** automática da tradução
- **Interface moderna** com tema oriental/wuxia
- **Backup automático** do arquivo original

## 📥 Como Usar

### Opção 1: Executável (Recomendado)
1. Baixe o `WWM Tradutor PT-BR.exe` da [página de releases](https://github.com/rodrigomiquilino/wwm_brasileiro/releases)
2. Execute o programa
3. O launcher detectará automaticamente o jogo (ou selecione manualmente)
4. Clique em **INSTALAR TRADUÇÃO**
5. Pronto! Clique em **Iniciar Jogo** para jogar

### Opção 2: Python
```bash
# Instale as dependências
pip install PyQt5 requests

# Execute o launcher
python wwm_ptbr_launcher.py
```

## 🔧 Compilar o Executável

Para criar o `.exe`, execute o script de build:

```bash
# Windows
build.bat
```

Ou manualmente:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "WWM Tradutor PT-BR" wwm_ptbr_launcher.py
```

## 📁 Estrutura

```
launcher/
├── wwm_ptbr_launcher.py    # Código fonte do launcher
├── build.bat               # Script de compilação
├── wwm_ptbr_config.json    # Configurações salvas (gerado automaticamente)
└── README.md               # Este arquivo
```

## ⚙️ Configuração

O launcher salva automaticamente:
- Caminho do jogo detectado/selecionado
- Versão da tradução instalada

O arquivo `wwm_ptbr_config.json` é criado na mesma pasta do launcher.

## 🌐 Atualizações

O launcher verifica automaticamente a release mais recente em:
https://github.com/rodrigomiquilino/wwm_brasileiro/releases

Para que o download automático funcione, a release deve conter um arquivo chamado `translate_words_map_en` nos assets.

## 📋 Requisitos

- Windows 10/11
- Where Winds Meet instalado (Steam)
- Python 3.8+ (apenas para versão .py)

## 🎨 Tema Visual

O launcher utiliza um tema escuro com acentos dourados, inspirado na estética oriental/wuxia do jogo Where Winds Meet.

---

**Comunidade WWM Brasil** • [GitHub](https://github.com/rodrigomiquilino/wwm_brasileiro)
