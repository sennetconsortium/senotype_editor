/*
Functions for management of field lists that are populated via valuesets in the
senlib database.

A Jinja template macro (_valueset_modal_macro.html) builds a modal component with
a list that this script populates. The list contains valueset elements. When
the user selects a value in a list, the script adds a corresponding list element.
*/

document.addEventListener('DOMContentLoaded', function() {
    // Build the content of the modal sections associated with valueset-based assertions.
    initValuesetModal('in_taxon', 'taxon');
    //initValuesetModal('located_in', 'location');
    initValuesetModal('has_microenvironment', 'microenvironment');
    initValuesetModal('has_cell_type','celltype');
    initValuesetModal('has_hallmark', 'hallmark');
    initValuesetModal('has_inducer', 'inducer');
    initValuesetModal('has_assay', 'assay');
    initValuesetModal('has_sex', 'sex');
});

// Remove item from list
function removeValue(btn) {
    btn.parentNode.remove();
}

// Add the specified valueset item, which corresponds to the specified
// assertion predicate, to the specified list in edit.html.
function addValuesetToList(fieldname, valuesetId, valuesetLabel) {

    var ul = document.getElementById(fieldname + '-list');

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


    // Check for duplicates by value
    var alreadyPresent = Array.from(ul.querySelectorAll('input')).some(function(input) {
        return input.value === valuesetId;
    });

    if (alreadyPresent) return; // Do not add duplicate

    // Create new list element.
    var li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';
    // Hidden input for the POST submission via the Update button.
    var input = document.createElement('input');
    input.type = 'hidden';
    input.className = 'form-control w-100';// d-none';
    input.value = valuesetId;
    console.log(input.value);
    li.appendChild(input);
    // Show label in list.
    var span = document.createElement('span');
    span.className = 'list-field-display';
    span.textContent = valuesetLabel;
    li.appendChild(span);
    // Remove button for the new item.
    var btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-danger ms-2';
    btn.style = "width: 2.5em;"
    btn.textContent = '-';
    btn.type = 'button';
    btn.onclick = function () { li.remove(); reindexInputs(fieldname + '-list', fieldname); };
    btn.title = 'Remove ' + valuesetLabel + ' from ' + fieldname + ' list';
    li.appendChild(btn);
    ul.appendChild(li);
    reindexInputs(fieldname + '-list', fieldname);

    // Global function in input-changes.js
    handleInputChange();
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
                        // Move focus out of the modal before hiding.
                        // This avoids triggering prevents accessibility errors about focused
                        // elements inside aria-hidden containers. (Bootstrap apparently inserts
                        // aria-hidden statements.)
                        document.activeElement.blur();

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

// Reindex all inputs after add/remove
function reindexInputs(listId, fieldname) {
    var ul = document.getElementById(listId);
    var inputs = ul.querySelectorAll('input[type="text"], input[type="hidden"]');
    inputs.forEach(function(input, idx) {
        input.name = fieldname + '-' + idx;
    });
}