// Function to add superscript to content inside [ ] and link to footnotes
function addSuperscript(element) {
    var text = element.innerHTML;
    var modifiedText = text.replace(/\[([\d,]+)\]/g, function(match, p1) {
        var footnotes = p1.split(',').map(function(footnote) {
            var footnoteId = 'footnote-' + footnote;
            return '<a href="#footnotes" onclick="scrollToFootnotes()"><sup>' + footnote + '</sup></a>';
        });
        return footnotes.join('<sup>,</sup> ');
    });
    element.innerHTML = modifiedText;
}

// Scroll to footnotes function
function scrollToFootnotes() {
    var element = document.getElementById('footnotes');
    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Apply superscript to specified elements
document.addEventListener('DOMContentLoaded', function() {
    var elementsToSuperscript = document.querySelectorAll('.superscript-content');
    elementsToSuperscript.forEach(function(element) {
        addSuperscript(element);
    });
});

// Script to show/hide the table
document.addEventListener('DOMContentLoaded', function() {
    var seeMoreButton = document.getElementById('see-more');
    var techSpecsTable = document.getElementById('tech-specs');

    if (seeMoreButton && techSpecsTable) {
        seeMoreButton.addEventListener('click', function() {
            if (techSpecsTable.style.display === 'none' || techSpecsTable.style.display === '') {
                techSpecsTable.style.display = 'table';
            } else {
                techSpecsTable.style.display = 'none';
            }
        });
    }
});

// Script to show/hide the companions list
document.addEventListener('DOMContentLoaded', function() {
    var seeMoreCompanionsButton = document.getElementById('see-more-companions');
    var companionsList = document.getElementById('companions');

    if (seeMoreCompanionsButton && companionsList) {
        seeMoreCompanionsButton.addEventListener('click', function() {
            if (companionsList.style.display === 'none' || companionsList.style.display === '') {
                companionsList.style.display = 'block';
            } else {
                companionsList.style.display = 'none';
            }
        });
    }
});

// Script to show/hide the footnotes
document.addEventListener('DOMContentLoaded', function() {
    var seeMoreFootnotesButton = document.getElementById('see-more-footnotes');
    var footnotesContent = document.getElementById('footnotes-content');

    if (seeMoreFootnotesButton && footnotesContent) {
        seeMoreFootnotesButton.addEventListener('click', function() {
            if (footnotesContent.style.display === 'none' || footnotesContent.style.display === '') {
                footnotesContent.style.display = 'block';
            } else {
                footnotesContent.style.display = 'none';
            }
        });
    }
});