// ========== GLOSSARY ADMIN ==========
// Admin interface for managing glossary terms
// SOMENTE ADMIN (owner do repositório) pode acessar

let glossaryData = null;
let filteredTerms = [];
let currentPage = 1;
const ITEMS_PER_PAGE = 20;

// ========== CONFIGURAÇÃO DE SEGURANÇA ==========
const SECURITY_CONFIG = {
    REPO_OWNER: 'rodrigomiquilino',
    REPO_NAME: 'wwm_brasileiro',
    TARGET_REPO: 'wwm_brasileiro_auto_path',
    // Versão do glossário para detectar mudanças
    GLOSSARY_VERSION_KEY: 'glossary_version',
};

let isAdmin = false;
let pendingIssues = [];
let isSaving = false; // Flag para evitar saves simultâneos

// ========== AUTO-SAVE TO GITHUB ==========
async function saveGlossaryToGitHub(action, termId = null, oldId = null) {
    const token = localStorage.getItem('github_token');
    if (!token) {
        showToast('⚠️ Token não encontrado. Faça login novamente.', 'warning');
        return false;
    }
    
    if (isSaving) {
        console.log('[Glossary] Save já em progresso, ignorando...');
        return false;
    }
    
    isSaving = true;
    
    try {
        // Converter glossaryData para base64
        const glossaryJson = JSON.stringify(glossaryData, null, 2);
        const glossaryBase64 = btoa(unescape(encodeURIComponent(glossaryJson)));
        
        const response = await fetch(
            `https://api.github.com/repos/${SECURITY_CONFIG.REPO_OWNER}/${SECURITY_CONFIG.REPO_NAME}/dispatches`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/vnd.github.v3+json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    event_type: 'update-glossary',
                    client_payload: {
                        glossary_base64: glossaryBase64,
                        terms_count: glossaryData.terms.length,
                        action: action,
                        term_id: termId,
                        old_id: oldId,
                        triggered_by: localStorage.getItem('github_username') || 'admin'
                    }
                })
            }
        );
        
        isSaving = false;
        
        if (response.status === 204 || response.ok) {
            console.log(`[Glossary] Auto-save disparado: ${action} ${termId || ''}`);
            return true;
        } else {
            console.error('[Glossary] Erro no auto-save:', response.status);
            showToast('⚠️ Erro ao salvar no GitHub. Tente novamente.', 'error');
            return false;
        }
    } catch (error) {
        isSaving = false;
        console.error('[Glossary] Erro ao salvar:', error);
        showToast('⚠️ Erro de conexão ao salvar.', 'error');
        return false;
    }
}

// Toast notification
function showToast(message, type = 'success') {
    const existingToast = document.querySelector('.glossary-toast');
    if (existingToast) existingToast.remove();
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    const colors = {
        success: 'linear-gradient(135deg, #10b981, #059669)',
        error: 'linear-gradient(135deg, #ef4444, #dc2626)',
        warning: 'linear-gradient(135deg, #f59e0b, #d97706)',
        info: 'linear-gradient(135deg, #3b82f6, #2563eb)'
    };
    
    const toast = document.createElement('div');
    toast.className = 'glossary-toast';
    toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: ${colors[type] || colors.info};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        display: flex;
        align-items: center;
        gap: 0.75rem;
        z-index: 1000;
        font-weight: 500;
        animation: slideIn 0.3s ease;
    `;
    toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i> ${message}`;
    
    // Add animation style
    if (!document.getElementById('toast-style')) {
        const style = document.createElement('style');
        style.id = 'toast-style';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// ========== INIT ==========
document.addEventListener('DOMContentLoaded', async () => {
    // Primeiro, verificar se é admin
    const isAuthorized = await checkAdminAccess();
    
    if (!isAuthorized) {
        showAccessDenied();
        return;
    }
    
    isAdmin = true;
    loadGlossary();
    setupEventListeners();
    loadPendingIssues();
});

// ========== VERIFICAÇÃO DE ADMIN ==========
async function checkAdminAccess() {
    const token = localStorage.getItem('github_token');
    const username = localStorage.getItem('github_username');
    
    if (!token || !username) {
        return false;
    }
    
    // Verificar se é o owner do repositório
    if (username !== SECURITY_CONFIG.REPO_OWNER) {
        return false;
    }
    
    // Verificar se o token ainda é válido
    try {
        const response = await fetch('https://api.github.com/user', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) return false;
        
        const user = await response.json();
        return user.login === SECURITY_CONFIG.REPO_OWNER;
    } catch (e) {
        console.error('Erro ao verificar admin:', e);
        return false;
    }
}

function showAccessDenied() {
    document.body.innerHTML = `
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #0a0a0f, #1a1a2e);
            color: white;
            font-family: 'Inter', sans-serif;
            text-align: center;
            padding: 2rem;
        ">
            <i class="fas fa-lock" style="font-size: 4rem; color: #f87171; margin-bottom: 1.5rem;"></i>
            <h1 style="font-family: 'Cinzel', serif; color: #c9a227; margin-bottom: 1rem;">Acesso Restrito</h1>
            <p style="color: #9ca3af; max-width: 400px; margin-bottom: 2rem;">
                Esta página é exclusiva para administradores do projeto.<br>
                Faça login como admin na página de tradução primeiro.
            </p>
            <a href="translate" style="
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.75rem 1.5rem;
                background: linear-gradient(135deg, #c9a227, #8b6914);
                color: #0a0a0f;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
            ">
                <i class="fab fa-github"></i> Ir para Tradução
            </a>
        </div>
    `;
}

// ========== CARREGAR ISSUES PENDENTES ==========
async function loadPendingIssues() {
    const token = localStorage.getItem('github_token');
    if (!token) return;
    
    try {
        const response = await fetch(
            `https://api.github.com/repos/${SECURITY_CONFIG.REPO_OWNER}/${SECURITY_CONFIG.REPO_NAME}/issues?state=open&labels=translation&per_page=100`,
            {
                headers: { 'Authorization': `Bearer ${token}` }
            }
        );
        
        if (response.ok) {
            pendingIssues = await response.json();
            console.log(`[Admin] Carregadas ${pendingIssues.length} issues pendentes`);
        }
    } catch (e) {
        console.warn('Erro ao carregar issues:', e);
    }
}

// Verifica se uma variável está em uso em issues pendentes
function checkVariableInPendingIssues(varName) {
    const issuesWithVar = pendingIssues.filter(issue => 
        issue.body && issue.body.includes(varName)
    );
    return issuesWithVar;
}

// ========== LOAD GLOSSARY ==========
async function loadGlossary() {
    try {
        const response = await fetch('glossary.json');
        if (!response.ok) throw new Error('Failed to load glossary');
        
        glossaryData = await response.json();
        
        // Build category dropdown
        buildCategoryDropdown();
        
        // Update stats
        updateStats();
        
        // Initial render
        filterTerms();
        
    } catch (error) {
        console.error('Error loading glossary:', error);
        document.getElementById('terms-body').innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Erro ao carregar glossário</p>
                </td>
            </tr>
        `;
    }
}

// ========== STATS ==========
function updateStats() {
    if (!glossaryData) return;
    
    document.getElementById('stat-total').textContent = glossaryData.terms.length;
    document.getElementById('stat-variables').textContent = glossaryData.terms.length; // All terms have variables
    document.getElementById('stat-notranslate').textContent = 
        glossaryData.terms.filter(t => t.doNotTranslate).length;
}

// ========== CATEGORY DROPDOWN ==========
function buildCategoryDropdown() {
    const select = document.getElementById('category-filter');
    const modalSelect = document.getElementById('term-category');
    
    if (!glossaryData?.categories) return;
    
    const options = Object.entries(glossaryData.categories).map(([key, cat]) => 
        `<option value="${key}">${cat.name}</option>`
    ).join('');
    
    select.innerHTML = `<option value="">Todas as categorias</option>${options}`;
    modalSelect.innerHTML = options;
}

// ========== FILTER & RENDER ==========
function filterTerms() {
    if (!glossaryData) return;
    
    const search = document.getElementById('search-input').value.toLowerCase().trim();
    const category = document.getElementById('category-filter').value;
    
    filteredTerms = glossaryData.terms.filter(term => {
        // Category filter
        if (category && term.category !== category) return false;
        
        // Search filter
        if (search) {
            const searchIn = [
                term.id,
                term.original,
                term.translation,
                term.chinese || '',
                term.context || ''
            ].join(' ').toLowerCase();
            
            if (!searchIn.includes(search)) return false;
        }
        
        return true;
    });
    
    currentPage = 1;
    renderTable();
    renderPagination();
}

function renderTable() {
    const tbody = document.getElementById('terms-body');
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    const pageTerms = filteredTerms.slice(start, end);
    
    if (pageTerms.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>Nenhum termo encontrado</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = pageTerms.map(term => {
        const category = glossaryData.categories[term.category];
        const varName = `{{${term.id.toUpperCase().replace(/-/g, '_')}}}`;
        
        return `
            <tr>
                <td class="term-id">${escapeHtml(term.id)}</td>
                <td class="term-original">${escapeHtml(term.original)}</td>
                <td class="term-translation">${escapeHtml(term.translation)}</td>
                <td><span class="term-variable">${varName}</span></td>
                <td>
                    <span class="term-category" style="color: ${category?.color || '#c9a227'}">
                        <i class="${category?.icon || 'fas fa-tag'}"></i>
                        ${category?.name || term.category}
                    </span>
                </td>
                <td class="term-actions">
                    <button onclick="renameVariable('${term.id}')" title="Renomear Variável">
                        <i class="fas fa-exchange-alt"></i>
                    </button>
                    <button onclick="editTerm('${term.id}')" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="delete" onclick="deleteTerm('${term.id}')" title="Excluir">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function renderPagination() {
    const totalPages = Math.ceil(filteredTerms.length / ITEMS_PER_PAGE);
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
    
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button onclick="goToPage(${i})" class="${i === currentPage ? 'active' : ''}">${i}</button>`;
    }
    
    html += `
        <button onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>
            <i class="fas fa-angle-right"></i>
        </button>
        <button onclick="goToPage(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}>
            <i class="fas fa-angle-double-right"></i>
        </button>
    `;
    
    pagination.innerHTML = html;
}

function goToPage(page) {
    currentPage = page;
    renderTable();
    renderPagination();
}

// ========== MODAL ==========
function openAddModal() {
    document.getElementById('modal-title').textContent = 'Adicionar Termo';
    document.getElementById('term-edit-id').value = '';
    document.getElementById('term-id').value = '';
    document.getElementById('term-id').disabled = false;
    document.getElementById('term-original').value = '';
    document.getElementById('term-translation').value = '';
    document.getElementById('term-chinese').value = '';
    document.getElementById('term-pinyin').value = '';
    document.getElementById('term-context').value = '';
    document.getElementById('term-aliases').value = '';
    document.getElementById('term-notranslate').checked = false;
    document.getElementById('term-category').selectedIndex = 0;
    updateVariablePreview();
    document.getElementById('term-modal').classList.add('active');
}

function editTerm(id) {
    const term = glossaryData.terms.find(t => t.id === id);
    if (!term) return;
    
    document.getElementById('modal-title').textContent = 'Editar Termo';
    document.getElementById('term-edit-id').value = term.id;
    document.getElementById('term-id').value = term.id;
    document.getElementById('term-id').disabled = true; // Can't change ID
    document.getElementById('term-original').value = term.original;
    document.getElementById('term-translation').value = term.translation;
    document.getElementById('term-chinese').value = term.chinese || '';
    document.getElementById('term-pinyin').value = term.pinyin || '';
    document.getElementById('term-context').value = term.context || '';
    document.getElementById('term-aliases').value = (term.aliases || []).join(', ');
    document.getElementById('term-notranslate').checked = term.doNotTranslate || false;
    document.getElementById('term-category').value = term.category;
    updateVariablePreview();
    document.getElementById('term-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('term-modal').classList.remove('active');
}

function updateVariablePreview() {
    const id = document.getElementById('term-id').value.trim();
    const preview = document.getElementById('variable-preview');
    
    if (id) {
        preview.textContent = `{{${id.toUpperCase().replace(/-/g, '_').replace(/\s+/g, '_')}}}`;
    } else {
        preview.textContent = '{{...}}';
    }
}

function setupEventListeners() {
    document.getElementById('term-id').addEventListener('input', updateVariablePreview);
    
    // Close modal on escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
}

// ========== SAVE TERM ==========
async function saveTerm() {
    const editId = document.getElementById('term-edit-id').value;
    const id = document.getElementById('term-id').value.trim().toLowerCase().replace(/\s+/g, '_');
    const original = document.getElementById('term-original').value.trim();
    const translation = document.getElementById('term-translation').value.trim();
    const chinese = document.getElementById('term-chinese').value.trim();
    const pinyin = document.getElementById('term-pinyin').value.trim();
    const context = document.getElementById('term-context').value.trim();
    const aliasesRaw = document.getElementById('term-aliases').value.trim();
    const doNotTranslate = document.getElementById('term-notranslate').checked;
    const category = document.getElementById('term-category').value;
    
    // Validation
    if (!id || !original || !translation) {
        alert('ID, Original e Tradução são obrigatórios!');
        return;
    }
    
    // Check for duplicate ID (only for new terms)
    if (!editId && glossaryData.terms.some(t => t.id === id)) {
        alert('Já existe um termo com este ID!');
        return;
    }
    
    const term = {
        id,
        original,
        translation,
        category,
        doNotTranslate
    };
    
    // Optional fields
    if (chinese) term.chinese = chinese;
    if (pinyin) term.pinyin = pinyin;
    if (context) term.context = context;
    if (aliasesRaw) {
        term.aliases = aliasesRaw.split(',').map(a => a.trim()).filter(a => a);
    }
    
    const isEdit = !!editId;
    
    if (isEdit) {
        // Update existing
        const index = glossaryData.terms.findIndex(t => t.id === editId);
        if (index !== -1) {
            glossaryData.terms[index] = term;
        }
    } else {
        // Add new
        glossaryData.terms.push(term);
    }
    
    // Update modified date
    glossaryData.lastUpdated = new Date().toISOString().split('T')[0];
    
    // Refresh UI
    updateStats();
    filterTerms();
    closeModal();
    
    // Auto-save to GitHub
    const action = isEdit ? 'edit' : 'add';
    const saved = await saveGlossaryToGitHub(action, id);
    if (saved) {
        showToast(`✅ Termo ${isEdit ? 'editado' : 'adicionado'} e salvo!`, 'success');
    }
}

async function deleteTerm(id) {
    if (!confirm(`Tem certeza que deseja excluir o termo "${id}"?`)) return;
    
    glossaryData.terms = glossaryData.terms.filter(t => t.id !== id);
    glossaryData.lastUpdated = new Date().toISOString().split('T')[0];
    
    updateStats();
    filterTerms();
    
    // Auto-save to GitHub
    const saved = await saveGlossaryToGitHub('delete', id);
    if (saved) {
        showToast('✅ Termo excluído e salvo!', 'success');
    }
}

// ========== RENOMEAR VARIÁVEL EM MASSA ==========
// Configuração do repositório de destino
const RENAME_CONFIG = {
    TARGET_OWNER: 'rodrigomiquilino',
    TARGET_REPO: 'wwm_brasileiro_auto_path',
    // O token será obtido do localStorage (mesmo usado no translate)
};

async function renameVariable(oldId) {
    const term = glossaryData.terms.find(t => t.id === oldId);
    if (!term) {
        alert('Termo não encontrado!');
        return;
    }
    
    // Verificar autenticação
    const token = localStorage.getItem('github_token');
    if (!token) {
        alert('⚠️ Você precisa estar logado no GitHub para renomear variáveis.\n\nFaça login primeiro na página de tradução.');
        return;
    }
    
    const oldVarName = `{{${oldId.toUpperCase().replace(/-/g, '_')}}}`;
    
    const newId = prompt(
        `🔄 Renomear variável ${oldVarName}\n\n` +
        `Digite o novo ID (será convertido para minúsculas):\n` +
        `Atual: ${oldId}`,
        oldId
    );
    
    if (!newId || newId === oldId) return;
    
    const normalizedNewId = newId.toLowerCase().replace(/\s+/g, '_');
    const newVarName = `{{${normalizedNewId.toUpperCase().replace(/-/g, '_')}}}`;
    
    // Verificar se já existe
    if (glossaryData.terms.some(t => t.id === normalizedNewId && t.id !== oldId)) {
        alert('Já existe um termo com este ID!');
        return;
    }
    
    // ========== VERIFICAR USO EM ISSUES PENDENTES ==========
    const issuesUsingVar = checkVariableInPendingIssues(oldVarName);
    let warningMessage = '';
    
    if (issuesUsingVar.length > 0) {
        warningMessage = `\n\n⚠️ ATENÇÃO: Esta variável está sendo usada em ${issuesUsingVar.length} issue(s) pendente(s):\n` +
            issuesUsingVar.slice(0, 3).map(i => `• #${i.number}: ${i.title.substring(0, 40)}...`).join('\n') +
            (issuesUsingVar.length > 3 ? `\n... e mais ${issuesUsingVar.length - 3}` : '') +
            `\n\nOs tradutores que usaram ${oldVarName} terão suas sugestões atualizadas no merge.`;
    }
    
    // Confirmar
    const confirmed = confirm(
        `📋 Confirma a renomeação?\n\n` +
        `DE: ${oldVarName}\n` +
        `PARA: ${newVarName}` +
        warningMessage +
        `\n\nIsso irá:\n` +
        `1. Atualizar o glossário automaticamente\n` +
        `2. Atualizar pt-br.tsv (branch dev)`
    );
    
    if (!confirmed) return;
    
    // Mostrar loading
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'rename-loading';
    loadingDiv.style.cssText = `
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2000;
    `;
    loadingDiv.innerHTML = `
        <div style="text-align: center; color: white;">
            <i class="fas fa-spinner fa-spin" style="font-size: 3rem; color: #c9a227; margin-bottom: 1rem;"></i>
            <p>Disparando atualização no repositório...</p>
        </div>
    `;
    document.body.appendChild(loadingDiv);
    
    try {
        // Dispara o workflow no repositório de destino
        const response = await fetch(
            `https://api.github.com/repos/${RENAME_CONFIG.TARGET_OWNER}/${RENAME_CONFIG.TARGET_REPO}/dispatches`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/vnd.github.v3+json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    event_type: 'rename-variable',
                    client_payload: {
                        old_var: oldVarName,
                        new_var: newVarName,
                        old_id: oldId,
                        new_id: normalizedNewId,
                        triggered_by: localStorage.getItem('github_username') || 'admin'
                    }
                })
            }
        );
        
        loadingDiv.remove();
        
        if (response.status === 204 || response.ok) {
            // Sucesso! Atualizar glossário local
            const index = glossaryData.terms.findIndex(t => t.id === oldId);
            if (index !== -1) {
                glossaryData.terms[index].id = normalizedNewId;
            }
            
            // Atualizar data
            glossaryData.lastUpdated = new Date().toISOString().split('T')[0];
            
            // Atualizar UI
            updateStats();
            filterTerms();
            
            // Auto-save glossary to GitHub
            await saveGlossaryToGitHub('rename', normalizedNewId, oldId);
            
            showToast(
                `✅ Variável renomeada: ${oldVarName} → ${newVarName}`,
                'success'
            );
        } else if (response.status === 404) {
            alert(
                `❌ Repositório não encontrado ou sem permissão.\n\n` +
                `Verifique se:\n` +
                `1. O repositório ${RENAME_CONFIG.TARGET_REPO} existe\n` +
                `2. O workflow rename-variable-receiver.yml está configurado\n` +
                `3. Seu token tem permissão para o repositório`
            );
        } else if (response.status === 401) {
            alert(
                `❌ Token expirado ou inválido.\n\n` +
                `Faça logout e login novamente na página de tradução.`
            );
        } else {
            const error = await response.json();
            alert(`❌ Erro ao disparar workflow: ${error.message || response.status}`);
        }
        
    } catch (error) {
        loadingDiv.remove();
        console.error('Erro ao renomear:', error);
        alert(`❌ Erro de conexão: ${error.message}`);
    }
}

// ========== EXPORT / IMPORT ==========
function exportGlossary() {
    const dataStr = JSON.stringify(glossaryData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `glossary-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
}

function importGlossary(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const imported = JSON.parse(e.target.result);
            
            if (!imported.terms || !Array.isArray(imported.terms)) {
                throw new Error('Formato inválido');
            }
            
            if (confirm(`Importar ${imported.terms.length} termos? Isso substituirá os dados atuais.`)) {
                glossaryData = imported;
                buildCategoryDropdown();
                updateStats();
                filterTerms();
                showSaveReminder();
            }
        } catch (error) {
            alert('Erro ao importar: ' + error.message);
        }
    };
    reader.readAsText(file);
    
    // Reset input
    event.target.value = '';
}

// ========== SAVE REMINDER (DEPRECATED - kept for backwards compatibility) ==========
// Note: Auto-save is now enabled, this function is no longer needed
function showSaveReminder() {
    // No-op - auto-save handles everything now
    console.log('[Glossary] showSaveReminder called - auto-save is active');
}

// ========== HELPERS ==========
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
