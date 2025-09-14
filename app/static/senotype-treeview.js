//Manages the function of the Senotype tree view.

document.addEventListener('DOMContentLoaded', function() {

  // Flag to distinguish between user-initiated selections in the
  // treeview and those initiated by events such as reloading of the form.
  // Prevents unwanted double-handling or form submissions.
  let programmaticSelection = true;

  // Populate the treeview with the JSON provided by Flask.
  // Maintain selection state.
  $('#senotype-tree').jstree({
    'core': { 'data': window.tree_data },
    'plugins': ['state']
  });

  // Show or hide spinner and label.
  function setSpinner(visible, labelText) {
    const spinner = document.getElementById('senotype-spinner');
    const spinnerLabel = document.getElementById('senotype-spinner-label');
    if (spinner) spinner.style.display = visible ? 'inline-block' : 'none';
    if (spinnerLabel) {
      spinnerLabel.style.display = visible ? 'inline-block' : 'none';
      if (visible && labelText) {
        spinnerLabel.textContent = labelText;
      }
    }
  }

  // On initial load, hide spinner.
  $(function() {
    setSpinner(false);
  });

  // On jstree ready (form reload), restore selection to
  // the last selected node (window.selected_node_id), with a default
  // of the root node. Hide the spinner.
  $('#senotype-tree').on('ready.jstree', function(e, data) {
    let selectedId = window.selected_node_id || (window.tree_data[0] && window.tree_data[0].id);
    if (!selectedId) {
      setSpinner(false);
      programmaticSelection = false;
      return;
    }

    programmaticSelection = true;
    data.instance.deselect_all();
    data.instance.select_node(selectedId);

    setTimeout(() => {
      let nodeObj = data.instance.get_node(selectedId);
      let icon = nodeObj && nodeObj.icon;
      let isFile = icon && (Array.isArray(icon) ? icon.includes('jstree-file') : icon === 'jstree-file');
      let nodeDom = data.instance.get_node(selectedId, true);
      let editable = nodeDom && nodeDom.find('.jstree-anchor').hasClass('editable');

      // Patch: also update new-version-btn on initial load
      updateNewVersionBtnState(nodeObj, data.instance);

      setSpinner(false);

      programmaticSelection = false;
    }, 10);
  });

  // Utility to determine if any nodes (by id array) are editable
  function anyEditable(nodeIds, treeInstance) {
    if (!Array.isArray(nodeIds)) return false;
    for (let id of nodeIds) {
      let nodeDom = treeInstance.get_node(id, true);
      if (nodeDom && nodeDom.find('.jstree-anchor').hasClass('editable')) {
        return true;
      }
    }
    return false;
  }

  function updateNewVersionBtnState(nodeObj, treeInstance) {
    let newVersionBtn = document.getElementById('new-version-btn');
    if (!newVersionBtn || !nodeObj) return;

    // 1. If node id is "Senotype", always disable
    if (nodeObj.id === "Senotype") {
        newVersionBtn.disabled = true;
        return;
    }

    // 2. If node id contains "rootwrap"
    if (nodeObj.id && nodeObj.id.includes("rootwrap")) {
        // If none of its children are editable, enable, else disable
        if (Array.isArray(nodeObj.children) && !anyEditable(nodeObj.children, treeInstance)) {
            newVersionBtn.disabled = false;
        } else {
            newVersionBtn.disabled = true;
        }
        return;
    }

    // 3. Otherwise: enable only if neither the node nor its siblings are editable
    let nodeDom = treeInstance.get_node(nodeObj.id, true);
    let nodeIsEditable = nodeDom && nodeDom.find('.jstree-anchor').hasClass('editable');

    let parentId = nodeObj.parent;
    let siblings = [];
    if (parentId && parentId !== "#") {
        let parentNode = treeInstance.get_node(parentId);
        if (parentNode && parentNode.children) {
        siblings = parentNode.children.filter(id => id !== nodeObj.id);
        }
    }

    let siblingsEditable = anyEditable(siblings, treeInstance);

    if (!nodeIsEditable && !siblingsEditable) {
        newVersionBtn.disabled = false;
    } else {
        newVersionBtn.disabled = true;
    }
  }

  // On user select, handle state and submit if needed (with spinner)
  $('#senotype-tree').on('select_node.jstree', function(e, data) {
    let nodeObj = data.node;
    let icon = nodeObj.icon;
    let isFile = icon && (Array.isArray(icon) ? icon.includes('jstree-file') : icon === 'jstree-file');
    let treeInstance = $('#senotype-tree').jstree(true);
    let nodeDom = treeInstance.get_node(data.node.id, true);
    let editable = nodeDom && nodeDom.find('.jstree-anchor').hasClass('editable');

    // Patch: update new-version-btn state on every selection
    updateNewVersionBtnState(nodeObj, treeInstance);

    if (programmaticSelection) {
      programmaticSelection = false;
      return; // skip programmatic select
    }

    if (!isFile) {
      // Not a file. Do nothing. Hide spinner just in case
      setSpinner(false);
      return;
    }
    // File node: always submit
    let hidden = document.getElementById('selected_node_id');
    if (hidden) hidden.value = data.node.id;

    setSpinner(true, `Loading ${data.node.id}...`);
    document.getElementById('edit_form').submit();
  });

});