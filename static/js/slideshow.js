document.addEventListener('DOMContentLoaded', function() {
    const mainImageContainer = document.querySelector('.gallery-main-image');
    const thumbnails = document.querySelectorAll('.gallery-thumbnails .thumbnail');

    if (mainImageContainer && thumbnails.length > 0) {
        // Function to set the main image
        const setMainImage = (url) => {
            mainImageContainer.innerHTML = `<img src="${url}" alt="Main product image">`;
        };

        // Set the first image as the main image on load
        const firstImageUrl = thumbnails[0].getAttribute('data-full-image');
        setMainImage(firstImageUrl);
        thumbnails[0].classList.add('active');

        // Add click listeners to all thumbnails
        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function() {
                // Get the full image URL from the data attribute
                const newImageUrl = this.getAttribute('data-full-image');
                
                // Update the main image
                setMainImage(newImageUrl);

                // Update the active thumbnail styling
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }
});