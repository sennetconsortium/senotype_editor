// Features to support management of DataCite DOIs for Senotype submission.

// Remove DOI from textarea and hidden input (if needed)
function removeDoiReference(doiid) {
    // Remove from textarea
    var textarea = document.getElementById('doi');
    var lines = textarea.value.split('\n').filter(line => !line.includes(doiid));
    textarea.value = lines.join('\n');
    // Remove hidden input
    var container = document.getElementById('doi-hidden-inputs');
    if (container) {
        var input = container.querySelector('input[value="' + doiid + '"]');
        if (input) input.remove();
    }
}

// Add DOI from DataCite API result
function addDoiReference(doiid, title) {
    // Add to textarea (append, newline-separated)
    var textarea = document.getElementById('doi');
    if (textarea.value && !textarea.value.endsWith('\n')) {
        textarea.value += '\n';
    }
    textarea.value += doiid + ' (' + (title ? (title.length > 70 ? title.slice(0, 70) + '...' : title) : '') + ')';

    // Add hidden input for WTForms (FieldList style)
    var container = document.getElementById('doi-hidden-inputs');
    if (!container) {
        container = document.createElement('div');
        container.id = 'doi-hidden-inputs';
        textarea.parentNode.insertBefore(container, textarea.nextSibling);
    }
    // Use FieldList pattern: doiid-<index>
    var idx = container.children.length;
    var input = document.createElement('input');
    input.type = 'text';
    input.name = 'doiid-' + idx;
    input.value = doiid;
    input.className = 'form-control d-none'; // Hidden but submitted
    container.appendChild(input);
}

// Modal search logic (fetching DOIs from DataCite)
let lastDoiSearch = '';
document.getElementById('doi-search-input').addEventListener('input', function () {
    var query = this.value.trim();
    var resultsDiv = document.getElementById('doi-search-results');
    resultsDiv.innerHTML = '';
    if (query.length > 2 && query !== lastDoiSearch) {
        lastDoiSearch = query;
        resultsDiv.innerHTML = '<div class="text-muted">Searching DataCite...</div>';
        // Initially, search for DOIs associated with the Senotype client id.
        // Once we have minted DOIs for Senotypes, we can filter for Senotype DOIs using
        // DataCite's /dois?query= endpoint.
        fetch('https://api.datacite.org/dois/10.60586/' + encodeURIComponent(query))
            .then(response => {
                if (!response.ok) throw new Error('Not found');
                return response.json();
            })
            .then(data => {
                resultsDiv.innerHTML = '';
                if (data.data && data.data.id) {
                    // DataCite response: data.id is the DOI, data.attributes.title is the title (may be array).
                    var doiid = data.data.id;
                    var title = '';
                    if (data.data.attributes && Array.isArray(data.data.attributes.titles) && data.data.attributes.titles.length > 0) {
                        title = data.data.attributes.titles[0].title;
                    } else if (data.data.attributes && data.data.attributes.title) {
                        title = data.data.attributes.title;
                    }
                    // Build result button
                    var btn = document.createElement('button');
                    btn.className = 'btn btn-link text-start w-100 mb-1';
                    btn.textContent = title ? title : doiid;
                    btn.onclick = function () {
                        addDoiReference(doiid, title);
                        // Hide modal with Bootstrap 5
                        var modalEl = document.getElementById('doiSearchModal');
                        var modal = bootstrap.Modal.getInstance(modalEl);
                        modal.hide();
                    };
                    resultsDiv.appendChild(btn);
                } else {
                    resultsDiv.innerHTML = '<div class="text-muted">No results found.</div>';
                }
            })
            .catch(() => {
                resultsDiv.innerHTML = '<div class="text-danger">Error searching DataCite.</div>';
            });
    }
});