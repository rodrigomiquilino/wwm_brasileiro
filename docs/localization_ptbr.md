# Regras de Tradução para translation_ptbr.tsv

## 📋 Princípios Gerais

### 1. Estratégia de Tradução

**⚠️ IMPORTANTE:** Ao traduzir, NÃO faça traduções literais palavra por palavra. Em vez disso:

- Adapte o texto para soar natural em Português Brasileiro
- Mantenha o tom e estilo do jogo (Wuxia, China medieval)
- Preserve nomes próprios chineses na romanização Pinyin

**Exemplo:**

- ❌ Ruim: "Complete any Hero Kingdom or Sword Trial at least once" → "Complete qualquer Reino de Herói ou Prova de Espada pelo menos uma vez"
- ✅ Bom: "Complete any Hero Kingdom or Sword Trial at least once" → "Conclua o Reino do Herói ou Desafio da Espada ao menos uma vez"

### 2. Verificação Ortográfica

**Obrigatório verificar:**

- Ortografia de todas as palavras
- Uso correto de maiúsculas/minúsculas
- Pontuação (vírgulas, pontos, travessões, dois-pontos)
- Concordância de gênero, número e pessoa
- Grafia correta de termos do jogo

**Ferramentas recomendadas:**

- Corretor ortográfico do editor de texto
- LanguageTool (extensão)
- VOLP (Vocabulário Ortográfico da Língua Portuguesa)

### 3. Preservação de Tags do Jogo

**CRÍTICO:** Nunca altere ou remova tags do jogo! Veja detalhes em [`tags.md`](tags.md).

#### Tipos principais de tags:

| Tag | Exemplo | Função |
|-----|---------|--------|
| `{0}`, `{1}` | `({0}/7)` | Variáveis dinâmicas |
| `#G...#E` | `#G140%#E` | Cores (verde) |
| `<...\|...\|...>` | `<Nome\|780\|#C\|15>` | Links/referências |
| `$T()`, `$S`, `$E` | - | Condicionais |
| `\n`, `\r` | - | Quebras de linha |

**Exemplo de tradução correta com tags:**

```
Original: "Login for 7 Days ({0}/7)"
Tradução: "Entre por 7 dias ({0}/7)"
```

**Exemplo de tradução INCORRETA:**

```
Original: "Login for 7 Days ({0}/7)"
❌ Errado: "Entre por 7 dias (0/7)" - removeu a variável
❌ Errado: "Entre por 7 dias {0}/7" - alterou os parênteses
```

### 4. Uso de IA para Tradução

Se usar IA (ChatGPT, Claude, DeepSeek, etc.), use este prompt:

---

#### Prompt para IA:

```
Você é um tradutor de um jogo no gênero Wuxia chinês (artes marciais).
Os dados são um arquivo TSV.

Sua tarefa é traduzir o texto para Português do Brasil, seguindo rigorosamente estas regras:

1. Todas as tags devem permanecer INTACTAS.
   Tags incluem:
   - Qualquer construção como: {}, %%, $T(), $S, $E
   - Palavras com "_" e números (ex: Ground_11, Obj_32, Skill_5)
   - Sequências de escape: \n, \r, \t (não remover ou mover)
   - Elementos no formato <...|...|...|...>
   
2. Traduzir APENAS texto que NÃO seja tag.
   Exemplo permitido de tradução de tag-parâmetro:
   <Ataque Físico Máx.|780|#C|15>
   (se o original tem texto, pode traduzir, mas manter estrutura "<", ">", "|")

3. Não alterar estrutura do TSV:
   - Quantidade de colunas
   - Ordem das colunas
   - Separadores
   - Quebras de linha no arquivo

4. Não quebrar linhas longas.
   Se a linha for longa (~280 caracteres), mantenha sentido, estilo e tamanho aproximado.

5. Não editar, remover ou mover tags, parâmetros, códigos de cor e formatação como:
   #G140%#E, <...>, {}, %% e construções similares.

Traduza com cuidado, mantendo o estilo e atmosfera de Wuxia.
```

---

## ✅ Checklist Antes de Salvar

- [ ] Texto traduzido de forma natural, não literal
- [ ] Todas as tags do jogo preservadas sem alterações
- [ ] Ortografia verificada
- [ ] Pontuação correta
- [ ] Estilo adequado ao contexto do jogo
- [ ] Tradução soa natural em Português Brasileiro

## 📝 Recomendações Adicionais

- Use terminologia consistente (consulte o dicionário do projeto)
- Mantenha o estilo de diálogos e descrições
- Considere o contexto (Wuxia, China antiga, artes marciais)
- Em caso de dúvida, consulte outros participantes do projeto
- Nomes chineses: manter em Pinyin (ex: Li Wei, Zhang San)

## 🎯 Glossário Básico PT-BR

| Inglês | Português |
|--------|-----------|
| Quest | Missão |
| Skill | Habilidade |
| Item | Item |
| Weapon | Arma |
| Armor | Armadura |
| Health | Vida |
| Stamina | Vigor |
| Experience | Experiência |
| Level | Nível |
| Guild | Guilda |
| Party | Grupo |
| Dungeon | Masmorra |
| Boss | Chefe |
| NPC | NPC |
| Reward | Recompensa |
| Inventory | Inventário |
| Equipment | Equipamento |

---

**Veja também:**

- [`tags.md`](tags.md) - Descrição detalhada das tags do jogo
- [README.md](../README.md) - Informações gerais do projeto
- [tools/](../tools/) - Ferramentas de tradução
