// Remove taxon from list
function removeTaxon(btn) {
    btn.parentNode.remove();
}

// Add taxon to list
function addTaxonToList(taxonId, taxonLabel) {
    var ul = document.getElementById('taxa-list');
    var li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';
    // Hidden input for WTForms submission
    var input = document.createElement('input');
    input.type = 'text';
    input.name = 'taxa-' + ul.children.length;
    input.value = taxonLabel;
    input.className = 'form-control d-none';
    li.appendChild(input);
    // Visible text: show the taxon label
    var span = document.createElement('span');
    span.textContent = taxonLabel;
    li.appendChild(span);
    // Remove button
    var btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-danger ms-2';
    btn.textContent = 'Remove';
    btn.onclick = function () { li.remove(); };
    li.appendChild(btn);
    ul.appendChild(li);
}

// Load taxon list in modal via AJAX
document.addEventListener('DOMContentLoaded', function() {
    var taxonModal = document.getElementById('taxonModal');
    taxonModal.addEventListener('show.bs.modal', function () {
        var taxonListDiv = document.getElementById('taxon-modal-list');
        taxonListDiv.innerHTML = '<div class="text-muted">Loading taxon list...</div>';
        fetch('/valueset?predicate=in_taxon') // This route should return JSON: [{id:..., label:...}, ...]
            .then(response => response.json())
            .then(data => {
                taxonListDiv.innerHTML = '';
                data.forEach(function(taxon) {
                    var btn = document.createElement('button');
                    btn.className = 'list-group-item list-group-item-action';
                    btn.textContent = taxon.label;
                    btn.onclick = function () {
                        addTaxonToList(taxon.id, taxon.label);
                        // Hide modal
                        var modalEl = document.getElementById('taxonModal');
                        var modal = bootstrap.Modal.getInstance(modalEl);
                        modal.hide();
                    };
                    taxonListDiv.appendChild(btn);
                });
            })
            .catch(() => {
                taxonListDiv.innerHTML = '<div class="text-danger">Error loading taxon list.</div>';
            });
    });
});