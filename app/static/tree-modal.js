/*
    Manages the function of the modal form used to select a FTU path (organ,
    FTU, FTU part) for a senotype.
    Uses a jstree control to display the full 2D FTU hierarchy.
*/

document.addEventListener('DOMContentLoaded', function() {
    var modal = document.getElementById('{{ modal_id }}');
    if (modal) {
        modal.addEventListener('show.bs.modal', function () {
            // Destroy any existing instance to avoid double-init
            if ($.jstree.reference('#{{ field_name }}-tree')) {
                $('#{{ field_name }}-tree').jstree('destroy');
            }
            $('#{{ field_name }}-tree').jstree({
                'core' : {
                    'data' : window.{{ field_name }}_tree_data
                }
            });

            $('#{{ field_name }}-tree').off("changed.jstree").on("changed.jstree", function (e, data) {
                if (data.selected.length) {
                    var node = $('#{{ field_name }}-tree').jstree(true).get_node(data.selected[0]);
                    addTreeValueToList('{{ field_name }}', node.id, node.text);

                    // Accessibility: move focus before hiding modal
                    document.activeElement.blur();
                    // Hide the modal
                    var bsModal = bootstrap.Modal.getInstance(modal);
                    if (bsModal) bsModal.hide();
                }
            });
        });
    }
});

// Add selected jsTree node to list
function addTreeValueToList(fieldname, nodeId, nodeLabel) {
    var ul = document.getElementById(fieldname + '-list');
    if (!ul) return;

    // Prevent duplicates
    var alreadyPresent = Array.from(ul.querySelectorAll('input[type="hidden"]')).some(function(input) {
        return input.value === nodeId;
    });
    if (alreadyPresent) return;

    // Create new item
    var li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center w-100';
    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = fieldname + '-' + ul.children.length;
    input.value = nodeId;
    li.appendChild(input);
    var span = document.createElement('span');
    span.className = 'list-field-display';
    span.textContent = nodeLabel;
    li.appendChild(span);
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-sm btn-danger ms-2';
    btn.style = "width: 2.5em;";
    btn.textContent = '-';
    btn.onclick = function () {
        li.remove();
        reindexInputs(fieldname + '-list', fieldname);
    };
    btn.title = 'Remove ' + nodeLabel + ' from ' + fieldname + ' list';
    li.appendChild(btn);
    ul.appendChild(li);
    reindexInputs(fieldname + '-list', fieldname);

    // If you have a global input-change handler, call here
    if (typeof handleInputChange === "function") handleInputChange();
}

// Reindex all inputs after add/remove
function reindexInputs(listId, fieldname) {
    var ul = document.getElementById(listId);
    var inputs = ul.querySelectorAll('input[type="hidden"], input[type="text"]');
    inputs.forEach(function(input, idx) {
        input.name = fieldname + '-' + idx;
    });
}