// Features to support management of SenNet datasets for Senotype submission.
// Assume a list that is initially populated via Flask/WTForms.
// Called by the edit.html template.

// Remove dataset from list (for client UX, WTForms update is handled on submit)
function removeDataset(btn) {
    btn.parentNode.remove();
}

// Add dataset from API result: Only add ID if not already present, but display description in the list
function addDataset(id, uuid, description, ) {
    var ul = document.getElementById('dataset-list');
    // Prevent duplicates
    var exists = Array.from(ul.querySelectorAll('input')).some(input => input.value === id);
    if (exists) return;
    var li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center w-100';

    // Hidden input for WTForms submission
    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'dataset-' + ul.children.length; // WTForms FieldList expects this pattern
    input.value = id;
    input.className = 'form-control d-none'; // Hidden but submitted
    li.appendChild(input);

    // Visible text: show the description instead of the ID
    var span = document.createElement('span');
    span.className = 'list-field-display';
    span.textContent = id + " (" + description.slice(0, 40) + "..." + ")";
    li.appendChild(span);

    // Placeholder for link button
    var placeholder = document.createElement('span');
    placeholder.className = 'dataset-link-placeholder ms-2';
    placeholder.id = 'dataset-link-' + id;

    // Link button
    var link = document.createElement('a');
    link.className = 'btn btn-sm btn-outline-primary ms-2';
    link.style.width = '2.5em';
    link.href = 'https://data.sennetconsortium.org/dataset?uuid=' + encodeURIComponent(uuid);
    link.target = '_blank';
    link.title = 'View dataset details';
    link.textContent = '🔗';
    placeholder.appendChild(link);

    li.appendChild(placeholder);

    // Remove button
    var btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-danger ms-2';
    btn.style = 'width: 2.5em;'
    btn.textContent = '-';
    btn.onclick = function () { li.remove(); };
    btn.title = 'Remove ' + id + ' from dataset list'
    li.appendChild(btn);

    ul.appendChild(li);
}

// Modal search logic (fetching dataset IDs, then their descriptions)
document.addEventListener('DOMContentLoaded', function () {
    let lastDatasetSearch = '';
    var searchInput = document.getElementById('dataset-search-input');
    if (!searchInput) {
        console.error('Element #dataset-search-input not found in DOM!');
        return;
    }
    searchInput.addEventListener('input', function () {
        var query = this.value.trim();
        var resultsDiv = document.getElementById('dataset-search-results');
        resultsDiv.innerHTML = '';

        // Accept ID:... format or free-text search; only search if >2 chars and changed
        if (query.length > 2 && query !== lastDatasetSearch) {
            lastDatasetSearch = query;
            resultsDiv.innerHTML = '<div class="text-muted">Searching SenNet Entity API...</div>';
            var apiUrl = 'https://entity.api.sennetconsortium.org/entities/' + encodeURIComponent(query);
            // NOTE: This will fail in browser due to CORS. Use backend proxy for production!
            fetch(apiUrl)
                .then(response => {
                    if (!response.ok) throw new Error("404 or API error");
                    return response.json();
                })
                .then(data => {
                    var id = data.sennetid || query;
                    var uuid = data.uuid;
                    var description = data.title || data.name || id;
                    var btn = document.createElement('button');
                    btn.className = 'btn btn-link text-start w-100 mb-1';
                    btn.textContent = description;
                    btn.onclick = function () {
                        addDataset(id, uuid, description); // Pass description for visible text
                        // Hide modal with Bootstrap 5
                        var modalEl = document.getElementById('datasetSearchModal');
                        var modal = bootstrap.Modal.getInstance(modalEl);

                        modal.hide();
                    };
                    resultsDiv.appendChild(btn);
                })
                .catch(() => {
                    resultsDiv.innerHTML = '<div class="text-danger">Error fetching dataset details or no results.</div>';
                });
        } else {
            resultsDiv.innerHTML = '<div class="text-muted">No results found.</div>';
        }
    });
});