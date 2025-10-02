document.addEventListener("DOMContentLoaded", function () {
    const localeDropdown = document.querySelector('.locale-dropdown');
    if (localeDropdown) {
        const localeBtn = localeDropdown.querySelector('.locale-btn');
        const dropdownContent = localeDropdown.querySelector('.locale-dropdown-content');
        const localeOptions = dropdownContent.querySelectorAll('.locale-option');

        localeBtn.addEventListener('click', function() {
            dropdownContent.style.display = dropdownContent.style.display === 'block' ? 'none' : 'block';
        });

        localeOptions.forEach(option => {
            option.addEventListener('click', function(e) {
                e.preventDefault();
                if (this.classList.contains('disabled')) return;

                const selectedLocale = this.dataset.locale;
                const sku = this.dataset.sku;

                if (selectedLocale && sku) {
                    const [cc, ll] = selectedLocale.split('-');
                    if (cc && ll) {
                        window.location.href = `/qr?pn=${sku}&cc=${cc}&ll=${ll}`;
                    }
                }
            });
        });

        window.addEventListener('click', function(e) {
            if (!localeDropdown.contains(e.target)) {
                dropdownContent.style.display = 'none';
            }
        });
    }
});