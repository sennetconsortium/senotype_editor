/*
Script that enables or disables inputs in the form based on whether the senotype selected
in the treeview is editable.
*/

$(function() {
  // When the tree is ready...
  $('#senotype-tree').on('ready.jstree', function(e, data) {
    var nodeid = window.selected_node_id;
    var tree = $('#senotype-tree').jstree(true);
    var isEditable = false;

    //... check for editable and authorized classes on the selected node.
    // (The classes are set by Flask.)
    if (nodeid) {
      var nodeDom = tree.get_node(nodeid, true);
      if (nodeDom && nodeDom.length) {
        isEditable = nodeDom.find('.jstree-anchor').hasClass('editable');
        isAuthorized = nodeDom.find('.jstree-anchor').hasClass('authorized');
      }
    }

    // Enable or disable controls.
    var form = document.getElementById('edit_form');
    if (!form) return;
    var elements = form.querySelectorAll('input, span, textarea, button, li');
    var update_btn = document.getElementById('update_btn');
    const disableColor = '#e9ecef';

    elements.forEach(function(el) {

        // Do not change the senotype jstree, the marker accordion, or the hidden
        // selected node input.

        // Collect all jsTree node and anchor IDs.
        var jsTreeElements = document.querySelectorAll('.jstree-node, .jstree-anchor');
        var leaveAlone = ['btn-accordion', 'selected_node_id'];
        // Add all jsTree node and anchor IDs to leaveAlone
        jsTreeElements.forEach(function(el) {
            if (el.id) {
                leaveAlone.push(el.id);
            }
        });
        if (leaveAlone.includes(el.id)) return;

        // Readonly controls are always disabled.
        var readonly = ['senotypeid','submitterfirst',
        'submitterlast','submitteremail','ageunit'];
        if (readonly.includes(el.id)) {
            el.disabled = true;
            el.style.backgroundColor = disableColor;
            return;
        }

        // Buttons that always display.
        var alwaysVisible = ['update_btn', 'new-version-btn'];

        // Input types
        var inputTypes = ['text','number'];

        // External inputs are indicated visually with a light blue background.
        var external = ['citation-list','origin-list','dataset-list','doi']
        var enabledColor = (external.includes(el.id)) ? '#EBF6F9' : 'white';

        // For all other inputs, enabled and possibly visibility are
        // determined by the selected node.
        if (isEditable && isAuthorized) {
            // Enabled and visible.
            if (el.tagName === 'SPAN') {
                el.style.pointerEvents = '';
                el.style.opacity = '';
                el.style.backgroundColor = '';
                el.style.visibility = 'display';
            } else if (el.tagName === 'INPUT' && inputTypes.includes(el.type)) {
                el.disabled = false;
                el.style.backgroundColor = enabledColor;
            } else if (el.tagName === 'TEXTAREA') {
                el.disabled = (el.id === "doi");
                el.style.backgroundColor = enabledColor;
            } else if (el.tagName === 'BUTTON') {
                el.disabled = false;
                el.style.display = 'block';
            } else if (el.tagName === 'LI') {
                el.style.background = enabledColor;
            }

        } else {

            // Disabled.
            // Add and remove buttons hidden.
            if (el.tagName === 'SPAN') {
                el.style.pointerEvents = 'none';
                el.style.opacity = 0.6;
                el.style.backgroundColor = disableColor;
                if (el.id.includes('link')) {
                    el.style.visibility = 'hidden';
                }
            } else if (el.tagName === 'INPUT' && inputTypes.includes(el.type)) {
                el.disabled = true;
                el.style.backgroundColor = disableColor;
            } else if (el.tagName === 'TEXTAREA') {
                el.disabled = true;
                el.style.backgroundColor = disableColor;
            } else if (el.tagName === 'BUTTON') {
                el.disabled = true;
                if (alwaysVisible.includes(el.id)) {
                    el.style.display = 'block';
                } else {
                    el.style.display = 'none';
                }
            } else if (el.tagName === 'LI') {
                el.style.background = disableColor;
            }
        }
    });

    // Update button label should be "Create" if "new" was selected, else "Update".
    if(update_btn) {
        var action = (nodeid === 'new') ? 'Create' : 'Update';
        update_btn.textContent = action;
        update_btn.title = action + ' ' + nodeid;
        update_btn.setAttribute('aria-label', action + ' ' + nodeid);
    }

  });
});