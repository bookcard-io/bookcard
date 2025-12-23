# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""XML-RPC utilities for PVR download clients.

This module provides shared XML-RPC request building and parsing utilities,
following DRY principles by centralizing duplicate XML-RPC logic.
"""

import base64
from typing import Any
from xml.etree import ElementTree as ET  # noqa: S405

from bookcard.pvr.exceptions import PVRProviderError


class XmlRpcBuilder:
    """Builder for XML-RPC requests.

    This class provides methods to build XML-RPC requests following
    the XML-RPC specification.

    Examples
    --------
    >>> builder = (
    ...     XmlRpcBuilder()
    ... )
    >>> request = builder.build_request(
    ...     "method.name",
    ...     "param1",
    ...     123,
    ... )
    """

    def _add_xmlrpc_array(self, data_elem: ET.Element, param: list[str | int]) -> None:
        """Add array parameter to XML-RPC request.

        Parameters
        ----------
        data_elem : ET.Element
            Data element to add items to.
        param : list[str | int]
            Array parameter values.
        """
        for item in param:
            item_param = ET.SubElement(data_elem, "value")
            if isinstance(item, str):
                string_elem = ET.SubElement(item_param, "string")
                string_elem.text = item
            elif isinstance(item, int):
                int_elem = ET.SubElement(item_param, "int")
                int_elem.text = str(item)

    def _add_xmlrpc_struct(
        self,
        struct_elem: ET.Element,
        param: dict[str, str | int | None],
    ) -> None:
        """Add struct parameter to XML-RPC request.

        Parameters
        ----------
        struct_elem : ET.Element
            Struct element to add members to.
        param : dict[str, str | int | None]
            Struct parameter values.
        """
        for key, val in param.items():
            member = ET.SubElement(struct_elem, "member")
            name_elem = ET.SubElement(member, "name")
            name_elem.text = str(key)
            value_elem2 = ET.SubElement(member, "value")
            if isinstance(val, str):
                string_elem = ET.SubElement(value_elem2, "string")
                string_elem.text = val
            elif isinstance(val, int):
                int_elem = ET.SubElement(value_elem2, "int")
                int_elem.text = str(val)

    def _add_xmlrpc_param(
        self,
        params_elem: ET.Element,
        param: str | bytes | int | list[str | int] | dict[str, str | int | None],
    ) -> None:
        """Add a parameter to XML-RPC request.

        Parameters
        ----------
        params_elem : ET.Element
            Params element to add parameter to.
        param : str | bytes | int | list[str | int] | dict[str, str | int | None]
            Parameter value.
        """
        param_elem = ET.SubElement(params_elem, "param")
        value_elem = ET.SubElement(param_elem, "value")

        if isinstance(param, str):
            string_elem = ET.SubElement(value_elem, "string")
            string_elem.text = param
        elif isinstance(param, bytes):
            base64_elem = ET.SubElement(value_elem, "base64")
            base64_elem.text = base64.b64encode(param).decode("utf-8")
        elif isinstance(param, int):
            int_elem = ET.SubElement(value_elem, "int")
            int_elem.text = str(param)
        elif isinstance(param, (list, tuple)):
            array_elem = ET.SubElement(value_elem, "array")
            data_elem = ET.SubElement(array_elem, "data")
            self._add_xmlrpc_array(data_elem, param)
        elif isinstance(param, dict):
            struct_elem = ET.SubElement(value_elem, "struct")
            self._add_xmlrpc_struct(struct_elem, param)

    def build_request(
        self,
        method: str,
        *params: str | bytes | int | list[str | int] | dict[str, str | int | None],
        rpc_token: str | None = None,
    ) -> str:
        """Build XML-RPC request.

        Parameters
        ----------
        method : str
            RPC method name.
        *params : str | bytes | int | list[str | int] | dict[str, str | int | None]
            Method parameters.
        rpc_token : str | None
            Optional RPC token to prepend as first parameter.

        Returns
        -------
        str
            XML-RPC request body.
        """
        root = ET.Element("methodCall")
        method_name = ET.SubElement(root, "methodName")
        method_name.text = method

        params_elem = ET.SubElement(root, "params")

        # Add token as first parameter if provided
        if rpc_token:
            param_elem = ET.SubElement(params_elem, "param")
            value_elem = ET.SubElement(param_elem, "value")
            string_elem = ET.SubElement(value_elem, "string")
            string_elem.text = rpc_token

        for param in params:
            self._add_xmlrpc_param(params_elem, param)

        return ET.tostring(root, encoding="utf-8").decode("utf-8")


class XmlRpcParser:
    """Parser for XML-RPC responses.

    This class provides methods to parse XML-RPC responses following
    the XML-RPC specification.
    """

    def check_fault(self, root: ET.Element, provider_name: str = "XML-RPC") -> None:
        """Check for XML-RPC fault and raise if found.

        Parameters
        ----------
        root : ET.Element
            XML root element.
        provider_name : str
            Provider name for error messages.

        Raises
        ------
        PVRProviderError
            If fault is found.
        """
        fault = root.find(".//fault")
        if fault is not None:
            fault_value = fault.find("value")
            if fault_value is not None:
                fault_struct = fault_value.find("struct")
                if fault_struct is not None:
                    fault_string = fault_struct.find(".//string")
                    if fault_string is not None:
                        error_msg = fault_string.text or "Unknown error"
                        msg = f"{provider_name} XML-RPC fault: {error_msg}"
                        raise PVRProviderError(msg)

    def parse_struct_value(self, value_elem: ET.Element) -> str | int | None:
        """Parse XML-RPC struct value element.

        Parameters
        ----------
        value_elem : ET.Element
            Value element to parse.

        Returns
        -------
        str | int | None
            Parsed value.
        """
        val = None
        string_elem = value_elem.find("string")
        if string_elem is not None and string_elem.text is not None:
            val = string_elem.text
        else:
            int_elem = value_elem.find("int")
            if int_elem is not None and int_elem.text is not None:
                val = int(int_elem.text)
            else:
                i8_elem = value_elem.find("i8")
                if i8_elem is not None and i8_elem.text is not None:
                    val = int(i8_elem.text)
        return val

    def parse_array(
        self, data: ET.Element
    ) -> list[str | int | dict[str, str | int | None]]:
        """Parse XML-RPC array element.

        Parameters
        ----------
        data : ET.Element
            Data element containing array values.

        Returns
        -------
        list[str | int | dict[str, str | int | None]]
            List of parsed values (strings, ints, or structs).
        """
        results = []
        for value_elem in data.findall("value"):
            # Check for string
            string_elem = value_elem.find("string")
            if string_elem is not None and string_elem.text is not None:
                results.append(string_elem.text)
                continue

            # Check for int
            int_elem = value_elem.find("int")
            if int_elem is not None and int_elem.text is not None:
                results.append(int(int_elem.text))
                continue

            # Check for i8
            i8_elem = value_elem.find("i8")
            if i8_elem is not None and i8_elem.text is not None:
                results.append(int(i8_elem.text))
                continue

            # Check for struct
            struct_elem = value_elem.find("struct")
            if struct_elem is not None:
                struct_dict: dict[str, str | int | None] = {}
                for member in struct_elem.findall("member"):
                    name_elem = member.find("name")
                    value_elem2 = member.find("value")
                    if name_elem is not None and value_elem2 is not None:
                        name = name_elem.text or ""
                        val = self.parse_struct_value(value_elem2)
                        struct_dict[name] = val
                results.append(struct_dict)

        return results

    def _parse_value_element(
        self, value_elem: ET.Element
    ) -> (
        str
        | int
        | list[str | int | dict[str, str | int | None]]
        | dict[str, str | int | None]
        | None
    ):
        """Parse XML-RPC value element.

        Parameters
        ----------
        value_elem : ET.Element
            Value element to parse.

        Returns
        -------
        str | int | list | dict | None
            Parsed value.
        """
        # Parse the value
        string_elem = value_elem.find("string")
        if string_elem is not None and string_elem.text is not None:
            return string_elem.text

        int_elem = value_elem.find("int")
        if int_elem is not None and int_elem.text is not None:
            return int(int_elem.text)

        i8_elem = value_elem.find("i8")
        if i8_elem is not None and i8_elem.text is not None:
            return int(i8_elem.text)

        array_elem = value_elem.find("array")
        if array_elem is not None:
            data = array_elem.find("data")
            if data is not None:
                return self.parse_array(data)

        struct_elem = value_elem.find("struct")
        if struct_elem is not None:
            struct_dict: dict[str, str | int | None] = {}
            for member in struct_elem.findall("member"):
                name_elem = member.find("name")
                value_elem2 = member.find("value")
                if name_elem is not None and value_elem2 is not None:
                    name = name_elem.text or ""
                    val = self.parse_struct_value(value_elem2)
                    struct_dict[name] = val
            return struct_dict

        return None

    def parse_response(self, xml_content: str) -> Any:  # noqa: ANN401
        """Parse XML-RPC response.

        Parameters
        ----------
        xml_content : str
            XML response content.

        Returns
        -------
        Any
            Parsed response value.

        Raises
        ------
        PVRProviderError
            If response contains a fault or cannot be parsed.
        """
        root = ET.fromstring(xml_content)  # noqa: S314
        self.check_fault(root)

        # Find methodResponse/params/param/value
        method_response = root.find("methodResponse")
        if method_response is None:
            msg = "Invalid XML-RPC response: missing methodResponse"
            raise PVRProviderError(msg)

        params = method_response.find("params")
        if params is None:
            # No params means void return
            return None

        param = params.find("param")
        if param is None:
            return None

        value_elem = param.find("value")
        if value_elem is None:
            return None

        return self._parse_value_element(value_elem)
