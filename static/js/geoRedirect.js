document.addEventListener("DOMContentLoaded", function () {
    const redirectInfo = document.getElementById('redirect-info');

    if (redirectInfo) {
        const pn = redirectInfo.dataset.pn;
        const redirectBaseUrl = redirectInfo.dataset.redirectUrl;

        const getGeoLocale = async () => {
            const res = await fetch("https://ipapi.co/json/");
            if (!res.ok) throw new Error('Failed to fetch geolocation data.');
            const data = await res.json();
            const cc = data.country_code.toLowerCase();
            let lc = (data.languages || 'en').split(',')[0].split('-')[0].toLowerCase();
            if (cc === 'mx') {
                lc = 'mx';
            }
            return { cc, lc };
        };

        (async () => {
            try {
                const { cc, lc } = await getGeoLocale();
                const finalLocale = `${cc}-${lc}`;

                if (confirm("Your locale: " + finalLocale + "\n\nClick OK to redirect")) {
                    window.location.href = `${redirectBaseUrl}?pn=${pn}&cc=${cc}&ll=${lc}`;
                }
            } catch (err) {
                console.error("Geolocation redirect failed:", err);
                alert("Could not determine location. Redirecting to the default page.");
                window.location.href = `${redirectBaseUrl}?pn=${pn}&cc=us&ll=en`;
            }
        })();
    }
});