document.addEventListener("DOMContentLoaded", function () {
    const mainContainer = document.querySelector('.product-gallery-main');
    const thumbnails = document.querySelectorAll('.product-gallery-thumbs .thumb-item');

    if (mainContainer && thumbnails.length > 0) {
        // Create and append the main image and video elements once
        mainContainer.innerHTML = ''; // Clear the container
        const mainImage = document.createElement('img');
        mainImage.style.maxWidth = '100%';
        mainImage.style.display = 'none'; // Initially hidden
        mainContainer.appendChild(mainImage);

        const mainVideo = document.createElement('video');
        mainVideo.style.maxWidth = '100%';
        mainVideo.style.display = 'none'; // Initially hidden
        mainVideo.controls = true;
        mainVideo.autoplay = true;
        mainContainer.appendChild(mainVideo);

        const showContent = (thumb) => {
            // Hide both elements first
            mainImage.style.display = 'none';
            mainVideo.style.display = 'none';
            mainVideo.pause(); // Stop video if it was playing

            if (thumb.dataset.videoSource) {
                // Show video
                mainVideo.src = thumb.dataset.videoSource;
                mainVideo.style.display = 'block';
                mainVideo.load();
                mainVideo.play();
            } else {
                // Show image
                mainImage.src = thumb.dataset.fullImage;
                mainImage.alt = thumb.alt;
                mainImage.style.display = 'block';
            }
        };

        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', function() {
                showContent(this);

                // Update active thumbnail state
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            });
        });

        // Initialize the gallery with the first thumbnail
        if (thumbnails[0]) {
            thumbnails[0].click();
        }
    }
});