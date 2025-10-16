// FTU jsTree selection handling and list management

document.addEventListener('DOMContentLoaded', function() {
    // Initialize FTU jsTree and selection handler
    if (window.ftutree_data) {
        $('#ftu-tree').jstree({
            'core' : {
                'data' : ftutree_data
            }
        });
        $('#ftu-tree').on("changed.jstree", function (e, data) {
            if (data.selected.length) {
                var node = $('#ftu-tree').jstree(true).get_node(data.selected[0]);
                addFtuToList(node.id, node.text);
                document.activeElement.blur();
                // Try Bootstrap 5 way first
                var ftuModal = document.getElementById('ftuSearchModal');
                var bsModal = window.bootstrap && bootstrap.Modal.getInstance(ftuModal);
                if (bsModal) {
                    bsModal.hide();
                } else if (typeof $ !== 'undefined') {
                    // Fallback for Bootstrap 4
                    $('#ftuSearchModal').modal('hide');
                }
            }
        });
    }
});

// Add FTU node to list (similar to addValuesetToList)
function addFtuToList(ftuId, ftuLabel) {
    var ul = document.getElementById('ftu-list');
    if (!ul) return;

    // Remove blank items
    Array.from(ul.children).forEach(function(li) {
        var input = li.querySelector('input[type="hidden"]');
        var span = li.querySelector('.list-field-display');
        if (!input || !input.value || input.value.trim() === "" || (span && span.textContent.trim() === "")) {
            li.remove();
        }
    });

    // Prevent duplicates
    var alreadyPresent = Array.from(ul.querySelectorAll('input')).some(function(input) {
        return input.value === ftuId;
    });
    if (alreadyPresent) return;

    // Create new item
    var li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';
    var input = document.createElement('input');
    input.type = 'hidden';
    input.className = 'form-control w-100';
    input.value = ftuId;
    li.appendChild(input);
    var span = document.createElement('span');
    span.className = 'list-field-display';
    span.textContent = ftuLabel;
    li.appendChild(span);
    var btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-danger ms-2';
    btn.style = "width: 2.5em;"
    btn.textContent = '-';
    btn.type = 'button';
    btn.onclick = function () { li.remove(); reindexInputs('ftu-list', 'ftu'); };
    btn.title = 'Remove ' + ftuLabel + ' from FTU list';
    li.appendChild(btn);
    ul.appendChild(li);
    reindexInputs('ftu-list', 'ftu');
    handleInputChange();
}

// Reindex function stays the same
function reindexInputs(listId, fieldname) {
    var ul = document.getElementById(listId);
    var inputs = ul.querySelectorAll('input[type="text"], input[type="hidden"]');
    inputs.forEach(function(input, idx) {
        input.name = fieldname + '-' + idx;
    });
}