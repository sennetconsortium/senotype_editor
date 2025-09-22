/*
Respond to changes in inputs:

1. Enable the update button only if there is a change in input
   or
   if there was an error during update/create.
2. Turn off display of any error messages.

*/

document.addEventListener('DOMContentLoaded', function() {
  const editForm = document.getElementById('edit_form');
  const updateBtn = document.getElementById('update_btn');

  // Store initial form data as serialized string
  let initialData = new FormData(editForm);
  let initialSerialized = serializeFormData(initialData);

  // Listen for any input or change event in the edit form.
  // Note that addEventListener events are not triggered for disabled inputs, such as
  // the DOI. The doi-modal.js script will add a custom event dispatch to trigger
  // a change event.
  editForm.addEventListener('input', handleInputChange);
  editForm.addEventListener('change', handleInputChange);

  // Handles the case of the edit form being loaded in response to validation
  // errors from an attempted create/update.
  checkForEnabled();

 function handleInputChange() {
    // Remove all error classes (text-danger, text-bg-danger)
    document.querySelectorAll('div.text-danger, div.text-bg-danger').forEach(div => {
      // Option 1: Hide the error div
      div.style.display = 'none';
    });

    checkForEnabled();
  }
  // Function to check for changes to inputs.
  function checkForChange() {
    const currentData = new FormData(editForm);
    const currentSerialized = serializeFormData(currentData);
    return currentSerialized !== initialSerialized;
  }

  // Function to check for evidence of a validation error.
  function checkForErrors() {
    // Select all div elements with the class "text-danger"
    const errorDivs = document.querySelectorAll('div.text-danger');
    // Return true if any such div exists
    return errorDivs.length > 0;
  }

  // This function controls enabling/disabling the update button
  function checkForEnabled() {
    const hasChange = checkForChange();
    const hasError = checkForErrors();
    updateBtn.disabled = !(hasChange || hasError);
  }

  // Serialize form data for detection of changes.
  function serializeFormData(formData) {
    return Array.from(formData.entries())
      .map(([key, value]) => encodeURIComponent(key) + '=' + encodeURIComponent(value))
      .sort()
      .join('&');
  }

});