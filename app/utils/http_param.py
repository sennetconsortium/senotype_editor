"""
http_param.py
HttpParam object to evaluate parameter strings.

Functionality copied over from ubkg-api.
"""

from flask import request
import re

class HttpParam:
    # coding: utf-8
    # Common functions used for format HTTP error messages (404, 400) for endpoints.

    from flask import request, jsonify
    import re

    def validate_query_parameter_names(self, parameter_name_list=None) -> str:
        """
        Validates query parameter name in the querystring. Prepares the content of a 400 message if the
        querystring includes an unexpected parameter.
        :param parameter_name_list: list of parameter names
        :return:
        - "ok"
        - error string for a 400 error
        """

        if parameter_name_list is None:
            return f"Invalid query parameter. This endpoint does not take query parameters. " \
                   f"Refer to the SmartAPI documentation for this endpoint for more information."

        for req in request.args:
            if req not in parameter_name_list:
                namelist = self.list_as_single_quoted_string(list_elements=parameter_name_list)
                prompt = self.get_number_agreement(list_items=parameter_name_list)
                err = f"Invalid query parameter: '{req}'. The possible parameter name{prompt}: {namelist}. " \
                      f"Refer to the SmartAPI documentation for this endpoint for more information."
                return err

        return "ok"

    def list_as_single_quoted_string(self, delim: str = ';', list_elements=None):
        """Converts the list of elements in list_elements into a string formatted with single quotes--
        e.g., ['a','b','c'] -> "'a'; 'b'; 'c'"

        """
        return f'{delim} '.join(f"'{x}'" for x in list_elements)

    def get_number_agreement(self, list_items=None):
        """
        Builds a clause with correct number agreement
        :param list_items: list of items
        :return:
        """
        if len(list_items) < 2:
            return ' is'
        else:
            return 's are'

    def validate_parameter_value_in_enum(self, param_name=None, param_value=None, enum_list=None):
        """
        Verifies that a parameter's value is a member of a defined set--i.e., the equivalent of in an enumeration.
        :param enum_list: list of enum values
        :param param_value: value to validate
        :param param_name: parameter name
        :return:
        --"ok"
        --error string suitable for a 400 message
        """

        if param_value is None:
            return "ok"

        if param_name is None:
            return "ok"

        if param_value not in enum_list:
            namelist = self.list_as_single_quoted_string(list_elements=enum_list)
            prompt = self.get_number_agreement(enum_list)
            err = f"Invalid value for parameter: '{param_name}'. The possible parameter value{prompt}: {namelist}. " \
                  f"Refer to the SmartAPI documentation for this endpoint for more information."
            return err

        return "ok"