// CSV upload and validation for regulating marker bulk add

document.addEventListener("DOMContentLoaded", function () {

    document.getElementById('regmarker-type-gene').checked = true;
    // Elements from the modal div/form for regulating markers in edit.html
    const form = document.getElementById("regmarker-csv-form");
    const fileInput = document.getElementById("regmarker-csv-file");
    const resultsDiv = document.getElementById("regcsv-validation-results");
    const submitBtn = document.getElementById("regmarker-csv-submit");

    // Reindex all marker inputs after removal so names are always sequential
    function reindexRegMarkerInputs() {
        const ul = document.getElementById("regmarker-list");
        Array.from(ul.querySelectorAll('input[name^="regmarker-"][name$="-marker"]')).forEach((input, i) => {
            input.name = `regmarker-${i}-marker`;
        });
        Array.from(ul.querySelectorAll('input[name^="regmarker-"][name$="-action"]')).forEach((input, i) => {
            input.name = `regmarker-${i}-action`;
        });
    }

    let parsedMarkers = [];

    // -----------------------
    // Support for cancellation
    // -----------------------
    let cancelled = false;
    let activeReader = null;
    let activeAbortController = null;

    function cancelProcessing() {
        cancelled = true;

        // abort FileReader if still reading
        if (activeReader && activeReader.readyState === FileReader.LOADING) {
            try { activeReader.abort(); } catch (err) { /* ignore */ }
        }
        activeReader = null;

        // abort any in-flight fetch
        if (activeAbortController) {
            try { activeAbortController.abort(); } catch (err) { /* ignore */ }
        }
        activeAbortController = null;

        // reset UI state

        resultsDiv.textContent = "";

        // Clear parsed state + file selection
        parsedMarkers = [];
        fileInput.value = "";
        setSpinner(spinnerId, spinnerLabelId, false, "");
        submitBtn.disabled = true;
    }

    // Cancel when modal is being hidden (X button, ESC, backdrop click, etc.)
    const modalEl = document.getElementById('regmarkerCsvModal');
    if (modalEl) {
        modalEl.addEventListener('hide.bs.modal', cancelProcessing);
    }

    fileInput.addEventListener("change", async function (e) {

        // Reset cancellation each time a new file is selected
        cancelled = false;

        // In case user selected a different file.
        resultsDiv.textContent = "";
        submitBtn.disabled = true;
        parsedMarkers = [];
        const file = e.target.files[0];
        if (!file) {
            return;
        }
        // Spinner controls passed to the external setSpinner function (spinner.js)
        const spinnerId = 'regmarker-spinner';
        const spinnerLabelId = 'regmarker-spinner-label';

        // show spinner immediately when a file is selected
        setSpinner(spinnerId, spinnerLabelId, true, "Validating CSV...");

        // Read file as text
        const reader = new FileReader();
        reader.onload = async function (evt) {
            try {
                // Stop early if modal window closed.
                if (cancelled) return;

                const text = evt.target.result.trim();
                // Parse CSV
                const rows = text.split(/\r?\n/).map(row => row.split(","));
                if (rows.length < 2) {
                    resultsDiv.textContent = "CSV must have at least one data row.";
                    return;
                }

                // Validate header
                const header = rows[0].map(h => h.trim().toLowerCase());
                if (!(header.includes("type") && header.includes("id") && header.includes("action"))) {
                    resultsDiv.textContent = "CSV must have columns named 'type', 'id', and 'action' (case-insensitive).";
                    return;
                }

                const typeIdx = header.indexOf("type");
                const idIdx = header.indexOf("id");
                const actionIdx = header.indexOf("action");
                let errors = [];
                let markers = [];

                // Validate rows
                for (let i = 1; i < rows.length; i++) {

                    const row = rows[i].map(cell => cell.trim());
                    const type = row[typeIdx].toLowerCase();

                    // id here is either a HGNC symbol (e.g., BRCA1) or a UniprotKB symbol.
                    const id = row[idIdx];

                    // Translate action from CSV into corresponding assertion.
                    const actionRaw = row[actionIdx];
                    let action;
                    if (actionRaw === "1" || actionRaw.toLowerCase() === "up" || actionRaw.toLowerCase() === "up_regulates") {
                        action = "up_regulates";
                    } else if (actionRaw === "-1" || actionRaw.toLowerCase() === "down" || actionRaw.toLowerCase() === "down_regulates") {
                        action = "down_regulates";
                    } else if (actionRaw === "0" || actionRaw.toLowerCase() === "inconclusive" || actionRaw.toLowerCase() === "inconclusively_regulates") {
                        action = "inconclusively_regulates";
                    } else {
                        errors.push(`Row ${i + 1}: action must be '1' (up), '-1' (down), '0' (inconclusive), or equivalent string`);
                        continue;
                    }

                    if (!(type === "gene" || type === "protein")) {
                        errors.push(`Row ${i + 1}: type must be 'gene' or 'protein'`);
                        continue;
                    }

                    if (!id) {
                        errors.push(`Row ${i + 1}: id is missing`);
                        continue;
                    }

                    // Add the marker from the CSV to the list of markers to validate.
                    markers.push({ type, id, action });
                }

                 // If basic validation errors, stop.
                if (errors.length) {
                    resultsDiv.innerHTML = errors.map(e => `<div class="text-danger">${e}</div>`).join("");
                    return;
                }

                // Validate markers via API
                resultsDiv.innerHTML = "Validating markers, please wait...";
                setSpinner(spinnerId, spinnerLabelId, true, "Validating markers via API...");

                // Create a controller for fetch cancellation.
                activeAbortController = new AbortController();

                let apiErrors = [];
                let validEntries = [];
                for (let i = 0; i < markers.length; i++) {

                    // Stop early if modal was closed.
                    if (cancelled) return;

                    // Update progress spinner.
                    setSpinner(spinnerId, spinnerLabelId, true, `${i+1} of ${markers.length}`)

                    const m = markers[i];
                    // Set up the appropriate endpoint.
                    let apiUrl = `/ontology/${m.type === "gene" ? "genes" : "proteins"}/${encodeURIComponent(m.id)}`;

                    try {
                        // Disable the ESLint no-await-in-loop checks and warnings--i.e.,
                        // that there is an await in a loop.
                        /* eslint-disable no-await-in-loop */
                        let resp = await fetch(apiUrl);
                        if (!resp.ok) throw new Error();

                        // Get response as JSON.
                        let data = await resp.json();

                        // Check for valid return value (array/object with proper id)
                        if (m.type === "gene") {

                            // If response is an array, then find the element in the array
                            // that corresponds to the marker from the CSV, searching by
                            // the HGNC approved symbol; otherwise, check the symbol of the single object.
                            // The search is case-insensitive.
                            // (The search may need to be expanded to include aliases and previous symbols.)
                            let found = Array.isArray(data)
                                ? data.find(obj => obj.approved_symbol && obj.approved_symbol.toLowerCase() === m.id.toLowerCase())
                                : (data.approved_symbol && data.approved_symbol.toLowerCase() === m.id.toLowerCase() ? data : null);
                            if (!found) throw new Error();

                            // HGNC code; approved symbol; action
                            validEntries.push({ type: "gene", code: found.hgnc_id, symbol: found.approved_symbol, action: m.action });

                        } else {

                            // If response is an array, then find the element in the array
                            // that corresponds to the marker from the CSV, searching by
                            // UniprotKB ID and recommended name; otherwise, check the ID and name of the single object.
                            // The search is case-insensitive.
                            let found = Array.isArray(data)
                                ? data.find(obj => obj.uniprotkb_id == m.id)
                                : (data.uniprotkb_id == m.id ? data : null);
                            let recNameArr = found && found.recommended_name;
                            let recName = recNameArr && Array.isArray(recNameArr) ? recNameArr[0] : recNameArr;

                            if (!found) throw new Error();
                            // UniprotKB code; recommended name; action
                            validEntries.push({ type: "protein", code: m.id, recommended_name: recName, action: m.action });
                        }

                    } catch (err) {

                        // If cancelled, don't show errors or update UI
                        if (cancelled) return;

                        // If fetch was aborted, stop quietly
                        if (err && err.name === "AbortError") return;

                        apiErrors.push(`Row ${i + 2}: ${m.type} ID '${m.id}' not found in ontology.`);
                    }
                }

                if (apiErrors.length) {
                    resultsDiv.innerHTML = apiErrors.map(e => `<div class="text-danger">${e}</div>`).join("");
                    //return;
                }

                // Stop early if cancelled.
                if (cancelled) return;

                // Enable submission of valid entries.
                parsedMarkers = validEntries;

                if (apiErrors.length > 0) {
                    // Show all validation errors (red) + one success message (green)
                    resultsDiv.innerHTML =
                        apiErrors.map(e => `<div class="text-danger">${e}</div>`).join("") +
                        `<div class="text-success">Valid entries are ready to add.</div>`;
                } else {
                    resultsDiv.innerHTML =
                        `<div class="text-success">All entries valid. Ready to add.</div>`;
                }

                submitBtn.disabled = (validEntries.length === 0);

            } finally {

                // Hide spinner no matter what (including cancellation)
                setSpinner(spinnerId, spinnerLabelId, false, "");

                // Clear active ops
                activeReader = null;
                activeAbortController = null;
            }

        };

        // If failed to read the file at all.
        reader.onerror = function () {
            if (cancelled) return;
            setSpinner(spinnerId, spinnerLabelId, false, "");
            resultsDiv.innerHTML = `<div class="text-danger">Failed to read the selected file.</div>`;
        };

        reader.readAsText(file);

    });

    // Add markers to regmarker-list.
    form.addEventListener("submit", function (e) {

        e.preventDefault();

        const ul = document.getElementById("regmarker-list");

        // Remove any empty or blank <li> (from WTForms or template)
        Array.from(ul.children).forEach(function(li) {
            var codeInput = li.querySelector('input[name^="regmarker-"][name$="-marker"]');
            var actionInput = li.querySelector('input[name^="regmarker-"][name$="-action"]');
            var span = li.querySelector('.list-field-display');
            // Remove li if inputs missing, blank, or span blank
            if (!codeInput || !codeInput.value || codeInput.value.trim() === "" ||
                !actionInput || !actionInput.value || actionInput.value.trim() === "" ||
                (span && span.textContent.trim() === "")) {
                li.remove();
            }
        });

        parsedMarkers.forEach(m => {
            let marker, description, action;
            // Translate the action into an icon for display.
            let actionSymbol;
            if (m.action === "up_regulates") {
                actionSymbol = "\u2191";
            } else if (m.action === "down_regulates") {
                actionSymbol = "\u2193";
            } else {
                actionSymbol = "?";
            }

            if (m.type === "gene") {
                // visible: HGNC:code (approved symbol) action symbol
                // hidden: HGNC:code action
                marker = "HGNC:" + m.code;
                description = m.symbol;
            } else {
                // visible: UNIPROTKB:code (recommended name) action symbol
                marker = "UNIPROTKB:" + m.code;
                description = m.recommended_name;
            }
            action = m.action;

            // Prevent duplicates of combinations of marker and action.

            let exists = Array.from(ul.querySelectorAll('li')).some(li => {
                 let codeInput = li.querySelector('input[name^="regmarker-"][name$="-marker"]');
                let actionInput = li.querySelector('input[name^="regmarker-"][name$="-action"]');
                return codeInput && actionInput && codeInput.value === marker && actionInput.value === action;
              });
            if (exists) {
                return;
            }

            // Calculate next index
            const index = ul.querySelectorAll('li').length;

            let li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';

            /// hidden input for marker ID
            let input = document.createElement('input');
            input.type = 'hidden';
            input.name = `regmarker-${index}-marker`;
            input.value = marker;
            input.className = 'form-control w-100';
            li.appendChild(input);

            // hidden input for action
            let inputAction = document.createElement('input');
            inputAction.type = 'hidden';
            inputAction.name = `regmarker-${index}-action`;
            inputAction.value = action;
            inputAction.className = 'form-control';
            li.appendChild(inputAction);

            // Display span: show the description
            let span = document.createElement('span');
            span.className = 'list-field-display';
            span.style = 'padding-left:2px; padding-right:2px;'
            span.textContent = marker + " (" + description + ") ";
            // Give the span a name that links it to its hidden field code.
            // Use setAttribute (span has no standard .name property)
            span.setAttribute('name', `regmarker-${ul.children.length}_field_display`);
            span.name = `regmarker-${ul.children.length}_field_display`;
            li.appendChild(span);

            // Display span: show action as arrow or question mark
            let spanaction = document.createElement('span');
            spanaction.className = 'action-symbol';
            spanaction.style = 'padding-left:2px; padding-right:2px';
            spanaction.textContent = actionSymbol;
            //spanaction.innerHTML = `<strong>${actionSymbol}</strong>`;

            li.appendChild(spanaction);

            // Entity detail link
            // Placeholder span for link button
            const placeholder = document.createElement('span');
            placeholder.className = `$marker-link-placeholder ms-2`;
            placeholder.id = `$marker-link-${marker}`;
            // Link button
            const markerlink = document.createElement('a');
            markerlink.className = 'btn btn-sm btn-outline-primary ms-2';
            markerlink.style.width = '2.5em';
            markerlink.href = `/bio/marker/detail/${encodeURIComponent(marker)}`;
            markerlink.target = '_blank';
            markerlink.title = description;
            markerlink.textContent = '🔗';
            placeholder.appendChild(markerlink);

            li.appendChild(placeholder);

            // Remove button
            let btn = document.createElement('button');
            btn.className = 'btn btn-sm btn-danger ms-2';
            btn.style = 'width: 2.5em;'
            btn.textContent = '-';
            btn.type = 'button';
            btn.onclick = function () { li.remove(); reindexRegMarkerInputs(); };
            li.appendChild(btn);

            ul.appendChild(li);
        });
        // Reindex all marker inputs for consistency
        reindexRegMarkerInputs();

        // Global function in input-changes.js
        handleInputChange();

        // Reset form and hide modal
        form.reset();
        resultsDiv.innerHTML = "";
        submitBtn.disabled = true;

        // Move focus out of the modal before hiding.
        // This avoids triggering prevents accessibility errors about focused
        // elements inside aria-hidden containers. (Bootstrap apparently inserts
        // aria-hidden statements.)
        document.activeElement.blur();

        let modalEl = document.getElementById('regmarkerCsvModal');
        let modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
    });
});