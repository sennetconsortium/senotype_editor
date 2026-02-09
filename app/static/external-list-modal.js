/*
Features to support addition and removal of external assertions (dataset, citation, origin, etc.) for Senotype submission.
DRY version: parameterized for type ('dataset', 'citation', 'origin', etc.).

Usage:
- HTML list should have id: `${type}-list`
- Modal search input should have id: `${type}-search-input`
- Modal results div should have id: `${type}-search-results`
- Modal element should have id: `${type}SearchModal`
- FieldList pattern: `${type}-<index>`
*/

// Reindex hidden input fields in a list after addition or removal.
// This ensures the name attributes stay sequential and WTForms (etc) process them correctly.
function reindexExternalInputs(type) {
    const ul = document.getElementById(`${type}-list`);
    if (!ul) return;
    const inputs = ul.querySelectorAll('input[type="hidden"]');
    inputs.forEach((input, idx) => {
        input.name = `${type}-${idx}`;
    });
}

// Truncates display to a width specified by the configuration.
// @ param withId: whether to include the code with the description.
function displayWithTruncate(info, withId = true) {
    const trunclength = info.trunclength;
    const desc = info.description || '';
    if (withId) {
        if (desc.length > trunclength - 3) {
            return `${info.id} (${desc.slice(0, trunclength - 3)}...)`;
        }
        return `${info.id} (${desc})`;
    } else {
        if (desc.length > trunclength - 3) {
            return `${desc.slice(0, trunclength - 3)}...`;
        }
        return `${desc}`;
    }
}

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

5. trunclength: length to which to truncate the display text

*/

// Factory function to create EXTERNAL_CONFIG.
function createExternalConfig() {
    return {
        dataset: {
            // Corresponds to a SenNet dataset.
            apiSearch: query => `/dataset/${encodeURIComponent(query)}`,
            parseApiResult: (data, query) => {
                // There will be, at most, one dataset.
                const sennetid = data.sennetid || query;
                const uuid = data.uuid || '';
                const description = data.title || data.name || sennetid || '';
                if (!sennetid) return [];
                return [{
                    id: sennetid,
                    uuid,
                    description,
                    trunclength: 15
                }];
            },
            link: info => ({
                // Go directly to the dataset's detail page in the Data Portal.
                href: `/dataset/portal/${encodeURIComponent(info.uuid)}`,
                title: 'View dataset details'
            }),
            //displayText: function(info) {
                //return displayWithTruncate(info);
            //}
            displayText: function(info) {
                return displayWithTruncate(info);
            }
        },
        citation: {
            // Corresponds to a PubMed citation.
            // Synchronous, two-step workflow with EUtils:
            // 1. Use eSearch (via the citation/search/term route) to find the publication in the NCBI data.
            // 2. Use eSummary (via the citation/search/id route) to obtain the title of the publication, if it exists.
            // Specify JSON response format.
            apiSearch: query =>
                `/citation/search/term/${encodeURIComponent(query)}`,
            parseApiResult: async (data) => {
                const pmids = data.esearchresult?.idlist || [];
                if (pmids.length === 0) return [];
                const summaryRes = await fetch(
                   `/citation/search/id/${pmids.join(',')}`
                );
                const summaryData = await summaryRes.json();
                // Eutils has array-based responses.
                return pmids.map(pmid => ({
                    id: `PMID:${pmid}`,
                    description: summaryData.result[pmid]?.title || pmid,
                    trunclength: 20
                }));
            },
            link: info => ({
                href: `/citation/detail/${encodeURIComponent(info.id.split(':')[1])}`,
                title: 'View citation details'
            }),
            displayText: function(info) {
                return displayWithTruncate(info);
            }
        },
        origin: {
            // Corresponds to a search of SciCrunch Resolver.
            apiSearch: query =>
                `/origin/search/${encodeURIComponent(query)}`,
            parseApiResult: data => {
                let items = [];
                if (data.hits && Array.isArray(data.hits.hits)) {
                    items = data.hits.hits.map(hit => hit._source.item);
                } else if (data.identifier || (data.item && data.item.identifier)) {
                    items = [data.item || data];
                }
                return items.map(item => ({
                    //id: `RRID:${item.docid || data.identifier || ''}`.replace(/^RRID:RRID:/, 'RRID:'),
                    //item.docid is consistent across SciCrunch resources, including plasmids
                    id: item.docid.replace(/^rrid:/i, match => match.toUpperCase()),
                    description: item.name || item.identifier || data.identifier || '',
                    trunclength: 25
                }));
            },
            link: info => ({
                href: `/origin/detail/${encodeURIComponent(info.id.replace(/^RRID:/, ''))}`,
                title: 'View origin details'
            }),
            displayText: function(info) {
                return displayWithTruncate(info);
            }
        },
        diagnosis: {
            // Corresponds to the response from the ontology API.
            apiSearch: query =>
                `/ontology/diagnoses/${encodeURIComponent(query)}`,
            parseApiResult: data => {
                // Response will be a list of JSON objects.
                if (Array.isArray(data)) {
                    return data.map(item => ({
                        id: item.code || '',
                        description: item.term || '',
                        trunclength: 65
                    }));
                } else if (data && data.code) {
                    return [{
                        id: data.code,
                        description: data.term,
                        trunclength: 65
                    }];
                }
                return [];
            },
            link: info => ({
                href: `/bio/obo/detail/${encodeURIComponent(info.id.replace(/^DOID:/, 'DOID_'))}`,
                title: 'View diagnoses'
            }),
            displayText: function(info) {
                return displayWithTruncate(info, false);
            }
        },
        celltype: {
            // Corresponds to the response from the ontology API.
            apiSearch: query =>
                `/ontology/celltypes/${encodeURIComponent(query)}`,
            parseApiResult: data => {
                // Response will be a list of JSON objects.
                let items = [];
                if (data && Array.isArray(data)) {
                    // Map over array and extract cell_type objects.
                    items = data
                        .map(item => item.cell_type)
                        .filter(Boolean); // remove undefined/null
                } else if (data.cell_type) {
                    // Single object
                    items = [data.cell_type];
                }
                return items.map(item => ({
                    id: item.id || item.identifier || '',
                    description: item.name || item.identifier || '',
                    trunclength: 13
                }));
            },
            link: info => ({
                href: `/bio/obo/detail/${encodeURIComponent(info.id.replace(/^CL:/, 'CL_'))}`,
                title: 'View celltype details'
            }),
            displayText: function(info) {
                return displayWithTruncate(info);
            }
        },
        location: {
            // Corresponds to the response from the ontology API.
            apiSearch: query =>
                `/ontology/organs/${encodeURIComponent(query)}/term`,
            parseApiResult: data => {
                // Response will be a list of JSON objects.
                console.log(data);
                if (Array.isArray(data)) {
                    return data.map(item => ({
                        id: item.code || '',
                        description: item.term || '',
                        trunclength: 40
                    }));
                } else if (data && data.code) {
                    return [{
                        id: data.code,
                        description: data.term,
                        trunclength: 40
                    }];
                }
                return [];
            },
            link: info => ({
                // Go directly to the organ's detail page in the Data Portal.
                href: `/organs/${encodeURIComponent(info.id)}`,
                title: 'View organ details'
            }),
            displayText: function(info) {
                return displayWithTruncate(info, false);
            }
        }
    };
}

//Initialize the configuration.
const EXTERNAL_CONFIG = createExternalConfig();

// --- Add, Remove, and EventListener Functions ---

function removeExternal(type, btn) {
    btn.parentNode.remove();
    reindexExternalInputs(type);
}

function addExternal(type, info) {

    // Obtain configuration information for the assertion type.
    const config = EXTERNAL_CONFIG[type];
    const ul = document.getElementById(`${type}-list`);
    if (!ul) return;

    // Remove any empty or blank <li> (from WTForms or template)
    Array.from(ul.children).forEach(function(li) {
        // li should contain a hidden input and a span
        var input = li.querySelector('input[type="hidden"]');
        var span = li.querySelector('.list-field-display');
        // Remove li if hidden input is missing OR value is blank, OR span is blank
        if (!input || !input.value || input.value.trim() === "" || (span && span.textContent.trim() === "")) {
            li.remove();
        }
    });

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

    reindexExternalInputs(type);

    // Global function in input-changes.js
    handleInputChange();
}

function setupExternalModalSearch(type) {

    // Obtain the configuration for the assertion type.
    const config = EXTERNAL_CONFIG[type];
    let lastSearch = '';
    const searchInput = document.getElementById(`${type}-search-input`);
    const resultsDiv = document.getElementById(`${type}-search-results`);
    if (!searchInput || !resultsDiv) return;

    searchInput.addEventListener('input', async function() {
        const query = this.value.trim();
        resultsDiv.innerHTML = '';
        if (query.length > 0 && query !== lastSearch) {
            lastSearch = query;
            resultsDiv.innerHTML = `<div class="text-muted">Searching ...</div>`;
            try {
                const apiUrl = config.apiSearch(query);
                const response = await fetch(apiUrl);
                if (!response.ok) throw new Error("API error");
                const data = await response.json();
                let items = [];
                // Citation parse is async, dataset/origin are sync
                if (type === "citation") {
                    items = await config.parseApiResult(data);
                } else if (type === "dataset") {
                    items = config.parseApiResult(data, query); // Pass query for dataset
                } else {
                    items = config.parseApiResult(data);
                }
                console.log(items);
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
                            // Hide modal with Bootstrap 5.

                            // Move focus out of the modal before hiding.
                            // This avoids triggering prevents accessibility errors about focused
                            // elements inside aria-hidden containers. (Bootstrap apparently inserts
                            // aria-hidden statements.)
                            document.activeElement.blur();

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
    ['dataset', 'citation', 'origin','celltype','diagnosis','location'].forEach(setupExternalModalSearch);
});