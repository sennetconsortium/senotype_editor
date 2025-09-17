/*
Features to support addition and removal of PubMed citations for Senotype submission.
Assumes a list that is initially populated via Flask/WTForms.
Called by the edit.html template:
1. The citationSearchModal modal div loads when the user clicks the "+" button next to the
   citation list. The addEventListener function in this script populates the modal's list
   with information from the NCBI EUtils API, including a link that describes the
   citation.
2. The removeCitation function is executed by the "-" button associated with each citation
   in a list.
3. The addCitation function is executed by the link in the citationSearchmodal.
   The function creates a list element that combines:
   a. a hidden input used for submission to the update route
   b. a display span
   c. a placeholder span
   d. a link button
*/

// Remove citation from list. A dataset in the list will feature a button that executes
// this function.
function removeCitation(btn) {
    btn.parentNode.remove();
}

// Add citation to the list.
// Only add ID if not already present.
// Display description obtained from API call with the ID in the list.
function addCitation(pmid, title) {

    var ul = document.getElementById('citation-list');

    // Prevent duplicates.
    var exists = Array.from(ul.querySelectorAll('input')).some(input => input.value === pmid);
    if (exists) return;

    // Build the list element for the new citation.
    var li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center w-100';

    // Build the hidden input for WTForms submission.
    var input = document.createElement('input');
    input.type = 'text';
    input.name = 'citation-' + ul.children.length; // WTForms FieldList expects this pattern
    input.value = pmid;
    input.className = 'form-control d-none'; // Hidden but submitted
    li.appendChild(input);

    // Build the display span in format
    // PMID (truncated title)
    var span = document.createElement('span');
    span.className = 'list-field-display';
    span.textContent = pmid + " (" + title.slice(0, 40) + "..." + ")";
    li.appendChild(span);

    // Add placeholder span for link button.
    var placeholder = document.createElement('span');
    placeholder.className = 'citation-link-placeholder ms-2';
    placeholder.id = 'citation-link-' + pmid;

    // Build link button with href that loads the PubMed detail
    // for the citation, using the PMID.
    var link = document.createElement('a');
    link.className = 'btn btn-sm btn-outline-primary ms-2';
    link.style.width = '2.5em';
    // Parse the PMID from the full id.
    var code = pmid.split(":")[1];
    link.href = 'https://pubmed.ncbi.nlm.nih.gov/' + encodeURIComponent(code);
    link.target = '_blank';
    link.title = 'View citation details';
    link.textContent = '🔗';
    placeholder.appendChild(link);

    li.appendChild(placeholder);

    // Build remove button.
    var btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-danger ms-2';
    btn.style = 'width: 2.5em;'
    btn.textContent = '-';
    btn.onclick = function () { li.remove(); };
    btn.title = 'Remove ' + pmid + ' from citation list';
    li.appendChild(btn);

    ul.appendChild(li);
}

// Search logic executed by the citationSearchModal modal form that is loaded
// in response to the add button in the citation list.
// Calls the NCBI EUtils API to fetch citation information.
let lastCitationSearch = '';
document.getElementById('citation-search-input').addEventListener('input', function () {
    var query = this.value.trim();
    var resultsDiv = document.getElementById('citation-search-results');
    resultsDiv.innerHTML = '';
    if (query.length > 2 && query !== lastCitationSearch) {
        lastCitationSearch = query;
        resultsDiv.innerHTML = '<div class="text-muted">Searching PubMed...</div>';
        // NOTE: This will fail in browser due to CORS. Use backend proxy for production!
        fetch('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term=' + encodeURIComponent(query))
            .then(response => response.json())
            .then(data => {
                const pmids = data.esearchresult.idlist;
                if (pmids.length > 0) {
                    // Fetch summary info for titles
                    fetch('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=' + pmids.join(','))
                        .then(response => response.json())
                        .then(summaryData => {
                            resultsDiv.innerHTML = '';
                            pmids.forEach(function(pmid) {
                                var item = summaryData.result[pmid];
                                var title = item && item.title ? item.title : pmid;
                                var btn = document.createElement('button');
                                btn.className = 'btn btn-link text-start w-100 mb-1';
                                btn.textContent = title;
                                btn.onclick = function () {
                                    addCitation('PMID:'+pmid, title);
                                    // Hide modal with Bootstrap 5
                                    var modalEl = document.getElementById('citationSearchModal');
                                    var modal = bootstrap.Modal.getInstance(modalEl);
                                    modal.hide();
                                };
                                resultsDiv.appendChild(btn);
                            });
                        })
                        .catch(() => {
                            resultsDiv.innerHTML = '<div class="text-danger">Error fetching citation details.</div>';
                        });
                } else {
                    resultsDiv.innerHTML = '<div class="text-muted">No results found.</div>';
                }
            })
            .catch(() => {
                resultsDiv.innerHTML = '<div class="text-danger">Error searching PubMed.</div>';
            });
    }
});