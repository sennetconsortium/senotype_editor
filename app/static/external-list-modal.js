/*
Features to support addition and removal of external assertions (dataset, citation, origin) for Senotype submission.
DRY version: parameterized for type ('dataset', 'citation', 'origin').

Usage:
- HTML list should have id: `${type}-list`
- Modal search input should have id: `${type}-search-input`
- Modal results div should have id: `${type}-search-results`
- Modal element should have id: `${type}SearchModal`
- FieldList pattern: `${type}-<index>`
*/

/*
EXTERNAL_CONFIG
is an object that centralizes all type-specific logic for handling
external assertions (datasets, citations, origins) in a Senotype.

The first-level key corresponds to a type of
external assertion (e.g., dataset).

Each assertion object contains keys that correspond to functions in the
add modal:
1. apiSearch: an endpoint for the API from which to obtain information
              specific to the type of assertion
2. parseApiReult: a function that parses the API response to obtain a display
                  of information specific to the type of assertion
3. link: a set of properties to be used in the link button associated with the
         assertion object
4. displayText: used in the display of the link button

*/
const EXTERNAL_CONFIG = {
    dataset: {
        apiSearch: query => `https://entity.api.sennetconsortium.org/entities/${encodeURIComponent(query)}`,
        parseApiResult: (data, query) => {
            const sennetid = data.sennetid || query;
            const uuid = data.uuid || '';
            const description = data.title || data.name || sennetid || '';
            if (!sennetid) return [];
            return [{
                id: sennetid,      // Consistent with citation/origin
                uuid,
                description
            }];
        },
        link: info => ({
            href: `https://data.sennetconsortium.org/dataset?uuid=${encodeURIComponent(info.uuid)}`,
            title: 'View dataset details'
        }),
        displayText: info => `${info.id} (${info.description})`
    },
    citation: {
        apiSearch: query =>
            `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term=${encodeURIComponent(query)}`,
        parseApiResult: async (data) => {
            const pmids = data.esearchresult?.idlist || [];
            if (pmids.length === 0) return [];
            const summaryRes = await fetch(
                `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=${pmids.join(',')}`
            );
            const summaryData = await summaryRes.json();
            return pmids.map(pmid => ({
                id: `PMID:${pmid}`,
                description: summaryData.result[pmid]?.title || pmid
            }));
        },
        link: info => ({
            href: `https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(info.id.split(':')[1])}`,
            title: 'View citation details'
        }),
        displayText: info => `${info.id} (${info.description.slice(0, 40)}...)`
    },
    origin: {
        apiSearch: query =>
            `https://scicrunch.org/resolver/${encodeURIComponent(query)}.json`,
        parseApiResult: data => {
            let items = [];
            if (data.hits && Array.isArray(data.hits.hits)) {
                items = data.hits.hits.map(hit => hit._source.item);
            } else if (data.identifier || (data.item && data.item.identifier)) {
                items = [data.item || data];
            }
            return items.map(item => ({
                id: `RRID:${item.identifier || data.identifier || ''}`.replace(/^RRID:RRID:/, 'RRID:'),
                description: item.description || item.name || item.identifier || data.identifier || ''
            }));
        },
        link: info => ({
            href: `https://scicrunch.org/resolver/${encodeURIComponent(info.id.replace(/^RRID:/, ''))}`,
            title: 'View origin details'
        }),
        displayText: info => `${info.id} (${info.description.slice(0, 40)}...)`
    }
};

// --- Add, Remove, and EventListener Functions ---

function removeExternal(type, btn) {
    btn.parentNode.remove();
}

function addExternal(type, info) {
    const config = EXTERNAL_CONFIG[type];
    const ul = document.getElementById(`${type}-list`);
    if (!ul) return;

    // Prevent duplicates
    const exists = Array.from(ul.querySelectorAll('input')).some(input => input.value === info.id);
    if (exists) return;

    const li = document.createElement('li');
    li.className = `list-group-item d-flex justify-content-between align-items-center w-100`;

    // Hidden input for WTForms
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = `${type}-${ul.children.length}`;
    input.value = info.id;
    input.className = 'form-control d-none';
    li.appendChild(input);

    // Display span
    const span = document.createElement('span');
    span.className = 'list-field-display';
    span.textContent = config.displayText(info);
    li.appendChild(span);

    // Placeholder span for link button
    const placeholder = document.createElement('span');
    placeholder.className = `${type}-link-placeholder ms-2`;
    placeholder.id = `${type}-link-${info.id}`;
    // Link button
    const linkInfo = config.link(info);
    const link = document.createElement('a');
    link.className = 'btn btn-sm btn-outline-primary ms-2';
    link.style.width = '2.5em';
    link.href = linkInfo.href;
    link.target = '_blank';
    link.title = linkInfo.title;
    link.textContent = '🔗';
    placeholder.appendChild(link);

    li.appendChild(placeholder);

    // Remove button
    const btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-danger ms-2';
    btn.style = 'width: 2.5em;';
    btn.textContent = '-';
    btn.onclick = function() { removeExternal(type, btn); };
    btn.title = `Remove ${info.id} from ${type} list`;
    li.appendChild(btn);

    ul.appendChild(li);
}

function setupExternalModalSearch(type) {
    const config = EXTERNAL_CONFIG[type];
    let lastSearch = '';
    const searchInput = document.getElementById(`${type}-search-input`);
    const resultsDiv = document.getElementById(`${type}-search-results`);
    if (!searchInput || !resultsDiv) return;

    searchInput.addEventListener('input', async function() {
        const query = this.value.trim();
        resultsDiv.innerHTML = '';
        if (query.length > 2 && query !== lastSearch) {
            lastSearch = query;
            resultsDiv.innerHTML = `<div class="text-muted">Searching ...</div>`;
            try {
                const apiUrl = config.apiSearch(query);
                const response = await fetch(apiUrl);
                if (!response.ok) throw new Error("API error");
                const data = await response.json();
                console.log(`[${type}] API Response:`, data);
                let items = [];
                // Citation parse is async, dataset/origin are sync
                if (type === "citation") {
                    items = await config.parseApiResult(data);
                } else if (type === "dataset") {
                    items = config.parseApiResult(data, query); // Pass query for dataset
                } else {
                    items = config.parseApiResult(data);
                }
                resultsDiv.innerHTML = '';
                if (!items || items.length === 0) {
                    resultsDiv.innerHTML = '<div class="text-muted">No results found.</div>';
                } else {
                    items.forEach(info => {
                        const btn = document.createElement('button');
                        btn.className = 'btn btn-link text-start w-100 mb-1';
                        btn.textContent = info.description;
                        btn.onclick = function () {
                            addExternal(type, info);
                            // Hide modal with Bootstrap 5
                            const modalEl = document.getElementById(`${type}SearchModal`);
                            const modal = bootstrap.Modal.getInstance(modalEl);
                            modal.hide();
                        };
                        resultsDiv.appendChild(btn);
                    });
                }
            } catch (e) {
                resultsDiv.innerHTML = `<div class="text-danger">Error fetching ${type} details or no results.</div>`;
            }
        } else {
            resultsDiv.innerHTML = '<div class="text-muted">No results found.</div>';
        }
    });
}

// --- Initialize all external modals ---
document.addEventListener('DOMContentLoaded', function () {
    ['dataset', 'citation', 'origin'].forEach(setupExternalModalSearch);
});