//Manages the function of the Senotype tree view.

document.addEventListener('DOMContentLoaded', function() {

  // Spinner controls passed to the external setSpinner function (spinner.js)
  const spinnerId = 'senotype-spinner';
  const spinnerLabelId = 'senotype-spinner-label';

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

  // On initial load, hide spinner.
  $(function() {
    setSpinner(spinnerId,spinnerLabelId,false);

  });

  // On jstree ready (form reload), restore selection to
  // the last selected node (window.selected_node_id), with a default
  // of the root node. Hide the spinner.
  $('#senotype-tree').on('ready.jstree', function(e, data) {
    let selectedId = window.selected_node_id || (window.tree_data[0] && window.tree_data[0].id);
    if (!selectedId) {
      setSpinner(spinnerId,spinnerLabelId,false);
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

      // Also update new-version-btn on initial load
      updateNewVersionBtnState(nodeObj, data.instance);
      setSpinner(spinnerId,spinnerLabelId,false);

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

  // Function to check whether to allow the creation of a new version
  // of a senotype.
  function updateNewVersionBtnState(nodeObj, treeInstance) {
    let newVersionBtn = document.getElementById('new-version-btn');
    if (!newVersionBtn || !nodeObj) return;

    // 1. If node id is "Senotype" or "new, always disable
    var alwaysDisable = ["Senotype", "new"]
    if (alwaysDisable.includes(nodeObj.id)) {
        newVersionBtn.disabled = true;
        return;
    }

    // 2. If node id contains "group", then enable only if the first child is not editable
    if (nodeObj.id && nodeObj.id.includes("group")) {
        if (Array.isArray(nodeObj.children) && nodeObj.children.length > 0) {
                let firstChildId = nodeObj.children[0];
                let firstChildDom = treeInstance.get_node(firstChildId, true);
                let firstChildEditable = firstChildDom && firstChildDom.find('.jstree-anchor').hasClass('editable');
                newVersionBtn.disabled = !!firstChildEditable;
                console.log('firstChildId= ' + firstChildId);
                console.log('firstChildEditable = ' + firstChildEditable);
            } else {
            // If no children, enable
            newVersionBtn.disabled = false;
        }
        return;
    }

    // 3. Otherwise: enable only if the first node in the branch path is not editable
    // Find nearest ancestor whose id contains "group"
    let currentNode = nodeObj;
    let groupNode = null;
    while (currentNode && currentNode.parent && currentNode.parent !== "#") {
        let parentNode = treeInstance.get_node(currentNode.parent);
        if (parentNode && parentNode.id && parentNode.id.includes("group")) {
            groupNode = parentNode;
            break;
        }
        currentNode = parentNode;
    }

    if (groupNode && Array.isArray(groupNode.children) && groupNode.children.length > 0) {
        let firstChildId = groupNode.children[0];
        let firstChildDom = treeInstance.get_node(firstChildId, true);
        let firstChildEditable = firstChildDom && firstChildDom.find('.jstree-anchor').hasClass('editable');
        newVersionBtn.disabled = !!firstChildEditable;
    } else {
        // If not under a group node, enable
        newVersionBtn.disabled = false;
    }

    //debug
    newVersionBtn.disabled = false;
 }

  // On user select, handle state and submit if needed (with spinner)
  $('#senotype-tree').on('select_node.jstree', function(e, data) {
    let nodeObj = data.node;
    let icon = nodeObj.icon;
    let isFile = icon && (Array.isArray(icon) ? icon.includes('jstree-file') : icon === 'jstree-file');
    let treeInstance = $('#senotype-tree').jstree(true);
    let nodeDom = treeInstance.get_node(data.node.id, true);
    let editable = nodeDom && nodeDom.find('.jstree-anchor').hasClass('editable');

    // Update new-version-btn state on every selection
    updateNewVersionBtnState(nodeObj, treeInstance);

    if (programmaticSelection) {
      programmaticSelection = false;
      return; // skip programmatic select
    }

    if (!isFile) {
      // Not a file. Do nothing. Hide spinner just in case
      setSpinner(spinnerId,spinnerLabelId,false);

      return;
    }
    // File node: always submit
    let hidden = document.getElementById('selected_node_id');
    if (hidden) hidden.value = data.node.id;

    setSpinner(spinnerId,spinnerLabelId,true,`Loading ${data.node.id}...`);
    document.getElementById('edit_form').submit();




  });

  // Function that identifies the first node in a tree path, corresponding to the
  // latest version of a senotype.
  function getFirstBranchNodeId(selectedNodeId, treeInstance) {
    let currentNode = treeInstance.get_node(selectedNodeId);
    let parentNode = null;
    let ancestor = currentNode;

    // Climb up until we reach the node whose parent is rootwrap/group or "#"
    while (ancestor.parent && ancestor.parent !== "#") {
        parentNode = treeInstance.get_node(ancestor.parent);
        // If parent is rootwrap/group or "#", ancestor is the first in the branch
        if (
            parentNode.id.includes("rootwrap") ||
            parentNode.id.includes("group") ||
            parentNode.parent === "#"
        ) {
            break;
        }
        ancestor = parentNode;
    }
    return ancestor.id;
  }

  // Handle new-version-btn click:
  const newVersionBtn = document.getElementById('new-version-btn');
  if (newVersionBtn) {
    newVersionBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const treeInstance = $('#senotype-tree').jstree(true);
        if (!window.selected_node_id || !treeInstance) return;

        // Find first node in the branch path
        const firstBranchNodeId = getFirstBranchNodeId(window.selected_node_id, treeInstance);

        // Append '-newversion' and set hidden field
        const newNodeId = firstBranchNodeId + '_newversion';
        const hidden = document.getElementById('selected_node_id');
        if (hidden) hidden.value = newNodeId;

        setSpinner(spinnerId,spinnerLabelId,true,`Creating new version for ${firstBranchNodeId}...`);


        // Submit to /version route
        const form = document.getElementById('edit_form');
        if (form) {
            form.action = '/version';
            form.submit();
        }
    });
  }
});