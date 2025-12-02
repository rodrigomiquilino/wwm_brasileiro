# 🚀 Launcher v2.0.0 - Suporte Multi-Plataforma

## Título da Release
```
v2.0.0 - Launcher Multi-Plataforma (Steam, Epic Games, Standalone)
```

## Descrição da Release

```markdown
# 🎮 WWM Tradutor PT-BR v2.0.0

## ✨ Novidades

### 🌐 Suporte Multi-Plataforma
O launcher agora suporta **todas as versões** do jogo:
- **Steam** - Detecta automaticamente e inicia via Steam
- **Epic Games** - Detecta e inicia via Epic Games Launcher
- **Standalone** - Detecta a versão oficial do site chinês

### 🔍 Detecção Inteligente
- Selecione o executável `wwm.exe` e o launcher detecta automaticamente a plataforma
- Encontra a pasta de tradução baseado no caminho do executável
- Não depende mais de caminhos fixos

### 🔐 Permissões Automáticas
- Detecta quando precisa de permissão de administrador
- Pergunta se deseja reiniciar como admin automaticamente
- Útil para jogos instalados em `C:\Program Files\`

### 🖥️ Suporte a DPI Alto
- Funciona corretamente em monitores com escala 125%, 150%, etc.
- Interface não fica cortada ou distorcida

### 🔙 Restaurar Original
- Novo botão para remover a tradução e restaurar arquivos originais
- Só aparece quando há backup disponível
- Útil para troubleshooting ou jogar na versão original

### 📊 Interface Melhorada
- Botão de atualização só aparece quando há nova versão
- Status mais claro (Original, PT-BR Ativo, Sobrescrita)
- Detecção se o jogo sobrescreveu a tradução (após updates)

---

## 📥 Downloads

| Arquivo | Descrição |
|---------|-----------|
| `WWM_Tradutor_PTBR.exe` | Launcher com interface gráfica (~40MB) |
| `traducao_ptbr.zip` | Arquivos de tradução para instalação manual |

---

## 🎯 Como Usar

1. Baixe o `WWM_Tradutor_PTBR.exe`
2. Execute o launcher
3. Clique em "Selecionar" e escolha o `wwm.exe` do seu jogo:
   - **Steam:** `Steam\steamapps\common\...\Engine\Binaries\Win64r\wwm.exe`
   - **Epic:** `Epic Games\...\Engine\Binaries\Win64r\wwm.exe`
   - **Standalone:** `wwm\wwm_standard\Engine\Binaries\Win64r\wwm.exe`
4. Clique em "Instalar Tradução"
5. Jogue em português! 🇧🇷

---

## 🛠️ Changelog Técnico

- Adicionado `Platform` enum (STEAM, EPIC, STANDALONE)
- Adicionado `TranslationStatus` enum para melhor controle de estado
- Implementado `PlatformDetector` para detectar plataforma pelo executável
- Configuração salva na pasta de tradução (`.wwm_ptbr_config`)
- Verificação de integridade via hash MD5
- Suporte a DPI com `SetProcessDpiAwareness` e variáveis Qt
- Solicitação de elevação admin via `ShellExecuteW`
- URLs de launch atualizadas:
  - Steam: `steam://rungameid/3564740`
  - Epic: `com.epicgames.launcher://apps/58a176?action=launch`
  - Standalone: Executa `Win32\deploy\launcher.exe`
```

---

## Comandos Git para Release

```bash
# Tag
git tag -a v2.0.0 -m "Launcher v2.0.0 - Suporte Multi-Plataforma"
git push origin v2.0.0

# Ou criar release pelo GitHub
# https://github.com/rodrigomiquilino/wwm_brasileiro/releases/new
```
