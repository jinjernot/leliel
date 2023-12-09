document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('see-more').addEventListener('click', function () {
       var table = document.getElementById('tech-specs');
       if (table.style.display === 'none') {
          table.style.display = 'table';
       } else {
          table.style.display = 'none';
       }
    });
 });

 /*document.addEventListener('DOMContentLoaded', function() {
    // Function to add superscript to content inside [ ] and link to footnotes
    function addSuperscript(element) {
      var text = element.innerHTML;
  
      // Counter to create unique identifiers for footnotes
      var footnoteCounter = 1;
  
      // Modify the content by adding <sup> tags and anchor links
      var modifiedText = text.replace(/\[(.*?)\]/g, function(match, p1) {
        var footnoteId = 'footnote-' + footnoteCounter;
        var superscriptLink = '<a href="#' + footnoteId + '"><sup>' + p1 + '</sup></a>';
        footnoteCounter++;
        return superscriptLink;
      });
  
      // Update the content of the element
      element.innerHTML = modifiedText;
    }
  
    // Apply superscript and add anchors to specified elements
    var elementsToSuperscript = document.querySelectorAll('.superscript-content');
    elementsToSuperscript.forEach(function(element) {
      addSuperscript(element);
    });
  });
  */