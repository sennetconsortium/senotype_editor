def clearerrors(form):
    # Clear errors for each field in the form
    for field in form:
        field.errors = []
        # If the field is a FieldList, clear errors for each entry
        if hasattr(field, 'entries'):
            for entry in field.entries:
                entry.errors = []
