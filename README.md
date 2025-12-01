# 🇧🇷 Tradução PT-BR para Where Winds Meet

[![Steam Store Game](https://img.shields.io/badge/Jogo%20na-Steam-blue?style=flat&logo=steam)](https://store.steampowered.com/app/3564740/Where_Winds_Meet/)
[![MIT License](https://img.shields.io/badge/Licença-MIT-green?style=flat)](LICENSE)
[![Português Brasileiro](https://img.shields.io/badge/Idioma-PT--BR-yellow?style=flat)](translation_ptbr.tsv)

## ℹ️ Sobre o Projeto

Esta é uma **tradução não-oficial** em Português do Brasil para o MMO [Where Winds Meet](https://store.steampowered.com/app/3564740/Where_Winds_Meet/) da Everstone Studio e NetEase Games. O projeto foi criado pela comunidade e não está vinculado aos desenvolvedores oficiais do jogo.

**Where Winds Meet** é um épico RPG de ação-aventura em mundo aberto no gênero Wuxia (artes marciais chinesas), ambientado na China do século X durante a Dinastia Song. O jogo é gratuito na Steam e suporta modo solo, cooperativo e PvP.

> 🙏 Este projeto é baseado no trabalho incrível da comunidade russa [wwm_russian](https://github.com/DOG729/wwm_russian)

---

## 📚 Documentação

- **[`docs/tags.md`](docs/tags.md)** — Descrição das tags e formatações usadas no jogo (links, variáveis, cores)
- **[`docs/localization_ptbr.md`](docs/localization_ptbr.md)** — Regras de tradução para **[`translation_ptbr.tsv`](translation_ptbr.tsv)**
- **[`tools/`](tools/)** — Ferramentas de extração e empacotamento

## 🛠️ Ferramentas

### WWM Tradutor PT-BR

Ferramenta GUI em Python para facilitar o processo de tradução:

```bash
# Instalar dependências
pip install pyzstd PyQt5

# Executar
python tools/wwm_tradutor_ptbr.py
```

**Funcionalidades:**
- 📦 Extrair arquivos do jogo (.bin → .dat)
- 📝 Extrair textos para TSV editável
- 🌐 Aplicar traduções de arquivo TSV
- 📦 Empacotar de volta para o jogo

## 📁 Estrutura do Projeto

```
wwm_brasileiro/
├── translation_en.tsv      # Textos originais em inglês (base)
├── translation_ptbr.tsv    # Traduções em Português BR
├── tools/                  # Ferramentas de tradução
│   └── wwm_tradutor_ptbr.py
├── docs/                   # Documentação
│   ├── tags.md
│   └── localization_ptbr.md
├── output/                 # Arquivos gerados
├── www/                    # Interface web
└── old_russo/              # Arquivos do projeto russo original
```

## 🚀 Como Contribuir

1. **Fork** este repositório
2. **Clone** para sua máquina
3. **Traduza** strings do `translation_en.tsv`
4. **Adicione** ao `translation_ptbr.tsv`
5. **Envie** um Pull Request

### Regras de Tradução

- ✅ Preservar TODAS as tags (`{0}`, `#G...#E`, `<...|...>`, etc.)
- ✅ Manter nomes próprios chineses em Pinyin
- ✅ Traduzir de forma natural, não literal
- ✅ Verificar ortografia

Veja [docs/localization_ptbr.md](docs/localization_ptbr.md) para regras detalhadas.

## 🔗 Links Úteis

- [Página do jogo na Steam](https://store.steampowered.com/app/3564740/Where_Winds_Meet/)
- [Projeto russo original](https://github.com/DOG729/wwm_russian)

---

## 👥 Créditos

<details open>
<summary>Expandir</summary>

### Projeto PT-BR
* [rodrigomiquilino](https://github.com/rodrigomiquilino) - Criador e mantenedor

### Projeto Russo Original
* [DOG729](https://github.com/DOG729) - Criador do projeto original
* [Dontaz](https://github.com/Dontaz) - Publicação e promoção
* [Claymore0098](https://github.com/Kirito0098) - Tradução com IA
* [ZoG Community](https://forum.zoneofgames.ru/topic/80635-where-winds-meet)

</details>
