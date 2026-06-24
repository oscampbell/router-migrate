document.addEventListener('DOMContentLoaded', () => {
    const migrateBtn = document.getElementById('migrate-btn');
    const sourceVendor = document.getElementById('source-vendor');
    const targetVendor = document.getElementById('target-vendor');
    const sourceConfig = document.getElementById('source-config');
    const targetConfig = document.getElementById('target-config');
    const resultsSection = document.getElementById('results-section');
    const outputConfig = document.getElementById('output-config');
    const copyBtn = document.getElementById('copy-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    const toast = document.getElementById('toast');

    function showToast(message, type = 'success') {
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.classList.remove('hidden');
        
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 3000);
    }

    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(outputConfig.textContent);
            showToast('Copied to clipboard!', 'success');
        } catch (err) {
            showToast('Failed to copy text', 'error');
        }
    });

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
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    source_vendor: sVendor,
                    target_vendor: tVendor,
                    source_config: sConfig,
                    target_config: tConfig
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Migration failed');
            }

            outputConfig.textContent = data.output;
            resultsSection.classList.remove('hidden');
            
            // Smooth scroll to results
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            showToast('Migration successful!', 'success');

        } catch (error) {
            showToast(error.message, 'error');
            console.error('Migration error:', error);
        } finally {
            loadingOverlay.classList.add('hidden');
        }
    });
});
