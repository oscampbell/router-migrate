const THEMES = [
    { id: 'default',          name: 'Midnight Horizon',  desc: 'Default cool indigo & teal on dark blue',               bg: '#0b0f19', primary: '#6366f1', accent: '#0ea5e9' },
    { id: 'cyberpunk',        name: 'Cyberpunk Neon',    desc: 'High-octane neon pink & cyan on absolute black',        bg: '#030203', primary: '#ff007f', accent: '#00f0ff' },
    { id: 'synthwave',        name: 'Synthwave Sunset',  desc: 'Retro hot pink & sunset orange over deep purple',       bg: '#0c021a', primary: '#ff00a0', accent: '#ff8c00' },
    { id: 'nord',             name: 'Nordic Frost',      desc: 'Cool arctic blues & mint slate accents',               bg: '#1e222a', primary: '#88c0d0', accent: '#8fbcbb' },
    { id: 'matrix',           name: 'Matrix Code',       desc: 'Glowing phosphor green on pitch black',                bg: '#000000', primary: '#00ff41', accent: '#10ef90' },
    { id: 'volcano',          name: 'Volcanic Ash',      desc: 'Fiery red & orange on dark charcoal',                  bg: '#0c0808', primary: '#ef4444', accent: '#f97316' },
    { id: 'forest',           name: 'Forest Moss',       desc: 'Sage emerald & gold on deep woodland green',           bg: '#080f09', primary: '#10b981', accent: '#ea580c' },
    { id: 'sakura',           name: 'Sakura Blossom',    desc: 'Cherry blossom pink & orchid over dark plum',          bg: '#14050e', primary: '#ec4899', accent: '#a855f7' },
    { id: 'luxury',           name: 'Luxury Gold',       desc: 'Champagne gold on dark chocolate',                     bg: '#0e0c0a', primary: '#d4af37', accent: '#f3e5ab' },
    { id: 'solarized',        name: 'Solarized Dark',    desc: 'Teal & amber on deep blue-green',                      bg: '#002b36', primary: '#2aa198', accent: '#cb4b16' },
    { id: 'lavender',         name: 'Lavender Fields',   desc: 'Soothing lavender & amethyst on dark purple',          bg: '#0a0718', primary: '#c084fc', accent: '#a78bfa' },
    { id: 'monochrome-light', name: 'Minimal Light',     desc: 'Clean slate & cobalt on elegant off-white',            bg: '#f8fafc', primary: '#4f46e5', accent: '#0ea5e9' },
    { id: 'cyber-light',      name: 'Neon Light',        desc: 'Neon pink & electric cyan on clean white',             bg: '#f5f6f8', primary: '#ff007f', accent: '#00b8e6' },
    { id: 'retro-amber',      name: 'CRT Amber',         desc: 'Phosphor amber glow on deep brown-black',              bg: '#0a0704', primary: '#ffb000', accent: '#ffcc00' },
    { id: 'pitch-black',      name: 'OLED Black',        desc: 'True black with electric cyan & royal violet',         bg: '#000000', primary: '#8b5cf6', accent: '#06b6d4' },
    { id: 'arctic-light',     name: 'Arctic Snow',       desc: 'Polar blue & glacial teal on pristine white',          bg: '#f8fafc', primary: '#3b82f6', accent: '#14b8a6' },
    { id: 'autumn',           name: 'Autumn Leaves',     desc: 'Copper, rust & maple orange on woody charcoal',        bg: '#120b08', primary: '#f97316', accent: '#ea580c' },
    { id: 'rose-gold',        name: 'Rose Gold Glam',    desc: 'Rose gold & bronze on deep luxury plum',               bg: '#110b0f', primary: '#f472b6', accent: '#fda4af' },
    { id: 'coffee',           name: 'Coffee Roast',      desc: 'Caramel & cream on rich espresso brown',               bg: '#110b08', primary: '#b45309', accent: '#d97706' },
    { id: 'ocean',            name: 'Abyssal Deep',      desc: 'Luminescent sea aquamarine & bio-teal on ink-black',   bg: '#020509', primary: '#0ea5e9', accent: '#06b6d4' },
    { id: 'dracula',          name: 'Dracula Goth',      desc: 'Gothic hot pink & electric purple on slate',           bg: '#1e1f29', primary: '#ff79c6', accent: '#bd93f9' },
    { id: 'bubblegum',        name: 'Bubblegum Pop',     desc: 'Pastel pink & baby turquoise on creamy white',         bg: '#fffafc', primary: '#f06292', accent: '#4dd0e1' },
    { id: 'slate',            name: 'Steel Slate',       desc: 'Industrial steel & cobalt on dark charcoal',           bg: '#111622', primary: '#38bdf8', accent: '#94a3b8' },
    { id: 'cyber-lime',       name: 'Lime Toxic',        desc: 'Radioactive neon green & cyber yellow on dark slate',  bg: '#070d0a', primary: '#84cc16', accent: '#22c55e' },
    { id: 'royal',            name: 'Royal Velvet',      desc: 'Deep royal blue & imperial purple on dark navy',       bg: '#060517', primary: '#8b5cf6', accent: '#3b82f6' },
];

const STORAGE_KEY = 'router-migrate-theme';

function applyTheme(themeId) {
    // Remove all theme- classes
    document.body.className = document.body.className
        .split(' ')
        .filter(c => !c.startsWith('theme-'))
        .join(' ');

    if (themeId !== 'default') {
        document.body.classList.add(`theme-${themeId}`);
    }

    localStorage.setItem(STORAGE_KEY, themeId);

    const theme = THEMES.find(t => t.id === themeId) || THEMES[0];
    const label = document.getElementById('theme-label');
    if (label) label.textContent = theme.name;

    // Update active state in grid
    document.querySelectorAll('.theme-card').forEach(card => {
        const isActive = card.dataset.themeId === themeId;
        card.classList.toggle('active', isActive);
        card.style.borderColor = isActive ? theme.primary : '';
        const check = card.querySelector('.theme-card-check');
        if (check) check.style.backgroundColor = isActive ? theme.primary : '';
    });
}

function buildThemeGrid() {
    const grid = document.getElementById('theme-grid');
    if (!grid) return;

    const currentThemeId = localStorage.getItem(STORAGE_KEY) || 'default';

    grid.innerHTML = THEMES.map(theme => {
        const isActive = theme.id === currentThemeId;
        const isLight = ['monochrome-light', 'cyber-light', 'arctic-light', 'bubblegum'].includes(theme.id);
        const textColor = isLight ? '#1e293b' : '#f8fafc';
        const descColor = isLight ? '#475569' : 'rgba(248,250,252,0.6)';

        return `
        <div class="theme-card ${isActive ? 'active' : ''}"
             data-theme-id="${theme.id}"
             style="
                background: ${theme.bg};
                border-color: ${isActive ? theme.primary : 'rgba(255,255,255,0.1)'};
                color: ${textColor};
             ">
            <div class="theme-card-check" style="background-color: ${isActive ? theme.primary : 'transparent'};">✓</div>
            <div class="theme-card-swatches">
                <div class="theme-swatch large" style="background:${theme.bg}; border-color: rgba(255,255,255,0.2);"></div>
                <div class="theme-swatch" style="background:${theme.primary};"></div>
                <div class="theme-swatch" style="background:${theme.accent};"></div>
            </div>
            <div class="theme-card-name" style="color:${textColor}">${theme.name}</div>
            <div class="theme-card-desc" style="color:${descColor}">${theme.desc}</div>
        </div>`;
    }).join('');

    // Click handler for each card
    grid.querySelectorAll('.theme-card').forEach(card => {
        card.addEventListener('click', () => {
            applyTheme(card.dataset.themeId);
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // ── Theme Picker ────────────────────────────────────────────
    const themeBtn      = document.getElementById('theme-btn');
    const themeModal    = document.getElementById('theme-modal');
    const themeBackdrop = document.getElementById('theme-backdrop');
    const themeClose    = document.getElementById('theme-close');

    if (!themeBtn)    { console.error('theme-btn not found'); }
    if (!themeModal)  { console.error('theme-modal not found'); }
    if (!themeClose)  { console.error('theme-close not found'); }

    // Apply saved theme on load
    const savedTheme = localStorage.getItem(STORAGE_KEY) || 'default';
    applyTheme(savedTheme);

    function openModal() {
        buildThemeGrid();
        themeModal.classList.remove('hidden');
    }
    function closeModal() {
        themeModal.classList.add('hidden');
    }

    if (themeBtn)      themeBtn.addEventListener('click', openModal);
    if (themeClose)    themeClose.addEventListener('click', closeModal);
    if (themeBackdrop) themeBackdrop.addEventListener('click', closeModal);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

    // ── Migration logic ─────────────────────────────────────────
    const migrateBtn     = document.getElementById('migrate-btn');
    const sourceVendor   = document.getElementById('source-vendor');
    const targetVendor   = document.getElementById('target-vendor');
    const sourceConfig   = document.getElementById('source-config');
    const targetConfig   = document.getElementById('target-config');
    const resultsSection = document.getElementById('results-section');
    const outputConfig   = document.getElementById('output-config');
    const copyBtn        = document.getElementById('copy-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    const toast          = document.getElementById('toast');

    function showToast(message, type = 'success') {
        if (!toast) return;
        toast.textContent = message;
        toast.className = 'toast ' + type;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 3000);
    }

    if (copyBtn) {
        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(outputConfig.textContent);
                showToast('Copied to clipboard!', 'success');
            } catch (err) {
                showToast('Failed to copy text', 'error');
            }
        });
    }

    if (migrateBtn) {
        migrateBtn.addEventListener('click', async () => {
            const sVendor = sourceVendor.value;
            const tVendor = targetVendor.value;
            const sConfig = sourceConfig.value.trim();
            const tConfig = targetConfig.value.trim();

            if (!sConfig || !tConfig) {
                showToast('Please provide both source and target configurations.', 'error');
                return;
            }

            loadingOverlay.classList.remove('hidden');
            resultsSection.classList.add('hidden');

            try {
                const response = await fetch('/api/migrate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        source_vendor: sVendor,
                        target_vendor: tVendor,
                        source_config: sConfig,
                        target_config: tConfig
                    })
                });

                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Migration failed');

                outputConfig.textContent = data.output;
                resultsSection.classList.remove('hidden');
                resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                showToast('Migration successful!', 'success');

            } catch (error) {
                showToast(error.message, 'error');
                console.error('Migration error:', error);
            } finally {
                loadingOverlay.classList.add('hidden');
            }
        });
    }
});
