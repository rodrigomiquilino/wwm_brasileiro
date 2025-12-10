/* ========================================
   WWM Brasileiro - Shared JavaScript
   Código compartilhado entre páginas
   ======================================== */

// ========== API CONFIG ==========
const GITHUB_API = 'https://api.github.com/repos/rodrigomiquilino/wwm_brasileiro';

// ========== CACHE SYSTEM ==========
const CacheManager = {
    CACHE_KEY: 'wwm_api_cache',
    CACHE_TTL: 15 * 60 * 1000, // 15 minutos
    
    get(key, allowExpired = false) {
        try {
            const cache = JSON.parse(localStorage.getItem(this.CACHE_KEY) || '{}');
            const item = cache[key];
            if (item && Date.now() - item.timestamp < this.CACHE_TTL) {
                console.log(`[Cache HIT] ${key}`);
                return item.data;
            }
            if (item && allowExpired) {
                console.log(`[Cache STALE] ${key} (usando dados antigos)`);
                return item.data;
            }
            if (item) {
                console.log(`[Cache EXPIRED] ${key}`);
            }
            return null;
        } catch (e) {
            return null;
        }
    },
    
    set(key, data) {
        try {
            const cache = JSON.parse(localStorage.getItem(this.CACHE_KEY) || '{}');
            cache[key] = { data, timestamp: Date.now() };
            localStorage.setItem(this.CACHE_KEY, JSON.stringify(cache));
            console.log(`[Cache SET] ${key}`);
        } catch (e) {
            console.warn('Cache write failed:', e);
        }
    },
    
    clear() {
        localStorage.removeItem(this.CACHE_KEY);
    }
};

// API call com cache e fallback para dados expirados
async function cachedApiCall(cacheKey, url, options = {}) {
    // Primeiro tenta cache válido
    const cached = CacheManager.get(cacheKey);
    if (cached) return cached;
    
    try {
        const response = await fetch(url, options);
        
        // Rate limit atingido
        if (response.status === 403) {
            const staleData = CacheManager.get(cacheKey, true); // allowExpired
            if (staleData) {
                console.warn(`[Rate Limit] Usando cache expirado para ${cacheKey}`);
                return staleData;
            }
            const resetTime = response.headers.get('X-RateLimit-Reset');
            const resetDate = resetTime ? new Date(parseInt(resetTime) * 1000).toLocaleTimeString('pt-BR') : 'em breve';
            throw new Error(`Rate limit excedido. Tente novamente às ${resetDate}`);
        }
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        CacheManager.set(cacheKey, data);
        return data;
    } catch (error) {
        // Em caso de erro de rede, tenta cache expirado
        const staleData = CacheManager.get(cacheKey, true);
        if (staleData) {
            console.warn(`[Fallback] Usando cache expirado para ${cacheKey}`);
            return staleData;
        }
        throw error;
    }
}

// ========== SECURITY ==========
// Escape HTML para prevenir XSS
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// ========== HALL DA FAMA (SHARED) ==========
async function loadContributors() {
    const container = document.getElementById('hall-container');
    if (!container) return;
    
    // Developers fixos
    const LEAD_DEV = 'rodrigomiquilino';
    const SECONDARY_DEV = 'DOG729';
    
    try {
        container.innerHTML = '<div class="hall-loading"><i class="fas fa-spinner fa-spin"></i> Carregando Hall da Fama...</div>';
        
        // Buscar dados em paralelo COM CACHE
        const [repoContributors, issues, leadDevData, secondaryDevData] = await Promise.all([
            cachedApiCall('contributors', 'https://api.github.com/repos/rodrigomiquilino/wwm_brasileiro/contributors?per_page=50'),
            cachedApiCall('applied_issues', 'https://api.github.com/repos/rodrigomiquilino/wwm_brasileiro/issues?state=closed&labels=applied&per_page=100'),
            cachedApiCall(`user_${LEAD_DEV}`, `https://api.github.com/users/${LEAD_DEV}`),
            cachedApiCall(`user_${SECONDARY_DEV}`, `https://api.github.com/users/${SECONDARY_DEV}`)
        ]);
        
        // Buscar commits dos devs principais
        const leadDevContrib = repoContributors.find(c => c.login === LEAD_DEV);
        const secondaryDevContrib = repoContributors.find(c => c.login === SECONDARY_DEV);
        
        // Processar autores de issues aprovadas
        let issueAuthors = [];
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
                                            <img src="${safeAvatarUrl}" alt="${safeLogin}" loading="lazy">
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

// ========== SMOOTH SCROLL ==========
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

// ========== CELEBRATION MODAL - LOAD CONTRIBUTORS RANKING ==========
async function loadCelebrationContributors() {
    const container = document.getElementById('celebration-contributors-list');
    if (!container) return;
    
    const LEAD_DEV = 'rodrigomiquilino';
    const SECONDARY_DEV = 'DOG729';
    
    // Mensagens de agradecimento aleatórias
    const thanksMessages = [
        'Guerreiro(a) lendário(a)!',
        'Herói(na) da tradução!',
        'Muito obrigado! ❤️',
        'Você fez a diferença!',
        'Gratidão eterna!',
        'Mestre tradutor(a)!',
        'Contribuição épica!',
        'Valeu demais!',
        'Incrível dedicação!',
        'Força e honra!'
    ];
    
    // Medalhas por posição
    const rankMedals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'];
    
    try {
        // Buscar issues aplicadas para pegar contribuidores
        const issues = await cachedApiCall('applied_issues', 
            'https://api.github.com/repos/rodrigomiquilino/wwm_brasileiro/issues?state=closed&labels=applied&per_page=100'
        );
        
        // Contar contribuições por usuário
        const contributorsMap = new Map();
        
        issues.forEach(issue => {
            if (issue.user && issue.user.type === 'User' && 
                issue.user.login !== LEAD_DEV && issue.user.login !== SECONDARY_DEV) {
                const login = issue.user.login;
                
                if (!contributorsMap.has(login)) {
                    contributorsMap.set(login, {
                        login: login,
                        avatar_url: issue.user.avatar_url,
                        html_url: issue.user.html_url,
                        contributions: 0
                    });
                }
                
                // Tentar extrair quantidade de traduções da issue
                try {
                    const jsonMatch = issue.body?.match(/"total"\s*:\s*(\d+)/);
                    const count = jsonMatch ? parseInt(jsonMatch[1]) : 1;
                    contributorsMap.get(login).contributions += count;
                } catch (e) {
                    contributorsMap.get(login).contributions += 1;
                }
            }
        });
        
        // Ordenar por contribuições e pegar todos
        const contributors = Array.from(contributorsMap.values())
            .sort((a, b) => b.contributions - a.contributions);
        
        if (contributors.length === 0) {
            container.innerHTML = '<span style="color: var(--text-muted); padding: 0.5rem; display: block; text-align: center;">Obrigado a todos que participaram! ❤️</span>';
            return;
        }
        
        container.innerHTML = contributors.map((c, index) => {
            const medal = rankMedals[index] || `${index + 1}º`;
            const thanks = thanksMessages[index % thanksMessages.length];
            
            return `
                <a href="${escapeHtml(c.html_url)}" target="_blank" rel="noopener" class="celebration-contributor">
                    <span class="celebration-contributor-rank">${medal}</span>
                    <img src="${escapeHtml(c.avatar_url)}" alt="${escapeHtml(c.login)}" loading="lazy">
                    <div class="celebration-contributor-info">
                        <div class="celebration-contributor-name">@${escapeHtml(c.login)}</div>
                        <div class="celebration-contributor-thanks">${thanks}</div>
                    </div>
                    <span class="celebration-contributor-score">${c.contributions}</span>
                </a>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading celebration contributors:', error);
        container.innerHTML = '<span style="color: var(--text-muted); padding: 0.5rem; display: block; text-align: center;">Obrigado a todos os heróis! ❤️</span>';
    }
}

// ========== 🎵 MUSIC PLAYER - WUXIA AMBIENT ==========
const MusicPlayer = {
    audio: null,
    isPlaying: false,
    volume: 0.3, // Volume padrão (30%)
    
    // URL da música local
    tracks: [
        {
            name: 'Epic Drums',
            url: 'assets/epic_drums.mp3'
        }
    ],
    currentTrackIndex: 0,
    
    init() {
        // Criar o player HTML
        this.createPlayerHTML();
        
        // Inicializar o áudio
        this.audio = new Audio();
        this.audio.loop = true; // Loop ativado!
        this.audio.volume = this.volume;
        
        // Carregar preferências salvas
        this.loadPreferences();
        
        // Eventos
        this.bindEvents();
        
        // Quando a música terminar, tocar a próxima
        this.audio.addEventListener('ended', () => {
            this.nextTrack();
        });
        
        console.log('🎵 Music Player initialized');
    },
    
    createPlayerHTML() {
        const container = document.createElement('div');
        container.className = 'music-player-container';
        container.innerHTML = `
            <div class="music-volume-control" id="music-volume-control">
                <div class="music-volume-header">
                    <span><i class="fas fa-volume-up"></i> Volume</span>
                    <span id="music-volume-value">30%</span>
                </div>
                <input type="range" class="music-volume-slider" id="music-volume-slider" min="0" max="100" value="30">
                <div class="music-track-info">
                    <i class="fas fa-music"></i>
                    <span id="music-track-name">Ancient Chinese Music</span>
                </div>
            </div>
            <button type="button" class="music-player-btn" id="music-player-btn" title="Música Ambiente Wuxia">
                <i class="fas fa-music"></i>
            </button>
            <div class="music-player-tooltip">
                <div class="music-tooltip-title">
                    <i class="fas fa-music"></i> Música Wuxia
                </div>
                <div class="music-tooltip-track">Clique para tocar</div>
            </div>
        `;
        document.body.appendChild(container);
    },
    
    bindEvents() {
        const btn = document.getElementById('music-player-btn');
        const volumeControl = document.getElementById('music-volume-control');
        const volumeSlider = document.getElementById('music-volume-slider');
        
        // Toggle play/pause com clique simples
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.togglePlay();
        });
        
        // Clique direito abre controle de volume
        btn.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            volumeControl.classList.toggle('active');
        });
        
        // Volume slider
        volumeSlider.addEventListener('input', (e) => {
            const value = e.target.value / 100;
            this.setVolume(value);
        });
        
        // Fechar volume control ao clicar fora
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.music-player-container')) {
                volumeControl.classList.remove('active');
            }
        });
        
        // Tecla de atalho (M para música)
        document.addEventListener('keydown', (e) => {
            if (e.key.toLowerCase() === 'm' && !e.ctrlKey && !e.altKey && !e.metaKey) {
                // Ignorar se estiver em um input
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
                this.togglePlay();
            }
        });
    },
    
    loadTrack() {
        const track = this.tracks[this.currentTrackIndex];
        this.audio.src = track.url;
        
        // Atualizar nome da track na UI
        const trackNameEl = document.getElementById('music-track-name');
        if (trackNameEl) {
            trackNameEl.textContent = track.name;
        }
    },
    
    nextTrack() {
        this.currentTrackIndex = (this.currentTrackIndex + 1) % this.tracks.length;
        this.loadTrack();
        if (this.isPlaying) {
            this.audio.play().catch(console.warn);
        }
        this.savePreferences();
    },
    
    togglePlay() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    },
    
    play() {
        // Carregar track se ainda não carregou
        if (!this.audio.src) {
            this.loadTrack();
        }
        
        this.audio.play()
            .then(() => {
                this.isPlaying = true;
                this.updateUI();
                this.savePreferences();
                console.log('🎵 Playing:', this.tracks[this.currentTrackIndex].name);
            })
            .catch(err => {
                console.warn('🎵 Autoplay blocked:', err.message);
                // Mostrar tooltip de que precisa interagir
                const tooltip = document.querySelector('.music-player-tooltip .music-tooltip-track');
                if (tooltip) {
                    tooltip.textContent = 'Clique para iniciar';
                }
            });
    },
    
    pause() {
        this.audio.pause();
        this.isPlaying = false;
        this.updateUI();
        this.savePreferences();
        console.log('🎵 Paused');
    },
    
    setVolume(value) {
        this.volume = Math.max(0, Math.min(1, value));
        this.audio.volume = this.volume;
        
        // Atualizar UI
        const volumeValue = document.getElementById('music-volume-value');
        if (volumeValue) {
            volumeValue.textContent = Math.round(this.volume * 100) + '%';
        }
        
        this.savePreferences();
    },
    
    updateUI() {
        const btn = document.getElementById('music-player-btn');
        const tooltip = document.querySelector('.music-player-tooltip .music-tooltip-track');
        
        if (this.isPlaying) {
            btn.classList.add('playing');
            btn.querySelector('i').className = 'fas fa-pause';
            if (tooltip) {
                tooltip.textContent = this.tracks[this.currentTrackIndex].name;
            }
        } else {
            btn.classList.remove('playing');
            btn.querySelector('i').className = 'fas fa-music';
            if (tooltip) {
                tooltip.textContent = 'Clique para tocar';
            }
        }
    },
    
    savePreferences() {
        try {
            localStorage.setItem('wwm_music_prefs', JSON.stringify({
                volume: this.volume,
                currentTrackIndex: this.currentTrackIndex,
                wasPlaying: this.isPlaying
            }));
        } catch (e) {
            console.warn('Could not save music preferences');
        }
    },
    
    loadPreferences() {
        try {
            const prefs = JSON.parse(localStorage.getItem('wwm_music_prefs'));
            if (prefs) {
                this.volume = prefs.volume ?? 0.3;
                this.currentTrackIndex = prefs.currentTrackIndex ?? 0;
                
                // Atualizar slider de volume
                const slider = document.getElementById('music-volume-slider');
                const volumeValue = document.getElementById('music-volume-value');
                if (slider) slider.value = this.volume * 100;
                if (volumeValue) volumeValue.textContent = Math.round(this.volume * 100) + '%';
                
                this.audio.volume = this.volume;
                
                // Se estava tocando antes, tentar continuar
                // (provavelmente será bloqueado pelo navegador)
                if (prefs.wasPlaying) {
                    // Esperamos interação do usuário
                    const tooltip = document.querySelector('.music-player-tooltip .music-tooltip-track');
                    if (tooltip) {
                        tooltip.textContent = 'Clique para continuar';
                    }
                }
            }
        } catch (e) {
            console.warn('Could not load music preferences');
        }
    }
};

// ========== 🎵 MUSIC ENTRY MODAL - FORÇA AUTOPLAY ==========
const MusicEntryModal = {
    hasEntered: false,
    
    init() {
        // Verificar se já entrou antes (sessão atual)
        if (sessionStorage.getItem('wwm_music_entered')) {
            this.hasEntered = true;
            // Se já entrou, iniciar música diretamente
            MusicPlayer.init();
            MusicPlayer.play();
            return;
        }
        
        // Criar o modal de entrada
        this.createModal();
        
        // Aguardar página carregar completamente antes de mostrar
        if (document.readyState === 'complete') {
            this.showModal();
        } else {
            window.addEventListener('load', () => {
                // Pequeno delay para garantir que tudo está carregado
                setTimeout(() => this.showModal(), 300);
            });
        }
    },
    
    createModal() {
        const overlay = document.createElement('div');
        overlay.className = 'music-entry-overlay';
        overlay.id = 'music-entry-overlay';
        overlay.innerHTML = `
            <div class="music-entry-modal">
                <div class="music-entry-icon">⚔️</div>
                <h2 class="music-entry-title">WWM Brasileiro</h2>
                <p class="music-entry-subtitle">
                    Bem-vindo ao projeto de tradução<br>
                    de Where Winds Meet para PT-BR!
                </p>
                <button type="button" class="music-entry-btn" id="music-entry-btn">
                    <i class="fas fa-torii-gate"></i>
                    Entrar
                </button>
                <p class="music-entry-hint">
                    <i class="fas fa-music"></i> Música ambiente será ativada
                </p>
            </div>
        `;
        document.body.appendChild(overlay);
        
        // Evento do botão
        document.getElementById('music-entry-btn').addEventListener('click', () => {
            this.enter();
        });
        
        // Permitir entrar com Enter ou Espaço
        document.addEventListener('keydown', (e) => {
            if (!this.hasEntered && (e.key === 'Enter' || e.key === ' ')) {
                e.preventDefault();
                this.enter();
            }
        });
    },
    
    showModal() {
        const overlay = document.getElementById('music-entry-overlay');
        if (overlay) {
            overlay.classList.add('active');
        }
    },
    
    enter() {
        if (this.hasEntered) return;
        this.hasEntered = true;
        
        // Marcar como entrado na sessão
        sessionStorage.setItem('wwm_music_entered', 'true');
        
        // Inicializar e tocar música
        MusicPlayer.init();
        MusicPlayer.play();
        
        // Fechar modal com animação
        const overlay = document.getElementById('music-entry-overlay');
        if (overlay) {
            overlay.classList.add('fade-out');
            setTimeout(() => {
                overlay.remove();
            }, 500);
        }
        
        console.log('🎵 User entered, music started!');
    }
};

// Inicializar modal de celebração e sistema de entrada quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    loadCelebrationContributors();
    
    // Inicializar Modal de Entrada (que vai iniciar o Music Player ao clicar)
    MusicEntryModal.init();
});
