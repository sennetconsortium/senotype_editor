// CSV upload and validation for specified marker bulk addition.

document.addEventListener("DOMContentLoaded", function () {
    // Elements from the modal div/form for specified markers in edit.html
    const form = document.getElementById("marker-csv-form");
    const fileInput = document.getElementById("marker-csv-file");
    const resultsDiv = document.getElementById("csv-validation-results");
    const submitBtn = document.getElementById("marker-csv-submit");

    let parsedMarkers = [];

    fileInput.addEventListener("change", async function (e) {
        // In case user selected a different file.
        resultsDiv.textContent = "";
        submitBtn.disabled = true;
        parsedMarkers = [];
        const file = e.target.files[0];
        if (!file) {
            return;
        }

        // Read file as text
        const reader = new FileReader();
        reader.onload = async function (evt) {
            const text = evt.target.result.trim();
            // Parse CSV
            const rows = text.split(/\r?\n/).map(row => row.split(","));
            if (rows.length < 2) {
                resultsDiv.textContent = "CSV must have at least one data row.";
                return;
            }
            // Validate header
            const header = rows[0].map(h => h.trim().toLowerCase());
            if (!(header.includes("type") && header.includes("id"))) {
                resultsDiv.textContent = "CSV must have columns named 'type' and 'id' (case-insensitive).";
                return;
            }
            const typeIdx = header.indexOf("type");
            const idIdx = header.indexOf("id");
            let errors = [];
            let markers = [];
            // Validate rows
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i].map(cell => cell.trim());
                const type = row[typeIdx].toLowerCase();
                // id here is either a HGNC symbol (e.g., BRCA1) or a UniprotKB symbol.
                const id = row[idIdx];
                if (!(type === "gene" || type === "protein")) {
                    errors.push(`Row ${i + 1}: type must be 'gene' or 'protein'`);
                    continue;
                }
                if (!id) {
                    errors.push(`Row ${i + 1}: id is missing`);
                    continue;
                }
                // Add the marker from the CSV to the list of markers to validate.
                markers.push({ type, id });
            }
            if (errors.length) {
                resultsDiv.innerHTML = errors.map(e => `<div class="text-danger">${e}</div>`).join("");
                return;
            }
            // Validate markers via API.
            resultsDiv.innerHTML = "Validating markers, please wait...";
            let apiErrors = [];
            let validEntries = [];
            for (let i = 0; i < markers.length; i++) {
                const m = markers[i];
                let apiUrl = `/ontology/${m.type === "gene" ? "genes" : "proteins"}/${encodeURIComponent(m.id)}`;
                try {
                    // Disable the ESLint no-await-in-loop checks and warnings--i.e.,
                    // that there is an await in a loop.
                    /* eslint-disable no-await-in-loop */

                    // Perform synchronous fetch.
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

                        // If a gene in the CSV was in the response, get the hgnc ID, approved symbol, and approved name.
                        validEntries.push({ type: "gene", id: found.hgnc_id, symbol: found.approved_symbol, name: found.approved_name });

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

                        // If the protein in the CSV was in the response, get the UniPeotKB ID and recommended name.
                        validEntries.push({ type: "protein", id: m.id, recommended_name: recName });
                    }
                } catch {
                    apiErrors.push(`Row ${i + 2}: ${m.type} ID '${m.id}' not found in ontology.`);
                }
            }
            if (apiErrors.length) {
                resultsDiv.innerHTML = apiErrors.map(e => `<div class="text-danger">${e}</div>`).join("");
                return;
            }
            // All valid
            parsedMarkers = validEntries;
            resultsDiv.innerHTML = `<div class="text-success">All entries valid. Ready to add.</div>`;
            submitBtn.disabled = false;
        };
        reader.readAsText(file);
    });

// Adds the markers specified in the CSV to the list so that the update function
// can POST them for validation.
    form.addEventListener("submit", function (e) {

        e.preventDefault();

        const ul = document.getElementById("marker-list");

        // Remove any empty or blank <li> (from WTForms or template)
        Array.from(ul.children).forEach(function(li) {
            var input = li.querySelector('input[type="hidden"]');
            var span = li.querySelector('.list-field-display');
            // Remove li if hidden input is missing OR value is blank, OR span is blank
            if (!input || !input.value || input.value.trim() === "" || (span && span.textContent.trim() === "")) {
                li.remove();
            }
        });

        parsedMarkers.forEach(m => {
            // id in format SAB:code
            const standardizedId = m.type === "gene" ? "HGNC:" + m.id : "UNIPROTKB:" + m.id;
            const description = m.type === "gene"
                ? m.approved_symbol || m.symbol || m.id
                : m.recommended_name || m.id;

            // Prevent duplicates in the marker list.
            if (Array.from(ul.querySelectorAll('input')).some(input => input.value === standardizedId)) return;
            //if (Array.from(ul.querySelectorAll('input')).some(input => input.value === id)) return;

            let li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';

            // Hidden input for WTForms submission
            const index = ul.querySelectorAll('li').length;
            let input = document.createElement('input');
            input.type = 'hidden';
            //input.name = 'marker-' + ul.children.length;
            input.name = 'marker-' + index;
            input.value = standardizedId;
            //input.value = id;
            input.className = 'form-control';
            li.appendChild(input);

            // Visible text: show the description instead of the ID
            var span = document.createElement('span');
            span.className = 'list-field-display';
            //span.textContent = description || id;
            span.textContent = standardizedId + " (" + description + ")";
            li.appendChild(span);

            // Add removal button.
            let btn = document.createElement('button');
            btn.className = 'btn btn-sm btn-danger ms-2';
            btn.style = 'width: 2.5em;'
            btn.textContent = '-';
            btn.onclick = function () { li.remove(); };
            li.appendChild(btn);
            ul.appendChild(li);
        });

        // Global function in input-changes.js
        handleInputChange();

        // Reset form and hide modal.
        form.reset();
        resultsDiv.innerHTML = "";
        submitBtn.disabled = true;

        // Move focus out of the modal before hiding.
        // This avoids triggering prevents accessibility errors about focused
        // elements inside aria-hidden containers. (Bootstrap apparently inserts
        // aria-hidden statements.)
        document.activeElement.blur();

        let modalEl = document.getElementById('markerCsvModal');
        let modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
    });
});