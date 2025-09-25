/*
Update script.
1. Collects state of inputs in edit form.
2. Writes state to hidden inputs.
3. Submits hidden inputs to update route.
*/
document.addEventListener("DOMContentLoaded", function () {

    // Spinner controls passed to the external setSpinner function (spinner.js)
    const spinnerId = 'update-spinner';
    const spinnerLabelId = 'update-spinner-label';

    const editForm = document.getElementById("edit_form");
    const updateForm = document.getElementById("update_form");
    const updateBtn = document.getElementById("update_btn");

    // List of list element IDs to track for changes (these are in edit_form, not modals)
    const listIds = [
        "taxon-list", "location-list", "celltype-list", "hallmark-list", "observable-list", "inducer-list",
        "assay-list", "citation-list", "origin-list", "dataset-list", "marker-list", "regmarker-list"
    ];

    // Helper to get current form state (including hidden).
    // Used to control the enabling of the Update button.
    function getFormState() {
        const elements = Array.from(editForm.elements).filter(el =>
            (el.tagName === "INPUT" || el.tagName === "SELECT" || el.tagName === "TEXTAREA")
            && editForm.contains(el)
        );
        const inputState = elements.map(el =>
            (el.type === "checkbox" || el.type === "radio") ? el.checked : el.value
        );
        // Add list state as stringified HTML
        const listState = listIds.map(id => {
            const ul = document.getElementById(id);
            return (ul && editForm.contains(ul)) ? ul.innerHTML : "";
        });
        return inputState.concat(listState);
    }

    // Store initial state
    const initialState = getFormState();

    function checkChanged() {
        const currentState = getFormState();
        const changed = currentState.some((val, i) => val !== initialState[i]);
        updateBtn.disabled = !changed;
    }

    // Listen for input/change events for fields
    editForm.addEventListener("input", checkChanged);
    editForm.addEventListener("change", checkChanged);

    // Listen for changes to the lists (add/remove)
    listIds.forEach(id => {
        const ul = document.getElementById(id);
        if (ul && editForm.contains(ul)) {
            const observer = new MutationObserver(checkChanged);
            observer.observe(ul, { childList: true, subtree: false });
        }
    });

    // On update_form submit, copy all edit_form inputs to update_form
    updateForm.addEventListener("submit", function (e) {

        // Show spinner
        console.log(update_btn.title);
        var spinText = update_btn.title.includes('Update') ? 'Updating' : 'Creating';
        setSpinner(spinnerId,spinnerLabelId,true,`${spinText}...`);

        // e.preventDefault();
        // Remove previously added hidden inputs
        Array.from(updateForm.querySelectorAll(".cloned-edit-input")).forEach(el => el.remove());

        // Clone all inputs/selects/textareas in edit_form (including hidden from lists)
        const elements = Array.from(editForm.elements).filter(el =>
            (el.tagName === "INPUT" || el.tagName === "SELECT" || el.tagName === "TEXTAREA") &&
            editForm.contains(el)
        );
        elements.forEach(el => {
            // For checkboxes/radios, only include checked
            if ((el.type === "checkbox" || el.type === "radio") && !el.checked) return;
            // Only clone if it has a name
            if (!el.name) return;
            const hidden = document.createElement("input");
            hidden.type = "hidden";
            hidden.name = el.name;
            hidden.value = el.value;
            hidden.className = "cloned-edit-input";
            updateForm.appendChild(hidden);
        });

        // Submit proceeds
    });
});