# Tags Utilizadas na Tradução - Where Winds Meet

Este documento descreve as tags e formatações especiais usadas nos textos do jogo.

## ⚠️ IMPORTANTE

**NUNCA modifique, remova ou traduza as tags!** Elas são processadas pelo jogo e qualquer alteração pode causar erros ou crashes.

---

## 📋 Lista de Tags

### 1. Variáveis Dinâmicas `{n}`

Placeholders que são substituídos por valores em tempo de execução.

```
Exemplo: "Entrar por 7 dias ({0}/7)"
         → O {0} será substituído pelo progresso atual (ex: 3/7)

Exemplo: "Você tem {0} moedas e {1} diamantes"
         → {0} e {1} serão substituídos pelos valores reais
```

### 2. Cores `#G...#E`

Tags de cor para destacar texto. O texto entre `#G` e `#E` aparece colorido.

```
#G = início da cor (geralmente verde)
#E = fim da cor

Exemplo: "Dano de #G140%#E aplicado"
         → "140%" aparecerá em verde no jogo

Variações comuns:
- #G...#E (verde)
- #R...#E (vermelho)
- #Y...#E (amarelo)
- #C...#E (ciano)
```

### 3. Links/Referências `<...|...|...|...>`

Tags que criam links clicáveis ou referências a itens/objetos do jogo.

```
Formato: <Nome|Valor|Cor|Tamanho>

Exemplo: <Ataque Físico Máx.|780|#C|15>
         → Mostra "Ataque Físico Máx." como link com valor 780

NOTA: O texto dentro pode ser traduzido, mas a estrutura <, >, | deve ser mantida!
```

### 4. Identificadores `id_n` ou `nome_n`

Referências a objetos, NPCs ou locais por ID interno.

```
Exemplo: Ground_11, Obj_32, Skill_5, NPC_Zhang

NUNCA traduzir esses identificadores!
```

### 5. Variáveis Globais `{NOME_VARIAVEL}`

Similar a `{0}`, mas com nomes descritivos.

```
Exemplos:
- {ACR_VALUE} → valor de precisão
- {DOG_VALUE} → valor de esquiva
- {month} {day} → mês e dia atuais
- {player_name} → nome do jogador
```

### 6. Condicionais `$S ... $E`

Marcadores de condições (similar a if/else).

```
Exemplo: $S texto condicional $E

Esses marcadores controlam quando o texto é exibido.
```

### 7. Quebras de Linha `\n` e `\r`

Caracteres de controle para quebra de linha.

```
\n = nova linha (Line Feed)
\r = retorno de carro (Carriage Return)

Exemplo: "Primeira linha\nSegunda linha"

IMPORTANTE: Não remover nem mover esses caracteres!
```

---

## ✅ Exemplos de Tradução Correta

| Original | Correto ✅ | Errado ❌ |
|----------|-----------|----------|
| `Login for {0} days` | `Entre por {0} dias` | `Entre por 0 dias` |
| `Deal #G150%#E damage` | `Cause #G150%#E de dano` | `Cause 150% de dano` |
| `Go to Ground_11` | `Vá até Ground_11` | `Vá até Chão_11` |
| `Line 1\nLine 2` | `Linha 1\nLinha 2` | `Linha 1 Linha 2` |

---

## 📚 Referência Rápida

| Tag | Pode Traduzir? | Exemplo |
|-----|----------------|---------|
| `{0}`, `{1}` | ❌ Não | `{0}/7` |
| `#G...#E` | ❌ Estrutura não | `#G150%#E` |
| `<...\|...\|...>` | ✅ Texto interno | `<Nome\|valor>` |
| `Ground_11` | ❌ Não | `Ground_11` |
| `{NOME}` | ❌ Não | `{player_name}` |
| `$S`, `$E` | ❌ Não | `$S texto $E` |
| `\n`, `\r` | ❌ Não | `texto\ntexto` |

---

**Veja também:**

- [localization_ptbr.md](localization_ptbr.md) - Regras gerais de tradução
- [README.md](../README.md) - Informações do projeto

