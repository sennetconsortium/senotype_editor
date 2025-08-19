// Features to support management of individual markers for Senotype submission.
// Assume a list that is initially populated via Flask/WTForms.

// Remove marker from list (for client UX, WTForms update is handled on submit)
function removeMarker(btn) {
    btn.parentNode.remove();
}

// Add marker from API result: Only add ID if not already present, but display description in the list
function addMarker(id, description) {
    var ul = document.getElementById('marker-list');
    // Prevent duplicates
    var exists = Array.from(ul.querySelectorAll('input')).some(input => input.value === id);
    if (exists) return;
    var li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';

    // Hidden input for WTForms submission
    var input = document.createElement('input');
    input.type = 'text';
    input.name = 'marker-' + ul.children.length; // WTForms FieldList expects this pattern
    input.value = id;
    input.className = 'form-control d-none'; // Hidden but submitted
    li.appendChild(input);

    // Visible text: show the description instead of the ID
    var span = document.createElement('span');
    span.textContent = description || id;
    li.appendChild(span);

    // Remove button
    var btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-danger ms-2';
    btn.textContent = 'Remove';
    btn.onclick = function () { li.remove(); };
    li.appendChild(btn);

    ul.appendChild(li);
}

// Modal search logic (fetching marker IDs, then their descriptions)
document.addEventListener('DOMContentLoaded', function () {
    let lastMarkerSearch = '';
    var searchInput = document.getElementById('marker-search-input');
    if (!searchInput) {
        console.error('Element #marker-search-input not found in DOM!');
        return;
    }
    searchInput.addEventListener('input', function () {
        var query = this.value.trim();
        var resultsDiv = document.getElementById('marker-search-results');
        resultsDiv.innerHTML = '';

        // Check which radio button is selected for marker type
        var markerType = document.querySelector('input[name="marker-type"]:checked');
        var type = markerType ? markerType.value : "gene"; // Default to "gene" if not found

        // Only search if >0 chars and changed
        if (query.length > 0 && query !== lastMarkerSearch) {
            lastMarkerSearch = query;
            resultsDiv.innerHTML = '<div class="text-muted">Searching UBKG API...</div>';

            var apiUrl;
            if (type === "protein") {
                apiUrl = '/ontology/proteins/' + encodeURIComponent(query);
            } else {
                apiUrl = '/ontology/genes/' + encodeURIComponent(query);
            }

            fetch(apiUrl)
                .then(response => {
                    if (!response.ok) throw new Error("404 or API error");
                    return response.json();
                })
                .then(data => {
                    resultsDiv.innerHTML = '';
                    var items = Array.isArray(data) ? data : [data];
                    if (items.length === 0) {
                        resultsDiv.innerHTML = '<div class="text-muted">No results found.</div>';
                        return;
                    }
                    items.forEach(item => {
                        var id, description;
                        if (type === "protein") {
                            // Use uniprotkb_id and recommended_name
                            id = item.uniprotkb_id || query;
                            var recNameArr = item.recommended_name || [];
                            var recName = Array.isArray(recNameArr) ? recNameArr[0] : recNameArr;
                            description = (id && recName) ? (id + ' (' + recName + ')') : (id || recName || query);
                        } else {
                            // Use HGNC ID and approved_symbol/name
                            id = item.hgnc_id || query;
                            var approved_symbol = item.approved_symbol;
                            var approved_name = item.approved_name;
                            description = (approved_symbol && approved_name)
                                ? (approved_symbol + ' (' + approved_name + ')')
                                : (approved_symbol || id);
                        }
                        var btn = document.createElement('button');
                        btn.className = 'btn btn-link text-start w-100 mb-1';
                        btn.textContent = description;
                        btn.onclick = function () {
                            // Use proper prefix for marker ID
                            // var markerId = (type === "protein") ? ('UNIPROTKB:' + id) : ('HGNC:' + id);
                            var markerId = (type === "gene") ? (approved_symbol) : (id);
                            addMarker(markerId, description);
                            // Hide modal with Bootstrap 5
                            var modalEl = document.getElementById('markerSearchModal');
                            var modal = bootstrap.Modal.getInstance(modalEl);
                            modal.hide();
                        };
                        resultsDiv.appendChild(btn);
                    });
                })
                .catch(() => {
                    resultsDiv.innerHTML = '<div class="text-danger">Error fetching marker details or no results.</div>';
                });
        } else {
            resultsDiv.innerHTML = '<div class="text-muted">No results found.</div>';
        }
    });

    // Optionally, trigger a new search when the marker type radio changes
    var markerTypeRadios = document.querySelectorAll('input[name="marker-type"]');
    markerTypeRadios.forEach(function(radio) {
        radio.addEventListener('change', function () {
            // Trigger search if input is not empty
            if (searchInput.value.trim().length > 0) {
                searchInput.dispatchEvent(new Event('input'));
            }
        });
    });
});