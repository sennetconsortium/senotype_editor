document.addEventListener("DOMContentLoaded", function () {
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
        //e.preventDefault();
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

        // Debug: Log all cloned inputs
        //Array.from(updateForm.querySelectorAll(".cloned-edit-input")).forEach(el => {
             //console.log("CLONED:", el.name, el.value);
         //});
        // Submit proceeds
    });
});