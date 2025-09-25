// Show or hide spinner and label.
  function setSpinner(spinnerId,spinnerLabelId,visible,labelText) {
    const spinner = document.getElementById(spinnerId);
    const spinnerLabel = document.getElementById(spinnerLabelId);
    if (spinner) spinner.style.display = visible ? 'inline-block' : 'none';
    if (spinnerLabel) {
      spinnerLabel.style.display = visible ? 'inline-block' : 'none';
      if (visible && labelText) {
        spinnerLabel.textContent = labelText;
      }
    }
  }