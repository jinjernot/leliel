document.addEventListener("DOMContentLoaded", function () {
    const localeSelector = document.getElementById('locale-selector');
    if (localeSelector) {
        localeSelector.addEventListener('change', function() {
            const selectedLocale = this.value;
            const sku = this.dataset.sku;
            if (selectedLocale && sku) {
                const [cc, ll] = selectedLocale.split('-');
                if (cc && ll) {
                    window.location.href = `/qr?pn=${sku}&cc=${cc}&ll=${ll}`;
                }
            }
        });
    }
});