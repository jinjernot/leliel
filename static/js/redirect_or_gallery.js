document.addEventListener("DOMContentLoaded", async function () {
    // The script will first check if the page is in "redirect mode".
    // It does this by looking for a special hidden div with the ID 'redirect-info'.
    const redirectInfo = document.getElementById('redirect-info');

    if (redirectInfo) {
        // === REDIRECT MODE ===
        // If the 'redirect-info' div exists, we run the geolocation logic.

        // Get the product number and redirect URL from the div's data attributes.
        const pn = redirectInfo.dataset.pn;
        const redirectBaseUrl = redirectInfo.dataset.redirectUrl;

        try {
            // Function to fetch the user's locale from an external service.
            const getGeoLocale = async () => {
                const res = await fetch("https://ipapi.co/json/");
                const data = await res.json();
                const cc = data.country_code.toLowerCase();
                const lc = (data.languages || 'en').split(',')[0].split('-')[0].toLowerCase();
                return cc + '-' + lc;
            };

            const detectedLocale = await getGeoLocale();
            let cc = detectedLocale.split('-')[0];
            let lc = detectedLocale.split('-')[1];

            // START: WORKAROUND FOR MX LOCALE
            // If the country is Mexico (mx), force the language to also be 'mx'.
            if (cc === 'mx') {
                lc = 'mx';
            }
            // END: WORKAROUND

            const finalLocale = cc + '-' + lc;

            // Confirm with the user before redirecting.
            if (confirm("Your locale: " + finalLocale + "\n\nClick OK to redirect")) {
                window.location.href = `${redirectBaseUrl}?pn=${pn}&cc=${cc}&ll=${lc}`;
            }

        } catch (err) {
            console.error("Geolocation redirect failed:", err);
            // If geolocation fails, redirect to a default locale as a fallback.
            alert("Could not determine location. Redirecting to the default page.");
            window.location.href = `${redirectBaseUrl}?pn=${pn}&cc=us&ll=en`;
        }

    } else {
        // === GALLERY MODE ===
        // If the 'redirect-info' div does NOT exist, it means the page has loaded
        // with full product data, and we should initialize the image gallery.

        const mainImageContainer = document.querySelector('.product-gallery-main');
        const thumbnails = document.querySelectorAll('.product-gallery-thumbs .thumb-item');

        if (mainImageContainer && thumbnails.length > 0) {
            const setMainImage = (url) => {
                mainImageContainer.innerHTML = `<img src="${url}" alt="Main product image">`;
            };

            // Initialize the gallery with the first image.
            const firstImageUrl = thumbnails[0].getAttribute('data-full-image');
            setMainImage(firstImageUrl);
            thumbnails[0].classList.add('active');

            // Add click listeners to all thumbnail images.
            thumbnails.forEach(thumbnail => {
                thumbnail.addEventListener('click', function() {
                    const newImageUrl = this.getAttribute('data-full-image');
                    setMainImage(newImageUrl);
                    thumbnails.forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                });
            });
        }
    }
});