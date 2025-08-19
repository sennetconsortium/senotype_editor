// Functions for management of field lists that are populated via the Senlib
// valuesets.

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the mappings between assertion predicates and fields in
    // edit.html
    initValuesetModal('in_taxon', 'taxa');
    initValuesetModal('located_in', 'location');
    initValuesetModal('has_cell_type','celltype');
    initValuesetModal('has_hallmark', 'hallmark');
    initValuesetModal('has_molecular_observable', 'observable');
    initValuesetModal('has_inducer', 'inducer');
    initValuesetModal('has_assay', 'assay');
});

// Remove item from list
function removeValue(btn) {
    btn.parentNode.remove();
}

// Add the specified valueset item, which corresponds to the specified
// assertion predicate, to the specified list in edit.html.
function addValuesetToList(fieldname, valuesetId, valuesetLabel) {
    // The name of a list of field values in edit.html concatenates the name
    // of the field and -list.
    var ul = document.getElementById(fieldname + '-list');

    // Check if valuesetId is already present in any hidden input in the list
    var alreadyPresent = false;
    Array.from(ul.getElementsByTagName('input')).forEach(function(input) {
        if (input.value === valuesetId || input.value === valuesetLabel) {
            alreadyPresent = true;
        }
    });
    if (alreadyPresent) return; // Do not add duplicate

    var li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';
    // Hidden input for WTForms submission
    var input = document.createElement('input');
    input.type = 'text';
    input.name = fieldname + '-' + ul.children.length;
    input.value = valuesetLabel;
    input.className = 'form-control d-none';
    li.appendChild(input);
    // Visible text: show the label
    var span = document.createElement('span');
    span.textContent = valuesetLabel;
    li.appendChild(span);
    // Remove button
    var btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-danger ms-2';
    btn.textContent = '-';
    btn.onclick = function () { li.remove(); };
    li.appendChild(btn);
    ul.appendChild(li);
}

// Load valueset list in modal via AJAX, parameterized by assertion predicate and field name
function initValuesetModal(predicate, fieldname) {
    var modalId = fieldname + 'Modal';
    var listDivId = fieldname + '-modal-list';
    var modal = document.getElementById(modalId);
    if (!modal) return;
    modal.addEventListener('show.bs.modal', function () {
        var valuesetListDiv = document.getElementById(listDivId);
        valuesetListDiv.innerHTML = '<div class="text-muted">Loading ' + fieldname + ' list...</div>';
        fetch('/valueset?predicate=' + encodeURIComponent(predicate)) // Flask route should return JSON [{id,label},...]
            .then(response => response.json())
            .then(data => {
                valuesetListDiv.innerHTML = '';
                data.forEach(function(item) {
                    var btn = document.createElement('button');
                    btn.className = 'list-group-item list-group-item-action';
                    btn.textContent = item.label;
                    btn.onclick = function () {
                        addValuesetToList(fieldname, item.id, item.label);
                        // Hide modal
                        var modalEl = document.getElementById(modalId);
                        var bsModal = bootstrap.Modal.getInstance(modalEl);
                        bsModal.hide();
                    };
                    valuesetListDiv.appendChild(btn);
                });
            })
            .catch(() => {
                valuesetListDiv.innerHTML = '<div class="text-danger">Error loading ' + predicate + ' list.</div>';
            });
    });
}