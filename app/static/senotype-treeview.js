document.addEventListener('DOMContentLoaded', function() {
  let programmaticSelection = true;

  $('#senotype-tree').jstree({
    'core': {
      'data': window.tree_data
    },
    'plugins': ['state']
  });

  // Get root node ID (first node in array)
  function getRootId() {
    if (window.tree_data && window.tree_data.length) {
      return window.tree_data[0].id;
    }
    return null;
  }

  $('#senotype-tree').on('ready.jstree', function(e, data) {
    let selectedId = window.selected_node_id || '';
    let rootId = getRootId();

    // If nothing is selected, select root (decorative)
    if (!selectedId && rootId) {
      selectedId = rootId;
    }
    if (selectedId) {
      programmaticSelection = true;
      data.instance.deselect_all();
      data.instance.select_node(selectedId);
    }
    setTimeout(() => { programmaticSelection = false; }, 0);
  });

  $('#senotype-tree').on('select_node.jstree', function(e, data) {
    if (programmaticSelection) return;

    // Only submit if selected node's icon is 'jstree-file'
    // Handles both string (single icon) and array (multiple icons)
    let icon = data.node.icon;
    if (Array.isArray(icon) ? icon.includes('jstree-file') : icon === 'jstree-file') {
      document.getElementById('selected_node_id').value = data.node.id;

      // Spinner logic
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
    // Otherwise, do not submit (folders, decorative root, etc)
  });
});