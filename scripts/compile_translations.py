#!/usr/bin/env python3
"""
Script de Compilação de Traduções
=================================
Substitui variáveis {{VAR}} pelos valores reais do glossário.

Uso:
    python compile_translations.py

Entrada:
    - pt-br.tsv (com variáveis {{XXX}})
    - glossary.json (definições dos termos)

Saída:
    - pt-br-compiled.tsv (com variáveis substituídas)
"""

import json
import re
import sys
from pathlib import Path

# Caminhos dos arquivos
GLOSSARY_PATH = Path("docs/glossary.json")
INPUT_TSV = Path("../wwm_brasileiro_auto_path/pt-br.tsv")  # Branch dev
OUTPUT_TSV = Path("../wwm_brasileiro_auto_path/pt-br-compiled.tsv")  # Arquivo compilado

def load_glossary():
    """Carrega o glossário e cria mapa de variáveis."""
    if not GLOSSARY_PATH.exists():
        print(f"❌ Glossário não encontrado: {GLOSSARY_PATH}")
        sys.exit(1)
    
    with open(GLOSSARY_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    variable_map = {}
    for term in data.get('terms', []):
        # Gera nome da variável: id uppercase, hífens viram underscores
        var_name = f"{{{{{term['id'].upper().replace('-', '_')}}}}}"
        variable_map[var_name] = term['translation']
    
    print(f"📚 Carregadas {len(variable_map)} variáveis do glossário")
    return variable_map

def compile_translations(variable_map):
    """Lê o TSV, substitui variáveis e salva."""
    if not INPUT_TSV.exists():
        print(f"❌ Arquivo de entrada não encontrado: {INPUT_TSV}")
        sys.exit(1)
    
    # Regex para encontrar {{VARIAVEL}}
    var_pattern = re.compile(r'\{\{([A-Z_0-9]+)\}\}')
    
    replaced_count = 0
    unknown_vars = set()
    lines_processed = 0
    
    with open(INPUT_TSV, 'r', encoding='utf-8') as f_in:
        content = f_in.read()
    
    def replace_var(match):
        nonlocal replaced_count, unknown_vars
        full_var = match.group(0)
        
        if full_var in variable_map:
            replaced_count += 1
            return variable_map[full_var]
        else:
            unknown_vars.add(full_var)
            return full_var  # Mantém original se não encontrar
    
    compiled_content = var_pattern.sub(replace_var, content)
    lines_processed = content.count('\n')
    
    # Salva o arquivo compilado
    with open(OUTPUT_TSV, 'w', encoding='utf-8') as f_out:
        f_out.write(compiled_content)
    
    print(f"\n✅ Compilação concluída!")
    print(f"   📄 Linhas processadas: {lines_processed:,}")
    print(f"   🔄 Variáveis substituídas: {replaced_count:,}")
    
    if unknown_vars:
        print(f"\n⚠️  Variáveis não encontradas ({len(unknown_vars)}):")
        for var in sorted(unknown_vars):
            print(f"      - {var}")
    
    print(f"\n📁 Arquivo compilado: {OUTPUT_TSV}")

def main():
    print("=" * 50)
    print("🔧 Compilador de Traduções - WWM Brasileiro")
    print("=" * 50)
    print()
    
    variable_map = load_glossary()
    compile_translations(variable_map)
    
    print("\n✨ Pronto para uso no jogo!")

if __name__ == "__main__":
    main()
