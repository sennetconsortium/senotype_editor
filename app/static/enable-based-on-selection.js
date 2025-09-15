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

    //.. check for an editable class on the selected node. (The class is set by Flask.)
    if (nodeid) {
      var nodeDom = tree.get_node(nodeid, true);
      if (nodeDom && nodeDom.length) {
        isEditable = nodeDom.find('.jstree-anchor').hasClass('editable');
      }
    }

    // Enable or disable controls.
    var form = document.getElementById('edit_form');
    if (!form) return;
    var elements = form.querySelectorAll('input, span, textarea, button');
    var update_btn = document.getElementById('update_btn');

    elements.forEach(function(el) {

      // Never disable the senotype treeview.
      if (el.id === 'selected_node_id') return;

      // Readonly controls are always disabled.
      var readonly = ['senotypeid','doi'];
      if (readonly.includes(el.id)) {
        el.disabled = true;
        el.style.backgroundColor = '#e5e5e5';
        return;
      }

      if (!isEditable) {
        if (el.tagName === "SPAN") {
          el.style.pointerEvents = 'none';
          el.style.opacity = 0.6;
          el.style.backgroundColor = '#e5e5e5';
        } else if (el.tagName === "INPUT" && el.type === "text") {
          el.disabled = true;
          el.style.backgroundColor = '#e5e5e5';
        } else if (el.tagName === "TEXTAREA") {
          el.disabled = true;
          el.style.backgroundColor = '#e5e5e5';
        } else if (el.tagName === "BUTTON") {
          el.disabled = true;
        }
      } else {
        if (el.tagName === "SPAN") {
          el.style.pointerEvents = '';
          el.style.opacity = '';
          el.style.backgroundColor = '';
        } else if (el.tagName === "INPUT" && el.type === "text") {
          el.disabled = false;
          el.style.backgroundColor = 'white';
        } else if (el.tagName === "TEXTAREA") {
          el.disabled = false;
          el.style.backgroundColor = 'white';
        } else if (el.tagName === "BUTTON") {
          el.disabled = false;
        }
      }
    });

    /* Update button:
       Label should be "Create" if "new" was selected, elss "Update".
    */
    if(update_btn) {
        update_btn.textContent = (nodeid === "new") ? "Create" : "Update";
    }


  });
});