# WWM Brasileiro - Launcher

Instalador automático da tradução PT-BR para **Where Winds Meet**.

## Funcionalidades

- Detecção automática do jogo
- Verificação de atualizações via GitHub
- Download e instalação automática
- Backup do arquivo original

## Uso

### Executável (Recomendado)

1. Baixe `WWM Tradutor PT-BR.exe` da [releases](https://github.com/rodrigomiquilino/wwm_brasileiro/releases)
2. Execute o programa
3. Clique em **Instalar Tradução**

### Python

```bash
pip install PyQt5 requests
python wwm_ptbr_launcher.py
```

## Build

```bash
build.bat
```

Ou manualmente:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "WWM Tradutor PT-BR" wwm_ptbr_launcher.py
```

## Estrutura

```
launcher/
├── wwm_ptbr_launcher.py    # Código fonte
├── build.bat               # Script de build
└── wwm_ptbr_config.json    # Config (auto-gerado)
```

O arquivo `wwm_ptbr_config.json` é criado na mesma pasta do launcher.

## 🌐 Atualizações

O launcher verifica automaticamente a release mais recente em:
https://github.com/rodrigomiquilino/wwm_brasileiro/releases

Para que o download automático funcione, a release deve conter um arquivo chamado `translate_words_map_en` nos assets.

## 📋 Requisitos

## Requisitos

- Windows 10/11
- Where Winds Meet (Steam)
- Python 3.8+ (apenas versão .py)

---

[rodrigomiquilino](https://github.com/rodrigomiquilino) • [wwm_brasileiro](https://github.com/rodrigomiquilino/wwm_brasileiro)
