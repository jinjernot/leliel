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
        var button = document.getElementById('see-more-footnotes');
        if (element) {
            if (element.style.display === 'none' || element.style.display === '') {
                element.style.display = 'block';
                if (button) button.classList.add('open');
            }
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    // Auto-link plain-text URLs inside the footnotes table
    function autoLinkUrls(element) {
        element.querySelectorAll('td').forEach(function(td) {
            td.innerHTML = td.innerHTML.replace(
                /(?<!['"=])(https?:\/\/[^\s<>"]+)/g,
                '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
            );
        });
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
                    button.classList.add('open');
                } else {
                    element.style.display = 'none';
                    button.classList.remove('open');
                }
            });
        }
    }
    
    // Toggle for tech specs, companions, and footnotes
    toggleDisplay('see-more', 'tech-specs');
    toggleDisplay('see-more-companions', 'companions');
    toggleDisplay('see-more-footnotes', 'footnotes');

    // Auto-link URLs in footnotes on page load (section may be hidden but content is already in DOM)
    var footnotesEl = document.getElementById('footnotes');
    if (footnotesEl) autoLinkUrls(footnotesEl);
});