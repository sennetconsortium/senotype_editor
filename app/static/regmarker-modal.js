// Features to support management of individual regulating markers for Senotype submission.
// Works with the provided modal HTML and list <ul id="regmarker-list">

// Remove marker from list (for client UX, WTForms update is handled on submit)
function removeRegMarker(btn) {
    btn.parentNode.remove();
}

// Add regulating marker from API result.
function addRegMarker(id, description, action) {

    var ul = document.getElementById('regmarker-list');
   // Prevent adding duplicate marker-action pairs
    var exists = Array.from(ul.children).some(li => {
        var inputCode = li.querySelector('input[name^="regmarker-code"]');
        var inputAction = li.querySelector('input[name^="regmarker-action"]');
        return inputCode && inputAction && inputCode.value === id && inputAction.value === action;
    });
    if (exists) return;

    var li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';

    // Hidden input for WTForms submission: code and action
    var inputCode = document.createElement('input');
    inputCode.type = 'hidden';
    inputCode.name = 'regmarker-code-' + ul.children.length; // WTForms FieldList expects this pattern
    inputCode.value = id ;
    inputCode.className = 'form-control';//d-none'; // Hidden but submitted
    li.appendChild(inputCode);

    // Hidden input for WTForms submission: action
    var inputAction = document.createElement('input');
    inputAction.type = 'hidden';
    inputAction.name = 'regmarker-action-' + ul.children.length;
    inputAction.value = action;
    inputAction.className = 'form-control';//d-none';
    li.appendChild(inputAction);

    // Visible text: show the description (or id) and action as arrow or question mark
    var span = document.createElement('span');
    span.className = 'list-field-display';
    let actionSymbol;
    if (action === "up_regulates") {
        actionSymbol = '\u2191'; // up arrow
    } else if (action === "down_regulates") {
        actionSymbol = '\u2193'; // down arrow
    } else {
        actionSymbol = '?'; // question mark
    }

    span.textContent =  description + " " + actionSymbol;
    span.className = 'list-field-display';
    li.appendChild(span);

    // Remove button
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-sm btn-danger ms-2';
    btn.textContent = '-';
    btn.onclick = function () { removeRegMarker(btn); };
    btn.title = 'Remove ' + description + ' from regulating marker list';
    li.appendChild(btn);

    ul.appendChild(li);
}

// Modal search logic (fetching marker IDs, then their descriptions)
document.addEventListener('DOMContentLoaded', function () {
    let lastMarkerSearch = '';
    var searchInput = document.getElementById('regmarker-search-input');
    if (!searchInput) {
        console.error('Element #regmarker-search-input not found in DOM!');
        return;
    }
    searchInput.addEventListener('input', function () {
        var query = this.value.trim();
        var resultsDiv = document.getElementById('regmarker-search-results');
        resultsDiv.innerHTML = '';

        // Get selected marker type and action
        var markerType = document.querySelector('input[name="marker-type"]:checked');
        var type = markerType ? markerType.value : "gene";
        var markerActionRadio = document.querySelector('input[name="regmarker-action"]:checked');
        var action = markerActionRadio ? markerActionRadio.value : "up_regulates";

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
                            id = item.uniprotkb_id || query;
                            var recNameArr = item.recommended_name || [];
                            var recName = Array.isArray(recNameArr) ? recNameArr[0] : recNameArr;
                            description = "UNIPROTKB:" + id + " (" + recName.trim() + ")" ;
                        } else {
                            id = item.hgnc_id || query;
                            var approved_symbol = item.approved_symbol;
                            var approved_name = item.approved_name;
                            description =  "HGNC:" + id + " (" + approved_symbol + ")" ;
                        }
                        var btn = document.createElement('button');
                        btn.type = "button";
                        btn.className = 'btn btn-link text-start w-100 mb-1';
                        btn.textContent = description;
                        btn.onclick = function () {
                            // Use proper prefix for marker ID
                            var markerId = (type === "gene") ? ("HGNC:" + id) : ("UNIPROTKB:" + id);
                            addRegMarker(markerId, description, action);

                            // Hide modal with Bootstrap 5
                            var modalEl = document.getElementById('regmarkerSearchModal');
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

    // Optionally, trigger a new search when marker type or action radio changes
    var markerTypeRadios = document.querySelectorAll('input[name="marker-type"]');
    markerTypeRadios.forEach(function(radio) {
        radio.addEventListener('change', function () {
            if (searchInput.value.trim().length > 0) {
                searchInput.dispatchEvent(new Event('input'));
            }
        });
    });
    var markerActionRadios = document.querySelectorAll('input[name="regmarker-action"]');
    markerActionRadios.forEach(function(radio) {
        radio.addEventListener('change', function () {
            if (searchInput.value.trim().length > 0) {
                searchInput.dispatchEvent(new Event('input'));
            }
        });
    });
});