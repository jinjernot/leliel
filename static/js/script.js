document.addEventListener('DOMContentLoaded', function () {
   var seeMoreButton = document.getElementById('see-more');
   var table = document.getElementById('tech-specs');

   seeMoreButton.addEventListener('click', function () {
       if (table.style.display === 'none') {
           table.style.display = 'table';
           seeMoreButton.textContent = 'See less';
       } else {
           table.style.display = 'none';
           seeMoreButton.textContent = 'See more';
       }
   });
});