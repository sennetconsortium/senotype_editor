/*
Features to support addition and removal of RRIDs for Senotype submission.
Assumes a list that is initially populated via Flask/WTForms.
Called by the edit.html template:
1. The originSearchModal modal div loads when the user clicks the "+" button next to the
   origin list. The addEventListener function in this script populates the modal's list
   with information from the SciCrunch Resolver API, including a link that describes the
   origin.
2. The removeOrigin function is executed by the "-" button associated with each origin
   in a list.
3. The addOrigin function is executed by the link in the originSearchmodal.
   The function creates a list element that combines:
   a. a hidden input used for submission to the update route
   b. a display span
   c. a placeholder span
   d. a link button
*/

// Remove origin from list. An origin in the list will feature a button that executes
// this function.
function removeOrigin(btn) {
    btn.parentNode.remove();
}

// Add origin to the list.
// Only add ID if not already present.
// Display description obtained from API call with the ID in the list.
function addOrigin(rrid, description) {
    var ul = document.getElementById('origin-list');

    // Prevent duplicates.
    var exists = Array.from(ul.querySelectorAll('input')).some(input => input.value === rrid);
    if (exists) return;

    // Build the list element for the new origin.
    var li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center w-100';

    // Build the hidden input for WTForms submission.
    var input = document.createElement('input');
    input.type = 'text';
    input.name = 'origin-' + ul.children.length; // WTForms FieldList expects this pattern
    input.value = rrid;
    input.className = 'form-control d-none'; // Hidden but submitted
    li.appendChild(input);

    // Build the display span in format
    // RRID (truncated description)
    var span = document.createElement('span');
    span.className = 'list-field-display';
    span.textContent = rrid + " (" + description.slice(0, 40) + "..." + ")";
    li.appendChild(span);

    // Add placeholder span for link button.
    var placeholder = document.createElement('span');
    placeholder.className = 'origin-link-placeholder ms-2';
    placeholder.id = 'origin-link-' + rrid;

    // Build link button with href that loads the SenNet Data Portal search detail
    // for the origin, using the RRID.
    var link = document.createElement('a');
    link.className = 'btn btn-sm btn-outline-primary ms-2';
    link.style.width = '2.5em';
    link.href = 'https://scicrunch.org/resolver/' + encodeURIComponent(rrid);
    link.target = '_blank';
    link.title = 'View origin details';
    link.textContent = '🔗';
    placeholder.appendChild(link);

    li.appendChild(placeholder);

    // Remove button
    var btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-danger ms-2';
    btn.style = 'width: 2.5em;'
    btn.textContent = '-';
    btn.onclick = function () { li.remove(); };
    btn.title = 'Remove ' + rrid + ' from origin list';
    li.appendChild(btn);

    ul.appendChild(li);
}

// Modal search logic (fetching RRIDs, then their descriptions)

document.getElementById('origin-search-input').addEventListener('input', function () {

    let lastOriginSearch = '';

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