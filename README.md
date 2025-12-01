# 🇧🇷 WWM Brasileiro - Tradução PT-BR para Where Winds Meet

<div align="center">

[![Steam](https://img.shields.io/badge/Steam-Where%20Winds%20Meet-1b2838?style=for-the-badge&logo=steam)](https://store.steampowered.com/app/3564740/Where_Winds_Meet/)
[![Licença](https://img.shields.io/badge/Licença-MIT-green?style=for-the-badge)](LICENSE)
[![Release](https://img.shields.io/github/v/release/rodrigomiquilino/wwm_brasileiro?style=for-the-badge&label=Versão)](https://github.com/rodrigomiquilino/wwm_brasileiro/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/rodrigomiquilino/wwm_brasileiro/total?style=for-the-badge&label=Downloads)](https://github.com/rodrigomiquilino/wwm_brasileiro/releases)

**Tradução não-oficial em Português Brasileiro para Where Winds Meet**

[📥 Download](#-instalação) • [🛠️ Ferramentas](#️-ferramentas) • [📖 Documentação](#-documentação) • [🤝 Contribuir](#-como-contribuir)

</div>

---

## 📖 Sobre

**Where Winds Meet** é um RPG de ação-aventura em mundo aberto no gênero Wuxia, ambientado na China do século X durante a Dinastia Song. O jogo é gratuito na Steam e suporta modo solo, cooperativo e PvP.

Este projeto oferece uma tradução completa da interface e textos do jogo para Português Brasileiro.

> Baseado no trabalho da comunidade russa [wwm_russian](https://github.com/DOG729/wwm_russian)

---

## 📥 Instalação

### Método 1: Launcher (Recomendado)

1. Baixe o **[WWM Tradutor PT-BR.exe](https://github.com/rodrigomiquilino/wwm_brasileiro/releases/latest)**
2. Execute o launcher
3. O programa detectará automaticamente sua instalação
4. Clique em **Instalar Tradução**
5. Pronto!

### Método 2: Manual

1. Baixe `translate_words_map_en` da [releases](https://github.com/rodrigomiquilino/wwm_brasileiro/releases/latest)
2. Navegue até:
   ```
   Steam\steamapps\common\Where Winds Meet\Package\HD\oversea\locale\
   ```
3. Substitua o arquivo `translate_words_map_en`
4. Inicie o jogo

---

## 🛠️ Ferramentas

### Tradutor (Para desenvolvedores)

```bash
pip install -r requirements.txt
python tools/wwm_tradutor_ptbr.py
```

- 📦 Extrair arquivos do jogo
- 📝 Editar traduções em TSV
- 📦 Empacotar de volta

### Launcher (Para usuários)

```bash
python launcher/wwm_ptbr_launcher.py
```

---

## 📁 Estrutura

```
wwm_brasileiro/
├── launcher/                    # Instalador automático
│   └── wwm_ptbr_launcher.py
├── tools/                       # Ferramentas de tradução
│   └── wwm_tradutor_ptbr.py
├── docs/                        # Documentação
│   ├── localization_ptbr.md
│   └── tags.md
├── translation_en.tsv          # Textos originais
├── translation_ptbr.tsv        # Traduções PT-BR
└── requirements.txt
```

---

## 📖 Documentação

| Documento | Descrição |
|-----------|-----------|
| [localization_ptbr.md](docs/localization_ptbr.md) | Guia de tradução |
| [tags.md](docs/tags.md) | Referência de tags |

---

## 🤝 Como Contribuir

1. Fork este repositório
2. Edite `translation_ptbr.tsv`
3. Envie um Pull Request

### Regras

- ✅ Preservar tags (`{0}`, `#G...#E`, `<...|...>`)
- ✅ Manter nomes próprios em Pinyin
- ✅ Traduzir naturalmente
- ✅ Verificar ortografia

---

## 🔗 Links

- [Steam](https://store.steampowered.com/app/3564740/Where_Winds_Meet/)
- [Projeto Russo](https://github.com/DOG729/wwm_russian)
- [Releases](https://github.com/rodrigomiquilino/wwm_brasileiro/releases)

---

## 👥 Créditos

### WWM Brasileiro
- **[rodrigomiquilino](https://github.com/rodrigomiquilino)** — Criador e mantenedor

### Projeto Original
- **[DOG729](https://github.com/DOG729)** — Criador do projeto russo
- **[ZoG Community](https://forum.zoneofgames.ru/topic/80635-where-winds-meet)**

---

## 📄 Licença

[MIT License](LICENSE) — Projeto da comunidade, não oficial.
