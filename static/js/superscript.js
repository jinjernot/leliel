document.addEventListener('DOMContentLoaded', function() {
    // Function to add superscript to content inside [ ] and link to footnotes
    function addSuperscript(element) {
        var text = element.innerHTML;
        var modifiedText = text.replace(/\[([\d,]+)\]/g, function(match, p1) {
            var footnotes = p1.split(',').map(function(footnote) {
                return '<a href="#footnotes" onclick="scrollToFootnotes()"><sup>' + footnote + '</sup></a>';
            });
            return footnotes.join('<sup>,</sup> ');
        });
        element.innerHTML = modifiedText;
    }

    // Scroll to footnotes function
    window.scrollToFootnotes = function() {
        var element = document.getElementById('footnotes');
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    // Apply superscript to all specified elements
    var elementsToSuperscript = document.querySelectorAll('.superscript-content');
    elementsToSuperscript.forEach(function(element) {
        addSuperscript(element);
    });

    // --- Event Listeners for "Show More" Buttons ---

    // Function to toggle display of an element
    function toggleDisplay(buttonId, elementId) {
        var button = document.getElementById(buttonId);
        var element = document.getElementById(elementId);

        if (button && element) {
            button.addEventListener('click', function() {
                if (element.style.display === 'none' || element.style.display === '') {
                    element.style.display = 'block';
                } else {
                    element.style.display = 'none';
                }
            });
        }
    }
    
    // Toggle for tech specs, companions, and footnotes
    toggleDisplay('see-more', 'tech-specs');
    toggleDisplay('see-more-companions', 'companions');
    toggleDisplay('see-more-footnotes', 'footnotes');
});