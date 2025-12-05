/* ========================================
   WWM Brasileiro - Index Page JavaScript
   ======================================== */

// ========== STATE ==========
let latestLauncher = null;
let latestTranslation = null;

// ========== RELEASE HELPERS ==========
function findLatestLauncher(releases) {
    return releases.find(r => r.tag_name.startsWith('launcher-'));
}

function findLatestTranslation(releases) {
    return releases.find(r => !r.tag_name.startsWith('launcher'));
}

function findAsset(release, extension) {
    if (!release || !release.assets) return null;
    return release.assets.find(a => a.name.endsWith(extension));
}

function extractVersion(tag) {
    return tag.replace(/^(launcher-|v)/i, '');
}

// ========== UPDATE DOWNLOAD LINKS ==========
function updateDownloadLinks() {
    // Launcher
    if (latestLauncher) {
        const launcherVersion = extractVersion(latestLauncher.tag_name);
        const launcherAsset = findAsset(latestLauncher, '.exe');
        const launcherUrl = launcherAsset ? launcherAsset.browser_download_url : latestLauncher.html_url;
        
        const heroLauncherText = document.getElementById('hero-launcher-text');
        if (heroLauncherText) heroLauncherText.textContent = `Baixar Launcher v${launcherVersion}`;
        
        const downloadLauncherText = document.getElementById('download-launcher-text');
        if (downloadLauncherText) downloadLauncherText.textContent = `Baixar Launcher v${launcherVersion} (.exe)`;
        
        const footerLauncherLink = document.getElementById('footer-launcher-link');
        if (footerLauncherLink) {
            footerLauncherLink.href = launcherUrl;
            footerLauncherLink.textContent = `Launcher v${launcherVersion} (.exe)`;
        }
        
        const modalLauncherDownload = document.getElementById('modal-launcher-download');
        if (modalLauncherDownload) {
            modalLauncherDownload.href = launcherUrl;
            modalLauncherDownload.innerHTML = `<i class="fas fa-download"></i> Baixar Launcher v${launcherVersion}`;
        }
    }
    
    // Tradução
    if (latestTranslation) {
        const translationVersion = extractVersion(latestTranslation.tag_name);
        const translationAsset = findAsset(latestTranslation, '.zip');
        const translationUrl = translationAsset ? translationAsset.browser_download_url : latestTranslation.html_url;
        
        const heroTranslationText = document.getElementById('hero-translation-text');
        if (heroTranslationText) heroTranslationText.textContent = `Baixar Tradução v${translationVersion}`;
        
        const downloadTranslationText = document.getElementById('download-translation-text');
        if (downloadTranslationText) downloadTranslationText.textContent = `Baixar Tradução v${translationVersion} (.zip)`;
        
        const footerTranslationLink = document.getElementById('footer-translation-link');
        if (footerTranslationLink) {
            footerTranslationLink.href = translationUrl;
            footerTranslationLink.textContent = `Tradução v${translationVersion} (.zip)`;
        }
        
        const modalManualDownload = document.getElementById('modal-manual-download');
        if (modalManualDownload) {
            modalManualDownload.href = translationUrl;
            modalManualDownload.innerHTML = `<i class="fas fa-file-archive"></i> Baixar Tradução v${translationVersion}`;
        }
        
        const statVersion = document.getElementById('stat-version');
        if (statVersion) statVersion.textContent = `v${translationVersion}`;
    }
}

// ========== FETCH RELEASES ==========
async function fetchReleases() {
    try {
        const releases = await cachedApiCall('releases', `${GITHUB_API}/releases`);
        
        const container = document.getElementById('releases-list');
        
        if (!releases.length) {
            container.innerHTML = '<div class="loading">Nenhuma release encontrada</div>';
            return;
        }
        
        latestLauncher = findLatestLauncher(releases);
        latestTranslation = findLatestTranslation(releases);
        
        updateDownloadLinks();
        
        let totalDownloads = 0;
        releases.forEach(r => {
            r.assets.forEach(a => totalDownloads += a.download_count);
        });
        
        const statDownloads = document.getElementById('stat-downloads');
        if (statDownloads) statDownloads.textContent = totalDownloads.toLocaleString('pt-BR');
        
        container.innerHTML = releases.slice(0, 10).map((release, index) => {
            const isLauncher = release.tag_name.startsWith('launcher-');
            const isLatestLauncher = latestLauncher && release.tag_name === latestLauncher.tag_name;
            const isLatestTranslation = latestTranslation && release.tag_name === latestTranslation.tag_name;
            const tagLabel = isLatestLauncher ? 'Launcher' : (isLatestTranslation ? 'Tradução' : '');
            
            return `
                <a href="${release.html_url}" target="_blank" class="release-item" style="text-decoration: none; color: inherit;">
                    <div class="release-icon">
                        <i class="fas ${isLauncher ? 'fa-rocket' : 'fa-tag'}"></i>
                    </div>
                    <div class="release-info">
                        <div class="release-version">${release.name || release.tag_name}</div>
                        <div class="release-date">${new Date(release.published_at).toLocaleDateString('pt-BR')}</div>
                    </div>
                    ${tagLabel ? `<span class="release-tag ${isLatestLauncher ? 'launcher' : 'latest'}">${tagLabel}</span>` : ''}
                </a>
            `;
        }).join('');
        
    } catch (error) {
        const container = document.getElementById('releases-list');
        if (container) {
            container.innerHTML = '<div class="loading"><i class="fas fa-exclamation-triangle"></i> Erro ao carregar releases</div>';
        }
    }
}

// ========== FETCH COMMITS ==========
async function fetchCommits() {
    try {
        const commits = await cachedApiCall('commits', `${GITHUB_API}/commits?per_page=15`);
        
        const container = document.getElementById('commits-list');
        
        if (!commits.length) {
            container.innerHTML = '<div class="loading">Nenhum commit encontrado</div>';
            return;
        }
        
        container.innerHTML = commits.map(commit => {
            const author = commit.author?.login || commit.commit.author.name;
            const initial = author.charAt(0).toUpperCase();
            const date = new Date(commit.commit.author.date).toLocaleDateString('pt-BR');
            const sha = commit.sha.substring(0, 7);
            const message = commit.commit.message.split('\n')[0];
            
            return `
                <a href="${commit.html_url}" target="_blank" class="commit-item" style="text-decoration: none; color: inherit;">
                    <div class="commit-avatar">${initial}</div>
                    <div class="commit-content">
                        <div class="commit-message">${message}</div>
                        <div class="commit-meta">
                            <span>${author}</span>
                            <span class="commit-sha">${sha}</span>
                            <span>${date}</span>
                        </div>
                    </div>
                </a>
            `;
        }).join('');
        
    } catch (error) {
        const container = document.getElementById('commits-list');
        if (container) {
            container.innerHTML = '<div class="loading"><i class="fas fa-exclamation-triangle"></i> Erro ao carregar commits</div>';
        }
    }
}

// ========== RECENT TRANSLATIONS ==========
async function loadRecentTranslations() {
    const grid = document.getElementById('recent-translations-grid');
    if (!grid) return;
    
    try {
        const allIssues = await cachedApiCall(
            'applied_issues',
            'https://api.github.com/repos/rodrigomiquilino/wwm_brasileiro/issues?state=closed&labels=applied&per_page=100'
        );
        
        const issues = [...allIssues]
            .sort((a, b) => new Date(b.closed_at) - new Date(a.closed_at))
            .slice(0, 6);
        
        if (!issues || issues.length === 0) {
            grid.innerHTML = '<div class="recent-translations-empty"><i class="fas fa-inbox"></i> Nenhuma tradução aprovada ainda. Seja o primeiro!</div>';
            return;
        }
        
        const cards = issues.slice(0, 6).map(issue => {
            let suggestions = [];
            let firstSuggestion = null;
            let editedCount = 0;
            
            try {
                const jsonMatch = issue.body?.match(/```json\s*\n([\s\S]*?)\n```/);
                if (jsonMatch) {
                    const data = JSON.parse(jsonMatch[1].trim());
                    suggestions = data.suggestions || [];
                    firstSuggestion = suggestions[0];
                    editedCount = suggestions.filter(s => s.editedByReviewer).length;
                }
            } catch (e) {
                console.warn('Erro ao parsear JSON da issue:', issue.number);
            }
            
            const closedDate = new Date(issue.closed_at);
            const dateStr = closedDate.toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: 'short',
                year: 'numeric'
            });
            
            let sampleOriginal = '';
            let sampleTranslation = '';
            let wasEdited = false;
            
            if (firstSuggestion) {
                sampleOriginal = firstSuggestion.id?.substring(0, 12) + '...';
                sampleTranslation = firstSuggestion.suggestion?.substring(0, 80) + (firstSuggestion.suggestion?.length > 80 ? '...' : '');
                wasEdited = firstSuggestion.editedByReviewer || false;
            } else {
                const summaryMatch = issue.body?.match(/\d+\.\s*`([^`]+)`\s*(✏️)?\s*→\s*([^\n]+)/);
                if (summaryMatch) {
                    sampleOriginal = summaryMatch[1].substring(0, 12) + '...';
                    wasEdited = !!summaryMatch[2];
                    sampleTranslation = summaryMatch[3].substring(0, 80);
                }
            }
            
            const reviewerBadge = editedCount > 0 ? `
                <span class="recent-translation-edited" title="${editedCount} tradução(ões) editada(s) pelo revisor">
                    <i class="fas fa-edit"></i> ${editedCount} editada${editedCount > 1 ? 's' : ''}
                </span>
            ` : '';
            
            return `
                <div class="recent-translation-card">
                    <div class="recent-translation-header">
                        <div class="recent-translation-meta">
                            <span class="recent-translation-date">
                                <i class="fas fa-calendar-check"></i> ${dateStr}
                            </span>
                            ${reviewerBadge}
                        </div>
                        <span class="recent-translation-count">
                            <i class="fas fa-language"></i> ${suggestions.length || '?'} tradução${suggestions.length !== 1 ? 'ões' : ''}
                        </span>
                    </div>
                    
                    ${sampleTranslation ? `
                        <div class="recent-translation-text">
                            <div class="recent-translation-original">
                                <i class="fas fa-quote-left" style="opacity: 0.5;"></i> ID: ${escapeHtml(sampleOriginal)}${wasEdited ? ' <span style="color: #60a5fa;" title="Editada pelo revisor">✏️</span>' : ''}
                            </div>
                            <div class="recent-translation-result">
                                "${escapeHtml(sampleTranslation)}"
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="recent-translation-credits">
                        <div class="recent-translation-author">
                            <span class="recent-translation-label">Tradutor</span>
                            <img src="${escapeHtml(issue.user?.avatar_url || '')}" alt="${escapeHtml(issue.user?.login || 'user')}">
                            <span>@${escapeHtml(issue.user?.login || 'anônimo')}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        grid.innerHTML = cards.join('');
        
    } catch (error) {
        console.error('Error loading recent translations:', error);
        grid.innerHTML = '<div class="recent-translations-empty"><i class="fas fa-exclamation-triangle"></i> Erro ao carregar traduções recentes</div>';
    }
}

// ========== PIX QR CODE GENERATOR ==========
function generatePixQRCode() {
    const pixKey = '5d92c454-726c-4f54-81fd-5129a76a8ed7';
    const merchantName = 'Rodrigo Miquilino';
    const merchantCity = 'Rio de Janeiro';
    
    function pad(num) {
        return num.toString().padStart(2, '0');
    }
    
    function field(id, val) {
        return id + pad(val.length) + val;
    }
    
    function crc16(str) {
        let crc = 0xFFFF;
        for (let c of str) {
            crc ^= c.charCodeAt(0) << 8;
            for (let i = 0; i < 8; i++) {
                crc = crc & 0x8000 ? (crc << 1) ^ 0x1021 : crc << 1;
            }
        }
        return (crc & 0xFFFF).toString(16).toUpperCase().padStart(4, '0');
    }
    
    const mai26 = field('00', 'br.gov.bcb.pix') + field('01', pixKey);
    
    let payload = '';
    payload += field('00', '01');
    payload += field('26', mai26);
    payload += field('52', '0000');
    payload += field('53', '986');
    payload += field('58', 'BR');
    payload += field('59', merchantName);
    payload += field('60', merchantCity);
    payload += '6304';
    
    const crcValue = crc16(payload);
    payload += crcValue;
    
    const img = document.getElementById('pix-qrcode-img');
    if (img) {
        const encodedData = encodeURIComponent(payload);
        img.src = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodedData}`;
    }
}

// ========== PIX COPY FUNCTION ==========
function copyPixKey(button) {
    const pixKey = '5d92c454-726c-4f54-81fd-5129a76a8ed7';
    
    navigator.clipboard.writeText(pixKey).then(() => {
        button.innerHTML = '<i class="fas fa-check"></i> Copiado!';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.innerHTML = '<i class="fas fa-copy"></i> Copiar Chave PIX';
            button.classList.remove('copied');
        }, 2000);
    }).catch(() => {
        const textarea = document.createElement('textarea');
        textarea.value = pixKey;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        
        button.innerHTML = '<i class="fas fa-check"></i> Copiado!';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.innerHTML = '<i class="fas fa-copy"></i> Copiar Chave PIX';
            button.classList.remove('copied');
        }, 2000);
    });
}

// ========== MODAL FUNCTIONS ==========
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function initModals() {
    // Event listeners para botões de download (usando data-modal)
    document.querySelectorAll('[data-modal]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const modalId = this.getAttribute('data-modal');
            openModal(modalId);
        });
    });
    
    // Event listeners para botões de fechar modal
    document.querySelectorAll('.modal-close, .modal-footer .btn-secondary').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const modal = this.closest('.modal-overlay');
            if (modal) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    });
    
    // Fechar modal ao clicar fora
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    });
    
    // Fechar modal com ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.active').forEach(modal => {
                modal.classList.remove('active');
            });
            document.body.style.overflow = '';
        }
    });
}

// ========== INITIALIZE ==========
document.addEventListener('DOMContentLoaded', () => {
    // Releases e commits - carregar imediatamente
    fetchReleases();
    fetchCommits();
    
    // Lazy load para Hall da Fama e Traduções Recentes
    const lazyLoadObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.id;
                if (id === 'hall-container' && !entry.target.dataset.loaded) {
                    entry.target.dataset.loaded = 'true';
                    loadContributors();
                } else if (id === 'recent-translations-grid' && !entry.target.dataset.loaded) {
                    entry.target.dataset.loaded = 'true';
                    loadRecentTranslations();
                }
                lazyLoadObserver.unobserve(entry.target);
            }
        });
    }, { rootMargin: '200px' });
    
    const hallContainer = document.getElementById('hall-container');
    const recentGrid = document.getElementById('recent-translations-grid');
    
    if (hallContainer) lazyLoadObserver.observe(hallContainer);
    if (recentGrid) lazyLoadObserver.observe(recentGrid);
    
    // Inicializar modais
    initModals();
    
    // Inicializar smooth scroll
    initSmoothScroll();
    
    // Gerar QR Code PIX
    generatePixQRCode();
    
    // Inicializar Discord Widget
    initDiscordWidget();
});

// ========== DISCORD WIDGET ==========
function openDiscordWidget() {
    const modal = document.getElementById('discord-widget-modal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeDiscordWidget() {
    const modal = document.getElementById('discord-widget-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function setDiscordWidgetSize(size) {
    const modal = document.querySelector('.discord-modal');
    if (!modal) return;
    
    // Remove all size classes
    modal.classList.remove('size-small', 'size-default', 'size-fullscreen');
    
    // Add new size class
    modal.classList.add(`size-${size}`);
    
    // Update button states
    document.querySelectorAll('.discord-size-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.size === size) {
            btn.classList.add('active');
        }
    });
}

function initDiscordWidget() {
    // Size buttons
    document.querySelectorAll('.discord-size-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            setDiscordWidgetSize(this.dataset.size);
        });
    });
    
    // Close on overlay click
    const overlay = document.getElementById('discord-widget-modal');
    if (overlay) {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                closeDiscordWidget();
            }
        });
    }
    
    // Close on ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const modal = document.getElementById('discord-widget-modal');
            if (modal && modal.classList.contains('active')) {
                closeDiscordWidget();
            }
        }
    });
    
    // Check if iframe loads (fallback if widget not enabled)
    const iframe = document.getElementById('discord-iframe');
    if (iframe) {
        iframe.addEventListener('error', function() {
            const body = document.querySelector('.discord-modal-body');
            if (body) body.classList.add('fallback-active');
        });
        
        // Timeout fallback
        setTimeout(() => {
            try {
                // If iframe is blank or has issues, show fallback
                if (!iframe.contentWindow || iframe.contentDocument?.body?.innerHTML === '') {
                    const body = document.querySelector('.discord-modal-body');
                    if (body) body.classList.add('fallback-active');
                }
            } catch (e) {
                // Cross-origin error means it loaded something
            }
        }, 5000);
    }
}
