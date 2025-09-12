document.addEventListener('DOMContentLoaded', function() {
  let programmaticSelection = true;

  $('#senotype-tree').jstree({
    'core': { 'data': window.tree_data },
    'plugins': ['state']
  });

  // Show or hide spinner and label
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

  // On initial load hide spinner
  $(function() {
    setSpinner(false);
  });

  // On jstree ready (form reload), hide spinner
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

      setSpinner(false);

      programmaticSelection = false;
    }, 10);
  });

  // On user select, handle state and submit if needed (with spinner)
  $('#senotype-tree').on('select_node.jstree', function(e, data) {
    let nodeObj = data.node;
    let icon = nodeObj.icon;
    let isFile = icon && (Array.isArray(icon) ? icon.includes('jstree-file') : icon === 'jstree-file');
    let nodeDom = $('#senotype-tree').jstree(true).get_node(data.node.id, true);
    let editable = nodeDom && nodeDom.find('.jstree-anchor').hasClass('editable');

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