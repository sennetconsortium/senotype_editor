// Features to support management of citations for Senotype submission.
// Assume a list that is initially populated via Flask/WTForms.
// Called by the edit.html template.

// Remove citation from list (for client UX, WTForms update is handled on submit)
function removeCitation(btn) {
    btn.parentNode.remove();
}

// Add citation from API result
function addCitation(pmid, title) {
    var ul = document.getElementById('citation-list');
    var li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';
    // Hidden input for WTForms submission
    var input = document.createElement('input');
    input.type = 'text';
    input.name = 'citation-' + ul.children.length; // WTForms FieldList expects this pattern
    input.value = pmid;
    input.className = 'form-control d-none'; // Hidden but submitted
    li.appendChild(input);
    // Visible text: show the PMID
    var span = document.createElement('span');
    span.className = 'form-control w-100'; // matches the input styling
    span.style.border = '1px solid #d3d3d3';
    span.style.marginLeft = '1px';
    span.style.padding = '6px 12px';
    span.style.background = '#fff'; // matches li background
    span.textContent = pmid + " (" + title.slice(0, 70) + "..." + ")";
    li.appendChild(span);
    // Remove button
    var btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-danger ms-2; width: 2.5em;';
    btn.textContent = '-';
    btn.onclick = function () { li.remove(); };
    btn.title = 'Remove ' + pmid + ' from citation list';
    li.appendChild(btn);
    ul.appendChild(li);
}

// Modal search logic (fetching PMIDs, then their titles)
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