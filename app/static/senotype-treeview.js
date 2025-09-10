/* Controls the senotype jstree.

1. Manages selection and focus.
2. Reacts programmatically to selection changes (for example, selecting a root node on load),
   and visually highlights the focused node. Distinguishes between user actions and
   events related to reloading the form, preventing infinite loops.
3. The jstree contains both nodes that organize the senotype hierarchy and those that
   correspond to senotype admission JSONs.
   When the user selects a node that corresponds a senotype admission JSON,
   the script:
   - updates a hidden field
   - submits the edit form
   - shows a spinner
*/

document.addEventListener('DOMContentLoaded', function() {

  // Flag to distinguish between user selections and programmatic selections of nodes.
  let programmaticSelection = true;

  // Initialize the jstree, using data provided from Flask/WTForms.
  // Uses the state plugin to keep track of jstree state.
  $('#senotype-tree').jstree({
    'core': { 'data': window.tree_data },
    'plugins': ['state']
  });

  // Identify the "Senotype" root node for the jstree.
  function getRootId() {
    if (window.tree_data && window.tree_data.length) {
      return window.tree_data[0].id;
    }
    return null;
  }

  // Manages a custom CSS class (focused-node) for visual feedback.
  function updateFocusedNode(nodeId) {
    $('#senotype-tree .jstree-anchor.focused-node').removeClass('focused-node');
    if (nodeId) {
      let nodeDom = $('#senotype-tree').jstree(true).get_node(nodeId, true);
      if (nodeDom && nodeDom.length) {
        nodeDom.find('.jstree-anchor').addClass('focused-node');
      }
    }
  }

  $('#senotype-tree').on('ready.jstree', function(e, data) {
    let selectedId = window.selected_node_id || '';
    let rootId = getRootId();

    if (!selectedId && rootId) {
      selectedId = rootId;
    }
    if (selectedId) {
      programmaticSelection = true;
      data.instance.deselect_all();
      data.instance.select_node(selectedId);
      setTimeout(() => updateFocusedNode(selectedId), 10);
    } else {
      // If jsTree's state plugin restored a selection, highlight that
      let sel = data.instance.get_selected();
      if (sel && sel.length) setTimeout(() => updateFocusedNode(sel[0]), 10);
    }
    setTimeout(() => { programmaticSelection = false; }, 0);
  });

  $('#senotype-tree').on('select_node.jstree', function(e, data) {
    if (programmaticSelection) return;
    updateFocusedNode(data.node.id);

    // Only submit if selected node's icon is 'jstree-file'
    let icon = data.node.icon;
    if (Array.isArray(icon) ? icon.includes('jstree-file') : icon === 'jstree-file') {
      document.getElementById('selected_node_id').value = data.node.id;

      const spinner = document.getElementById('senotype-spinner');
      const spinnerLabel = document.getElementById('senotype-spinner-label');
      if (spinner) spinner.style.display = 'inline-block';
      if (spinnerLabel) {
        spinnerLabel.textContent = `Loading ${data.node.id}...`;
        spinnerLabel.style.display = 'inline-block';
      }
      const updateBtn = document.getElementById('update_btn');
      if (updateBtn) updateBtn.disabled = true;
      document.getElementById('edit_form').submit();
    }
  });

  $('#senotype-tree').on('hover_node.jstree', function(e, data) {
    updateFocusedNode(data.node.id);
  });

  $('#senotype-tree').on('dehover_node.jstree', function(e, data) {
    updateFocusedNode(null);
  });
});