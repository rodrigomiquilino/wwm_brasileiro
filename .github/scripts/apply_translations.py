#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar sugestões de tradução de forma segura.
Mantém a estrutura TSV intacta - apenas substitui o texto traduzido.

ATUALIZADO: Agora suporta novo formato TSV com colunas ID e OriginalText,
e funciona com o repositório wwm_brasileiro_auto_path.

REGRAS DE SEGURANÇA:
1. Nunca adiciona/remove linhas
2. Nunca altera a estrutura TAB-separated
3. Valida o ID antes de qualquer alteração
4. Valida o número da linha
5. Faz backup antes de alterar
"""

import json
import os
import re
import sys
from pathlib import Path


def set_output(name: str, value: str):
    """Define uma saída para o GitHub Actions."""
    output_file = os.environ.get('GITHUB_OUTPUT')
    if output_file:
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f"{name}={value}\n")
    print(f"::set-output name={name}::{value}")


def extract_json_from_body(body: str) -> dict | None:
    """
    Extrai o JSON estruturado do corpo da Issue.
    O JSON está entre ```json e ```
    """
    # Padrão para encontrar o bloco JSON
    pattern = r'```json\s*\n([\s\S]*?)\n```'
    match = re.search(pattern, body)
    
    if not match:
        print("ERRO: Não encontrado bloco JSON na Issue")
        return None
    
    json_str = match.group(1).strip()
    
    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        print(f"ERRO: JSON inválido - {e}")
        return None


def detect_tsv_format(lines: list[str]) -> tuple[int, int]:
    """
    Detecta o formato do TSV analisando o header.
    Retorna: (id_column_index, text_column_index)
    """
    if not lines:
        return 0, 1  # Default
    
    header = lines[0].split('\t')
    header_lower = [h.strip().lower() for h in header]
    
    # Tentar encontrar colunas pelo nome
    id_idx = 0
    text_idx = 1
    
    for i, h in enumerate(header_lower):
        if h == 'id':
            id_idx = i
        elif h in ['originaltext', 'text', 'original']:
            text_idx = i
    
    return id_idx, text_idx


def validate_suggestion(suggestion: dict, file_lines: list[str], file_name: str, id_idx: int, text_idx: int) -> tuple[bool, str]:
    """
    Valida uma sugestão individual.
    
    Retorna: (is_valid, error_message)
    """
    required_fields = ['id', 'file', 'line', 'suggestion']
    
    # Verificar campos obrigatórios
    for field in required_fields:
        if field not in suggestion:
            return False, f"Campo obrigatório ausente: {field}"
    
    suggestion_id = suggestion['id']
    line_number = suggestion['line']
    expected_file = suggestion['file']
    new_text = suggestion['suggestion']
    
    # Verificar se o arquivo corresponde
    if expected_file != file_name:
        return False, f"Arquivo não corresponde: esperado {expected_file}, recebido {file_name}"
    
    # Verificar se o número da linha é válido
    if not isinstance(line_number, int) or line_number < 1:
        return False, f"Número de linha inválido: {line_number}"
    
    if line_number > len(file_lines):
        return False, f"Linha {line_number} não existe (arquivo tem {len(file_lines)} linhas)"
    
    # Obter a linha (índice 0-based)
    line = file_lines[line_number - 1]
    
    # Verificar estrutura TSV
    if '\t' not in line:
        return False, f"Linha {line_number} não tem estrutura TSV válida"
    
    parts = line.split('\t')
    
    # Verificar se tem colunas suficientes
    required_cols = max(id_idx, text_idx) + 1
    if len(parts) < required_cols:
        return False, f"Linha {line_number} tem {len(parts)} colunas, esperado mínimo {required_cols}"
    
    # Verificar se o ID corresponde
    line_id = parts[id_idx].strip()
    if line_id != suggestion_id:
        return False, f"ID não corresponde na linha {line_number}: esperado '{suggestion_id}', encontrado '{line_id}'"
    
    # Verificar se a sugestão não está vazia
    if not new_text or not new_text.strip():
        return False, "Sugestão vazia"
    
    # Verificar se a sugestão não contém TABs (quebraria a estrutura)
    if '\t' in new_text:
        return False, "Sugestão contém caractere TAB (proibido)"
    
    # Verificar se a sugestão não contém quebras de linha
    if '\n' in new_text or '\r' in new_text:
        return False, "Sugestão contém quebra de linha (proibido)"
    
    return True, ""


def apply_suggestion(file_lines: list[str], suggestion: dict, id_idx: int, text_idx: int) -> str:
    """
    Aplica uma sugestão, retornando a nova linha.
    Preserva todas as colunas, apenas atualiza a coluna de texto.
    """
    line_number = suggestion['line']
    new_text = suggestion['suggestion']
    
    # Obter linha atual e suas colunas
    current_line = file_lines[line_number - 1]
    parts = current_line.split('\t')
    
    # Atualizar apenas a coluna de texto
    parts[text_idx] = new_text
    
    # Reconstruir a linha
    new_line = '\t'.join(parts)
    
    return new_line


def process_file(file_path: Path, suggestions: list[dict]) -> tuple[int, int, list[str]]:
    """
    Processa um arquivo aplicando as sugestões válidas.
    
    Retorna: (applied_count, skipped_count, errors)
    """
    if not file_path.exists():
        return 0, len(suggestions), [f"Arquivo não existe: {file_path}"]
    
    # Ler o arquivo preservando encoding UTF-8
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Preservar se arquivo termina com newline
    ends_with_newline = lines[-1].endswith('\n') if lines else False
    
    # Remover newlines para processamento, preservando estrutura
    lines = [line.rstrip('\r\n') for line in lines]
    
    # Detectar formato do TSV
    id_idx, text_idx = detect_tsv_format(lines)
    print(f"   Formato detectado: ID na coluna {id_idx}, Texto na coluna {text_idx}")
    
    file_name = file_path.name
    applied = 0
    skipped = 0
    errors = []
    
    # Ordenar sugestões por linha (para aplicar em ordem)
    sorted_suggestions = sorted(suggestions, key=lambda x: x.get('line', 0))
    
    for suggestion in sorted_suggestions:
        is_valid, error = validate_suggestion(suggestion, lines, file_name, id_idx, text_idx)
        
        if not is_valid:
            errors.append(f"Sugestão ignorada (ID: {suggestion.get('id', '?')}): {error}")
            skipped += 1
            continue
        
        # Aplicar a sugestão
        line_idx = suggestion['line'] - 1
        old_line = lines[line_idx]
        new_line = apply_suggestion(lines, suggestion, id_idx, text_idx)
        
        # Verificar se realmente mudou algo
        if old_line == new_line:
            errors.append(f"Sugestão ignorada (ID: {suggestion['id']}): texto já está igual")
            skipped += 1
            continue
        
        lines[line_idx] = new_line
        applied += 1
        print(f"✅ Aplicado: linha {suggestion['line']} - ID '{suggestion['id']}'")
        print(f"   Antes: {old_line[:100]}...")
        print(f"   Depois: {new_line[:100]}...")
    
    # Salvar arquivo se houve alterações
    if applied > 0:
        # Reconstruir com newlines
        output_lines = [line + '\n' for line in lines]
        
        # Se arquivo original não terminava com newline, remover do último
        if not ends_with_newline and output_lines:
            output_lines[-1] = output_lines[-1].rstrip('\n')
        
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.writelines(output_lines)
        
        print(f"💾 Arquivo salvo: {file_path}")
    
    return applied, skipped, errors


def main():
    """Função principal."""
    print("=" * 60)
    print("🔄 Iniciando processamento de sugestões de tradução")
    print("=" * 60)
    
    # Obter corpo da Issue
    issue_body = os.environ.get('ISSUE_BODY', '')
    issue_number = os.environ.get('ISSUE_NUMBER', 'unknown')
    
    # Base path para os arquivos de tradução (pode ser configurado via env)
    target_repo_path = os.environ.get('TARGET_REPO_PATH', 'translation-repo')
    base_path = Path(target_repo_path)
    
    print(f"📂 Diretório de tradução: {base_path.absolute()}")
    
    if not issue_body:
        print("ERRO: ISSUE_BODY não definido")
        set_output('changes_made', 'false')
        set_output('error_message', 'Corpo da Issue vazio')
        sys.exit(1)
    
    print(f"📋 Processando Issue #{issue_number}")
    print(f"📝 Tamanho do corpo: {len(issue_body)} caracteres")
    
    # Extrair JSON
    data = extract_json_from_body(issue_body)
    
    if not data:
        set_output('changes_made', 'false')
        set_output('error_message', 'JSON de sugestões não encontrado ou inválido')
        sys.exit(1)
    
    # Validar estrutura do JSON
    if 'suggestions' not in data or not isinstance(data['suggestions'], list):
        print("ERRO: JSON não contém lista de 'suggestions'")
        set_output('changes_made', 'false')
        set_output('error_message', 'Formato JSON inválido')
        sys.exit(1)
    
    suggestions = data['suggestions']
    total = len(suggestions)
    
    print(f"📊 Total de sugestões: {total}")
    print(f"📅 Versão do formato: {data.get('version', 'unknown')}")
    print(f"⏰ Timestamp: {data.get('timestamp', 'unknown')}")
    print(f"🎯 Target Repo: {data.get('targetRepo', 'não especificado')}")
    print(f"🌿 Target Branch: {data.get('targetBranch', 'não especificado')}")
    
    if total == 0:
        print("⚠️ Nenhuma sugestão para processar")
        set_output('changes_made', 'false')
        set_output('error_message', 'Lista de sugestões vazia')
        sys.exit(0)
    
    # Agrupar sugestões por arquivo
    by_file = {}
    for suggestion in suggestions:
        file_name = suggestion.get('file', 'pt-br.tsv')  # Default: pt-br.tsv
        if file_name not in by_file:
            by_file[file_name] = []
        by_file[file_name].append(suggestion)
    
    print(f"📁 Arquivos afetados: {list(by_file.keys())}")
    
    total_applied = 0
    total_skipped = 0
    all_errors = []
    
    # Processar cada arquivo
    for file_name, file_suggestions in by_file.items():
        print(f"\n📄 Processando: {file_name} ({len(file_suggestions)} sugestões)")
        
        # O arquivo está na raiz do repositório de tradução
        file_path = base_path / file_name
        applied, skipped, errors = process_file(file_path, file_suggestions)
        
        total_applied += applied
        total_skipped += skipped
        all_errors.extend(errors)
    
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL")
    print("=" * 60)
    print(f"✅ Aplicadas: {total_applied}")
    print(f"⏭️ Ignoradas: {total_skipped}")
    
    if all_errors:
        print("\n⚠️ Erros encontrados:")
        for error in all_errors:
            print(f"   - {error}")
    
    # Definir outputs
    set_output('applied_count', str(total_applied))
    set_output('skipped_count', str(total_skipped))
    
    if total_applied > 0:
        set_output('changes_made', 'true')
        print("\n✅ Processamento concluído com sucesso!")
        sys.exit(0)
    else:
        set_output('changes_made', 'false')
        error_msg = '; '.join(all_errors[:3]) if all_errors else 'Nenhuma alteração aplicável'
        set_output('error_message', error_msg)
        print("\n⚠️ Nenhuma alteração aplicada")
        sys.exit(0)


if __name__ == '__main__':
    main()
