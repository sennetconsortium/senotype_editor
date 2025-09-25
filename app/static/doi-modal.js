/*
Features to support management of DataCite DOIs for Senotype submission.
The DOI requires an external search, but the input is a textarea instead of a link.
*/

// Remove DOI from textarea and hidden input
function clearAllDoiReferences() {
    // Clear the textarea
    var textarea = document.getElementById('doi');
    if (textarea) textarea.value = '';
    // Remove all hidden inputs
    var container = document.getElementById('doi-hidden-inputs');
    if (container) container.innerHTML = '';
    // Hide or remove disclaimer
    var disclaimer = document.getElementById('doi-association-disclaimer');
    if (disclaimer) disclaimer.style.display = 'none';
}

// Add DOI from DataCite API result
function addDoiReference(doiid, title) {
    // Add to textarea (append, newline-separated)
    var textarea = document.getElementById('doi');
    if (textarea.value && !textarea.value.endsWith('\n')) {
        textarea.value += '\n';
    }
    textarea.value += doiid + ' (' + (title ? (title.length > 70 ? title.slice(0, 70) + '...' : title) : '') + ')';

    // Because the DOI input is disabled for direct entry (via typing inside the textarea
    // itself, change events are not triggered. Trigger the change event manually via
    // a custom dispatch.
    const event = new Event('input', { bubbles: true });
    textarea.dispatchEvent(event);

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
    input.type = 'hidden';
    input.name = 'doiid-' + idx;
    input.value = doiid;
    input.className = 'form-control d-none'; // Hidden but submitted
    container.appendChild(input);

    // Link button
    var link = document.createElement('a');
    link.className = 'btn btn-sm btn-outline-primary ms-2';
    link.style.width = '2.5em';
    // For now, the DataCite Commons URI will include the generic SenNet provider ID.
    link.href = 'https://commons.datacite.org/doi.org/' + encodeURIComponent(doiid);
    link.target = '_blank';
    link.title = 'View DOI details';
    link.setAttribute('aria-label', 'View DOI details');
    link.textContent = '🔗';
    container.appendChild(link);

    // Global function in input-changes.js
    handleInputChange();
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

                        // Show disclaimer when a DOI is added
                        var disclaimerId = 'doi-association-disclaimer';
                        var disclaimer = document.getElementById(disclaimerId);
                        if (!disclaimer) {
                            // Insert disclaimer below the textarea
                            var textarea = document.getElementById('doi');
                            disclaimer = document.createElement('div');
                            disclaimer.id = disclaimerId;
                            disclaimer.className = 'alert alert-warning mt-2';
                            disclaimer.textContent = 'Adding a DOI will make the senotype read-only.';
                            textarea.parentNode.insertBefore(disclaimer, textarea.nextSibling);
                        } else {
                            disclaimer.style.display = 'block'; // show if previously hidden
                        }

                        // Hide modal with Bootstrap 5.

                        // Move focus out of the modal before hiding.
                        // This avoids triggering prevents accessibility errors about focused
                        // elements inside aria-hidden containers. (Bootstrap apparently inserts
                        // aria-hidden statements.)
                        document.activeElement.blur();

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