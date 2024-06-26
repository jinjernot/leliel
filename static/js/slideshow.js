let slideIndex = 1;
let slideInterval;
let isDragging = false;
let startX;
let scrollLeft;

document.addEventListener('DOMContentLoaded', (event) => {
  showSlides(slideIndex);
  startAutoSlides();

  // Add event listeners to thumbnails
  document.querySelectorAll('.thumbnail img').forEach(img => {
    img.addEventListener('click', function() {
      let index = this.getAttribute('data-slide-index');
      currentSlide(parseInt(index));
    });
  });

  // Dragging functionality
  const thumbnailContainer = document.querySelector('.thumbnail-container');

  thumbnailContainer.addEventListener('mousedown', (e) => {
    isDragging = true;
    thumbnailContainer.classList.add('active');
    startX = e.pageX - thumbnailContainer.offsetLeft;
    scrollLeft = thumbnailContainer.scrollLeft;
  });

  thumbnailContainer.addEventListener('mouseleave', () => {
    isDragging = false;
    thumbnailContainer.classList.remove('active');
  });

  thumbnailContainer.addEventListener('mouseup', () => {
    isDragging = false;
    thumbnailContainer.classList.remove('active');
  });

  thumbnailContainer.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    e.preventDefault();
    const x = e.pageX - thumbnailContainer.offsetLeft;
    const walk = (x - startX) * 2; // Scroll speed
    thumbnailContainer.scrollLeft = scrollLeft - walk;
  });
});

// Function to start the automatic slideshow
function startAutoSlides() {
  slideInterval = setInterval(autoSlides, 3000);
}

// Function to advance slides automatically
function autoSlides() {
  plusSlides(1);
}

// Function to clear and restart the interval
function restartAutoSlides() {
  clearInterval(slideInterval);
  startAutoSlides();
}

function plusSlides(n) {
  showSlides(slideIndex += n);
  restartAutoSlides(); // Restart the slideshow after manually advancing
}

function currentSlide(n) {
  showSlides(slideIndex = n);
  restartAutoSlides(); // Restart the slideshow after selecting a thumbnail
}

function showSlides(n) {
  let i;
  let slides = document.getElementsByClassName("mySlides");
  let dots = document.querySelectorAll(".thumbnail img");
  if (n > slides.length) { slideIndex = 1; }
  if (n < 1) { slideIndex = slides.length; }
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";
  }
  for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
  }
  slides[slideIndex - 1].style.display = "block";
  dots[slideIndex - 1].className += " active";
}

// Function to open the modal with the clicked image
function openModal(imageUrl) {
  var modal = document.getElementById("myModal");
  var modalImg = document.getElementById("modal-img");
  modal.style.display = "block";
  modalImg.src = imageUrl;
}

// Function to close the modal
function closeModal() {
  var modal = document.getElementById("myModal");
  modal.style.display = "none";
}