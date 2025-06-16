$(document).ready(function(){
  $('.main-slideshow').slick({
    slidesToShow: 1,
    slidesToScroll: 1,
    arrows: false, // Changed from true
    fade: true,
    asNavFor: '.thumbnail-carousel'
  });
  $('.thumbnail-carousel').slick({
    slidesToShow: 3,
    slidesToScroll: 1,
    asNavFor: '.main-slideshow',
    dots: false,
    arrows: true,
    centerMode: true,
    focusOnSelect: true,
    autoplay: false, // Changed from true
  });
});

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