// Disables inputs.
// Most are disabled conditionally based on whether the selected senotype version
// has been published.

document.addEventListener('DOMContentLoaded', function() {
  var doiValue = window.senotype_doi_value;
  var form = document.getElementById('edit_form');
  if (!form) return;

  // Form elements to enable or disable.
  var elements = form.querySelectorAll('input, span, textarea, button');

  // Update button.
  var update_btn = document.getElementById('update_btn');

  // Loop through the main form elements.
  elements.forEach(function(el) {
    // Don't disable the jsTree's hidden input for selection
    if (el.id === 'selected_node_id') return;
    readonly = ['senotypeid'];
    if (readonly.includes(el.id)) {
        el.disabled = true;
        el.style.backgroundColor = '#e5e5e5';
        return;
    }
    if (doiValue) {
      if (el.tagName === "SPAN") {
        // visually indicate disabled for span
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

  update_btn.disabled = doiValue;


});