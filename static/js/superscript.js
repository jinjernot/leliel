// Function to add superscript to content inside [ ] and link to footnotes
function addSuperscript(element) {
    var text = element.innerHTML;
    var modifiedText = text.replace(/\[([\d,]+)\]/g, function(match, p1) {
        var footnotes = p1.split(',').map(function(footnote) {
            var footnoteId = 'footnote-' + footnote;
            return '<a href="#' + footnoteId + '"><sup>' + footnote + '</sup></a>';
        });
        return footnotes.join('<sup>,</sup> ');
    });
    element.innerHTML = modifiedText;
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
