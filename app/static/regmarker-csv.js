// CSV upload and validation for regulating marker bulk add

document.addEventListener("DOMContentLoaded", function () {
    // Elements from the modal div/form for regulating markers in edit.html
    const form = document.getElementById("regmarker-csv-form");
    const fileInput = document.getElementById("regmarker-csv-file");
    const resultsDiv = document.getElementById("regcsv-validation-results");
    const submitBtn = document.getElementById("regmarker-csv-submit");

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
                markers.push({ type, id, action });
            }
            if (errors.length) {
                resultsDiv.innerHTML = errors.map(e => `<div class="text-danger">${e}</div>`).join("");
                return;
            }

            // Validate markers via API
            resultsDiv.innerHTML = "Validating markers, please wait...";
            let apiErrors = [];
            let validEntries = [];
            for (let i = 0; i < markers.length; i++) {
                const m = markers[i];
                let apiUrl = `/ontology/${m.type === "gene" ? "genes" : "proteins"}/${encodeURIComponent(m.id)}`;
                try {

                    /* eslint-disable no-await-in-loop */
                    let resp = await fetch(apiUrl);
                    if (!resp.ok) throw new Error();
                    let data = await resp.json();

                    // Check for valid return value (array/object with proper id)
                    if (m.type === "gene") {
                        let found = Array.isArray(data)
                            ? data.find(obj => obj.approved_symbol && obj.approved_symbol.toLowerCase() === m.id.toLowerCase())
                            : (data.approved_symbol && data.approved_symbol.toLowerCase() === m.id.toLowerCase() ? data : null);
                        if (!found) throw new Error();
                        // HGNC code; approved symbol; action
                        validEntries.push({ type: "gene", code: found.hgnc_id, symbol: found.approved_symbol, action: m.action });
                    } else {
                        let found = Array.isArray(data)
                            ? data.find(obj => obj.uniprotkb_id == m.id)
                            : (data.uniprotkb_id == m.id ? data : null);
                        let recNameArr = found && found.recommended_name;
                        let recName = recNameArr && Array.isArray(recNameArr) ? recNameArr[0] : recNameArr;
                        if (!found) throw new Error();
                        // UniprotKB code; recommended name; action
                        validEntries.push({ type: "protein", code: m.id, recommended_name: recName, action: m.action });
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

    // Add markers to regmarker-list.
    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const ul = document.getElementById("regmarker-list");

        parsedMarkers.forEach(m => {
            let id, description, action;
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
                id = m.code;
                marker= "HGNC:" + id ;
                description = m.symbol;
            } else {
                // visible: UNIPROTKB:code (recommended name) action symbol
                let id = m.code;
                marker = "UNIPROTKB:" + id;
                description = m.recommended_name;
            }
            // Prevent duplicates (ID only)
            let exists = Array.from(ul.querySelectorAll('input.form-control.w-100')).some(input => input.value === id);
            if (exists) return;

            let li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center w-100';

            // hidden input for marker ID submitted by Update button in Edit form
            let input = document.createElement('input');
            input.type = 'text';
            input.name = 'regmarker-code-' + ul.children.length;
            input.value = marker;
            input.className = 'form-control w-100';
            li.appendChild(input);

            // hidden input for action submitted by Update button in Edit form
            let inputAction = document.createElement('input');
            inputAction.type = 'text';
            inputAction.name = 'regmarker-action-' + ul.children.length;
            inputAction.value = m.action;
            inputAction.className = 'form-control';// d-none';
            li.appendChild(inputAction);

            // Visible description
            let span = document.createElement('span');
            span.className = 'list-field-display';
            span.textContent = marker + " (" + description + ") " + actionSymbol;
            li.appendChild(span);

            // Remove button
            let btn = document.createElement('button');
            btn.className = 'btn btn-sm btn-danger ms-2';
            btn.textContent = '-';
            btn.type = 'button';
            btn.onclick = function () { li.remove(); };
            li.appendChild(btn);

            ul.appendChild(li);
        });
        // Reset form and hide modal
        form.reset();
        resultsDiv.innerHTML = "";
        submitBtn.disabled = true;
        let modalEl = document.getElementById('regmarkerCsvModal');
        let modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
    });
});