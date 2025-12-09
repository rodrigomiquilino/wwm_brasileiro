const CONFIG = {
    // Repositório principal (issues, hall da fama)
    GITHUB_REPO: 'rodrigomiquilino/wwm_brasileiro',
    GITHUB_OWNER: 'rodrigomiquilino',
    GITHUB_OWNER_ID: 22358284, // ID numérico imutável - segurança extra
    GITHUB_REPO_NAME: 'wwm_brasileiro',
    // OAuth
    GITHUB_CLIENT_ID: 'Ov23liLPua7ghOOFV8WG',
    OAUTH_PROXY_URL: 'https://wwm-github-oauth.rodrigomiquilino.workers.dev',
    // Repositório de traduções (arquivos TSV)
    TRANSLATION_REPO: 'rodrigomiquilino/wwm_brasileiro_auto_path',
    TRANSLATION_REPO_NAME: 'wwm_brasileiro_auto_path',
    TRANSLATION_BRANCH: 'dev',      // Branch para leitura e escrita
    // Arquivos TSV (novo formato: ID\tOriginalText)
    ENGLISH_FILE: 'en.tsv',         // Original em inglês
    PTBR_FILE: 'pt-br.tsv',         // Traduções PT-BR
    ITEMS_PER_PAGE: 50,
    // Cache settings
    CACHE_DURATION: 15 * 60 * 1000, // 15 minutos em ms
    CACHE_PREFIX: 'wwm_cache_'
};

// ========== SISTEMA DE CACHE ==========
const apiCache = {
    // Salva dados no cache com timestamp
    set(key, data) {
        const cacheItem = {
            data: data,
            timestamp: Date.now()
        };
        try {
            localStorage.setItem(CONFIG.CACHE_PREFIX + key, JSON.stringify(cacheItem));
        } catch (e) {
            console.warn('Cache storage full, clearing old entries');
            this.clearOld();
        }
    },
    
    // Recupera dados do cache se ainda válidos
    get(key, allowExpired = false) {
        try {
            const cached = localStorage.getItem(CONFIG.CACHE_PREFIX + key);
            if (!cached) return null;
            
            const cacheItem = JSON.parse(cached);
            const age = Date.now() - cacheItem.timestamp;
            
            if (age < CONFIG.CACHE_DURATION) {
                console.log(`[Cache HIT] ${key} (age: ${Math.round(age/1000)}s)`);
                return cacheItem.data;
            }
            
            if (allowExpired) {
                console.log(`[Cache STALE] ${key} (usando dados antigos)`);
                return cacheItem.data;
            }
            
            console.log(`[Cache EXPIRED] ${key}`);
            return null;
        } catch (e) {
            return null;
        }
    },
    
    // Limpa entradas antigas do cache
    clearOld() {
        const keysToRemove = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(CONFIG.CACHE_PREFIX)) {
                try {
                    const cached = JSON.parse(localStorage.getItem(key));
                    if (Date.now() - cached.timestamp > CONFIG.CACHE_DURATION) {
                        keysToRemove.push(key);
                    }
                } catch (e) {
                    keysToRemove.push(key);
                }
            }
        }
        keysToRemove.forEach(k => localStorage.removeItem(k));
    },
    
    // Limpa todo o cache
    clearAll() {
        const keysToRemove = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(CONFIG.CACHE_PREFIX)) {
                keysToRemove.push(key);
            }
        }
        keysToRemove.forEach(k => localStorage.removeItem(k));
        console.log('[Cache] Cleared all entries');
    }
};

// ========== FETCH COM CACHE E AUTH ==========
async function cachedFetch(url, cacheKey, options = {}) {
    // Tenta cache primeiro
    const cached = apiCache.get(cacheKey);
    if (cached) return { ok: true, data: cached, fromCache: true };
    
    // Prepara headers com token se disponível
    const headers = { ...options.headers };
    if (githubToken) {
        headers['Authorization'] = `Bearer ${githubToken}`;
    }
    
    try {
        const response = await fetch(url, { ...options, headers });
        
        // Verifica rate limit
        const remaining = response.headers.get('X-RateLimit-Remaining');
        const limit = response.headers.get('X-RateLimit-Limit');
        if (remaining !== null) {
            console.log(`[API] Rate limit: ${remaining}/${limit}`);
            if (parseInt(remaining) < 10) {
                console.warn('[API] Rate limit baixo!');
            }
        }
        
        if (!response.ok) {
            if (response.status === 403) {
                const resetTime = response.headers.get('X-RateLimit-Reset');
                if (resetTime) {
                    const resetDate = new Date(parseInt(resetTime) * 1000);
                    console.error(`[API] Rate limit exceeded. Resets at: ${resetDate.toLocaleTimeString()}`);
                }
                // Tenta usar dados expirados como fallback
                const staleData = apiCache.get(cacheKey, true);
                if (staleData) {
                    console.warn(`[API] Usando cache expirado como fallback para ${cacheKey}`);
                    return { ok: true, data: staleData, fromCache: true, stale: true };
                }
            }
            return { ok: false, status: response.status, data: null };
        }
        
        const data = await response.json();
        
        // Salva no cache
        apiCache.set(cacheKey, data);
        
        return { ok: true, data: data, fromCache: false };
    } catch (error) {
        console.error(`[API] Fetch error for ${cacheKey}:`, error);
        // Em caso de erro de rede, tenta cache expirado
        const staleData = apiCache.get(cacheKey, true);
        if (staleData) {
            console.warn(`[API] Usando cache expirado como fallback para ${cacheKey}`);
            return { ok: true, data: staleData, fromCache: true, stale: true };
        }
        return { ok: false, data: null, error };
    }
}

// GitHub Auth State
let githubUser = null;
let githubToken = localStorage.getItem('github_token') || null;

// Dados de tradução (removido Main/Diff - agora é um único arquivo)
let allData = [];
let filteredData = [];
let currentPage = 1;
let currentFilter = 'all';

// ========== GLOSSÁRIO E DUPLICATAS ==========
let glossaryData = null;
let glossaryIndex = {}; // Índice para busca rápida de termos
let duplicatesMap = {}; // Mapa de textos originais -> array de IDs

// ========== CART INDICATOR - Set para O(1) lookup ==========
let cartIdSet = new Set(); // IDs no carrinho para verificação rápida

// Verificar se ID está no carrinho - O(1)
function isInCart(id) {
    return cartIdSet.has(id);
}

// Obter item do carrinho por ID
function getCartItem(id) {
    return suggestionCart.find(item => item.id === id);
}

// Atualizar Set de IDs do carrinho
function updateCartIdSet() {
    cartIdSet = new Set(suggestionCart.map(item => item.id));
}


// Fetch TSV file from GitHub (repositório de traduções)
async function fetchTSV(filename) {
    const url = `https://raw.githubusercontent.com/${CONFIG.TRANSLATION_REPO}/${CONFIG.TRANSLATION_BRANCH}/${filename}`;
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch');
        return await response.text();
    } catch (error) {
        console.error(`Error fetching ${filename}:`, error);
        return null;
    }
}

// Parse TSV content para Map - novo formato: ID\tOriginalText
function parseTSVtoMap(content) {
    const lines = content.trim().split('\n');
    const map = new Map();
    
    if (lines.length === 0) return map;
    
    // Detecta colunas do header
    const header = lines[0].split('\t').map(h => h.trim().toLowerCase());
    const idIndex = header.findIndex(h => h === 'id');
    const textIndex = header.findIndex(h => 
        h === 'originaltext' || h === 'text' || h === 'original'
    );
    
    // Fallback para formato antigo (ID\tText sem header explícito)
    const useIdIdx = idIndex >= 0 ? idIndex : 0;
    const useTextIdx = textIndex >= 0 ? textIndex : 1;
    
    // Parse das linhas (começa de 1 se tem header, 0 se não)
    const startLine = (idIndex >= 0 || textIndex >= 0) ? 1 : 0;
    
    for (let i = startLine; i < lines.length; i++) {
        const cols = lines[i].split('\t');
        const id = cols[useIdIdx]?.trim();
        const text = cols[useTextIdx]?.trim();
        
        if (id && id !== '0000000000000000' && id.toLowerCase() !== 'id') {
            map.set(id, { text: text || '', lineNumber: i + 1 });
        }
    }
    
    return map;
}

// Compara original (EN) com traduzido (PT-BR) e retorna array com status
function compareTranslations(originalMap, translateMap) {
    const data = [];
    
    // Itera sobre o arquivo PT-BR (que é a base)
    translateMap.forEach((translateItem, id) => {
        const originalItem = originalMap.get(id);
        const originalText = originalItem ? originalItem.text : '';
        const translatedText = translateItem.text;
        
        // Se o texto traduzido é diferente do original = traduzido
        // Se igual = pendente (ainda em inglês)
        const isTranslated = originalText !== translatedText && translatedText.length > 0;
        
        data.push({
            id,
            originalText,
            translatedText,
            lineNumber: translateItem.lineNumber,
            isTranslated
        });
    });
    
    return data;
}

// Load translations - simplificado para arquivos únicos
async function loadTranslations() {
    const loadingEl = document.getElementById('loading');
    
    // Step 1: Iniciando
    loadingEl.innerHTML = `
        <div class="spinner"></div>
        <p>📥 Conectando ao repositório...</p>
        <div class="loading-progress">
            <div class="loading-step active"><i class="fas fa-plug"></i> Conectando</div>
            <div class="loading-step"><i class="fas fa-file-alt"></i> en.tsv</div>
            <div class="loading-step"><i class="fas fa-language"></i> pt-br.tsv</div>
            <div class="loading-step"><i class="fas fa-cogs"></i> Processando</div>
        </div>
    `;
    
    // Step 2: Carregando arquivos
    setTimeout(() => {
        loadingEl.querySelector('.loading-step:nth-child(2)')?.classList.add('active');
        loadingEl.querySelector('p').textContent = '📥 Baixando en.tsv...';
    }, 300);
    
    const [englishContent, ptbrContent] = await Promise.all([
        fetchTSV(CONFIG.ENGLISH_FILE),
        fetchTSV(CONFIG.PTBR_FILE)
    ]);
    
    // Update progress
    loadingEl.querySelector('.loading-step:nth-child(3)')?.classList.add('active');
    loadingEl.querySelector('p').textContent = '📥 Baixando pt-br.tsv...';
    
    // Carrega glossário em paralelo (não bloqueia o carregamento principal)
    loadGlossary();
    
    if (!ptbrContent) {
        loadingEl.innerHTML = `
            <p style="color: var(--red-primary);">
                <i class="fas fa-exclamation-triangle"></i> 
                Erro ao carregar arquivo de tradução (${CONFIG.PTBR_FILE})
            </p>
            <p style="color: var(--text-muted); font-size: 0.9rem;">
                Verifique se o repositório ${CONFIG.TRANSLATION_REPO} está acessível.
            </p>
        `;
        return;
    }
    
    // Step 4: Processando
    loadingEl.querySelector('.loading-step:nth-child(4)')?.classList.add('active');
    loadingEl.querySelector('p').textContent = '⚙️ Processando dados...';
    
    // Parse dos arquivos
    const englishMap = englishContent ? parseTSVtoMap(englishContent) : new Map();
    const ptbrMap = parseTSVtoMap(ptbrContent);
    
    // Atualiza com contagem
    loadingEl.querySelector('p').textContent = `⚙️ Processando ${ptbrMap.size.toLocaleString('pt-BR')} linhas...`;
    
    // Compara originais com traduzidos
    allData = compareTranslations(englishMap, ptbrMap);
    
    // Constrói mapa de duplicatas
    buildDuplicatesMap();
    
    console.log(`[Translate] Carregadas ${allData.length} linhas de tradução`);
    
    // Atualiza estatísticas e renderiza
    updateStats();
    applyFilter();
    
    loadingEl.classList.add('hidden');
    document.getElementById('table-scroll').classList.remove('hidden');
}

// ========== GLOSSÁRIO ==========
// Carrega dados do glossário
async function loadGlossary() {
    try {
        const response = await fetch('glossary.json');
        if (!response.ok) throw new Error('Failed to load glossary');
        
        glossaryData = await response.json();
        
        // Cria índice para busca rápida O(1)
        glossaryIndex = {};
        glossaryData.terms.forEach(term => {
            // Indexa pelo original em lowercase
            const originalKey = term.original.toLowerCase();
            glossaryIndex[originalKey] = term;
            
            // Indexa pelos aliases
            if (term.aliases) {
                term.aliases.forEach(alias => {
                    const aliasKey = alias.toLowerCase();
                    if (!glossaryIndex[aliasKey]) {
                        glossaryIndex[aliasKey] = term;
                    }
                });
            }
        });
        
        console.log(`[Glossary] Carregados ${glossaryData.terms.length} termos`);
        
        // Constrói índice de NPCs para filtragem
        buildNpcIndex();
        
        // Detecta diferenças de NPCs e cria issue automaticamente
        setTimeout(() => detectNpcDifferences(), 1000);
        
        // Re-aplica filtro para ocultar NPCs
        if (allData.length > 0) {
            applyFilter();
        }
    } catch (error) {
        console.warn('[Glossary] Erro ao carregar glossário:', error);
        glossaryData = null;
        glossaryIndex = {};
    }
}

// Encontra termos do glossário no texto
function findGlossaryTerms(text) {
    if (!glossaryData || !text) return [];
    
    const found = [];
    const textLower = text.toLowerCase();
    
    // Busca cada termo do glossário no texto
    for (const term of glossaryData.terms) {
        // Verifica o termo original
        if (textLower.includes(term.original.toLowerCase())) {
            if (!found.some(t => t.id === term.id)) {
                found.push(term);
            }
            continue;
        }
        
        // Verifica aliases
        if (term.aliases) {
            for (const alias of term.aliases) {
                if (textLower.includes(alias.toLowerCase())) {
                    if (!found.some(t => t.id === term.id)) {
                        found.push(term);
                    }
                    break;
                }
            }
        }
    }
    
    return found;
}

// ========== NPC DETECTION ==========
// Lista de NPCs do glossário (category='npcs' com doNotTranslate=true)
let npcNames = new Set();
let npcIndex = {};  // original lowercase -> term

// Constrói índice de nomes de NPCs
function buildNpcIndex() {
    npcNames = new Set();
    npcIndex = {};
    
    if (!glossaryData || !glossaryData.terms) return;
    
    glossaryData.terms
        .filter(term => term.category === 'npcs' && term.doNotTranslate === true)
        .forEach(term => {
            const nameLower = term.original.toLowerCase();
            npcNames.add(nameLower);
            npcIndex[nameLower] = term;
            
            // Também adiciona aliases
            if (term.aliases) {
                term.aliases.forEach(alias => {
                    const aliasLower = alias.toLowerCase();
                    npcNames.add(aliasLower);
                    npcIndex[aliasLower] = term;
                });
            }
        });
    
    console.log(`[NPC] Indexados ${npcNames.size} nomes de NPC para ocultar`);
}

// Verifica se um texto é um nome de NPC (para ocultar da tradução)
function isNpcName(originalText) {
    if (!originalText || npcNames.size === 0) return false;
    
    const textLower = originalText.trim().toLowerCase();
    
    // Verifica correspondência exata
    if (npcNames.has(textLower)) return true;
    
    // Verifica se o texto é apenas o nome do NPC (sem texto adicional)
    for (const npcName of npcNames) {
        if (textLower === npcName) return true;
    }
    
    return false;
}

// Detecta diferenças nos nomes de NPCs entre EN e PT-BR e cria issue automaticamente
let npcDifferences = [];

async function detectNpcDifferences() {
    npcDifferences = [];
    
    if (!glossaryData || !allData) return;
    
    // Busca por linhas onde o texto é um NPC e a tradução PT-BR é diferente
    for (const item of allData) {
        if (!item.originalText) continue;
        
        const textLower = item.originalText.trim().toLowerCase();
        const npcTerm = npcIndex[textLower];
        
        if (npcTerm && item.isTranslated) {
            // O NPC deveria manter o nome original, mas foi traduzido
            const expectedName = npcTerm.original;
            const actualTranslation = item.translatedText.trim();
            
            // Se o nome no PT-BR é diferente do esperado (nome original)
            if (actualTranslation.toLowerCase() !== expectedName.toLowerCase()) {
                npcDifferences.push({
                    id: item.id,
                    npcName: npcTerm.original,
                    englishText: item.originalText,
                    ptbrText: item.translatedText,
                    expected: expectedName,
                    lineNumber: item.lineNumber
                });
            }
        }
    }
    
    if (npcDifferences.length > 0) {
        console.log(`[NPC] Detectadas ${npcDifferences.length} diferenças nos nomes de NPCs`);
        // Auto-cria issue se for admin
        if (githubUser && githubUser.id === CONFIG.GITHUB_OWNER_ID) {
            await autoCreateNpcIssue();
        }
    }
}

// Cria issue automaticamente com as diferenças de NPC
async function autoCreateNpcIssue() {
    if (npcDifferences.length === 0 || !githubToken) return;
    
    // Verifica se já existe uma issue aberta sobre NPCs
    try {
        const existingIssuesResult = await cachedFetch(
            `https://api.github.com/repos/${CONFIG.GITHUB_REPO}/issues?state=open&labels=npc-review&per_page=10`,
            'npc_issues_check'
        );
        
        if (existingIssuesResult.ok && existingIssuesResult.data.length > 0) {
            console.log('[NPC] Já existe uma issue aberta para revisão de NPCs');
            return;
        }
    } catch (e) {
        console.warn('[NPC] Erro ao verificar issues existentes:', e);
    }
    
    // Cria o corpo da issue
    const issueBody = `## 🔎 Diferenças Detectadas em Nomes de NPCs

Os seguintes nomes de NPCs no arquivo **pt-br.tsv** estão diferentes do esperado:

| ID | NPC | Esperado | Encontrado (PT-BR) |
|---|---|---|---|
${npcDifferences.slice(0, 50).map(d => 
    `| \`${d.id}\` | ${d.npcName} | ${d.expected} | ${d.ptbrText} |`
).join('\n')}

${npcDifferences.length > 50 ? `\n*... e mais ${npcDifferences.length - 50} diferenças*` : ''}

---
**Ação necessária:** Revisar e corrigir os nomes de NPCs para manter consistência.

*Issue criada automaticamente pelo sistema de detecção.*`;
    
    try {
        const response = await fetch(`https://api.github.com/repos/${CONFIG.GITHUB_REPO}/issues`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${githubToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: `[Auto] 🔎 Revisão de Nomes de NPCs (${npcDifferences.length} diferenças)`,
                body: issueBody,
                labels: ['npc-review', 'automated']
            })
        });
        
        if (response.ok) {
            const issue = await response.json();
            console.log(`[NPC] Issue criada automaticamente: #${issue.number}`);
            showNotification(`Issue #${issue.number} criada para revisão de NPCs`, 'success');
        } else {
            console.error('[NPC] Erro ao criar issue:', await response.text());
        }
    } catch (error) {
        console.error('[NPC] Erro ao criar issue:', error);
    }
}

// ========== DUPLICATAS ==========
// Constrói mapa de textos idênticos (para edição em massa)
function buildDuplicatesMap() {
    duplicatesMap = {};
    
    allData.forEach(item => {
        if (!item.originalText) return;
        
        const key = item.originalText.trim().toLowerCase();
        if (!duplicatesMap[key]) {
            duplicatesMap[key] = [];
        }
        duplicatesMap[key].push({
            id: item.id,
            lineNumber: item.lineNumber,
            isTranslated: item.isTranslated
        });
    });
    
    // Conta duplicatas reais (>1 ocorrência)
    const duplicateCount = Object.values(duplicatesMap).filter(arr => arr.length > 1).length;
    console.log(`[Duplicates] Encontrados ${duplicateCount} textos com múltiplas ocorrências`);
}

// Obtém IDs duplicados para um determinado texto original
function getDuplicateIds(originalText) {
    if (!originalText) return [];
    const key = originalText.trim().toLowerCase();
    return duplicatesMap[key] || [];
}

// Conta quantas linhas têm o mesmo texto original
function getDuplicateCount(originalText) {
    return getDuplicateIds(originalText).length;
}



// Exibe painel admin (apenas para o owner)
function showAdminPanel(show = true) {
    const adminPanel = document.getElementById('admin-panel');
    const tableScroll = document.getElementById('table-scroll');
    const adminTab = document.getElementById('admin-tab');
    
    if (show) {
        if (adminPanel) adminPanel.classList.remove('hidden');
        if (tableScroll) tableScroll.classList.add('hidden');
        if (adminTab) adminTab.classList.add('active');
        startAdminPolling();
    } else {
        if (adminPanel) adminPanel.classList.add('hidden');
        if (tableScroll) tableScroll.classList.remove('hidden');
        if (adminTab) adminTab.classList.remove('active');
        stopAdminPolling();
    }
}

// Update statistics
function updateStats() {
    const total = allData.length;
    const translated = allData.filter(item => item.isTranslated).length;
    const pending = total - translated;
    const progress = total > 0 ? ((translated / total) * 100).toFixed(1) : 0;
    
    document.getElementById('stat-total').textContent = total.toLocaleString('pt-BR');
    document.getElementById('stat-translated').textContent = translated.toLocaleString('pt-BR');
    document.getElementById('stat-pending').textContent = pending.toLocaleString('pt-BR');
    document.getElementById('stat-progress').textContent = `${progress}%`;
    
    // Atualiza barra de progresso visual
    document.getElementById('progress-percent').textContent = `${progress}%`;
    document.getElementById('progress-fill').style.width = `${progress}%`;
    document.getElementById('progress-done').textContent = translated.toLocaleString('pt-BR');
    document.getElementById('progress-pending').textContent = pending.toLocaleString('pt-BR');
    document.getElementById('progress-total').textContent = total.toLocaleString('pt-BR');
}

// Apply filter and search
function applyFilter() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase().trim();
    
    filteredData = allData.filter(item => {
        // Oculta NPCs automaticamente (não precisam de tradução)
        if (isNpcName(item.originalText)) {
            return false;
        }
        
        // Filter by status
        if (currentFilter === 'pending' && item.isTranslated) {
            return false;
        }
        if (currentFilter === 'translated' && !item.isTranslated) {
            return false;
        }
        
        // Filter by search
        if (searchTerm) {
            return item.id.toLowerCase().includes(searchTerm) ||
                   item.originalText.toLowerCase().includes(searchTerm) ||
                   item.translatedText.toLowerCase().includes(searchTerm);
        }
        
        return true;
    });
    
    currentPage = 1;
    renderTable();
    renderPagination();
}

// Render table
function renderTable() {
    const tbody = document.getElementById('table-body');
    const start = (currentPage - 1) * CONFIG.ITEMS_PER_PAGE;
    const end = start + CONFIG.ITEMS_PER_PAGE;
    const pageData = filteredData.slice(start, end);
    
    if (pageData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; padding: 3rem; color: var(--text-muted);">
                    <i class="fas fa-search" style="font-size: 2rem; margin-bottom: 1rem; display: block;"></i>
                    Nenhuma linha encontrada
                </td>
            </tr>
        `;
        return;
    }
    
    // Arquivo de tradução (PT-BR) - agora é único
    const translateFile = CONFIG.PTBR_FILE;
    
    tbody.innerHTML = pageData.map((item, index) => {
        const statusClass = item.isTranslated ? 'status-done' : 'status-pending';
        const statusText = item.isTranslated ? 'Traduzido' : 'Pendente';
        const translationClass = item.isTranslated ? 'text-translated' : 'text-empty';
        const displayTranslation = item.translatedText || '(vazio)';
        
        // Dados para o modal - usando encodeURIComponent para TODOS os valores
        const safeId = encodeURIComponent(item.id || '');
        const dataOriginal = encodeURIComponent(item.originalText || '');
        const dataCurrent = encodeURIComponent(item.translatedText || '');
        
        // ========== CART INDICATOR ==========
        const inCart = isInCart(item.id);
        const cartItem = inCart ? getCartItem(item.id) : null;
        const rowClass = inCart ? 'in-cart' : '';
        const cartBadge = inCart ? '<span class="cart-badge-inline" title="Já está no lote"><i class="fas fa-clipboard-check"></i></span>' : '';
        
        // Botão muda baseado no estado do carrinho
        const btnClass = inCart ? 'btn-in-cart' : 'btn-edit';
        const btnIcon = inCart ? 'fa-check' : 'fa-lightbulb';
        const btnText = inCart ? 'No Lote' : 'Sugerir';
        
        // Tooltip com preview da sugestão
        const tooltipText = inCart && cartItem 
            ? `Sugestão: ${cartItem.suggestion.substring(0, 50)}${cartItem.suggestion.length > 50 ? '...' : ''}`
            : 'Sugerir tradução';
        
        return `
            <tr class="${rowClass}">
                <td class="col-id">
                    <span class="status-badge ${statusClass}">${statusText}</span>
                    <div class="id-wrapper">
                        ${cartBadge}
                        <code>${escapeHtml(item.id)}</code>
                        <button class="btn-copy-id" data-copy="${safeId}" title="Copiar ID">
                            <i class="fas fa-copy"></i>
                        </button>
                    </div>
                </td>
                <td class="col-original">
                    <div class="text-cell text-original">${escapeHtml(item.originalText)}</div>
                </td>
                <td class="col-translation">
                    <div class="text-cell ${translationClass}">${escapeHtml(displayTranslation)}</div>
                </td>
                <td class="col-actions">
                    <button class="${btnClass}" 
                            data-id="${safeId}" 
                            data-original="${dataOriginal}" 
                            data-current="${dataCurrent}" 
                            data-line="${item.lineNumber}"
                            title="${tooltipText}">
                        <i class="fas ${btnIcon}"></i> ${btnText}
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    // Adiciona event listeners aos botões (mais seguro que onclick inline)
    tbody.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = decodeURIComponent(this.dataset.id);
            const original = this.dataset.original; // Já está encoded
            const current = this.dataset.current;   // Já está encoded  
            const line = parseInt(this.dataset.line, 10);
            openSuggestionModal(id, original, current, line);
        });
    });
    
    // Event listeners para botões de copiar ID
    tbody.querySelectorAll('.btn-copy-id').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation(); // Evita abrir modal
            const id = decodeURIComponent(this.dataset.copy);
            navigator.clipboard.writeText(id).then(() => {
                // Feedback visual
                this.innerHTML = '<i class="fas fa-check"></i>';
                this.classList.add('copied');
                setTimeout(() => {
                    this.innerHTML = '<i class="fas fa-copy"></i>';
                    this.classList.remove('copied');
                }, 1500);
            });
        });
    });
}

// Escape HTML
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML.replace(/\n/g, '<br>');
}

// ========== CONTADOR DE CARACTERES ==========
function updateCharCounter(originalLength) {
    const suggestionEl = document.getElementById('modal-suggestion');
    let counterEl = document.getElementById('char-counter');
    
    // Cria o elemento se não existir
    if (!counterEl) {
        counterEl = document.createElement('div');
        counterEl.id = 'char-counter';
        counterEl.className = 'char-counter';
        suggestionEl.parentNode.insertBefore(counterEl, suggestionEl.nextSibling);
    }
    
    const currentLength = suggestionEl.value.length;
    const diff = currentLength - originalLength;
    const diffPercent = originalLength > 0 ? Math.round((diff / originalLength) * 100) : 0;
    
    let statusClass = 'neutral';
    let statusIcon = 'fa-equals';
    
    if (diff > 0) {
        statusClass = diff > originalLength * 0.3 ? 'warning' : 'longer';
        statusIcon = 'fa-arrow-up';
    } else if (diff < 0) {
        statusClass = diff < -originalLength * 0.3 ? 'warning' : 'shorter';
        statusIcon = 'fa-arrow-down';
    }
    
    counterEl.className = `char-counter ${statusClass}`;
    counterEl.innerHTML = `
        <span class="counter-current">${currentLength}</span>
        <span class="counter-separator">/</span>
        <span class="counter-original">${originalLength}</span>
        <span class="counter-diff">
            <i class="fas ${statusIcon}"></i>
            ${diff >= 0 ? '+' : ''}${diff} (${diffPercent >= 0 ? '+' : ''}${diffPercent}%)
        </span>
    `;
}

// Render pagination
function renderPagination() {
    const totalPages = Math.ceil(filteredData.length / CONFIG.ITEMS_PER_PAGE);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = `
        <button onclick="goToPage(1)" ${currentPage === 1 ? 'disabled' : ''}>
            <i class="fas fa-angle-double-left"></i>
        </button>
        <button onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
            <i class="fas fa-angle-left"></i>
        </button>
    `;
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <button onclick="goToPage(${i})" class="${i === currentPage ? 'active' : ''}">
                ${i}
            </button>
        `;
    }
    
    html += `
        <button onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>
            <i class="fas fa-angle-right"></i>
        </button>
        <button onclick="goToPage(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}>
            <i class="fas fa-angle-double-right"></i>
        </button>
        <span class="pagination-info">
            Página ${currentPage} de ${totalPages} (${filteredData.length.toLocaleString('pt-BR')} itens)
        </span>
    `;
    
    pagination.innerHTML = html;
}

// Go to page
function goToPage(page) {
    const totalPages = Math.ceil(filteredData.length / CONFIG.ITEMS_PER_PAGE);
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderTable();
    renderPagination();
    document.getElementById('table-scroll').scrollTop = 0;
}

// Load Hall of Fame - Two Column Layout (COM CACHE)
async function loadContributors() {
    const container = document.getElementById('hall-container');
    if (!container) return;
    
    // Developers fixos
    const LEAD_DEV = 'rodrigomiquilino';
    const SECONDARY_DEV = 'DOG729';
    
    try {
        container.innerHTML = '<div class="hall-loading"><i class="fas fa-spinner fa-spin"></i> Carregando Hall da Fama...</div>';
        
        // Buscar dados em paralelo COM CACHE
        const [contributorsResult, issuesResult, leadUserResult, secondaryUserResult] = await Promise.all([
            cachedFetch(
                `https://api.github.com/repos/${CONFIG.GITHUB_REPO}/contributors?per_page=50`,
                'contributors'
            ),
            cachedFetch(
                `https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues?state=closed&labels=applied&per_page=100`,
                'issues_applied'
            ),
            cachedFetch(`https://api.github.com/users/${LEAD_DEV}`, `user_${LEAD_DEV}`),
            cachedFetch(`https://api.github.com/users/${SECONDARY_DEV}`, `user_${SECONDARY_DEV}`)
        ]);
        
        // Dados dos desenvolvedores
        const leadDevData = leadUserResult.ok ? leadUserResult.data : null;
        const secondaryDevData = secondaryUserResult.ok ? secondaryUserResult.data : null;
        
        // Processar contributors do repo
        const repoContributors = contributorsResult.ok ? contributorsResult.data : [];
        
        // Buscar commits dos devs principais
        const leadDevContrib = repoContributors.find(c => c.login === LEAD_DEV);
        const secondaryDevContrib = repoContributors.find(c => c.login === SECONDARY_DEV);
        
        // Processar autores de issues aprovadas
        let issueAuthors = [];
        if (issuesResult.ok) {
            const issues = issuesResult.data;
            const authorCounts = {};
            issues.forEach(issue => {
                if (issue.user && issue.user.type === 'User') {
                    const login = issue.user.login;
                    if (!authorCounts[login]) {
                        authorCounts[login] = {
                            login: login,
                            avatar_url: issue.user.avatar_url,
                            html_url: issue.user.html_url,
                            contributions: 0,
                            source: 'issues'
                        };
                    }
                    try {
                        const jsonMatch = issue.body?.match(/"total"\s*:\s*(\d+)/);
                        const count = jsonMatch ? parseInt(jsonMatch[1]) : 1;
                        authorCounts[login].contributions += count;
                    } catch (e) {
                        authorCounts[login].contributions += 1;
                    }
                }
            });
            issueAuthors = Object.values(authorCounts);
        }
        
        // Combinar contributors (excluindo os devs principais)
        const communityContributors = new Map();
        
        repoContributors
            .filter(c => c.type === 'User' && c.login !== LEAD_DEV && c.login !== SECONDARY_DEV)
            .forEach(c => {
                communityContributors.set(c.login, {
                    login: c.login,
                    avatar_url: c.avatar_url,
                    html_url: c.html_url,
                    contributions: c.contributions,
                    source: 'commits'
                });
            });
        
        issueAuthors
            .filter(a => a.login !== LEAD_DEV && a.login !== SECONDARY_DEV)
            .forEach(author => {
                if (communityContributors.has(author.login)) {
                    const existing = communityContributors.get(author.login);
                    existing.contributions += author.contributions;
                    existing.source = 'both';
                } else {
                    communityContributors.set(author.login, author);
                }
            });
        
        // Ordenar e pegar top 10
        const topCommunity = Array.from(communityContributors.values())
            .sort((a, b) => b.contributions - a.contributions)
            .slice(0, 10);
        
        // Renderizar o layout
        container.innerHTML = `
            <!-- Left Column: Developers Castle -->
            <div class="devs-castle">
                <div class="castle-title"><i class="fas fa-crown"></i> Desenvolvedores</div>
                
                <!-- Lead Developer - GOLD -->
                <div class="dev-card lead">
                    <div class="dev-header">
                        <div class="dev-rank-badge">👑</div>
                        <div class="dev-avatar">
                            <div class="dev-avatar-glow"></div>
                            <a href="${leadDevData?.html_url || 'https://github.com/' + LEAD_DEV}" target="_blank">
                                <img src="${leadDevData?.avatar_url || 'https://github.com/' + LEAD_DEV + '.png'}" alt="${LEAD_DEV}">
                            </a>
                        </div>
                        <div class="dev-info">
                            <div class="dev-name">
                                <a href="${leadDevData?.html_url || 'https://github.com/' + LEAD_DEV}" target="_blank">@${LEAD_DEV}</a>
                            </div>
                            <div class="dev-title">
                                <i class="fas fa-code"></i> Desenvolvedor Principal
                            </div>
                        </div>
                    </div>
                    <div class="dev-stats">
                        <div class="dev-stat">
                            <div class="dev-stat-value">${leadDevContrib?.contributions || '∞'}</div>
                            <div class="dev-stat-label">Commits</div>
                        </div>
                        <div class="dev-stat">
                            <div class="dev-stat-value">${leadDevData?.public_repos || '-'}</div>
                            <div class="dev-stat-label">Repos</div>
                        </div>
                        <div class="dev-stat">
                            <div class="dev-stat-value">${leadDevData?.followers || '-'}</div>
                            <div class="dev-stat-label">Seguidores</div>
                        </div>
                    </div>
                </div>
                
                <!-- Secondary Developer - SILVER -->
                <div class="dev-card secondary">
                    <div class="dev-header">
                        <div class="dev-rank-badge">🥈</div>
                        <div class="dev-avatar">
                            <a href="${secondaryDevData?.html_url || 'https://github.com/' + SECONDARY_DEV}" target="_blank">
                                <img src="${secondaryDevData?.avatar_url || 'https://github.com/' + SECONDARY_DEV + '.png'}" alt="${SECONDARY_DEV}">
                            </a>
                        </div>
                        <div class="dev-info">
                            <div class="dev-name">
                                <a href="${secondaryDevData?.html_url || 'https://github.com/' + SECONDARY_DEV}" target="_blank">@${SECONDARY_DEV}</a>
                            </div>
                            <div class="dev-title">
                                <i class="fas fa-code-branch"></i> Desenvolvedor Secundário
                            </div>
                        </div>
                    </div>
                    <div class="dev-stats">
                        <div class="dev-stat">
                            <div class="dev-stat-value">${secondaryDevContrib?.contributions || '-'}</div>
                            <div class="dev-stat-label">Commits</div>
                        </div>
                        <div class="dev-stat">
                            <div class="dev-stat-value">${secondaryDevData?.public_repos || '-'}</div>
                            <div class="dev-stat-label">Repos</div>
                        </div>
                        <div class="dev-stat">
                            <div class="dev-stat-value">${secondaryDevData?.followers || '-'}</div>
                            <div class="dev-stat-label">Seguidores</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Right Column: Community Ranking -->
            <div class="community-ranking">
                <div class="ranking-title"><i class="fas fa-medal"></i> Top Tradutores</div>
                
                ${topCommunity.length > 0 ? `
                    <div class="ranking-list">
                        ${topCommunity.map((contributor, index) => {
                            const position = index + 1;
                            const roleName = contributor.source === 'issues' ? 'Tradutor' : 
                                             contributor.source === 'both' ? 'Tradutor & Dev' : 'Contributor';
                            // Sanitizar dados do usuário para prevenir XSS
                            const safeLogin = escapeHtml(contributor.login);
                            const safeHtmlUrl = escapeHtml(contributor.html_url);
                            const safeAvatarUrl = escapeHtml(contributor.avatar_url);
                            
                            return `
                                <div class="ranking-item">
                                    <div class="ranking-position">${position}º</div>
                                    <div class="ranking-avatar">
                                        <a href="${safeHtmlUrl}" target="_blank">
                                            <img src="${safeAvatarUrl}" alt="${safeLogin}">
                                        </a>
                                    </div>
                                    <div class="ranking-info">
                                        <div class="ranking-name">
                                            <a href="${safeHtmlUrl}" target="_blank">@${safeLogin}</a>
                                        </div>
                                        <div class="ranking-role">${roleName}</div>
                                    </div>
                                    <div class="ranking-score">
                                        <div class="ranking-score-value">${contributor.contributions}</div>
                                        <div class="ranking-score-label">pts</div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                ` : `
                    <div class="ranking-empty">
                        <i class="fas fa-users"></i>
                        <p>Seja o primeiro tradutor!</p>
                    </div>
                `}
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading hall of fame:', error);
        container.innerHTML = `
            <div class="hall-loading">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Erro ao carregar Hall da Fama</p>
            </div>
        `;
    }
}

// Event Listeners
document.getElementById('search-input').addEventListener('input', debounce(applyFilter, 300));

document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        applyFilter();
    });
});

// ========== KEYBOARD SHORTCUTS ==========
document.addEventListener('keydown', (e) => {
    // Ignora se estiver em input/textarea
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        // Esc fecha modal mesmo em inputs
        if (e.key === 'Escape') {
            closeModal();
        }
        return;
    }
    
    switch (e.key) {
        case '/':
            // Focar na busca
            e.preventDefault();
            document.getElementById('search-input').focus();
            break;
        case 'ArrowLeft':
            // Página anterior
            if (currentPage > 1) goToPage(currentPage - 1);
            break;
        case 'ArrowRight':
            // Próxima página
            const totalPages = Math.ceil(filteredData.length / CONFIG.ITEMS_PER_PAGE);
            if (currentPage < totalPages) goToPage(currentPage + 1);
            break;
        case 'p':
        case 'P':
            // Filtro Pendentes
            document.querySelector('.filter-btn[data-filter="pending"]')?.click();
            break;
        case 't':
        case 'T':
            // Filtro Traduzidos
            document.querySelector('.filter-btn[data-filter="translated"]')?.click();
            break;
        case 'a':
        case 'A':
            // Filtro Todos
            document.querySelector('.filter-btn[data-filter="all"]')?.click();
            break;
        case 'Escape':
            // Fechar modal
            closeModal();
            break;
    }
});

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// ========== MODAL & CART FUNCTIONS ==========
let currentSuggestionId = '';
let suggestionCart = []; // Carrinho de sugestões

// ========== PERSISTÊNCIA DO CARRINHO ==========
const CART_STORAGE_KEY = 'wwm_suggestion_cart';

// Salvar carrinho no localStorage
function saveCartToStorage() {
    try {
        localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(suggestionCart));
    } catch (e) {
        console.warn('Erro ao salvar carrinho:', e);
    }
}

// Carregar carrinho do localStorage
function loadCartFromStorage() {
    try {
        const saved = localStorage.getItem(CART_STORAGE_KEY);
        if (saved) {
            suggestionCart = JSON.parse(saved);
            if (suggestionCart.length > 0) {
                updateCartUI();
                showToast(`${suggestionCart.length} sugestão(ões) restaurada(s) do rascunho`, 'info');
            }
        }
    } catch (e) {
        console.warn('Erro ao carregar carrinho:', e);
        suggestionCart = [];
    }
}

// Limpar carrinho do localStorage
function clearCartFromStorage() {
    try {
        localStorage.removeItem(CART_STORAGE_KEY);
    } catch (e) {
        console.warn('Erro ao limpar carrinho:', e);
    }
}

function openSuggestionModal(id, originalEncoded, currentEncoded, lineNumber) {
    currentSuggestionId = id;
    
    const original = decodeURIComponent(originalEncoded);
    const current = decodeURIComponent(currentEncoded);
    
    document.getElementById('modal-id').textContent = id;
    document.getElementById('modal-original').value = original;
    document.getElementById('modal-current').value = current || '(sem tradução atual)';
    document.getElementById('modal-suggestion').value = current; // Pré-preenche com a tradução atual
    document.getElementById('modal-file').value = CONFIG.PTBR_FILE; // Arquivo único de tradução
    document.getElementById('modal-line').value = lineNumber;
    
    // ========== CONTADOR DE CARACTERES ==========
    updateCharCounter(original.length);
    const suggestionInput = document.getElementById('modal-suggestion');
    suggestionInput.addEventListener('input', function() {
        updateCharCounter(original.length);
    });
    
    // ========== GLOSSÁRIO ==========
    const glossaryHints = document.getElementById('glossary-hints');
    const glossaryTermsList = document.getElementById('glossary-terms-list');
    
    if (glossaryHints && glossaryTermsList) {
        const terms = findGlossaryTerms(original);
        
        if (terms.length > 0) {
            glossaryHints.style.display = 'block';
            glossaryTermsList.innerHTML = terms.map(term => {
                const category = glossaryData?.categories[term.category];
                const categoryColor = category?.color || '#c9a227';
                const statusClass = term.doNotTranslate ? 'no-translate' : 'translate';
                const statusIcon = term.doNotTranslate ? 'fa-ban' : 'fa-check';
                
                return `
                    <div class="glossary-term-hint" style="--term-color: ${categoryColor}">
                        <div class="term-hint-header">
                            <span class="term-hint-original">${escapeHtml(term.original)}</span>
                            ${term.chinese ? `<span class="term-hint-chinese">${term.chinese}</span>` : ''}
                        </div>
                        <div class="term-hint-translation">
                            <i class="fas ${statusIcon} ${statusClass}"></i>
                            ${escapeHtml(term.translation)}
                        </div>
                        ${term.context ? `<div class="term-hint-context">${escapeHtml(term.context)}</div>` : ''}
                    </div>
                `;
            }).join('');
        } else {
            glossaryHints.style.display = 'none';
            glossaryTermsList.innerHTML = '';
        }
    }
    
    // ========== DUPLICATAS ==========
    const bulkEditSection = document.getElementById('bulk-edit-section');
    const duplicateCountEl = document.getElementById('duplicate-count');
    const duplicateIdsList = document.getElementById('duplicate-ids-list');
    const applyToAllCheckbox = document.getElementById('apply-to-all');
    
    if (bulkEditSection) {
        const duplicates = getDuplicateIds(original);
        
        if (duplicates.length > 1) {
            bulkEditSection.style.display = 'block';
            duplicateCountEl.textContent = duplicates.length;
            
            // Mostra lista de IDs (limitado a 10 para não sobrecarregar)
            const displayDuplicates = duplicates.slice(0, 10);
            const hasMore = duplicates.length > 10;
            
            duplicateIdsList.innerHTML = displayDuplicates.map(dup => {
                const statusClass = dup.isTranslated ? 'translated' : 'pending';
                const currentItem = dup.id === id;
                return `
                    <span class="duplicate-id ${statusClass} ${currentItem ? 'current' : ''}" title="Linha ${dup.lineNumber}">
                        ${dup.id.substring(0, 8)}...
                    </span>
                `;
            }).join('') + (hasMore ? `<span class="duplicate-more">+${duplicates.length - 10} mais</span>` : '');
            
            // Reseta checkbox
            if (applyToAllCheckbox) {
                applyToAllCheckbox.checked = false;
            }
        } else {
            bulkEditSection.style.display = 'none';
        }
    }
    
    document.getElementById('suggestion-modal').classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Foca no campo de sugestão
    setTimeout(() => {
        document.getElementById('modal-suggestion').focus();
    }, 100);
}


function closeModal() {
    document.getElementById('suggestion-modal').classList.remove('active');
    document.body.style.overflow = '';
    currentSuggestionId = '';
}

// Adiciona ao carrinho
async function addToCart() {
    const id = currentSuggestionId;
    const original = document.getElementById('modal-original').value;
    const current = document.getElementById('modal-current').value;
    const suggestion = document.getElementById('modal-suggestion').value.trim();
    const file = document.getElementById('modal-file').value;
    const lineNumber = parseInt(document.getElementById('modal-line').value);
    
    // Verifica se deve aplicar a todas as duplicatas
    const applyToAllCheckbox = document.getElementById('apply-to-all');
    const applyToAll = applyToAllCheckbox && applyToAllCheckbox.checked;
    
    if (!suggestion) {
        await showAlert('Por favor, digite sua sugestão de tradução.', 'Campo Obrigatório', 'warning');
        return;
    }
    
    const currentClean = current === '(sem tradução atual)' ? '' : current;
    if (suggestion === currentClean) {
        await showAlert('Sua sugestão é igual à tradução atual. Por favor, faça alguma alteração.', 'Sugestão Idêntica', 'warning');
        return;
    }
    
    // Se aplicar a todas as duplicatas
    if (applyToAll) {
        const duplicates = getDuplicateIds(original);
        let addedCount = 0;
        
        for (const dup of duplicates) {
            // Verifica se já existe no carrinho
            const existingIndex = suggestionCart.findIndex(item => item.id === dup.id);
            
            if (existingIndex >= 0) {
                suggestionCart[existingIndex].suggestion = suggestion;
            } else {
                suggestionCart.push({
                    id: dup.id,
                    original,
                    current: currentClean,
                    suggestion,
                    file,
                    lineNumber: dup.lineNumber,
                    bulkApplied: true // Marca como aplicado em massa
                });
                addedCount++;
            }
        }
        
        updateCartUI();
        closeModal();
        
        // Mostra feedback especial para edição em massa
        showToast(`${duplicates.length} sugestões adicionadas em massa! (${suggestionCart.length} no lote)`);
        return;
    }
    
    // Comportamento normal (uma sugestão)
    const existingIndex = suggestionCart.findIndex(item => item.id === id);
    if (existingIndex >= 0) {
        suggestionCart[existingIndex].suggestion = suggestion;
    } else {
        suggestionCart.push({
            id,
            original,
            current: currentClean,
            suggestion,
            file,
            lineNumber
        });
    }
    
    updateCartUI();
    closeModal();
    
    // Mostra feedback
    showToast(`Sugestão adicionada! (${suggestionCart.length} no lote)`);
}


// Toggle carrinho
function toggleCart() {
    document.getElementById('cart-panel').classList.toggle('active');
}

// Limpa carrinho
async function clearCart() {
    if (suggestionCart.length === 0) return;
    const confirmed = await showConfirm(
        'Tem certeza que deseja limpar todas as sugestões do carrinho?',
        {
            title: 'Limpar Carrinho',
            type: 'warning',
            confirmText: 'Sim, limpar',
            cancelText: 'Cancelar',
            confirmClass: 'custom-modal-btn-danger'
        }
    );
    if (confirmed) {
        suggestionCart = [];
        clearCartFromStorage();
        updateCartUI();
        showToast('Carrinho limpo', 'info');
    }
}

// Remove item do carrinho
function removeFromCart(index) {
    suggestionCart.splice(index, 1);
    updateCartUI();
}

// Atualiza UI do carrinho
function updateCartUI() {
    const badge = document.getElementById('cart-badge');
    const count = document.getElementById('cart-count');
    const items = document.getElementById('cart-items');
    const submit = document.getElementById('cart-submit');
    
    // Atualiza Set de IDs para O(1) lookup
    updateCartIdSet();
    
    // Atualiza contador
    badge.textContent = suggestionCart.length;
    count.textContent = suggestionCart.length;
    badge.classList.toggle('hidden', suggestionCart.length === 0);
    submit.disabled = suggestionCart.length === 0;
    
    // Salvar no localStorage
    saveCartToStorage();
    
    // Re-renderiza a tabela para atualizar indicadores de carrinho
    renderTable();
    
    // Renderiza itens no painel do carrinho
    if (suggestionCart.length === 0) {
        items.innerHTML = `
            <div class="cart-empty">
                <i class="fas fa-inbox cart-empty-icon"></i>
                Nenhuma sugestão adicionada
            </div>
        `;
    } else {
        items.innerHTML = suggestionCart.map((item, index) => `
            <div class="cart-item">
                <button class="cart-item-remove" onclick="removeFromCart(${index})" title="Remover">
                    <i class="fas fa-times"></i>
                </button>
                <div class="cart-item-id">${escapeHtml(item.id)}</div>
                <div class="cart-item-text">${escapeHtml(item.suggestion)}</div>
            </div>
        `).join('');
    }
}

// Envia todas as sugestões
// ========================================
// GitHub OAuth e API
// ========================================

// Verificar se voltou do OAuth com código
function checkOAuthCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const error = urlParams.get('error');
    
    if (error) {
        // Usuário cancelou ou erro
        window.history.replaceState({}, document.title, window.location.pathname);
        showToast('Login cancelado', 'warning');
        return;
    }
    
    if (code) {
        // Limpar URL
        window.history.replaceState({}, document.title, window.location.pathname);
        
        // Trocar código por token via Worker
        exchangeCodeForToken(code);
    } else if (githubToken) {
        // Já tem token, verificar se ainda é válido
        validateToken();
    }
}

// Trocar código OAuth por token via Cloudflare Worker
async function exchangeCodeForToken(code) {
    // Mostrar loading
    showLoadingModal('Autenticando com GitHub...');
    
    try {
        const response = await fetch(CONFIG.OAUTH_PROXY_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code }),
        });
        
        const data = await response.json();
        
        closeLoadingModal();
        
        if (data.error) {
            showToast('Erro: ' + data.error, 'error');
            return;
        }
        
        if (data.access_token) {
            githubToken = data.access_token;
            localStorage.setItem('github_token', githubToken);
            
            // Buscar dados do usuário
            await validateToken();
            
            if (githubUser) {
                showToast(`Bem-vindo, ${githubUser.login}!`);
            }
        }
        
    } catch (error) {
        closeLoadingModal();
        console.error('Erro na autenticação:', error);
        showToast('Erro na autenticação. Tente novamente.', 'error');
    }
}

// Modal de loading
function showLoadingModal(message) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'loading-modal';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 350px; text-align: center; padding: 2rem;">
            <i class="fas fa-spinner fa-spin" style="font-size: 3rem; color: var(--gold-primary); margin-bottom: 1rem;"></i>
            <p style="color: var(--text-secondary);">${message}</p>
        </div>
    `;
    document.body.appendChild(modal);
    modal.style.display = 'flex';
}

function closeLoadingModal() {
    const modal = document.getElementById('loading-modal');
    if (modal) modal.remove();
}

// Validar token existente
async function validateToken() {
    if (!githubToken) return;
    
    try {
        const response = await fetch('https://api.github.com/user', {
            headers: {
                'Authorization': `Bearer ${githubToken}`,
                'Accept': 'application/vnd.github.v3+json'
            }
        });
        
        if (response.ok) {
            githubUser = await response.json();
            updateAuthButton();
        } else {
            // Token inválido
            logout();
        }
    } catch (error) {
        console.error('Erro ao validar token:', error);
    }
}

// Handler do botão de auth - AGORA USA OAUTH!
function handleGitHubAuth() {
    if (githubToken && githubUser) {
        // Já logado - mostrar opções
        showUserMenu();
    } else {
        // Redirecionar para GitHub OAuth
        // Remove .html do pathname para corresponder ao redirect_uri configurado no GitHub OAuth App
        const pathname = window.location.pathname.replace(/\.html$/, '');
        const redirectUri = encodeURIComponent(window.location.origin + pathname);
        const scope = encodeURIComponent('public_repo');
        const authUrl = `https://github.com/login/oauth/authorize?client_id=${CONFIG.GITHUB_CLIENT_ID}&redirect_uri=${redirectUri}&scope=${scope}`;
        
        window.location.href = authUrl;
    }
}

// Atualizar botão de auth
function updateAuthButton() {
    const btn = document.getElementById('github-auth-btn');
    
    if (githubUser) {
        btn.classList.add('logged-in');
        // Sanitizar dados do usuário para prevenir XSS
        const safeLogin = escapeHtml(githubUser.login);
        const safeAvatarUrl = escapeHtml(githubUser.avatar_url);
        btn.innerHTML = `
            <img src="${safeAvatarUrl}" class="avatar" alt="${safeLogin}">
            ${safeLogin}
            <i class="fas fa-sign-out-alt logout-icon" onclick="event.stopPropagation(); logout();" title="Sair"></i></i>
        `;
    } else {
        btn.classList.remove('logged-in');
        btn.innerHTML = '<i class="fab fa-github"></i> Entrar com GitHub';
    }
    // Atualiza visibilidade da aba admin caso o usuário seja o dono do repo
    showAdminTabIfOwner();
}

// Logout
function logout() {
    githubToken = null;
    githubUser = null;
    localStorage.removeItem('github_token');
    updateAuthButton();
    showToast('Desconectado do GitHub', 'info');
}

// Menu do usuário
async function showUserMenu() {
    // Sanitizar dados do usuário para prevenir XSS
    const safeLogin = escapeHtml(githubUser?.login || 'usuário');
    
    // Por simplicidade, só faz logout
    const confirmed = await showConfirm(
        `Você está logado como <strong>${safeLogin}</strong>.<br><br>Deseja sair da conta?`,
        {
            title: 'Conta GitHub',
            type: 'info',
            confirmText: 'Sair',
            cancelText: 'Ficar logado',
            confirmClass: 'custom-modal-btn-danger',
            icon: 'fa-user-circle'
        }
    );
    if (confirmed) {
        logout();
    }
}

// ========================================
// Admin Issues Panel (apenas dono/owner)
// ========================================

// Verifica se o usuário é realmente o dono com múltiplas camadas de segurança
async function isAuthenticatedOwner() {
    if (!githubUser || !githubToken) return false;
    
    // 1. Verificação por username (case-insensitive)
    const usernameMatch = githubUser.login && 
        githubUser.login.toLowerCase() === CONFIG.GITHUB_OWNER.toLowerCase();
    
    // 2. Verificação por ID numérico (imutável - mais seguro)
    const idMatch = githubUser.id && githubUser.id === CONFIG.GITHUB_OWNER_ID;
    
    // Se ambos não baterem, não é o dono
    if (!usernameMatch || !idMatch) {
        console.warn('Admin check failed: username or ID mismatch');
        return false;
    }
    
    // 3. Verificação de permissão no repositório via API
    try {
        const resp = await fetch(
            `https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/collaborators/${githubUser.login}/permission`,
            {
                headers: {
                    'Accept': 'application/vnd.github.v3+json',
                    'Authorization': `Bearer ${githubToken}`
                }
            }
        );
        
        if (!resp.ok) {
            console.warn('Admin check failed: could not verify repo permission');
            return false;
        }
        
        const data = await resp.json();
        // Só permite se for 'admin' ou 'write' (owner tem admin)
        const hasPermission = data.permission === 'admin' || data.permission === 'write';
        
        if (!hasPermission) {
            console.warn('Admin check failed: insufficient repo permission:', data.permission);
            return false;
        }
        
        return true;
    } catch (e) {
        console.error('Admin permission check error:', e);
        return false;
    }
}

// Mostra a aba admin somente se passar em TODAS as verificações de segurança
async function showAdminTabIfOwner() {
    const adminTab = document.getElementById('admin-tab');
    const adminPanel = document.getElementById('admin-panel');
    if (!adminTab || !adminPanel) return;
    
    try {
        const isOwner = await isAuthenticatedOwner();
        
        if (isOwner) {
            adminTab.style.display = '';
            // Remove listener antigo para evitar duplicatas
            adminTab.onclick = () => {
                showAdminPanel(true);
                loadAdminIssues();
            };
            console.log('✅ Admin access granted');
        } else {
            adminTab.style.display = 'none';
            adminPanel.classList.add('hidden');
            adminTab.onclick = null;
        }
    } catch (e) {
        console.error('showAdminTabIfOwner error', e);
        adminTab.style.display = 'none';
        adminPanel.classList.add('hidden');
    }
}

// Força atualização das issues do admin (limpa cache)
function refreshAdminIssues() {
    localStorage.removeItem(CONFIG.CACHE_PREFIX + 'admin_open_issues');
    loadAdminIssues();
}

// ========== AUTO-REFRESH INTELIGENTE ==========
let adminPollingInterval = null;
let countdownInterval = null;
let countdownSeconds = 120; // 2 minutos
let lastKnownIssueIds = new Set();
const ADMIN_POLL_INTERVAL = 2 * 60 * 1000; // 2 minutos - gentil com a API

// Inicia polling quando entra na aba admin
function startAdminPolling() {
    if (adminPollingInterval) return; // Já está rodando
    
    console.log('[Admin] Auto-refresh iniciado (a cada 2 min)');
    countdownSeconds = 120;
    updateCountdownDisplay();
    
    // Countdown visual
    countdownInterval = setInterval(() => {
        if (document.visibilityState === 'visible' && currentFile === 'admin') {
            countdownSeconds--;
            updateCountdownDisplay();
            
            if (countdownSeconds <= 0) {
                countdownSeconds = 120;
                checkForNewIssues();
            }
        }
    }, 1000);
    
    // Marcar como ativo
    const countdownEl = document.getElementById('admin-countdown');
    if (countdownEl) countdownEl.classList.add('active');
}

// Atualiza display do countdown
function updateCountdownDisplay() {
    const timerEl = document.getElementById('countdown-timer');
    if (timerEl) {
        const mins = Math.floor(countdownSeconds / 60);
        const secs = countdownSeconds % 60;
        timerEl.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}

// Para polling quando sai da aba admin
function stopAdminPolling() {
    if (countdownInterval) {
        clearInterval(countdownInterval);
        countdownInterval = null;
    }
    if (adminPollingInterval) {
        clearInterval(adminPollingInterval);
        adminPollingInterval = null;
    }
    
    const countdownEl = document.getElementById('admin-countdown');
    if (countdownEl) countdownEl.classList.remove('active');
    
    console.log('[Admin] Auto-refresh pausado');
}

// Verificação manual (botão)
async function manualCheckNewIssues() {
    const btn = document.querySelector('.admin-refresh-btn');
    if (btn) {
        btn.disabled = true;
        btn.classList.add('checking');
        btn.innerHTML = '<i class="fas fa-sync-alt"></i> Verificando...';
    }
    
    try {
        await checkForNewIssues(true); // force = true
        showToast('✓ Verificação concluída', 'success');
    } catch (e) {
        showToast('Erro ao verificar: ' + e.message, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.classList.remove('checking');
            btn.innerHTML = '<i class="fas fa-search"></i> Verificar';
        }
        // Resetar countdown após verificação manual
        countdownSeconds = 120;
        updateCountdownDisplay();
    }
}

// Verifica se há novas issues (sem recarregar tudo)
async function checkForNewIssues(forceReload = false) {
    try {
        const headers = { 'Accept': 'application/vnd.github.v3+json' };
        if (githubToken) headers['Authorization'] = `Bearer ${githubToken}`;
        
        // Buscar apenas issues mais recentes (per_page=20 para economizar)
        const resp = await fetch(
            `https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues?state=open&per_page=20&sort=created&direction=desc`,
            { headers }
        );
        
        if (!resp.ok) throw new Error('Falha ao buscar issues');
        
        const issues = await resp.json();
        const currentIds = new Set(issues.map(i => i.number));
        
        // Verificar novas issues
        const newIssues = issues.filter(i => !lastKnownIssueIds.has(i.number));
        
        // Se forceReload ou há novas issues
        if (forceReload || (newIssues.length > 0 && lastKnownIssueIds.size > 0)) {
            if (newIssues.length > 0 && lastKnownIssueIds.size > 0) {
                // Só mostra notificação se não foi manual
                if (!forceReload) {
                    showNewIssuesNotification(newIssues.length);
                }
            }
            
            // Limpar cache e recarregar
            localStorage.removeItem(CONFIG.CACHE_PREFIX + 'admin_open_issues');
            await loadAdminIssues();
        }
        
        // Atualizar IDs conhecidos
        lastKnownIssueIds = currentIds;
        
    } catch (e) {
        console.warn('[Admin] Erro no auto-refresh:', e);
        throw e; // Re-throw para o handler manual capturar
    }
}

// Notificação discreta de novas issues
function showNewIssuesNotification(count) {
    const notification = document.createElement('div');
    notification.className = 'new-issues-notification';
    notification.innerHTML = `
        <i class="fas fa-bell"></i>
        <span>${count} nova${count > 1 ? 's' : ''} issue${count > 1 ? 's' : ''} de tradução!</span>
    `;
    document.body.appendChild(notification);
    
    // Animar entrada
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Remover após 4 segundos
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Carrega Issues abertas (todas, filtrando por título/conteúdo de tradução)
async function loadAdminIssues() {
    const adminPanel = document.getElementById('admin-panel');
    const adminList = document.getElementById('admin-list');
    const adminLoading = document.getElementById('admin-loading');
    if (!adminPanel || !adminList || !adminLoading) return;
    adminPanel.classList.remove('hidden');
    adminLoading.classList.remove('hidden');
    adminList.innerHTML = '';

    try {
        const headers = { 'Accept': 'application/vnd.github.v3+json' };
        if (githubToken) headers['Authorization'] = `Bearer ${githubToken}`;
        
        // Buscar issues abertas COM CACHE (TTL curto de 2 min via key específica)
        const cacheKey = 'admin_open_issues';
        let issues = apiCache.get(cacheKey);
        
        if (!issues) {
            const resp = await fetch(
                `https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues?state=open&per_page=100&sort=created&direction=desc`,
                { headers }
            );
            
            if (!resp.ok) throw new Error('Falha ao buscar issues: ' + resp.status);
            issues = await resp.json();
            
            // Cache curto de 2 minutos para admin (precisa ser mais atualizado)
            const shortCache = {
                data: issues,
                timestamp: Date.now()
            };
            localStorage.setItem(CONFIG.CACHE_PREFIX + cacheKey, JSON.stringify(shortCache));
        }
        
        // Filtrar issues que parecem ser de tradução:
        issues = issues.filter(issue => {
            if (issue.pull_request) return false;
            
            const title = (issue.title || '').toLowerCase();
            const body = (issue.body || '').toLowerCase();
            const hasTranslationLabel = issue.labels && issue.labels.some(l => 
                l.name === 'translation' || l.name === 'batch-suggestion'
            );
            
            const wasProcessed = issue.labels && issue.labels.some(l => 
                l.name === 'approved' || l.name === 'rejected'
            );
            if (wasProcessed) return false;
            
            const titleMatch = title.includes('[tradução]') || 
                               title.includes('tradução') || 
                               title.includes('translation') ||
                               title.includes('sugestão') ||
                               title.includes('sugestões');
            const bodyMatch = body.includes('"suggestions"') || 
                              body.includes('```json') ||
                              body.includes('sugestão de tradução');
            
            return hasTranslationLabel || titleMatch || bodyMatch;
        });

        if (!issues || issues.length === 0) {
            adminList.innerHTML = `
                <div class="admin-empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>Nenhuma issue de tradução pendente</p>
                </div>
            `;
            return;
        }

        // Render cards grid
        adminList.innerHTML = `<div class="admin-issues-grid">${issues.map(issue => {
            const created = new Date(issue.created_at);
            const dateStr = created.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
            const timeStr = created.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
            
            // Tentar extrair contagem de sugestões do corpo
            let suggestionCount = 0;
            const totalMatch = issue.body?.match(/\*\*Total:\*\*\s*(\d+)/);
            if (totalMatch) suggestionCount = parseInt(totalMatch[1]);
            else {
                const jsonMatch = issue.body?.match(/"total"\s*:\s*(\d+)/);
                if (jsonMatch) suggestionCount = parseInt(jsonMatch[1]);
            }
            
            // Título mais curto
            let shortTitle = issue.title || 'Sem título';
            if (shortTitle.startsWith('[Tradução]')) shortTitle = shortTitle.replace('[Tradução]', '').trim();
            if (shortTitle.length > 50) shortTitle = shortTitle.substring(0, 47) + '...';
            
            // Sanitizar dados do usuário para prevenir XSS
            const safeUserLogin = escapeHtml(issue.user?.login || 'anônimo');
            const safeUserAvatar = escapeHtml(issue.user?.avatar_url || '');
            
            return `
                <div class="admin-issue-card" data-issue="${issue.number}">
                    <div class="admin-card-header">
                        <span class="admin-issue-number"><i class="fas fa-hashtag"></i> ${issue.number}</span>
                        <span class="admin-issue-title">${escapeHtml(shortTitle)}</span>
                    </div>
                    <div class="admin-card-meta">
                        <div class="admin-meta-author">
                            <img src="${safeUserAvatar}" alt="${safeUserLogin}">
                            <span>@${safeUserLogin}</span>
                        </div>
                        <div class="admin-meta-date">
                            <i class="fas fa-calendar-alt"></i> ${dateStr} ${timeStr}
                        </div>
                        ${suggestionCount > 0 ? `
                            <div class="admin-meta-count">
                                <i class="fas fa-list"></i> ${suggestionCount} sugestão${suggestionCount > 1 ? 'ões' : ''}
                            </div>
                        ` : ''}
                    </div>
                    <div class="admin-card-actions">
                        <button class="admin-btn-view" onclick="openAdminIssueModal(${issue.number})">
                            <i class="fas fa-eye"></i> Revisar
                        </button>
                        <button class="admin-btn-reject" onclick="rejectIssue(${issue.number})">
                            <i class="fas fa-times"></i>
                        </button>
                        <button class="admin-btn-approve" onclick="approveIssue(${issue.number})">
                            <i class="fas fa-check"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('')}</div>`;
        
        // Atualizar IDs conhecidos para o auto-refresh
        lastKnownIssueIds = new Set(issues.map(i => i.number));

    } catch (e) {
        console.error(e);
        adminList.innerHTML = `<div class="admin-empty-state"><i class="fas fa-exclamation-triangle"></i><p>Erro: ${e.message}</p></div>`;
    } finally {
        adminLoading.classList.add('hidden');
    }
}

// Parse sugestões do corpo da issue
function parseIssueSuggestions(body) {
    if (!body) return [];
    
    // Tentar extrair JSON do bloco ```json ... ```
    const jsonMatch = body.match(/```json\s*\n([\s\S]*?)\n```/);
    if (!jsonMatch) return [];
    
    try {
        const data = JSON.parse(jsonMatch[1].trim());
        if (data.suggestions && Array.isArray(data.suggestions)) {
            return data.suggestions;
        }
    } catch (e) {
        console.error('Erro ao parsear JSON da issue:', e);
    }
    return [];
}

// Abre modal com detalhes da issue - versão melhorada
async function openAdminIssueModal(issueNumber) {
    try {
        showLoadingModal('Carregando detalhes...');
        
        const headers = { 'Accept': 'application/vnd.github.v3+json' };
        if (githubToken) headers['Authorization'] = `Bearer ${githubToken}`;
        const resp = await fetch(`https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues/${issueNumber}`, { headers });
        if (!resp.ok) throw new Error('Falha ao buscar issue');
        const issue = await resp.json();
        
        closeLoadingModal();
        
        // Extrair sugestões do corpo
        const suggestions = parseIssueSuggestions(issue.body);
        
        // Buscar dados originais do arquivo TSV para comparação
        // Passa as sugestões completas para saber de qual arquivo cada uma veio
        let originalData = [];
        if (suggestions.length > 0) {
            originalData = await fetchOriginalTexts(suggestions);
        }
        
        const created = new Date(issue.created_at).toLocaleString('pt-BR');
        
        // Sanitizar dados do usuário para prevenir XSS
        const safeUserLogin = escapeHtml(issue.user?.login || 'anônimo');
        const safeUserAvatar = escapeHtml(issue.user?.avatar_url || '');
        const safeHtmlUrl = escapeHtml(issue.html_url || '');
        
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = 'admin-issue-modal';
        modal.innerHTML = `
            <div class="modal-content admin-review-modal">
                <div class="modal-header">
                    <h3><i class="fas fa-clipboard-check"></i> Revisão da Issue #${issue.number}</h3>
                    <button class="modal-close" onclick="document.getElementById('admin-issue-modal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="admin-modal-info">
                        <div class="admin-info-item">
                            <div class="admin-info-label">Autor</div>
                            <div class="admin-info-value">
                                <img src="${safeUserAvatar}" style="width:18px;height:18px;border-radius:50%;vertical-align:middle;margin-right:4px;">
                                @${safeUserLogin}
                            </div>
                        </div>
                        <div class="admin-info-item">
                            <div class="admin-info-label">Data</div>
                            <div class="admin-info-value">${created}</div>
                        </div>
                        <div class="admin-info-item">
                            <div class="admin-info-label">Sugestões</div>
                            <div class="admin-info-value">${suggestions.length}</div>
                        </div>
                        <div class="admin-info-item">
                            <div class="admin-info-label">GitHub</div>
                            <div class="admin-info-value"><a href="${safeHtmlUrl}" target="_blank"><i class="fas fa-external-link-alt"></i> Abrir</a></div>
                        </div>
                    </div>
                    
                    ${suggestions.length > 0 ? `
                        <div class="form-group">
                            <label><i class="fas fa-list-alt"></i> Sugestões de Tradução</label>
                        </div>
                        <div class="admin-suggestions-list" id="admin-suggestions-list">
                            ${suggestions.map((sug, idx) => {
                                // Buscar pelo ID E arquivo para evitar conflito de IDs duplicados
                                const orig = originalData.find(o => o.id === sug.id && o.file === sug.file)
                                          || originalData.find(o => o.id === sug.id); // fallback
                                const originalText = orig?.originalText || '(não encontrado)';
                                const currentTranslation = orig?.translatedText || '';
                                const sourceFile = sug.file === 'translate_words_map_en_diff.tsv' ? 'Diff' : 'Main';
                                
                                // Só mostra "Tradução Atual" se for DIFERENTE do original (já foi traduzido)
                                const hasCurrentTranslation = currentTranslation && 
                                    currentTranslation.trim() !== '' && 
                                    currentTranslation !== originalText;
                                
                                return `
                                    <div class="admin-suggestion-item" data-index="${idx}" data-file="${escapeHtml(sug.file)}" data-rejected="false">
                                        <div class="admin-suggestion-header">
                                            <span class="admin-suggestion-id"><i class="fas fa-fingerprint"></i> ${escapeHtml(sug.id)}</span>
                                            <span class="admin-suggestion-file" title="Arquivo: ${escapeHtml(sug.file)}"><i class="fas fa-file-alt"></i> ${escapeHtml(sourceFile)}</span>
                                            <span class="admin-suggestion-index">#${idx + 1} de ${suggestions.length}</span>
                                            <button type="button" class="admin-reject-line-btn" onclick="toggleRejectSuggestion(${idx})" title="Rejeitar esta sugestão">
                                                <i class="fas fa-times"></i> Rejeitar
                                            </button>
                                        </div>
                                        <div class="admin-suggestion-body">
                                            <div class="admin-text-row">
                                                <div class="admin-text-label"><i class="fas fa-globe"></i> Original (EN)</div>
                                                <div class="admin-text-content original">${escapeHtml(originalText)}</div>
                                            </div>
                                            ${hasCurrentTranslation ? `
                                                <div class="admin-text-row">
                                                    <div class="admin-text-label"><i class="fas fa-check-circle" style="color: var(--success);"></i> Já Traduzido (PT-BR)</div>
                                                    <div class="admin-text-content current">${escapeHtml(currentTranslation)}</div>
                                                </div>
                                                <div class="admin-already-translated-notice">
                                                    <i class="fas fa-info-circle"></i> Esta linha já possui tradução aprovada. A nova sugestão substituirá a existente se aprovada.
                                                </div>
                                            ` : ''}
                                            <div class="admin-text-row">
                                                <div class="admin-text-label"><i class="fas fa-lightbulb"></i> Nova Sugestão</div>
                                                <textarea class="admin-edit-suggestion" data-sug-id="${escapeHtml(sug.id)}" data-sug-idx="${idx}">${escapeHtml(sug.suggestion)}</textarea>
                                            </div>
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    ` : `
                        <div class="admin-empty-state">
                            <i class="fas fa-question-circle"></i>
                            <p>Não foi possível extrair sugestões do corpo da issue.<br>Verifique manualmente no GitHub.</p>
                        </div>
                    `}
                </div>
                <div class="modal-footer admin-modal-actions">
                    <button class="btn-cancel" onclick="document.getElementById('admin-issue-modal').remove()">
                        <i class="fas fa-times"></i> Fechar
                    </button>
                    <button class="btn-reject" onclick="rejectIssueWithEdits(${issue.number})">
                        <i class="fas fa-ban"></i> Rejeitar
                    </button>
                    <button class="btn-approve" onclick="approveIssueWithEdits(${issue.number})">
                        <i class="fas fa-check-circle"></i> Aprovar
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.style.display = 'flex';

    } catch (e) {
        closeLoadingModal();
        console.error(e);
        showToast('Erro ao abrir a issue: ' + e.message, 'error');
    }
}

// Busca textos originais para comparação no admin
// Simplificado: agora usa allData (único array)
async function fetchOriginalTexts(suggestions) {
    const results = [];
    
    // Se os dados não foram carregados ainda, aguardar carregamento
    if (allData.length === 0) {
        await loadTranslationsIfNeeded();
    }
    
    suggestions.forEach(sug => {
        const id = sug.id;
        const fileName = sug.file || CONFIG.PTBR_FILE;
        
        // Buscar no array único
        const found = allData.find(item => item.id === id);
        if (found) {
            results.push({
                id: found.id,
                file: fileName,
                originalText: found.originalText,
                translatedText: found.translatedText
            });
        } else {
            // Não encontrado
            results.push({
                id: id,
                file: fileName,
                originalText: '(não encontrado)',
                translatedText: ''
            });
        }
    });
    
    return results;
}

// Função auxiliar para carregar traduções se necessário
async function loadTranslationsIfNeeded() {
    if (allData.length > 0) return;
    
    try {
        const [englishContent, ptbrContent] = await Promise.all([
            fetchTSV(CONFIG.ENGLISH_FILE),
            fetchTSV(CONFIG.PTBR_FILE)
        ]);
        
        if (ptbrContent) {
            const englishMap = englishContent ? parseTSVtoMap(englishContent) : new Map();
            const ptbrMap = parseTSVtoMap(ptbrContent);
            allData = compareTranslations(englishMap, ptbrMap);
        }
    } catch (e) {
        console.error('Erro ao carregar traduções:', e);
    }
}

// Salva edições feitas nas sugestões
async function saveAdminEdits(issueNumber) {
    try {
        const headers = { 'Accept': 'application/vnd.github.v3+json' };
        if (githubToken) headers['Authorization'] = `Bearer ${githubToken}`;
        
        // Buscar issue atual
        const resp = await fetch(`https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues/${issueNumber}`, { headers });
        if (!resp.ok) throw new Error('Falha ao buscar issue');
        const issue = await resp.json();
        
        // Extrair sugestões atuais
        const suggestions = parseIssueSuggestions(issue.body);
        if (suggestions.length === 0) {
            showToast('Não há sugestões para editar', 'warning');
            return;
        }
        
        // Coletar valores editados dos textareas
        const textareas = document.querySelectorAll('.admin-edit-suggestion');
        textareas.forEach(ta => {
            const idx = parseInt(ta.dataset.sugIdx);
            if (suggestions[idx]) {
                suggestions[idx].suggestion = ta.value;
            }
        });
        
        // Reconstruir o JSON
        const jsonMatch = issue.body.match(/```json\s*\n([\s\S]*?)\n```/);
        if (!jsonMatch) {
            showToast('Formato de issue inválido', 'error');
            return;
        }
        
        let data = JSON.parse(jsonMatch[1].trim());
        data.suggestions = suggestions;
        
        // Reconstruir corpo da issue com JSON atualizado
        const newJson = JSON.stringify(data);
        const newBody = issue.body.replace(/```json\s*\n[\s\S]*?\n```/, '```json\n' + newJson + '\n```');
        
        const confirmSave = await showConfirm(
            'Deseja salvar as edições feitas nas sugestões?',
            {
                title: 'Salvar Edições',
                type: 'confirm',
                confirmText: 'Salvar',
                cancelText: 'Cancelar',
                icon: 'fa-save'
            }
        );
        if (!confirmSave) return;
        
        // Atualizar issue
        const updateResp = await fetch(`https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues/${issueNumber}`, {
            method: 'PATCH',
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ body: newBody })
        });
        
        if (!updateResp.ok) throw new Error('Falha ao salvar');
        
        showToast('Edições salvas com sucesso!', 'success');
        loadAdminIssues();
        
    } catch (e) {
        console.error(e);
        showToast('Erro ao salvar: ' + e.message, 'error');
    }
}

// Aprova issue: adiciona label 'approved'
async function approveIssue(issueNumber) {
    // 🚨 VALIDAÇÃO DE SEGURANÇA: Verificar se é admin antes de prosseguir
    const isOwner = await isAuthenticatedOwner();
    if (!isOwner) {
        showToast('❌ Acesso negado: você não tem permissão para aprovar issues.', 'error');
        return;
    }
    
    const confirmed = await showConfirm(
        'Tem certeza que deseja <strong>aprovar</strong> esta issue?<br><br>' +
        '<small style="color: var(--text-muted);">Isso acionará a automação que aplicará as traduções no repositório.</small>',
        {
            title: 'Aprovar Issue',
            type: 'success',
            confirmText: 'Aprovar',
            cancelText: 'Cancelar',
            confirmClass: 'custom-modal-btn-success',
            icon: 'fa-check-circle'
        }
    );
    if (!confirmed) return;
    try {
        const headers = { 'Accept': 'application/vnd.github.v3+json' };
        if (githubToken) headers['Authorization'] = `Bearer ${githubToken}`;
        const resp = await fetch(`https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues/${issueNumber}/labels`, {
            method: 'POST', headers, body: JSON.stringify({ labels: ['approved'] })
        });
        if (!resp.ok) throw new Error('Falha ao aplicar label');
        showToast('Issue aprovada (label "approved" aplicada).', 'success');
        // Limpa cache e refresh admin list
        localStorage.removeItem(CONFIG.CACHE_PREFIX + 'admin_open_issues');
        localStorage.removeItem(CONFIG.CACHE_PREFIX + 'applied_issues');
        loadAdminIssues();
        // close modal if open
        const m = document.getElementById('admin-issue-modal'); if (m) m.remove();
    } catch (e) {
        console.error(e);
        showToast('Erro ao aprovar issue: ' + e.message, 'error');
    }
}

// Rejeitar issue: aplica label 'rejected', fecha issue e adiciona comentário
async function rejectIssue(issueNumber) {
    // 🚨 VALIDAÇÃO DE SEGURANÇA: Verificar se é admin antes de prosseguir
    const isOwner = await isAuthenticatedOwner();
    if (!isOwner) {
        showToast('❌ Acesso negado: você não tem permissão para rejeitar issues.', 'error');
        return;
    }
    
    const reason = await showPrompt(
        'Digite o motivo da rejeição. Isso será postado como comentário na Issue.',
        {
            title: 'Rejeitar Issue',
            type: 'danger',
            defaultValue: 'Sugestão não adequada / Formato incorreto',
            placeholder: 'Motivo da rejeição...',
            confirmText: 'Rejeitar',
            cancelText: 'Cancelar'
        }
    );
    if (reason === null) return;
    try {
        const headers = { 'Accept': 'application/vnd.github.v3+json' };
        if (githubToken) headers['Authorization'] = `Bearer ${githubToken}`;
        
        // Aplica label 'rejected' E FECHA a issue
        await fetch(`https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues/${issueNumber}`, {
            method: 'PATCH', 
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                state: 'closed',
                labels: ['rejected']
            })
        });
        
        // Adiciona comentário
        await fetch(`https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues/${issueNumber}/comments`, {
            method: 'POST', headers, body: JSON.stringify({ body: `❌ **Rejeitado pelo revisor**\n\n${reason}` })
        });
        
        showToast('Issue rejeitada e fechada.', 'info');
        // Limpa cache e refresh admin list
        localStorage.removeItem(CONFIG.CACHE_PREFIX + 'admin_open_issues');
        loadAdminIssues();
        const m = document.getElementById('admin-issue-modal'); if (m) m.remove();
    } catch (e) {
        console.error(e);
        showToast('Erro ao rejeitar issue: ' + e.message, 'error');
    }
}

// ========== FUNÇÕES COMBINADAS: EDITAR + APROVAR/REJEITAR ==========

// Coleta edições dos textareas do modal (inclui status de rejeitado)
function collectEditsFromModal() {
    const items = document.querySelectorAll('.admin-suggestion-item');
    const edits = [];
    items.forEach(item => {
        const textarea = item.querySelector('.admin-edit-suggestion');
        if (textarea) {
            edits.push({
                idx: parseInt(textarea.dataset.sugIdx),
                id: textarea.dataset.sugId,
                value: textarea.value,
                rejected: item.dataset.rejected === 'true'
            });
        }
    });
    return edits;
}

// Toggle rejeitar/aceitar uma sugestão individual
function toggleRejectSuggestion(idx) {
    const item = document.querySelector(`.admin-suggestion-item[data-index="${idx}"]`);
    if (!item) return;
    
    const isRejected = item.dataset.rejected === 'true';
    const btn = item.querySelector('.admin-reject-line-btn');
    
    if (isRejected) {
        // Desfazer rejeição
        item.dataset.rejected = 'false';
        item.classList.remove('rejected');
        if (btn) btn.innerHTML = '<i class="fas fa-times"></i> Rejeitar';
    } else {
        // Rejeitar
        item.dataset.rejected = 'true';
        item.classList.add('rejected');
        if (btn) btn.innerHTML = '<i class="fas fa-undo"></i> Desfazer';
    }
    
    // Atualizar contador no header do modal
    updateRejectedCounter();
}

// Atualiza contador de rejeitados no modal
function updateRejectedCounter() {
    const total = document.querySelectorAll('.admin-suggestion-item').length;
    const rejected = document.querySelectorAll('.admin-suggestion-item.rejected').length;
    const approved = total - rejected;
    
    // Atualizar o header do modal se existir
    let counter = document.getElementById('admin-suggestion-counter');
    if (!counter) {
        const header = document.querySelector('.admin-modal-info');
        if (header) {
            const counterDiv = document.createElement('div');
            counterDiv.className = 'admin-info-item';
            counterDiv.innerHTML = `
                <div class="admin-info-label">Status</div>
                <div class="admin-info-value" id="admin-suggestion-counter"></div>
            `;
            header.appendChild(counterDiv);
            counter = document.getElementById('admin-suggestion-counter');
        }
    }
    
    if (counter) {
        if (rejected > 0) {
            counter.innerHTML = `<span style="color: var(--success);">${approved} ✓</span> / <span style="color: #ef4444;">${rejected} ✗</span>`;
        } else {
            counter.innerHTML = `<span style="color: var(--success);">${approved} aprovadas</span>`;
        }
    }
}

// Verifica se houve edições ou rejeições comparando com os valores originais
function hasChanges(suggestions, edits) {
    for (const edit of edits) {
        // Se algum foi rejeitado, há mudança
        if (edit.rejected) return true;
        // Se o texto foi editado, há mudança
        if (suggestions[edit.idx] && suggestions[edit.idx].suggestion !== edit.value) {
            return true;
        }
    }
    return false;
}

// Atualiza a seção de Resumo no corpo da issue para refletir as edições e rejeições
function updateSummarySection(body, suggestions, rejectedIds = []) {
    // Gerar novo resumo com indicação de edições e rejeições
    const newSummary = suggestions.map((item, i) => {
        const text = item.suggestion.substring(0, 50);
        const edited = item.editedByReviewer ? ' ✏️' : '';
        return `${i+1}. \`${item.id}\`${edited} → ${text}...`;
    }).join('\n');
    
    // Adicionar notas sobre edições e rejeições
    const editedCount = suggestions.filter(s => s.editedByReviewer).length;
    const rejectedCount = rejectedIds.length;
    
    let reviewerNotes = [];
    if (editedCount > 0) {
        reviewerNotes.push(`✏️ **${editedCount} tradução(ões) editada(s)** pelo revisor`);
    }
    if (rejectedCount > 0) {
        reviewerNotes.push(`❌ **${rejectedCount} tradução(ões) rejeitada(s)** pelo revisor: \`${rejectedIds.join('`, `')}\``);
    }
    
    let reviewerNote = '';
    if (reviewerNotes.length > 0) {
        reviewerNote = '\n\n> ' + reviewerNotes.join('\n> ');
    }
    
    // Substituir a seção de resumo existente
    // Padrão: "### 📄 Resumo" seguido de linhas numeradas até "---"
    const summaryPattern = /### 📄 Resumo\n([\s\S]*?)(\n---|\n\n---|\n> ⚠️)/;
    const match = body.match(summaryPattern);
    
    if (match) {
        const newSection = `### 📄 Resumo\n${newSummary}${reviewerNote}\n\n---`;
        body = body.replace(summaryPattern, newSection);
    }
    
    return body;
}

// Salva edições na issue (retorna objeto com resultado)
// IMPORTANTE: edits deve ser passado como parâmetro (coletado ANTES de fechar o modal)
// Retorna: { success, hadEdits, hadRejections, approvedCount, rejectedCount, rejectedIds }
async function saveEditsIfNeeded(issueNumber, edits = null) {
    const headers = { 'Accept': 'application/vnd.github.v3+json' };
    if (githubToken) headers['Authorization'] = `Bearer ${githubToken}`;

    try {
        // Se não passou edições, tenta coletar do modal (fallback)
        if (!edits || edits.length === 0) {
            edits = collectEditsFromModal();
        }
        
        // Se ainda não tem edições, não há o que salvar
        if (!edits || edits.length === 0) {
            console.warn('saveEditsIfNeeded: Nenhuma edição para salvar');
            return { success: true, hadEdits: false, hadRejections: false, approvedCount: 0, rejectedCount: 0, editedCount: 0, rejectedIds: [] };
        }
        
        // Separar aprovados e rejeitados
        const approvedEdits = edits.filter(e => !e.rejected);
        const rejectedEdits = edits.filter(e => e.rejected);
        const rejectedIds = rejectedEdits.map(e => e.id);
        
        console.log(`saveEditsIfNeeded: ${approvedEdits.length} aprovadas, ${rejectedEdits.length} rejeitadas`);

        // Buscar issue atual
        const resp = await fetch(`https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues/${issueNumber}`, { headers });
        if (!resp.ok) throw new Error('Falha ao buscar issue');
        const issue = await resp.json();

        // Extrair sugestões originais
        const originalSuggestions = parseIssueSuggestions(issue.body);
        if (originalSuggestions.length === 0) {
            return { success: true, hadEdits: false, hadRejections: false, approvedCount: 0, rejectedCount: 0, editedCount: 0, rejectedIds: [] };
        }

        // Verificar se houve mudanças (edições ou rejeições)
        if (!hasChanges(originalSuggestions, edits)) {
            console.log('saveEditsIfNeeded: Sem mudanças detectadas');
            return { success: true, hadEdits: false, hadRejections: false, approvedCount: approvedEdits.length, rejectedCount: 0, editedCount: 0, rejectedIds: [] };
        }

        // Aplicar edições e filtrar rejeitados
        // IMPORTANTE: Aplicar edições primeiro, depois filtrar
        const finalSuggestions = [];
        let hadTextEdits = false;
        let editedCount = 0;
        
        edits.forEach(edit => {
            const original = originalSuggestions[edit.idx];
            if (!original) return;
            
            if (edit.rejected) {
                // Sugestão rejeitada - não incluir no array final
                console.log(`Rejeitando sugestão ${edit.id}`);
                return;
            }
            
            // Verificar se texto foi editado
            if (original.suggestion !== edit.value) {
                hadTextEdits = true;
                editedCount++;
                finalSuggestions.push({
                    ...original,
                    suggestion: edit.value,
                    editedByReviewer: true
                });
            } else {
                finalSuggestions.push(original);
            }
        });
        
        console.log(`Final: ${finalSuggestions.length} sugestões aprovadas, ${rejectedIds.length} rejeitadas, ${editedCount} editadas`);
        
        // 🚨 VALIDAÇÃO CRÍTICA: Se todas as sugestões foram rejeitadas, não podemos salvar
        // O bot falharia com lista vazia
        if (finalSuggestions.length === 0) {
            console.error('ERRO: Todas as sugestões foram rejeitadas!');
            return { 
                success: false, 
                error: 'Não é possível aprovar: todas as sugestões foram rejeitadas. Use "Rejeitar" para rejeitar a issue inteira.',
                allRejected: true
            };
        }

        // Tentar localizar bloco JSON com mais tolerância
        // 1) procurar fence ```json ... ``` (case-insensitive)
        let jsonMatch = issue.body.match(/```(?:json)?\s*\n([\s\S]*?)\n```/i);
        let newBody;
        if (jsonMatch) {
            try {
                let data = JSON.parse(jsonMatch[1].trim());
                data.suggestions = finalSuggestions;
                data.total = finalSuggestions.length;
                const newJson = JSON.stringify(data);
                
                // Atualizar o bloco JSON
                newBody = issue.body.replace(/```(?:json)?\s*\n[\s\S]*?\n```/i, '```json\n' + newJson + '\n```');
                
                // Atualizar também a seção de Resumo para refletir as edições e rejeições
                newBody = updateSummarySection(newBody, finalSuggestions, rejectedIds);
            } catch (e) {
                console.warn('JSON existente inválido, fallback para busca de objeto JSON:', e);
                jsonMatch = null; // forçar fallback
            }
        }

        // 2) fallback: tentar encontrar primeiro objeto JSON bruto no corpo
        if (!jsonMatch) {
            const objMatch = issue.body.match(/\{[\s\S]*\}/);
            if (objMatch) {
                try {
                    let data = JSON.parse(objMatch[0]);
                    data.suggestions = finalSuggestions;
                    data.total = finalSuggestions.length;
                    const newJson = JSON.stringify(data);
                    // substituir o objeto JSON encontrado
                    newBody = issue.body.replace(/\{[\s\S]*\}/, newJson);
                    // Atualizar também a seção de Resumo
                    newBody = updateSummarySection(newBody, finalSuggestions, rejectedIds);
                } catch (e) {
                    console.error('Falha ao parsear JSON no fallback:', e);
                    return { success: false, error: 'JSON inválido no corpo da issue' };
                }
            } else {
                // Não encontrou JSON; vamos anexar um bloco JSON ao final
                const payload = { suggestions: finalSuggestions, total: finalSuggestions.length };
                const newJson = JSON.stringify(payload);
                newBody = issue.body + '\n\n```json\n' + newJson + '\n```';
            }
        }

        // Atualizar issue com novo body
        const updateResp = await fetch(`https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues/${issueNumber}`, {
            method: 'PATCH',
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ body: newBody })
        });

        if (!updateResp.ok) {
            const errText = await updateResp.text();
            throw new Error('Falha ao salvar edições: ' + updateResp.status + ' ' + errText);
        }

        return { 
            success: true, 
            hadEdits: hadTextEdits, 
            hadRejections: rejectedIds.length > 0,
            approvedCount: finalSuggestions.length,
            rejectedCount: rejectedIds.length,
            editedCount: editedCount,
            rejectedIds: rejectedIds
        };
    } catch (e) {
        console.error('Erro ao salvar edições:', e);
        return { success: false, error: e.message };
    }
}

// APROVAR COM EDIÇÕES - Salva edições automaticamente e aprova
async function approveIssueWithEdits(issueNumber) {
    // 🚨 VALIDAÇÃO DE SEGURANÇA: Verificar se é admin antes de prosseguir
    const isOwner = await isAuthenticatedOwner();
    if (!isOwner) {
        showToast('❌ Acesso negado: você não tem permissão para aprovar issues.', 'error');
        console.error('Tentativa de aprovar sem permissão de admin');
        return;
    }
    
    // ⚠️ CRÍTICO: Coletar edições ANTES de qualquer confirmação ou fechamento do modal!
    const editsBeforeClose = collectEditsFromModal();
    console.log('approveIssueWithEdits: Edições coletadas:', editsBeforeClose);
    
    // Contar aprovados e rejeitados para mostrar na confirmação
    const approvedCount = editsBeforeClose.filter(e => !e.rejected).length;
    const rejectedCount = editsBeforeClose.filter(e => e.rejected).length;
    
    // 🚨 VALIDAÇÃO: Se todas as sugestões foram rejeitadas, não permitir aprovar
    if (approvedCount === 0) {
        showToast('⚠️ Todas as sugestões foram rejeitadas. Use "Rejeitar" para rejeitar a issue inteira.', 'warning');
        return;
    }
    
    // Mensagem de confirmação dinâmica
    let confirmMessage = '<strong>Aprovar esta tradução?</strong><br><br>';
    if (rejectedCount > 0) {
        confirmMessage += `<div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 0.75rem; margin-bottom: 1rem;">
            <strong style="color: #ef4444;"><i class="fas fa-exclamation-triangle"></i> Atenção:</strong><br>
            <span style="color: var(--text-secondary);">
                ✅ ${approvedCount} sugestão(ões) será(ão) aprovada(s)<br>
                ❌ ${rejectedCount} sugestão(ões) será(ão) removida(s) do lote
            </span>
        </div>`;
    }
    confirmMessage += '<small style="color: var(--text-muted);">' +
        'Se você fez edições nas sugestões, elas serão salvas automaticamente.<br>' +
        'A automação será acionada para aplicar as traduções no repositório.' +
        '</small>';
    
    const confirmed = await showConfirm(confirmMessage, {
            title: rejectedCount > 0 ? 'Aprovar com Rejeições' : 'Aprovar Tradução',
            type: rejectedCount > 0 ? 'warning' : 'success',
            confirmText: rejectedCount > 0 ? `Aprovar ${approvedCount} / Rejeitar ${rejectedCount}` : 'Aprovar',
            cancelText: 'Cancelar',
            confirmClass: 'custom-modal-btn-success',
            icon: rejectedCount > 0 ? 'fa-tasks' : 'fa-check-circle'
        }
    );
    if (!confirmed) return;
    
    // Agora sim podemos fechar o modal (já coletamos as edições)
    const modal = document.getElementById('admin-issue-modal'); 
    if (modal) modal.remove();
    
    // Remover card da lista visualmente (feedback instantâneo)
    const card = document.querySelector(`.admin-issue-card[data-issue="${issueNumber}"]`);
    if (card) {
        card.style.transition = 'all 0.3s ease';
        card.style.opacity = '0.5';
        card.style.transform = 'scale(0.95)';
        card.innerHTML = `<div style="text-align:center;padding:1rem;"><i class="fas fa-spinner fa-spin"></i> Processando...</div>`;
    }
    
    try {
        const headers = { 'Accept': 'application/vnd.github.v3+json' };
        if (githubToken) headers['Authorization'] = `Bearer ${githubToken}`;
        
        // 1. Salvar edições PRIMEIRO (passando as edições coletadas)
        const saveResult = await saveEditsIfNeeded(issueNumber, editsBeforeClose);
        if (!saveResult.success) {
            // Tratamento especial para todas rejeitadas
            if (saveResult.allRejected) {
                showToast('⚠️ Todas as sugestões foram rejeitadas. Use "Rejeitar" para rejeitar a issue inteira.', 'warning');
            } else {
                showToast('Erro ao salvar edições: ' + saveResult.error, 'error');
            }
            if (card) {
                card.style.opacity = '1';
                card.style.transform = 'scale(1)';
            }
            loadAdminIssues(); // Recarregar em caso de erro
            return;
        }
        
        // 2. Pequeno delay para garantir que o GitHub processou o PATCH antes de disparar o workflow
        // Isso evita race condition onde o workflow pega o body antigo
        // IMPORTANTE: delay deve acontecer se houve QUALQUER modificação (edições OU rejeições)
        if (saveResult.hadEdits || saveResult.hadRejections) {
            console.log('Aguardando 1.5s para GitHub processar as modificações...');
            await new Promise(resolve => setTimeout(resolve, 1500));
        }
        
        // 3. Aplicar label de aprovação (dispara o workflow)
        const resp = await fetch(`https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues/${issueNumber}/labels`, {
            method: 'POST', 
            headers, 
            body: JSON.stringify({ labels: ['approved'] })
        });
        
        if (!resp.ok) throw new Error('Falha ao aplicar label');
        
        // Remover card completamente
        if (card) {
            card.style.opacity = '0';
            card.style.transform = 'scale(0.8)';
            setTimeout(() => card.remove(), 300);
        }
        
        // Mensagem de sucesso detalhada
        let message = '✅ ';
        const parts = [];
        if (saveResult.approvedCount > 0) {
            parts.push(`${saveResult.approvedCount} aprovada(s)`);
        }
        if (saveResult.editedCount > 0) {
            parts.push(`${saveResult.editedCount} editada(s)`);
        }
        if (saveResult.hadRejections) {
            parts.push(`${saveResult.rejectedCount} rejeitada(s)`);
        }
        message += parts.length > 0 ? parts.join(', ') : 'Issue aprovada!';
        showToast(message, 'success');
        
        // Limpa cache (para próximo reload)
        localStorage.removeItem(CONFIG.CACHE_PREFIX + 'admin_open_issues');
        localStorage.removeItem(CONFIG.CACHE_PREFIX + 'applied_issues');
        
        // Verificar se lista ficou vazia
        checkEmptyAdminList();
        
    } catch (e) {
        console.error(e);
        showToast('Erro ao aprovar: ' + e.message, 'error');
        if (card) card.remove();
        loadAdminIssues(); // Recarregar em caso de erro
    }
}

// REJEITAR COM EDIÇÕES - Pergunta motivo e rejeita (edições são descartadas)
async function rejectIssueWithEdits(issueNumber) {
    // 🚨 VALIDAÇÃO DE SEGURANÇA: Verificar se é admin antes de prosseguir
    const isOwner = await isAuthenticatedOwner();
    if (!isOwner) {
        showToast('❌ Acesso negado: você não tem permissão para rejeitar issues.', 'error');
        console.error('Tentativa de rejeitar sem permissão de admin');
        return;
    }
    
    const reason = await showPrompt(
        'Digite o motivo da rejeição.<br><small style="color: var(--text-muted);">Será postado como comentário na Issue.</small>',
        {
            title: 'Rejeitar Tradução',
            type: 'danger',
            defaultValue: '',
            placeholder: 'Ex: Tradução incorreta, erro gramatical, etc.',
            confirmText: 'Rejeitar',
            cancelText: 'Cancelar'
        }
    );
    if (reason === null) return;
    
    // Fechar modal IMEDIATAMENTE
    const modal = document.getElementById('admin-issue-modal'); 
    if (modal) modal.remove();
    
    // Remover card da lista visualmente (feedback instantâneo)
    const card = document.querySelector(`.admin-issue-card[data-issue="${issueNumber}"]`);
    if (card) {
        card.style.transition = 'all 0.3s ease';
        card.style.opacity = '0.5';
        card.style.transform = 'scale(0.95)';
        card.innerHTML = `<div style="text-align:center;padding:1rem;"><i class="fas fa-spinner fa-spin"></i> Rejeitando...</div>`;
    }
    
    try {
        const headers = { 'Accept': 'application/vnd.github.v3+json' };
        if (githubToken) headers['Authorization'] = `Bearer ${githubToken}`;
        
        // 1. Aplicar label 'rejected' E FECHAR a issue
        await fetch(`https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues/${issueNumber}`, {
            method: 'PATCH', 
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                state: 'closed',
                labels: ['rejected']
            })
        });
        
        // 2. Adicionar comentário com motivo (se fornecido) - fire and forget
        if (reason.trim()) {
            fetch(`https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues/${issueNumber}/comments`, {
                method: 'POST', 
                headers, 
                body: JSON.stringify({ body: `❌ **Rejeitado pelo revisor**\n\n${reason}` })
            }); // Não espera - comentário é secundário
        }
        
        // Remover card completamente
        if (card) {
            card.style.opacity = '0';
            card.style.transform = 'scale(0.8)';
            setTimeout(() => card.remove(), 300);
        }
        
        showToast('❌ Issue rejeitada.', 'info');
        
        // Limpa cache
        localStorage.removeItem(CONFIG.CACHE_PREFIX + 'admin_open_issues');
        
        // Verificar se lista ficou vazia
        checkEmptyAdminList();
        
    } catch (e) {
        console.error(e);
        showToast('Erro ao rejeitar: ' + e.message, 'error');
        if (card) card.remove();
        loadAdminIssues();
    }
}

// Verifica se a lista de admin ficou vazia
function checkEmptyAdminList() {
    const grid = document.querySelector('.admin-issues-grid');
    if (grid && grid.children.length === 0) {
        const adminList = document.getElementById('admin-list');
        if (adminList) {
            adminList.innerHTML = `
                <div class="admin-empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>Nenhuma issue de tradução pendente</p>
                </div>
            `;
        }
    }
}

// ========================================
// Verificação de Issues Duplicadas
// ========================================

// Cache de IDs já com Issues abertas (evita múltiplas requisições)
let pendingIssuesCache = null;
let pendingIssuesCacheTime = 0;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutos

// Busca Issues abertas com label 'translation'
async function fetchPendingIssues() {
    const now = Date.now();
    
    // Usar cache se ainda válido
    if (pendingIssuesCache && (now - pendingIssuesCacheTime) < CACHE_DURATION) {
        return pendingIssuesCache;
    }
    
    try {
        const response = await fetch(
            `https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues?state=open&labels=translation&per_page=100`,
            {
                headers: {
                    'Accept': 'application/vnd.github.v3+json'
                }
            }
        );
        
        if (!response.ok) return new Set();
        
        const issues = await response.json();
        
        // Extrai todos os IDs mencionados nas Issues
        const pendingIds = new Set();
        
        issues.forEach(issue => {
            // Procura IDs no corpo da Issue (formato: `id`)
            const idMatches = issue.body.match(/`([a-f0-9]{16})`/g);
            if (idMatches) {
                idMatches.forEach(match => {
                    const id = match.replace(/`/g, '');
                    pendingIds.add(id);
                });
            }
        });
        
        // Atualiza cache
        pendingIssuesCache = pendingIds;
        pendingIssuesCacheTime = now;
        
        return pendingIds;
        
    } catch (error) {
        console.error('Erro ao buscar Issues pendentes:', error);
        return new Set();
    }
}

// Verifica quais IDs do carrinho já têm Issues abertas
async function checkDuplicates(cartIds) {
    const pendingIds = await fetchPendingIssues();
    return cartIds.filter(id => pendingIds.has(id));
}

// ========================================
// Enviar Sugestões via API
// ========================================

async function submitAllSuggestions() {
    if (suggestionCart.length === 0) return;
    
    // Verificar se está logado
    if (!githubToken || !githubUser) {
        // Redirecionar para OAuth (não mostrar modal de token)
        handleGitHubAuth();
        return;
    }
    
    // Mostrar loading
    const submitBtn = document.getElementById('cart-submit');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verificando...';
    
    try {
        // Verificar duplicatas
        const cartIds = suggestionCart.map(item => item.id);
        const duplicates = await checkDuplicates(cartIds);
        
        if (duplicates.length > 0) {
            // Tem duplicatas - perguntar ao usuário
            const duplicateItems = suggestionCart.filter(item => duplicates.includes(item.id));
            const uniqueItems = suggestionCart.filter(item => !duplicates.includes(item.id));
            
            const duplicatesList = duplicateItems.map(item => `<code>${item.id.substring(0, 12)}...</code>`).join('<br>');
            const message = `<strong>${duplicates.length}</strong> sugestão(ões) já têm Issues abertas:<br><br>` +
                `<div style="max-height: 100px; overflow-y: auto; background: var(--bg-dark); padding: 0.5rem; border-radius: 6px; margin-bottom: 1rem;">${duplicatesList}</div>` +
                (uniqueItems.length > 0 
                    ? `Deseja enviar apenas as <strong>${uniqueItems.length}</strong> sugestão(ões) restantes?`
                    : `Todas as sugestões já têm Issues abertas. Deseja enviar mesmo assim?`);
            
            const confirmed = await showConfirm(message, {
                title: 'Issues Duplicadas',
                type: 'warning',
                confirmText: uniqueItems.length > 0 ? 'Enviar restantes' : 'Enviar assim mesmo',
                cancelText: 'Cancelar',
                confirmClass: 'custom-modal-btn-confirm'
            });
            
            if (!confirmed) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
                updateCartUI();
                return;
            }
            
            // Se houver itens únicos, enviar apenas eles
            if (uniqueItems.length > 0 && uniqueItems.length < suggestionCart.length) {
                suggestionCart = uniqueItems;
                updateCartUI();
            }
        }
        
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
        
        // Monta o JSON estruturado para o GitHub Action processar
        const jsonData = {
            version: "2.0",  // Nova versão do formato
            timestamp: new Date().toISOString(),
            total: suggestionCart.length,
            // Informações do repositório de tradução
            targetRepo: CONFIG.TRANSLATION_REPO,
            targetBranch: CONFIG.TRANSLATION_BRANCH,
            suggestions: suggestionCart.map(item => ({
                id: item.id,
                file: CONFIG.PTBR_FILE,  // Arquivo único de tradução
                line: item.lineNumber,
                suggestion: item.suggestion
            }))
        };
        
        // Monta o título
        const issueTitle = `[Tradução] Lote com ${suggestionCart.length} sugestão(ões)`;
        
        // Monta o corpo da Issue
        const issueBody = `## 📝 Sugestões de Tradução

**Total:** ${suggestionCart.length} | **Data:** ${new Date().toLocaleString('pt-BR')} | **Autor:** @${githubUser.login}

### 📋 Dados para Processamento

\`\`\`json
${JSON.stringify(jsonData)}
\`\`\`

### 📄 Resumo
${suggestionCart.map((item, i) => `${i+1}. \`${item.id}\` → ${item.suggestion.substring(0, 50)}...`).join('\n')}

---
> ⚠️ Adicione a label \`approved\` para aplicar automaticamente.`;

        // Criar Issue via API
        const response = await fetch(`https://api.github.com/repos/${CONFIG.GITHUB_OWNER}/${CONFIG.GITHUB_REPO_NAME}/issues`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${githubToken}`,
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: issueTitle,
                body: issueBody,
                labels: ['translation', 'batch-suggestion']
            })
        });
        
        if (response.ok) {
            const issue = await response.json();
            
            // Sucesso!
            showToast(`Issue #${issue.number} criada com sucesso!`);
            
            // Limpar carrinho e localStorage
            suggestionCart = [];
            clearCartFromStorage();
            updateCartUI();
            toggleCart();
            
            // Invalidar cache de duplicatas para próxima verificação
            pendingIssuesCache = null;
            pendingIssuesCacheTime = 0;
            
            // Mostrar link para a issue
            showIssueCreatedModal(issue);
            
        } else {
            const error = await response.json();
            console.error('Erro ao criar issue:', error);
            
            if (response.status === 401) {
                logout();
                showToast('Token expirado. Faça login novamente.', 'error');
            } else if (response.status === 403) {
                showToast('Sem permissão. Verifique se o token tem permissão "public_repo".', 'error');
            } else {
                showToast(`Erro: ${error.message || 'Falha ao criar issue'}`, 'error');
            }
        }
        
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro de conexão. Tente novamente.', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        updateCartUI();
    }
}

// Modal de sucesso
function showIssueCreatedModal(issue) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'success-modal';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px; text-align: center;">
            <div class="modal-header" style="justify-content: center; border: none;">
                <h2 style="color: var(--success);"><i class="fas fa-check-circle"></i> Sucesso!</h2>
            </div>
            <div class="modal-body">
                <p style="font-size: 1.1rem; margin-bottom: 1rem;">
                    Sua sugestão foi enviada com sucesso!
                </p>
                <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                    Issue <strong>#${issue.number}</strong> criada no repositório.
                    <br>Ela será revisada e aplicada em breve.
                </p>
                <a href="${issue.html_url}" target="_blank" class="btn btn-primary" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1.5rem;">
                    <i class="fab fa-github"></i> Ver Issue no GitHub
                </a>
            </div>
            <div class="modal-footer" style="justify-content: center; border: none;">
                <button class="btn btn-secondary" onclick="document.getElementById('success-modal').remove()">
                    Fechar
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    
    // Fechar ao clicar fora
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

// ========================================
// Sistema de Modais Customizados
// ========================================

/**
 * Modal de alerta customizado (substitui alert())
 */
function showAlert(message, title = 'Atenção', type = 'warning') {
    return new Promise((resolve) => {
        const icons = {
            warning: 'fa-exclamation-triangle',
            error: 'fa-times-circle',
            success: 'fa-check-circle',
            info: 'fa-info-circle'
        };
        
        const overlay = document.createElement('div');
        overlay.className = 'custom-modal-overlay';
        overlay.innerHTML = `
            <div class="custom-modal-box">
                <div class="custom-modal-header ${type}">
                    <i class="fas ${icons[type] || icons.warning}"></i>
                    <h3>${title}</h3>
                </div>
                <div class="custom-modal-body">
                    <p>${message}</p>
                </div>
                <div class="custom-modal-footer">
                    <button class="custom-modal-btn custom-modal-btn-confirm" id="alert-ok-btn">
                        <i class="fas fa-check"></i> Entendido
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        const okBtn = overlay.querySelector('#alert-ok-btn');
        okBtn.focus();
        
        const close = () => {
            overlay.remove();
            resolve();
        };
        
        okBtn.addEventListener('click', close);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close();
        });
        document.addEventListener('keydown', function handler(e) {
            if (e.key === 'Escape' || e.key === 'Enter') {
                document.removeEventListener('keydown', handler);
                close();
            }
        });
    });
}

/**
 * Modal de confirmação customizado (substitui confirm())
 */
function showConfirm(message, options = {}) {
    const {
        title = 'Confirmar',
        type = 'confirm',
        confirmText = 'Confirmar',
        cancelText = 'Cancelar',
        confirmClass = 'custom-modal-btn-confirm',
        icon = null
    } = options;
    
    return new Promise((resolve) => {
        const icons = {
            confirm: 'fa-question-circle',
            warning: 'fa-exclamation-triangle',
            danger: 'fa-exclamation-circle',
            success: 'fa-check-circle',
            info: 'fa-info-circle'
        };
        
        const overlay = document.createElement('div');
        overlay.className = 'custom-modal-overlay';
        overlay.innerHTML = `
            <div class="custom-modal-box">
                <div class="custom-modal-header ${type}">
                    <i class="fas ${icon || icons[type] || icons.confirm}"></i>
                    <h3>${title}</h3>
                </div>
                <div class="custom-modal-body">
                    <p>${message.replace(/\n/g, '<br>')}</p>
                </div>
                <div class="custom-modal-footer">
                    <button class="custom-modal-btn custom-modal-btn-cancel" id="confirm-cancel-btn">
                        <i class="fas fa-times"></i> ${cancelText}
                    </button>
                    <button class="custom-modal-btn ${confirmClass}" id="confirm-ok-btn">
                        <i class="fas fa-check"></i> ${confirmText}
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        const okBtn = overlay.querySelector('#confirm-ok-btn');
        const cancelBtn = overlay.querySelector('#confirm-cancel-btn');
        okBtn.focus();
        
        const close = (result) => {
            overlay.remove();
            resolve(result);
        };
        
        okBtn.addEventListener('click', () => close(true));
        cancelBtn.addEventListener('click', () => close(false));
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close(false);
        });
        document.addEventListener('keydown', function handler(e) {
            if (e.key === 'Escape') {
                document.removeEventListener('keydown', handler);
                close(false);
            } else if (e.key === 'Enter') {
                document.removeEventListener('keydown', handler);
                close(true);
            }
        });
    });
}

/**
 * Modal de prompt customizado (substitui prompt())
 */
function showPrompt(message, options = {}) {
    const {
        title = 'Entrada',
        type = 'info',
        defaultValue = '',
        placeholder = '',
        confirmText = 'Confirmar',
        cancelText = 'Cancelar'
    } = options;
    
    return new Promise((resolve) => {
        const icons = {
            info: 'fa-keyboard',
            warning: 'fa-exclamation-triangle',
            danger: 'fa-exclamation-circle'
        };
        
        const overlay = document.createElement('div');
        overlay.className = 'custom-modal-overlay';
        overlay.innerHTML = `
            <div class="custom-modal-box">
                <div class="custom-modal-header ${type}">
                    <i class="fas ${icons[type] || icons.info}"></i>
                    <h3>${title}</h3>
                </div>
                <div class="custom-modal-body">
                    <p>${message}</p>
                    <input type="text" class="custom-modal-input" id="prompt-input" 
                           value="${escapeHtml(defaultValue)}" placeholder="${escapeHtml(placeholder)}">
                </div>
                <div class="custom-modal-footer">
                    <button class="custom-modal-btn custom-modal-btn-cancel" id="prompt-cancel-btn">
                        <i class="fas fa-times"></i> ${cancelText}
                    </button>
                    <button class="custom-modal-btn custom-modal-btn-confirm" id="prompt-ok-btn">
                        <i class="fas fa-check"></i> ${confirmText}
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        const input = overlay.querySelector('#prompt-input');
        const okBtn = overlay.querySelector('#prompt-ok-btn');
        const cancelBtn = overlay.querySelector('#prompt-cancel-btn');
        input.focus();
        input.select();
        
        const close = (result) => {
            overlay.remove();
            resolve(result);
        };
        
        okBtn.addEventListener('click', () => close(input.value));
        cancelBtn.addEventListener('click', () => close(null));
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close(null);
        });
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                close(input.value);
            } else if (e.key === 'Escape') {
                close(null);
            }
        });
    });
}

// Toast notification com tipos
function showToast(message, type = 'success') {
    // Remove toast anterior se existir
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) existingToast.remove();
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i> ${message}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Fecha modal ao clicar fora
document.getElementById('suggestion-modal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

// Atalhos de teclado
document.addEventListener('keydown', function(e) {
    const modal = document.getElementById('suggestion-modal');
    const isModalOpen = modal.classList.contains('active');
    
    // ESC - fechar modal ou carrinho
    if (e.key === 'Escape') {
        if (isModalOpen) {
            closeModal();
        } else {
            document.getElementById('cart-panel').classList.remove('active');
        }
    }
    
    // Enter no modal - adicionar ao carrinho (só se não for Shift+Enter para nova linha)
    if (e.key === 'Enter' && !e.shiftKey && isModalOpen) {
        const activeElement = document.activeElement;
        // Só ativa se estiver no textarea de sugestão
        if (activeElement && activeElement.id === 'modal-suggestion') {
            e.preventDefault();
            addToCart();
        }
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkOAuthCallback(); // Verificar login
    loadCartFromStorage(); // Restaurar carrinho salvo
    loadTranslations();
    loadContributors();
    
    // Pausar polling quando página fica invisível (economia de API)
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            stopAdminPolling();
        } else if (currentFile === 'admin') {
            startAdminPolling();
        }
    });
});
