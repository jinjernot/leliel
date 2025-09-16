document.addEventListener("DOMContentLoaded", function () {
    const redirectInfo = document.getElementById('redirect-info');

    if (redirectInfo) {
        const pn = redirectInfo.dataset.pn;
        const redirectBaseUrl = redirectInfo.dataset.redirectUrl;

        try {
            const destinationUrl = new URL(redirectBaseUrl, window.location.origin);
            if (destinationUrl.origin !== window.location.origin) {
                console.error("Redirect blocked: URL is not on the same origin.", redirectBaseUrl);
                return;
            }
        } catch (e) {
            console.error("Redirect blocked: Invalid URL format.", redirectBaseUrl);
            return;
        }

        const getGeoLocale = async () => {
            const res = await fetch("https://ipapi.co/json/");
            if (!res.ok) throw new Error('Failed to fetch geolocation data.');
            const data = await res.json();
            const countryCodeRegex = /^[a-z]{2}$/;
            const langCodeRegex = /^[a-z]{2}$/;
            let cc = data.country_code ? data.country_code.toLowerCase() : 'us';
            let lc = (data.languages || 'en').split(',')[0].split('-')[0].toLowerCase();
            if (cc === 'mx') {
                lc = 'mx';
            }
            if (!countryCodeRegex.test(cc)) {
                cc = 'us';
            }
            if (!langCodeRegex.test(lc)) {
                lc = 'en';
            }
            return { cc, lc };
        };

        (async () => {
            try {
                const { cc, lc } = await getGeoLocale();
                if (confirm(`Your locale: ${cc}-${lc}\n\nClick OK to redirect`)) {
                    const finalUrl = `${redirectBaseUrl}?pn=${encodeURIComponent(pn)}&cc=${encodeURIComponent(cc)}&ll=${encodeURIComponent(lc)}`;
                    window.location.href = finalUrl;
                }
            } catch (err) {
                console.error("Geolocation redirect failed:", err);
                alert("Could not determine location. Redirecting to the default page.");
                const fallbackUrl = `${redirectBaseUrl}?pn=${encodeURIComponent(pn)}&cc=us&ll=en`;
                window.location.href = fallbackUrl;
            }
        })();
    }
});