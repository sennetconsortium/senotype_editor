document.addEventListener("DOMContentLoaded", function () {
    const editForm = document.getElementById("edit_form");
    const updateForm = document.getElementById("update_form");
    const updateBtn = document.getElementById("update_btn");

    // On update_form submit, copy non-modal edit_form inputs to update_form
    updateForm.addEventListener("submit", function (e) {
        // Remove previously added hidden inputs
        Array.from(updateForm.querySelectorAll(".cloned-edit-input")).forEach(el => el.remove());

        // Get all inputs/selects/textareas in edit_form (excluding modal forms)
        // Only consider elements that are actually in editForm (not modals)
        const elements = Array.from(editForm.elements).filter(el =>
            (el.tagName === "INPUT" || el.tagName === "SELECT" || el.tagName === "TEXTAREA")
            && el.type !== "hidden"
            && editForm.contains(el)
        );
        elements.forEach(el => {
            let value;
            if (el.type === "checkbox" || el.type === "radio") {
                if (!el.checked) return; // skip unchecked
                value = el.value;
            } else {
                value = el.value;
            }
            // Create a hidden input to clone the value
            const hidden = document.createElement("input");
            hidden.type = "hidden";
            hidden.name = el.name;
            hidden.value = value;
            hidden.className = "cloned-edit-input";
            updateForm.appendChild(hidden);
        });
        // For lists: copy values of inputs inside lists
        const listIds = [
            "taxa-list", "location-list", "celltype-list", "hallmark-list", "observable-list", "inducer-list",
            "assay-list", "citation-list", "origin-list", "dataset-list", "marker-list", "regmarker-list"
        ];
        listIds.forEach(id => {
            const ul = document.getElementById(id);
            if (ul && editForm.contains(ul)) {
                Array.from(ul.querySelectorAll("input,select,textarea")).forEach(el => {
                    if (!el.name) return;
                    const hidden = document.createElement("input");
                    hidden.type = "hidden";
                    hidden.name = el.name;
                    hidden.value = el.value;
                    hidden.className = "cloned-edit-input";
                    updateForm.appendChild(hidden);
                });
            }
        });
        // Submit proceeds
    });
});