function handleMouseover(element, replacementText) {
    // Save the original text
    var originalText = element.textContent.trim();
  
    // Change the text content to the replacement text
    element.textContent = replacementText;
  
    // Set up mouseout event listener to revert to original text
    element.onmouseout = function() {
      element.textContent = originalText;
    };
  }