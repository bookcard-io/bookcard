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

# Recursive type alias for XML-RPC values
type XmlRpcValue = (
    str | int | bytes | bool | float | list[XmlRpcValue] | dict[str, XmlRpcValue]
)


class XmlElementFactory:
    """Factory for creating XML-RPC elements.

    Follows SRP by handling only low-level XML element creation.
    """

    def create_value(self, parent: ET.Element) -> ET.Element:
        """Create a value element."""
        return ET.SubElement(parent, "value")

    def create_string(self, parent: ET.Element, value: str) -> ET.Element:
        """Create a string element."""
        elem = ET.SubElement(parent, "string")
        elem.text = value
        return elem

    def create_int(self, parent: ET.Element, value: int) -> ET.Element:
        """Create an int element."""
        elem = ET.SubElement(parent, "int")
        elem.text = str(value)
        return elem

    def create_base64(self, parent: ET.Element, value: bytes) -> ET.Element:
        """Create a base64 element."""
        elem = ET.SubElement(parent, "base64")
        elem.text = base64.b64encode(value).decode("utf-8")
        return elem

    def create_array(self, parent: ET.Element) -> ET.Element:
        """Create an array element (returns the data sub-element)."""
        array_elem = ET.SubElement(parent, "array")
        return ET.SubElement(array_elem, "data")

    def create_struct(self, parent: ET.Element) -> ET.Element:
        """Create a struct element."""
        return ET.SubElement(parent, "struct")

    def create_member(self, struct_elem: ET.Element, name: str) -> ET.Element:
        """Create a struct member (returns the value sub-element)."""
        member = ET.SubElement(struct_elem, "member")
        name_elem = ET.SubElement(member, "name")
        name_elem.text = name
        return ET.SubElement(member, "value")


class XmlRpcBuilder:
    """Builder for XML-RPC requests.

    Uses XmlElementFactory to build high-level XML-RPC requests.
    """

    def __init__(self) -> None:
        self.factory = XmlElementFactory()

    def _add_array(self, data_elem: ET.Element, param: list["XmlRpcValue"]) -> None:
        """Add array items."""
        for item in param:
            item_param = self.factory.create_value(data_elem)
            self._add_param_value(item_param, item)

    def _add_struct(
        self, struct_elem: ET.Element, param: dict[str, "XmlRpcValue"]
    ) -> None:
        """Add struct members."""
        for key, val in param.items():
            value_elem = self.factory.create_member(struct_elem, str(key))
            self._add_param_value(value_elem, val)

    def _add_param_value(
        self,
        value_elem: ET.Element,
        param: "XmlRpcValue",
    ) -> None:
        """Add parameter value to a value element."""
        if isinstance(param, str):
            self.factory.create_string(value_elem, param)
        elif isinstance(param, bytes):
            self.factory.create_base64(value_elem, param)
        elif isinstance(param, int):
            self.factory.create_int(value_elem, param)
        elif isinstance(param, (list, tuple)):
            data_elem = self.factory.create_array(value_elem)
            self._add_array(data_elem, list(param))
        elif isinstance(param, dict):
            struct_elem = self.factory.create_struct(value_elem)
            self._add_struct(struct_elem, param)

    def build_request(
        self,
        method: str,
        *params: XmlRpcValue,
        rpc_token: str | None = None,
    ) -> str:
        """Build XML-RPC request.

        Parameters
        ----------
        method : str
            RPC method name.
        *params : XmlRpcValue
            Method parameters.
        rpc_token : str | None
            Optional RPC token to prepend as first parameter.

        Returns
        -------
        str
            XML-RPC request body.
        """
        root = ET.Element("methodCall")
        ET.SubElement(root, "methodName").text = method
        params_elem = ET.SubElement(root, "params")

        # Helper to add a full parameter wrapper
        def add_param(value: XmlRpcValue) -> None:
            param_elem = ET.SubElement(params_elem, "param")
            value_elem = self.factory.create_value(param_elem)
            self._add_param_value(value_elem, value)

        if rpc_token:
            add_param(rpc_token)

        for param in params:
            add_param(param)

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

        # Root element should be methodResponse
        if root.tag != "methodResponse":
            # Some implementations might wrap it or have different root
            # Try to find it as a child just in case
            method_response = root.find("methodResponse")
            if method_response is None:
                msg = "Invalid XML-RPC response: missing methodResponse"
                raise PVRProviderError(msg)
            root = method_response

        params = root.find("params")
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
