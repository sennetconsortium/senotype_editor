// Enable the update button only if there is a change in input
// or
// if there was an error during update/create.
console.log('enable-update.js loaded after redirect');
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOMContentLoaded');
  const editForm = document.getElementById('edit_form');
  const updateBtn = document.getElementById('update_btn');

  // Store initial form data as serialized string
  let initialData = new FormData(editForm);
  let initialSerialized = serializeFormData(initialData);

  // Listen for any input, change, or textarea event in the edit form
  editForm.addEventListener('input', checkForEnabled);
  editForm.addEventListener('change', checkForEnabled);

  checkForEnabled();

  function checkForChange() {
    console.log('checkForChange');
    const currentData = new FormData(editForm);
    const currentSerialized = serializeFormData(currentData);
    return currentSerialized !== initialSerialized;
  }

  function checkForErrors() {
        console.log('checkForErrors');
        // Select all div elements with the class "text-danger"
        const errorDivs = document.querySelectorAll('div.text-danger');
        console.log(errorDivs);
        // Return true if any such div exists
        return errorDivs.length > 0;
  }

    // This function controls enabling/disabling the update button
  function checkForEnabled() {
    console.log('checkForEnabled');
    const hasChange = checkForChange();
    const hasError = checkForErrors();
    console.log(hasError);
    updateBtn.disabled = !(hasChange || hasError);
  }

  function serializeFormData(formData) {
    console.log('serializeFormData');
    return Array.from(formData.entries())
      .map(([key, value]) => encodeURIComponent(key) + '=' + encodeURIComponent(value))
      .sort()
      .join('&');
  }
});