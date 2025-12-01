# 🇧🇷 WWM Brasileiro - Tradução PT-BR para Where Winds Meet

<div align="center">

![WWM Brasileiro Banner](https://img.shields.io/badge/⚔_Where_Winds_Meet-Tradução_Brasileiro-c9a227?style=for-the-badge&labelColor=0a0a0f)

[![Website](https://img.shields.io/badge/🌐_Site_Oficial-Acesse_Aqui-c9a227?style=for-the-badge)](https://rodrigomiquilino.github.io/wwm_brasileiro/)
[![Steam](https://img.shields.io/badge/Steam-Jogo_Gratuito-1b2838?style=for-the-badge&logo=steam)](https://store.steampowered.com/app/3564740/Where_Winds_Meet/)
[![Release](https://img.shields.io/github/v/release/rodrigomiquilino/wwm_brasileiro?style=for-the-badge&label=Versão&color=2e7d32)](https://github.com/rodrigomiquilino/wwm_brasileiro/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/rodrigomiquilino/wwm_brasileiro/total?style=for-the-badge&label=Downloads&color=1565c0)](https://github.com/rodrigomiquilino/wwm_brasileiro/releases)
[![Licença](https://img.shields.io/badge/Licença-MIT-green?style=for-the-badge)](LICENSE)

**Tradução completa e não-oficial em Português Brasileiro para Where Winds Meet**

---

### ⬇️ Download Rápido

[![Download Launcher](https://img.shields.io/badge/⬇_BAIXAR_LAUNCHER-WWM__Tradutor__PTBR.exe-c9a227?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/rodrigomiquilino/wwm_brasileiro/releases/latest/download/WWM_Tradutor_PTBR.exe)

[![Download Manual](https://img.shields.io/badge/📦_Download_Manual-traducao__ptbr.zip-blue?style=flat-square)](https://github.com/rodrigomiquilino/wwm_brasileiro/releases/latest/download/traducao_ptbr.zip)

---

[🚀 Launcher](#-launcher-automático) • [📁 Manual](#-instalação-manual) • [✨ Recursos](#-recursos-do-launcher) • [🛠️ Desenvolvedores](#️-para-desenvolvedores) • [🤝 Contribuir](#-como-contribuir)

</div>

---

## 📖 Sobre o Projeto

**Where Winds Meet** é um RPG de ação-aventura em mundo aberto no gênero Wuxia, ambientado na China do século X durante a Dinastia Song. O jogo é **gratuito na Steam** e suporta modo solo, cooperativo e PvP.

Este projeto oferece uma **tradução completa** para **Português Brasileiro**, desenvolvida pela comunidade brasileira.

### O que está traduzido?

| Conteúdo | Status |
|----------|--------|
| 💬 Diálogos e Missões | ✅ Traduzido |
| 🖥️ Interface e Menus | ✅ Traduzido |
| ⚔️ Habilidades e Talentos | ✅ Traduzido |
| 📦 Itens e Equipamentos | ✅ Traduzido |
| 📜 Lore e Ambientação | ✅ Traduzido |
| 🗺️ Localizações | ✅ Traduzido |

> 📚 Baseado no trabalho da comunidade russa [wwm_russian](https://github.com/DOG729/wwm_russian)

---

## 🚀 Launcher Automático

A forma mais fácil de instalar a tradução! O launcher faz tudo por você.

<div align="center">

[![Download Launcher](https://img.shields.io/badge/⬇_BAIXAR_LAUNCHER_(40MB)-WWM__Tradutor__PTBR.exe-c9a227?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/rodrigomiquilino/wwm_brasileiro/releases/latest/download/WWM_Tradutor_PTBR.exe)

</div>

### ✨ Recursos do Launcher

| Recurso | Descrição |
|---------|-----------|
| 🔍 **Detecção Automática** | Encontra sua instalação do jogo automaticamente |
| 📦 **Instalação com 1 Clique** | Baixa e instala a tradução instantaneamente |
| 💾 **Backup Automático** | Cria backup dos arquivos originais (.backup) |
| 🔄 **Verificação de Atualizações** | Verifica se há novas versões disponíveis |
| 🎮 **Iniciar via Steam** | Inicia o jogo diretamente pelo launcher |
| 🎨 **Interface Moderna** | Design escuro com tema oriental/wuxia |

### Como Usar

1. **Baixe** o `WWM_Tradutor_PTBR.exe`
2. **Execute** o arquivo (não precisa instalar)
3. **Clique** em "Instalar Tradução"
4. **Pronto!** Jogue em português 🎮

<details>
<summary>📸 Screenshots do Launcher</summary>

O launcher possui uma interface moderna com:
- Detecção automática do caminho do jogo
- Cards mostrando versão instalada e disponível
- Barra de progresso durante o download
- Botões para instalar, verificar atualizações e iniciar o jogo

</details>

---

## 📁 Instalação Manual

Prefere instalar manualmente? Sem problemas!

<div align="center">

[![Download ZIP](https://img.shields.io/badge/📦_BAIXAR_ZIP-traducao__ptbr.zip-blue?style=for-the-badge)](https://github.com/rodrigomiquilino/wwm_brasileiro/releases/latest/download/traducao_ptbr.zip)

</div>

### Passo a Passo

1. **Baixe** o arquivo `traducao_ptbr.zip`

2. **Extraia** os arquivos

3. **Copie** para a pasta do jogo:
   ```
   C:\Program Files (x86)\Steam\steamapps\common\Where Winds Meet\Package\HD\oversea\locale\
   ```

4. **Substitua** os arquivos quando perguntado:
   - `translate_words_map_en`
   - `translate_words_map_en_diff`

5. **Inicie** o jogo pela Steam!

### 📂 Arquivos Incluídos no ZIP

| Arquivo | Descrição |
|---------|-----------|
| `translate_words_map_en` | Arquivo principal de tradução (~30k strings) |
| `translate_words_map_en_diff` | Arquivo de traduções adicionais (~20k strings) |

> 💡 **Dica:** Faça backup dos arquivos originais antes de substituir!

---

## 🛠️ Para Desenvolvedores

Quer contribuir ou criar sua própria versão? Temos ferramentas completas!

### Ferramentas Disponíveis

#### 🔧 Tradutor GUI (v2.1.0)

```bash
# Instalar dependências
py -m pip install -r requirements.txt

# Executar
py tools/wwm_tradutor_ptbr.py
```

**Funcionalidades:**
- 📦 Extrair arquivos binários do jogo
- 📝 Converter para TSV editável (Excel/Google Sheets)
- 🔄 Reempacotar com suas traduções
- 📊 Suporte completo a arquivos `_diff`

#### 🚀 Launcher (v1.1.0)

```bash
# Executar código fonte
py launcher/wwm_ptbr_launcher.py

# Compilar executável
py -m pip install pyinstaller
py -m PyInstaller --onefile --windowed --icon "icon.ico" --name "WWM_Tradutor_PTBR" wwm_ptbr_launcher.py
```

### 📁 Estrutura do Projeto

```
wwm_brasileiro/
├── 📂 docs/                     # Site GitHub Pages
│   ├── index.html              # Página principal
│   ├── 404.html                # Página de erro
│   └── _config.yml             # Configuração
├── 📂 launcher/                 # Instalador automático
│   ├── wwm_ptbr_launcher.py    # Código fonte (v1.1.0)
│   ├── icon.ico                # Ícone do executável
│   └── build.bat               # Script de build
├── 📂 tools/                    # Ferramentas de tradução
│   └── wwm_tradutor_ptbr.py    # GUI de tradução (v2.1.0)
├── translation_en.tsv          # Textos originais
├── translation_ptbr.tsv        # Traduções PT-BR
└── requirements.txt            # Dependências
```

---

## 🤝 Como Contribuir

Adoramos contribuições da comunidade!

### 📝 Melhorar a Tradução

1. Fork este repositório
2. Edite o arquivo `translation_ptbr.tsv`
3. Envie um Pull Request

### 🐛 Reportar Bugs

Encontrou um erro? [Abra uma issue](https://github.com/rodrigomiquilino/wwm_brasileiro/issues/new)

### ⭐ Apoiar o Projeto

Gostou? Dê uma estrela no repositório! ⭐

---

## 📖 Documentação

| Documento | Descrição |
|-----------|-----------|
| [🌐 Site Oficial](https://rodrigomiquilino.github.io/wwm_brasileiro/) | Downloads e instruções |
| [📋 Releases](https://github.com/rodrigomiquilino/wwm_brasileiro/releases) | Histórico de versões |
| [📝 localization_ptbr.md](docs/localization_ptbr.md) | Guia de tradução |
| [🏷️ tags.md](docs/tags.md) | Referência de tags especiais |

---

## 🔗 Links Úteis

| Link | Descrição |
|------|-----------|
| [🎮 Steam - Where Winds Meet](https://store.steampowered.com/app/3564740/Where_Winds_Meet/) | Página do jogo (Gratuito) |
| [🇷🇺 Projeto Russo](https://github.com/DOG729/wwm_russian) | Projeto base |
| [💬 Discord](https://discordapp.com/users/rodrigo.dev) | Contato direto |

---

## 👥 Créditos

<table>
<tr>
<td align="center"><strong>WWM Brasileiro</strong></td>
<td align="center"><strong>Projeto Base</strong></td>
</tr>
<tr>
<td align="center">
<a href="https://github.com/rodrigomiquilino">
<img src="https://github.com/rodrigomiquilino.png" width="60" style="border-radius: 50%"><br>
<strong>rodrigomiquilino</strong>
</a><br>
<sub>Criador & Mantenedor</sub>
</td>
<td align="center">
<a href="https://github.com/DOG729">
<img src="https://github.com/DOG729.png" width="60" style="border-radius: 50%"><br>
<strong>DOG729</strong>
</a><br>
<sub>Projeto Russo Original</sub>
</td>
</tr>
</table>

---

## 📄 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).

Você é livre para usar, modificar e distribuir este projeto.

---

<div align="center">

### ⚔️ Feito com ❤️ pela Comunidade WWM Brasil

[![GitHub](https://img.shields.io/badge/GitHub-rodrigomiquilino-181717?style=for-the-badge&logo=github)](https://github.com/rodrigomiquilino)
[![Discord](https://img.shields.io/badge/Discord-rodrigo.dev-5865F2?style=for-the-badge&logo=discord)](https://discordapp.com/users/rodrigo.dev)

---

*Where Winds Meet © Everstone Games*  
*Este é um projeto não-oficial da comunidade brasileira.*

**🇧🇷 Jogue em Português! 🇧🇷**

</div>
