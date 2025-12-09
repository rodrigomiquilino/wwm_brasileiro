/* ========================================
   WWM Brasileiro - Glossary Page JavaScript
   ======================================== */

// ========== STATE ==========
let glossaryData = null;
let filteredTerms = [];
let currentPage = 1;
let currentCategory = 'all';
let currentFilter = 'all'; // all, translate, notranslate
let searchQuery = '';
const ITEMS_PER_PAGE = 24;

// ========== INIT ==========
document.addEventListener('DOMContentLoaded', () => {
    loadGlossary();
    setupEventListeners();
});

// ========== LOAD GLOSSARY ==========
async function loadGlossary() {
    try {
        // Check if running locally (file:// protocol)
        const isLocalFile = window.location.protocol === 'file:';
        
        const response = await fetch('glossary.json');
        if (!response.ok) throw new Error('Failed to load glossary');
        
        glossaryData = await response.json();
        
        // Build category buttons
        buildCategoryButtons();
        
        // Update stats
        updateStats();
        
        // Initial render
        applyFilters();
        
        // ========== DEEP-LINK SUPPORT ==========
        // Check if URL has #term_id to open modal directly
        if (window.location.hash) {
            const termId = decodeURIComponent(window.location.hash.slice(1));
            const term = glossaryData.terms.find(t => t.id === termId);
            if (term) {
                setTimeout(() => openTermModal(termId), 300);
            }
        }
        
    } catch (error) {
        console.error('Error loading glossary:', error);
        
        // Check if it's a local file access issue
        const isLocalFile = window.location.protocol === 'file:';
        const errorMsg = isLocalFile 
            ? `
                <div class="empty-state">
                    <i class="fas fa-desktop"></i>
                    <h3>Arquivo aberto localmente</h3>
                    <p>Para ver o glossário, acesse via <strong>GitHub Pages</strong>:</p>
                    <a href="https://rodrigomiquilino.github.io/wwm_brasileiro/glossary" 
                       class="btn-copy" style="display: inline-flex; margin-top: 1rem; text-decoration: none;">
                        <i class="fas fa-external-link-alt"></i> Abrir no GitHub Pages
                    </a>
                    <p style="margin-top: 1rem; font-size: 0.85rem; opacity: 0.7;">
                        Ou use um servidor local para testar.
                    </p>
                </div>
            `
            : `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Erro ao carregar glossário</h3>
                    <p>Por favor, tente recarregar a página.</p>
                </div>
            `;
        
        document.getElementById('glossary-grid').innerHTML = errorMsg;
    }
}

// ========== BUILD CATEGORY BUTTONS ==========
function buildCategoryButtons() {
    const container = document.getElementById('category-filters');
    container.innerHTML = `
        <button class="category-btn active" data-category="all">
            <i class="fas fa-globe"></i> Todos
        </button>
    `;
    
    // Add category buttons
    for (const [key, cat] of Object.entries(glossaryData.categories)) {
        const count = glossaryData.terms.filter(t => t.category === key).length;
        const btn = document.createElement('button');
        btn.className = 'category-btn';
        btn.dataset.category = key;
        btn.innerHTML = `<i class="${cat.icon}"></i> ${cat.name} <span style="opacity: 0.7; font-size: 0.8em;">(${count})</span>`;
        btn.style.setProperty('--category-color', cat.color);
        container.appendChild(btn);
    }
    
    // Add event listeners
    container.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            container.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentCategory = btn.dataset.category;
            currentPage = 1;
            applyFilters();
        });
    });
}

// ========== UPDATE STATS ==========
function updateStats() {
    const total = glossaryData.terms.length;
    const npcs = glossaryData.terms.filter(t => t.category === 'npcs').length;
    const combat = glossaryData.terms.filter(t => t.category === 'combat').length;
    const noTranslate = glossaryData.terms.filter(t => t.doNotTranslate).length;
    
    document.getElementById('stat-total').textContent = total;
    document.getElementById('stat-npcs').textContent = npcs;
    document.getElementById('stat-combat').textContent = combat;
    document.getElementById('stat-notranslate').textContent = noTranslate;
}

// ========== SETUP EVENT LISTENERS ==========
function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById('search-input');
    const clearSearch = document.getElementById('clear-search');
    
    searchInput.addEventListener('input', debounce(() => {
        searchQuery = searchInput.value.toLowerCase().trim();
        clearSearch.style.display = searchQuery ? 'block' : 'none';
        currentPage = 1;
        applyFilters();
    }, 300));
    
    clearSearch.addEventListener('click', () => {
        searchInput.value = '';
        searchQuery = '';
        clearSearch.style.display = 'none';
        currentPage = 1;
        applyFilters();
    });
    
    // Filter tags
    document.querySelectorAll('.filter-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            document.querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));
            tag.classList.add('active');
            currentFilter = tag.dataset.filter;
            currentPage = 1;
            applyFilters();
        });
    });
    
    // Modal close on overlay click
    document.getElementById('term-modal').addEventListener('click', (e) => {
        if (e.target.id === 'term-modal') {
            closeTermModal();
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeTermModal();
        }
    });
}

// ========== APPLY FILTERS ==========
function applyFilters() {
    if (!glossaryData) return;
    
    filteredTerms = glossaryData.terms.filter(term => {
        // Category filter
        if (currentCategory !== 'all' && term.category !== currentCategory) {
            return false;
        }
        
        // Translate/No translate filter
        if (currentFilter === 'translate' && term.doNotTranslate) {
            return false;
        }
        if (currentFilter === 'notranslate' && !term.doNotTranslate) {
            return false;
        }
        
        // Search filter
        if (searchQuery) {
            const searchFields = [
                term.original,
                term.translation,
                term.chinese || '',
                term.pinyin || '',
                term.context || '',
                ...(term.aliases || [])
            ].map(s => s.toLowerCase());
            
            return searchFields.some(field => field.includes(searchQuery));
        }
        
        return true;
    });
    
    renderGrid();
    renderPagination();
    
    // Show/hide empty state
    const emptyState = document.getElementById('empty-state');
    const grid = document.getElementById('glossary-grid');
    
    if (filteredTerms.length === 0) {
        grid.innerHTML = '';
        emptyState.classList.remove('hidden');
    } else {
        emptyState.classList.add('hidden');
    }
}

// ========== RENDER GRID ==========
function renderGrid() {
    const grid = document.getElementById('glossary-grid');
    
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const pageTerms = filteredTerms.slice(startIndex, endIndex);
    
    if (pageTerms.length === 0) {
        grid.innerHTML = '';
        return;
    }
    
    grid.innerHTML = pageTerms.map(term => {
        const category = glossaryData.categories[term.category];
        const categoryColor = category?.color || '#c9a227';
        
        // Usar data-id para evitar problemas com aspas no onclick
        return `
            <div class="term-card ${term.doNotTranslate ? 'no-translate' : ''}" 
                 style="--category-color: ${categoryColor}"
                 data-term-id="${encodeURIComponent(term.id)}">
                <div class="term-header">
                    <span class="term-original">${escapeHtml(term.original)}</span>
                    ${term.chinese ? `<span class="term-chinese">${term.chinese}</span>` : ''}
                </div>
                <div class="term-translation">${escapeHtml(term.translation)}</div>
                ${term.context ? `<div class="term-context">${escapeHtml(term.context)}</div>` : ''}
                <div class="term-footer">
                    <span class="term-category" style="--category-color: ${categoryColor}">
                        <i class="${category?.icon || 'fas fa-tag'}"></i>
                        ${category?.name || term.category}
                    </span>
                    <span class="term-badge ${term.doNotTranslate ? 'no-translate' : 'translate'}">
                        ${term.doNotTranslate ? 'Não Traduzir' : 'Traduzir'}
                    </span>
                </div>
            </div>
        `;
    }).join('');
    
    // Event delegation para cards
    grid.querySelectorAll('.term-card').forEach(card => {
        card.addEventListener('click', function() {
            const termId = decodeURIComponent(this.dataset.termId);
            openTermModal(termId);
        });
    });
}

// ========== RENDER PAGINATION ==========
function renderPagination() {
    const pagination = document.getElementById('pagination');
    const totalPages = Math.ceil(filteredTerms.length / ITEMS_PER_PAGE);
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    html += `<button ${currentPage === 1 ? 'disabled' : ''} onclick="goToPage(${currentPage - 1})">
        <i class="fas fa-chevron-left"></i>
    </button>`;
    
    // Page numbers
    const visiblePages = getVisiblePages(currentPage, totalPages);
    
    visiblePages.forEach((page, index) => {
        if (page === '...') {
            html += `<button disabled>...</button>`;
        } else {
            html += `<button class="${page === currentPage ? 'active' : ''}" onclick="goToPage(${page})">${page}</button>`;
        }
    });
    
    // Next button
    html += `<button ${currentPage === totalPages ? 'disabled' : ''} onclick="goToPage(${currentPage + 1})">
        <i class="fas fa-chevron-right"></i>
    </button>`;
    
    pagination.innerHTML = html;
}

function getVisiblePages(current, total) {
    if (total <= 7) {
        return Array.from({length: total}, (_, i) => i + 1);
    }
    
    if (current <= 4) {
        return [1, 2, 3, 4, 5, '...', total];
    }
    
    if (current >= total - 3) {
        return [1, '...', total - 4, total - 3, total - 2, total - 1, total];
    }
    
    return [1, '...', current - 1, current, current + 1, '...', total];
}

function goToPage(page) {
    const totalPages = Math.ceil(filteredTerms.length / ITEMS_PER_PAGE);
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    renderGrid();
    renderPagination();
    
    // Scroll to top of grid
    document.getElementById('glossary-grid').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ========== TERM MODAL ==========
let currentTermId = null;

function openTermModal(termId) {
    const term = glossaryData.terms.find(t => t.id === termId);
    if (!term) return;
    
    currentTermId = termId;
    const category = glossaryData.categories[term.category];
    
    // Update URL hash for sharing
    history.replaceState(null, '', `#${encodeURIComponent(termId)}`);
    
    // Populate modal
    document.getElementById('modal-title').textContent = term.original;
    document.getElementById('modal-original').textContent = term.original;
    document.getElementById('modal-translation').textContent = term.translation;
    
    // Chinese
    const chineseSection = document.getElementById('modal-chinese-section');
    if (term.chinese) {
        document.getElementById('modal-chinese').textContent = term.chinese;
        chineseSection.style.display = 'block';
    } else {
        chineseSection.style.display = 'none';
    }
    
    // Pinyin
    const pinyinSection = document.getElementById('modal-pinyin-section');
    if (term.pinyin) {
        document.getElementById('modal-pinyin').textContent = term.pinyin;
        pinyinSection.style.display = 'block';
    } else {
        pinyinSection.style.display = 'none';
    }
    
    // Context
    document.getElementById('modal-context').textContent = term.context || 'Sem contexto disponível';
    
    // Aliases
    const aliasesSection = document.getElementById('modal-aliases-section');
    if (term.aliases && term.aliases.length > 0) {
        document.getElementById('modal-aliases').innerHTML = term.aliases
            .map(a => `<span>${escapeHtml(a)}</span>`)
            .join('');
        aliasesSection.style.display = 'block';
    } else {
        aliasesSection.style.display = 'none';
    }
    
    // Category
    const categoryBadge = document.getElementById('modal-category');
    categoryBadge.innerHTML = `<i class="${category?.icon || 'fas fa-tag'}"></i> ${category?.name || term.category}`;
    categoryBadge.style.background = `rgba(${hexToRgb(category?.color || '#c9a227')}, 0.2)`;
    categoryBadge.style.color = category?.color || '#c9a227';
    
    // Status
    const statusBadge = document.getElementById('modal-status');
    statusBadge.textContent = term.doNotTranslate ? 'Não Traduzir' : 'Traduzir';
    statusBadge.className = `status-badge ${term.doNotTranslate ? 'no-translate' : 'translate'}`;
    
    // Show modal
    document.getElementById('term-modal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeTermModal() {
    document.getElementById('term-modal').classList.remove('active');
    document.body.style.overflow = '';
    currentTermId = null;
    
    // Clear URL hash
    history.replaceState(null, '', window.location.pathname);
}

function copyTerm() {
    if (!currentTermId) return;
    
    const term = glossaryData.terms.find(t => t.id === currentTermId);
    if (!term) return;
    
    navigator.clipboard.writeText(term.translation).then(() => {
        // Show feedback
        const btn = document.querySelector('.btn-copy');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Copiado!';
        btn.style.background = 'linear-gradient(135deg, #27ae60, #1e8449)';
        
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.style.background = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// ========== UTILITIES ==========
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result 
        ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
        : '201, 162, 39';
}

// ========== EXPORTS FOR ONCLICK ==========
window.openTermModal = openTermModal;
window.closeTermModal = closeTermModal;
window.copyTerm = copyTerm;
window.goToPage = goToPage;
