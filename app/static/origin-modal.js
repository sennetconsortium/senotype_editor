// Features to support management of RRID origins for Senotype submission.
// Assume a list that is initially populated via Flask/WTForms.
// Called by the edit.html template.

// Remove origin from list (for client UX, WTForms update is handled on submit)
function removeOrigin(btn) {
    btn.parentNode.remove();
}

// Add origin from API result: Only add RRID if not already present, but display description in the list
function addOrigin(rrid, description) {
    var ul = document.getElementById('origin-list');
    // Prevent duplicates
    var exists = Array.from(ul.querySelectorAll('input')).some(input => input.value === rrid);
    if (exists) return;
    var li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';

    // Hidden input for WTForms submission
    var input = document.createElement('input');
    input.type = 'text';
    input.name = 'origin-' + ul.children.length; // WTForms FieldList expects this pattern
    input.value = rrid;
    input.className = 'form-control d-none'; // Hidden but submitted
    li.appendChild(input);

    // Visible text: RRID (description)
    var span = document.createElement('span');
    span.className = 'form-control w-100'; // matches the input styling
    span.style.border = '1px solid #d3d3d3';
    span.style.marginLeft = '1px';
    span.style.padding = '6px 12px';
    span.style.background = '#fff'; // matches li background
    span.textContent = rrid + " (" + description.slice(0, 70) + "..." + ")";
    li.appendChild(span);

    // Remove button
    var btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-danger ms-2; width: 2.5em;';
    btn.textContent = '-';
    btn.onclick = function () { li.remove(); };
    btn.title = 'Remove ' + rrid + ' from origin list';
    li.appendChild(btn);

    ul.appendChild(li);
}

// Modal search logic (fetching RRIDs, then their descriptions)
let lastOriginSearch = '';
document.getElementById('origin-search-input').addEventListener('input', function () {
    var query = this.value.trim();
    var resultsDiv = document.getElementById('origin-search-results');
    resultsDiv.innerHTML = '';

    // Accept RRID:... format or free-text search; only search if >2 chars and changed
    if (query.length > 2 && query !== lastOriginSearch) {
        lastOriginSearch = query;
        resultsDiv.innerHTML = '<div class="text-muted">Searching SciCrunch Resolver...</div>';
        let apiUrl = '';
        // If input matches RRID:SCR_xxxxxx format, use direct resolver API
        if (/^RRID:\S+$/.test(query)) {
            apiUrl = 'https://scicrunch.org/resolver/' + encodeURIComponent(query) + '.json';
        } else {
            // Otherwise, treat as free text (could adjust for real API if available)
            // For demonstration, treat as direct resolver (may not work for non-RRID terms)
            apiUrl = 'https://scicrunch.org/resolver/' + encodeURIComponent(query) + '.json';
        }
        // NOTE: This will fail in browser due to CORS. Use backend proxy for production!
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) throw new Error("404 or API error");
                return response.json();
            })
            .then(data => {
                // SciCrunch registry returns data.hits.hits array for search, or data/item for direct RRID
                let items = [];
                if (data.hits && Array.isArray(data.hits.hits)) {
                    items = data.hits.hits.map(hit => hit._source.item);
                } else if (data.identifier || (data.item && data.item.identifier)) {
                    // Direct RRID:SCR_xxxxxx lookup
                    items = [data.item || data];
                }
                resultsDiv.innerHTML = '';
                items.forEach(item => {
                    var rrid = item.identifier || query;
                    var description = item.description || item.name || rrid;
                    var btn = document.createElement('button');
                    btn.className = 'btn btn-link text-start w-100 mb-1';
                    btn.textContent = description;
                    btn.onclick = function () {
                        addOrigin('RRID:' + rrid.replace(/^RRID:/, ''), description); // Pass description for visible text
                        // Hide modal with Bootstrap 5
                        var modalEl = document.getElementById('originSearchModal');
                        var modal = bootstrap.Modal.getInstance(modalEl);
                        modal.hide();
                    };
                    resultsDiv.appendChild(btn);
                });
            })
            .catch(() => {
                resultsDiv.innerHTML = '<div class="text-danger">Error fetching origin details or no results.</div>';
            });
    } else {
        resultsDiv.innerHTML = '<div class="text-muted">No results found.</div>';
    }
});