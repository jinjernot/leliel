$(document).ready(function(){
    // Initialize the main image slider
    $('.slider').slick({
      infinite: true,
      slidesToShow: 1,
      slidesToScroll: 1,
      autoplay: false,
      autoplaySpeed: 2000, // Set the autoplay speed in milliseconds,
      asNavFor: '.thumbnail-slider', // Connect the main slider with the thumbnail slider
      swipe: false 
    });

    // Initialize the thumbnail slider
    $('.thumbnail-slider').slick({
      slidesToShow: 3,
      slidesToScroll: 1,
      asNavFor: '.slider', // Connect the thumbnail slider with the main slider
      focusOnSelect: true,
      swipe: false 
    });
  });