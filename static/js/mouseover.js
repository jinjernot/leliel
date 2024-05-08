function handleMouseover(element, replacementText) {
  // Create a new element for the pop-up
  var popup = document.createElement('div');
  popup.textContent = replacementText;
  popup.style.position = 'absolute';
  popup.style.background = '#fff'; 
  popup.style.border = '1px solid #ccc'; 
  popup.style.padding = '5px'; 
  popup.style.zIndex = '1000';
  popup.style.width = (2 * parseFloat(getComputedStyle(popup).width)) + 'px';
  popup.style.height = (2 * parseFloat(getComputedStyle(popup).height)) + 'px';
  
  
  var rect = element.getBoundingClientRect();
  popup.style.top = (rect.top + window.pageYOffset) + 'px';
  popup.style.left = (rect.left + window.pageXOffset) + 'px';

  document.body.appendChild(popup);

  element.onmouseout = function() {
    document.body.removeChild(popup);
  };
}
