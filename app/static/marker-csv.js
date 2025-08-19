// CSV upload and validation for marker bulk add

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
                const id = row[idIdx];
                if (!(type === "gene" || type === "protein")) {
                    errors.push(`Row ${i + 1}: type must be 'gene' or 'protein'`);
                    continue;
                }
                if (!id) {
                    errors.push(`Row ${i + 1}: id is missing`);
                    continue;
                }
                markers.push({ type, id });
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
                        validEntries.push({ type: "gene", id: m.id, symbol: found.approved_symbol, name: found.approved_name });
                    } else {
                        let found = Array.isArray(data)
                            ? data.find(obj => obj.uniprotkb_id == m.id)
                            : (data.uniprotkb_id == m.id ? data : null);
                        let recNameArr = found && found.recommended_name;
                        let recName = recNameArr && Array.isArray(recNameArr) ? recNameArr[0] : recNameArr;
                        if (!found) throw new Error();
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

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        // Add markers to marker-list
        const ul = document.getElementById("marker-list");
        parsedMarkers.forEach(m => {
            let id, description;
            if (m.type === "gene") {
                // Use approved_symbol if present, else symbol, else id
                let symbol = m.approved_symbol || m.symbol || m.id;
                id = "HGNC:" + symbol;
                description = id;
            } else {
                // Use uniprotkb_id if present, else id
                let proteinId = m.uniprotkb_id || m.id;
                id = "UNIPROTKB:" + proteinId;
                description = id;
            }
            // Prevent duplicates
            if (Array.from(ul.querySelectorAll('input')).some(input => input.value === id)) return;
            let li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            let input = document.createElement('input');
            input.type = 'text';
            input.name = 'marker-' + ul.children.length;
            input.value = id;
            input.className = 'form-control d-none';
            li.appendChild(input);
            let span = document.createElement('span');
            span.textContent = description || id;
            li.appendChild(span);
            let btn = document.createElement('button');
            btn.className = 'btn btn-sm btn-danger ms-2';
            btn.textContent = '-';
            btn.onclick = function () { li.remove(); };
            li.appendChild(btn);
            ul.appendChild(li);
        });
        // Reset form and hide modal
        form.reset();
        resultsDiv.innerHTML = "";
        submitBtn.disabled = true;
        let modalEl = document.getElementById('markerCsvModal');
        let modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
    });
});