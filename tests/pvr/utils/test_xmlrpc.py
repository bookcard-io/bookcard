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

"""Tests for XML-RPC utilities."""

import base64
from typing import Any
from xml.etree import ElementTree as ET  # noqa: S405

import pytest

from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.utils.xmlrpc import (
    XmlElementFactory,
    XmlRpcBuilder,
    XmlRpcParser,
    XmlRpcValue,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def xml_element_factory() -> XmlElementFactory:
    """Create XmlElementFactory instance."""
    return XmlElementFactory()


@pytest.fixture
def xmlrpc_builder() -> XmlRpcBuilder:
    """Create XmlRpcBuilder instance."""
    return XmlRpcBuilder()


@pytest.fixture
def xmlrpc_parser() -> XmlRpcParser:
    """Create XmlRpcParser instance."""
    return XmlRpcParser()


@pytest.fixture
def root_element() -> ET.Element:
    """Create root XML element for testing."""
    return ET.Element("root")


# ============================================================================
# XmlElementFactory Tests
# ============================================================================


class TestXmlElementFactory:
    """Test XmlElementFactory class."""

    def test_create_value(
        self, xml_element_factory: XmlElementFactory, root_element: ET.Element
    ) -> None:
        """Test create_value method."""
        value_elem = xml_element_factory.create_value(root_element)
        assert value_elem.tag == "value"
        assert value_elem in root_element

    def test_create_string(
        self, xml_element_factory: XmlElementFactory, root_element: ET.Element
    ) -> None:
        """Test create_string method."""
        value_elem = xml_element_factory.create_value(root_element)
        string_elem = xml_element_factory.create_string(value_elem, "test string")
        assert string_elem.tag == "string"
        assert string_elem.text == "test string"
        assert string_elem in value_elem

    @pytest.mark.parametrize("value", ["", "hello", "test with spaces", "123"])
    def test_create_string_various_values(
        self,
        xml_element_factory: XmlElementFactory,
        root_element: ET.Element,
        value: str,
    ) -> None:
        """Test create_string with various string values."""
        value_elem = xml_element_factory.create_value(root_element)
        string_elem = xml_element_factory.create_string(value_elem, value)
        assert string_elem.text == value

    def test_create_int(
        self, xml_element_factory: XmlElementFactory, root_element: ET.Element
    ) -> None:
        """Test create_int method."""
        value_elem = xml_element_factory.create_value(root_element)
        int_elem = xml_element_factory.create_int(value_elem, 42)
        assert int_elem.tag == "int"
        assert int_elem.text == "42"
        assert int_elem in value_elem

    @pytest.mark.parametrize("value", [0, 1, -1, 123456, -999])
    def test_create_int_various_values(
        self,
        xml_element_factory: XmlElementFactory,
        root_element: ET.Element,
        value: int,
    ) -> None:
        """Test create_int with various integer values."""
        value_elem = xml_element_factory.create_value(root_element)
        int_elem = xml_element_factory.create_int(value_elem, value)
        assert int_elem.text == str(value)

    def test_create_base64(
        self, xml_element_factory: XmlElementFactory, root_element: ET.Element
    ) -> None:
        """Test create_base64 method."""
        value_elem = xml_element_factory.create_value(root_element)
        data = b"test binary data"
        base64_elem = xml_element_factory.create_base64(value_elem, data)
        assert base64_elem.tag == "base64"
        assert base64_elem.text == base64.b64encode(data).decode("utf-8")
        assert base64_elem in value_elem

    @pytest.mark.parametrize("data", [b"", b"test", b"\x00\x01\x02", b"hello world"])
    def test_create_base64_various_values(
        self,
        xml_element_factory: XmlElementFactory,
        root_element: ET.Element,
        data: bytes,
    ) -> None:
        """Test create_base64 with various byte values."""
        value_elem = xml_element_factory.create_value(root_element)
        base64_elem = xml_element_factory.create_base64(value_elem, data)
        assert base64_elem.text == base64.b64encode(data).decode("utf-8")

    def test_create_array(
        self, xml_element_factory: XmlElementFactory, root_element: ET.Element
    ) -> None:
        """Test create_array method."""
        value_elem = xml_element_factory.create_value(root_element)
        data_elem = xml_element_factory.create_array(value_elem)
        assert data_elem.tag == "data"
        # Check that array element exists as parent
        array_elem = value_elem.find("array")
        assert array_elem is not None
        assert array_elem.tag == "array"
        # Check that data is inside array
        assert data_elem in array_elem

    def test_create_struct(
        self, xml_element_factory: XmlElementFactory, root_element: ET.Element
    ) -> None:
        """Test create_struct method."""
        value_elem = xml_element_factory.create_value(root_element)
        struct_elem = xml_element_factory.create_struct(value_elem)
        assert struct_elem.tag == "struct"
        assert struct_elem in value_elem

    def test_create_member(
        self, xml_element_factory: XmlElementFactory, root_element: ET.Element
    ) -> None:
        """Test create_member method."""
        value_elem = xml_element_factory.create_value(root_element)
        struct_elem = xml_element_factory.create_struct(value_elem)
        value_elem2 = xml_element_factory.create_member(struct_elem, "test_key")
        assert value_elem2.tag == "value"
        # Check that member element exists in struct
        members = struct_elem.findall("member")
        assert len(members) == 1
        member = members[0]
        assert member.tag == "member"
        name_elem = member.find("name")
        assert name_elem is not None
        assert name_elem.text == "test_key"
        # Check that value is inside member
        assert value_elem2 in member


# ============================================================================
# XmlRpcBuilder Tests
# ============================================================================


class TestXmlRpcBuilder:
    """Test XmlRpcBuilder class."""

    def test_init(self, xmlrpc_builder: XmlRpcBuilder) -> None:
        """Test XmlRpcBuilder initialization."""
        assert isinstance(xmlrpc_builder.factory, XmlElementFactory)

    @pytest.mark.parametrize(
        ("method", "params", "rpc_token", "expected_method"),
        [
            ("test.method", (), None, "test.method"),
            ("system.getVersion", (), None, "system.getVersion"),
            ("download.add", ("magnet:?xt=urn:btih:abc",), None, "download.add"),
            ("test.method", (), "token123", "test.method"),
            ("test.method", ("param1",), "token123", "test.method"),
        ],
    )
    def test_build_request_basic(
        self,
        xmlrpc_builder: XmlRpcBuilder,
        method: str,
        params: tuple[XmlRpcValue, ...],
        rpc_token: str | None,
        expected_method: str,
    ) -> None:
        """Test build_request with basic parameters."""
        xml = xmlrpc_builder.build_request(method, *params, rpc_token=rpc_token)
        root = ET.fromstring(xml)  # noqa: S314
        assert root.tag == "methodCall"
        method_name = root.find("methodName")
        assert method_name is not None
        assert method_name.text == expected_method

    def test_build_request_no_params(self, xmlrpc_builder: XmlRpcBuilder) -> None:
        """Test build_request with no parameters."""
        xml = xmlrpc_builder.build_request("test.method")
        root = ET.fromstring(xml)  # noqa: S314
        params = root.find("params")
        assert params is not None
        param_list = params.findall("param")
        assert len(param_list) == 0

    def test_build_request_with_string_param(
        self, xmlrpc_builder: XmlRpcBuilder
    ) -> None:
        """Test build_request with string parameter."""
        xml = xmlrpc_builder.build_request("test.method", "test string")
        root = ET.fromstring(xml)  # noqa: S314
        params = root.find("params")
        assert params is not None
        param = params.find("param")
        assert param is not None
        value = param.find("value")
        assert value is not None
        string_elem = value.find("string")
        assert string_elem is not None
        assert string_elem.text == "test string"

    def test_build_request_with_int_param(self, xmlrpc_builder: XmlRpcBuilder) -> None:
        """Test build_request with integer parameter."""
        xml = xmlrpc_builder.build_request("test.method", 42)
        root = ET.fromstring(xml)  # noqa: S314
        params = root.find("params")
        assert params is not None
        param = params.find("param")
        assert param is not None
        value = param.find("value")
        assert value is not None
        int_elem = value.find("int")
        assert int_elem is not None
        assert int_elem.text == "42"

    def test_build_request_with_bytes_param(
        self, xmlrpc_builder: XmlRpcBuilder
    ) -> None:
        """Test build_request with bytes parameter."""
        data = b"test binary data"
        xml = xmlrpc_builder.build_request("test.method", data)
        root = ET.fromstring(xml)  # noqa: S314
        params = root.find("params")
        assert params is not None
        param = params.find("param")
        assert param is not None
        value = param.find("value")
        assert value is not None
        base64_elem = value.find("base64")
        assert base64_elem is not None
        assert base64_elem.text == base64.b64encode(data).decode("utf-8")

    def test_build_request_with_list_param(self, xmlrpc_builder: XmlRpcBuilder) -> None:
        """Test build_request with list parameter."""
        xml = xmlrpc_builder.build_request("test.method", ["item1", "item2", 123])
        root = ET.fromstring(xml)  # noqa: S314
        params = root.find("params")
        assert params is not None
        param = params.find("param")
        assert param is not None
        value = param.find("value")
        assert value is not None
        array_elem = value.find("array")
        assert array_elem is not None
        data = array_elem.find("data")
        assert data is not None
        values = data.findall("value")
        assert len(values) == 3

    def test_build_request_with_tuple_param(
        self, xmlrpc_builder: XmlRpcBuilder
    ) -> None:
        """Test build_request with list parameter."""
        xml = xmlrpc_builder.build_request("test.method", ["item1", "item2"])
        root = ET.fromstring(xml)  # noqa: S314
        params = root.find("params")
        assert params is not None
        param = params.find("param")
        assert param is not None
        value = param.find("value")
        assert value is not None
        array_elem = value.find("array")
        assert array_elem is not None

    def test_build_request_with_dict_param(self, xmlrpc_builder: XmlRpcBuilder) -> None:
        """Test build_request with dict parameter."""
        xml = xmlrpc_builder.build_request(
            "test.method", {"key1": "value1", "key2": 42}
        )
        root = ET.fromstring(xml)  # noqa: S314
        params = root.find("params")
        assert params is not None
        param = params.find("param")
        assert param is not None
        value = param.find("value")
        assert value is not None
        struct_elem = value.find("struct")
        assert struct_elem is not None
        members = struct_elem.findall("member")
        assert len(members) == 2

    def test_build_request_with_nested_structures(
        self, xmlrpc_builder: XmlRpcBuilder
    ) -> None:
        """Test build_request with nested list and dict structures."""
        nested = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "string": "test",
        }
        xml = xmlrpc_builder.build_request("test.method", nested)
        root = ET.fromstring(xml)  # noqa: S314
        params = root.find("params")
        assert params is not None
        param = params.find("param")
        assert param is not None
        value = param.find("value")
        assert value is not None
        struct_elem = value.find("struct")
        assert struct_elem is not None

    def test_build_request_with_rpc_token(self, xmlrpc_builder: XmlRpcBuilder) -> None:
        """Test build_request with RPC token."""
        xml = xmlrpc_builder.build_request(
            "test.method", "param1", rpc_token="token123"
        )
        root = ET.fromstring(xml)  # noqa: S314
        params = root.find("params")
        assert params is not None
        param_list = params.findall("param")
        assert len(param_list) == 2
        # First param should be the token
        first_value = param_list[0].find("value")
        assert first_value is not None
        first_string = first_value.find("string")
        assert first_string is not None
        assert first_string.text == "token123"

    def test_build_request_with_multiple_params(
        self, xmlrpc_builder: XmlRpcBuilder
    ) -> None:
        """Test build_request with multiple parameters."""
        xml = xmlrpc_builder.build_request("test.method", "param1", 42, ["list"])
        root = ET.fromstring(xml)  # noqa: S314
        params = root.find("params")
        assert params is not None
        param_list = params.findall("param")
        assert len(param_list) == 3


# ============================================================================
# XmlRpcParser Tests
# ============================================================================


class TestXmlRpcParser:
    """Test XmlRpcParser class."""

    def test_check_fault_no_fault(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test check_fault when no fault is present."""
        root = ET.Element("methodResponse")
        params = ET.SubElement(root, "params")
        param = ET.SubElement(params, "param")
        value = ET.SubElement(param, "value")
        ET.SubElement(value, "string").text = "success"
        # Should not raise
        xmlrpc_parser.check_fault(root)

    def test_check_fault_with_fault(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test check_fault when fault is present."""
        root = ET.Element("methodResponse")
        fault = ET.SubElement(root, "fault")
        value = ET.SubElement(fault, "value")
        struct = ET.SubElement(value, "struct")
        member = ET.SubElement(struct, "member")
        ET.SubElement(member, "name").text = "faultString"
        value2 = ET.SubElement(member, "value")
        ET.SubElement(value2, "string").text = "Test error message"
        with pytest.raises(PVRProviderError, match="XML-RPC fault: Test error message"):
            xmlrpc_parser.check_fault(root)

    def test_check_fault_with_custom_provider_name(
        self, xmlrpc_parser: XmlRpcParser
    ) -> None:
        """Test check_fault with custom provider name."""
        root = ET.Element("methodResponse")
        fault = ET.SubElement(root, "fault")
        value = ET.SubElement(fault, "value")
        struct = ET.SubElement(value, "struct")
        member = ET.SubElement(struct, "member")
        ET.SubElement(member, "name").text = "faultString"
        value2 = ET.SubElement(member, "value")
        ET.SubElement(value2, "string").text = "Test error"
        with pytest.raises(
            PVRProviderError, match="CustomProvider XML-RPC fault: Test error"
        ):
            xmlrpc_parser.check_fault(root, provider_name="CustomProvider")

    def test_check_fault_with_unknown_error(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test check_fault with fault but no string element."""
        root = ET.Element("methodResponse")
        fault = ET.SubElement(root, "fault")
        value = ET.SubElement(fault, "value")
        struct = ET.SubElement(value, "struct")
        # Add a member but with int instead of string
        member = ET.SubElement(struct, "member")
        ET.SubElement(member, "name").text = "faultCode"
        value2 = ET.SubElement(member, "value")
        ET.SubElement(value2, "int").text = "500"
        # Should not raise because no string element found
        # The code only raises if a string element is found
        xmlrpc_parser.check_fault(root)

    def test_check_fault_fault_without_struct(
        self, xmlrpc_parser: XmlRpcParser
    ) -> None:
        """Test check_fault with fault but no struct."""
        root = ET.Element("methodResponse")
        fault = ET.SubElement(root, "fault")
        ET.SubElement(fault, "value")
        # No struct element
        # Should not raise (fault exists but no struct)
        xmlrpc_parser.check_fault(root)

    def test_check_fault_fault_without_value(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test check_fault with fault but no value."""
        root = ET.Element("methodResponse")
        ET.SubElement(root, "fault")
        # No value element
        # Should not raise (fault exists but no value)
        xmlrpc_parser.check_fault(root)

    @pytest.mark.parametrize(
        ("xml_content", "expected"),
        [
            ("<value><string>test</string></value>", "test"),
            ("<value><int>42</int></value>", 42),
            ("<value><i8>123</i8></value>", 123),
            ("<value><string></string></value>", None),
            ("<value><int></int></value>", None),
            ("<value></value>", None),
        ],
    )
    def test_parse_struct_value(
        self, xmlrpc_parser: XmlRpcParser, xml_content: str, expected: str | int | None
    ) -> None:
        """Test parse_struct_value with various value types."""
        value_elem = ET.fromstring(xml_content)  # noqa: S314
        result = xmlrpc_parser.parse_struct_value(value_elem)
        assert result == expected

    def test_parse_array_strings(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_array with string values."""
        data = ET.Element("data")
        for text in ["item1", "item2", "item3"]:
            value = ET.SubElement(data, "value")
            ET.SubElement(value, "string").text = text
        result = xmlrpc_parser.parse_array(data)
        assert result == ["item1", "item2", "item3"]

    def test_parse_array_ints(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_array with integer values."""
        data = ET.Element("data")
        for num in [1, 2, 3]:
            value = ET.SubElement(data, "value")
            ET.SubElement(value, "int").text = str(num)
        result = xmlrpc_parser.parse_array(data)
        assert result == [1, 2, 3]

    def test_parse_array_i8(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_array with i8 values."""
        data = ET.Element("data")
        for num in [100, 200]:
            value = ET.SubElement(data, "value")
            ET.SubElement(value, "i8").text = str(num)
        result = xmlrpc_parser.parse_array(data)
        assert result == [100, 200]

    def test_parse_array_structs(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_array with struct values."""
        data = ET.Element("data")
        value = ET.SubElement(data, "value")
        struct = ET.SubElement(value, "struct")
        member = ET.SubElement(struct, "member")
        ET.SubElement(member, "name").text = "key"
        value2 = ET.SubElement(member, "value")
        ET.SubElement(value2, "string").text = "value"
        result = xmlrpc_parser.parse_array(data)
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["key"] == "value"

    def test_parse_array_mixed(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_array with mixed value types."""
        data = ET.Element("data")
        # String
        value1 = ET.SubElement(data, "value")
        ET.SubElement(value1, "string").text = "test"
        # Int
        value2 = ET.SubElement(data, "value")
        ET.SubElement(value2, "int").text = "42"
        # Struct
        value3 = ET.SubElement(data, "value")
        struct = ET.SubElement(value3, "struct")
        member = ET.SubElement(struct, "member")
        ET.SubElement(member, "name").text = "key"
        value4 = ET.SubElement(member, "value")
        ET.SubElement(value4, "string").text = "value"
        result = xmlrpc_parser.parse_array(data)
        assert result == ["test", 42, {"key": "value"}]

    def test_parse_array_empty(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_array with empty data."""
        data = ET.Element("data")
        result = xmlrpc_parser.parse_array(data)
        assert result == []

    def test_parse_array_struct_with_missing_name(
        self, xmlrpc_parser: XmlRpcParser
    ) -> None:
        """Test parse_array with struct member missing name."""
        data = ET.Element("data")
        value = ET.SubElement(data, "value")
        struct = ET.SubElement(value, "struct")
        member = ET.SubElement(struct, "member")
        # No name element
        value2 = ET.SubElement(member, "value")
        ET.SubElement(value2, "string").text = "value"
        result = xmlrpc_parser.parse_array(data)
        assert len(result) == 1
        assert isinstance(result[0], dict)
        # When name_elem is None, the code doesn't add to dict (checks if name_elem is not None)
        assert len(result[0]) == 0  # Empty dict because name is missing

    def test_parse_array_struct_with_missing_value(
        self, xmlrpc_parser: XmlRpcParser
    ) -> None:
        """Test parse_array with struct member missing value."""
        data = ET.Element("data")
        value = ET.SubElement(data, "value")
        struct = ET.SubElement(value, "struct")
        member = ET.SubElement(struct, "member")
        ET.SubElement(member, "name").text = "key"
        # No value element
        result = xmlrpc_parser.parse_array(data)
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert len(result[0]) == 0  # Empty dict because value is missing

    def test_parse_array_struct_with_none_value(
        self, xmlrpc_parser: XmlRpcParser
    ) -> None:
        """Test parse_array with struct member having None value."""
        data = ET.Element("data")
        value = ET.SubElement(data, "value")
        struct = ET.SubElement(value, "struct")
        member = ET.SubElement(struct, "member")
        ET.SubElement(member, "name").text = "key"
        ET.SubElement(member, "value")
        # Empty value element
        result = xmlrpc_parser.parse_array(data)
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["key"] is None

    @pytest.mark.parametrize(
        ("xml_content", "expected"),
        [
            ("<value><string>test</string></value>", "test"),
            ("<value><int>42</int></value>", 42),
            ("<value><i8>123</i8></value>", 123),
            (
                "<value><array><data><value><string>item</string></value></data></array></value>",
                ["item"],
            ),
            (
                "<value><struct><member><name>key</name><value><string>value</string></value></member></struct></value>",
                {"key": "value"},
            ),
            ("<value></value>", None),
        ],
    )
    def test_parse_value_element(
        self,
        xmlrpc_parser: XmlRpcParser,
        xml_content: str,
        expected: str | float | bool | list[Any] | dict[str, Any] | None,
    ) -> None:
        """Test _parse_value_element with various value types."""
        value_elem = ET.fromstring(xml_content)  # noqa: S314
        result = xmlrpc_parser._parse_value_element(value_elem)
        assert result == expected

    def test_parse_response_string(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_response with string result."""
        xml = """<?xml version="1.0"?>
        <methodResponse>
            <params>
                <param>
                    <value><string>success</string></value>
                </param>
            </params>
        </methodResponse>"""
        result = xmlrpc_parser.parse_response(xml)
        assert result == "success"

    def test_parse_response_int(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_response with integer result."""
        xml = """<?xml version="1.0"?>
        <methodResponse>
            <params>
                <param>
                    <value><int>42</int></value>
                </param>
            </params>
        </methodResponse>"""
        result = xmlrpc_parser.parse_response(xml)
        assert result == 42

    def test_parse_response_array(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_response with array result."""
        xml = """<?xml version="1.0"?>
        <methodResponse>
            <params>
                <param>
                    <value>
                        <array>
                            <data>
                                <value><string>item1</string></value>
                                <value><string>item2</string></value>
                            </data>
                        </array>
                    </value>
                </param>
            </params>
        </methodResponse>"""
        result = xmlrpc_parser.parse_response(xml)
        assert result == ["item1", "item2"]

    def test_parse_response_struct(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_response with struct result."""
        xml = """<?xml version="1.0"?>
        <methodResponse>
            <params>
                <param>
                    <value>
                        <struct>
                            <member>
                                <name>key1</name>
                                <value><string>value1</string></value>
                            </member>
                            <member>
                                <name>key2</name>
                                <value><int>42</int></value>
                            </member>
                        </struct>
                    </value>
                </param>
            </params>
        </methodResponse>"""
        result = xmlrpc_parser.parse_response(xml)
        assert result == {"key1": "value1", "key2": 42}

    def test_parse_response_no_params(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_response with no params."""
        xml = """<?xml version="1.0"?>
        <methodResponse>
        </methodResponse>"""
        result = xmlrpc_parser.parse_response(xml)
        assert result is None

    def test_parse_response_no_param(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_response with params but no param."""
        xml = """<?xml version="1.0"?>
        <methodResponse>
            <params>
            </params>
        </methodResponse>"""
        result = xmlrpc_parser.parse_response(xml)
        assert result is None

    def test_parse_response_no_value(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_response with param but no value."""
        xml = """<?xml version="1.0"?>
        <methodResponse>
            <params>
                <param>
                </param>
            </params>
        </methodResponse>"""
        result = xmlrpc_parser.parse_response(xml)
        assert result is None

    def test_parse_response_wrapped_method_response(
        self, xmlrpc_parser: XmlRpcParser
    ) -> None:
        """Test parse_response with wrapped methodResponse."""
        xml = """<?xml version="1.0"?>
        <root>
            <methodResponse>
                <params>
                    <param>
                        <value><string>success</string></value>
                    </param>
                </params>
            </methodResponse>
        </root>"""
        result = xmlrpc_parser.parse_response(xml)
        assert result == "success"

    def test_parse_response_invalid_missing_method_response(
        self, xmlrpc_parser: XmlRpcParser
    ) -> None:
        """Test parse_response with invalid XML missing methodResponse."""
        xml = """<?xml version="1.0"?>
        <root>
            <other>
            </other>
        </root>"""
        with pytest.raises(
            PVRProviderError, match="Invalid XML-RPC response: missing methodResponse"
        ):
            xmlrpc_parser.parse_response(xml)

    def test_parse_response_with_fault(self, xmlrpc_parser: XmlRpcParser) -> None:
        """Test parse_response with fault."""
        xml = """<?xml version="1.0"?>
        <methodResponse>
            <fault>
                <value>
                    <struct>
                        <member>
                            <name>faultString</name>
                            <value><string>Test error</string></value>
                        </member>
                    </struct>
                </value>
            </fault>
        </methodResponse>"""
        with pytest.raises(PVRProviderError, match="XML-RPC fault: Test error"):
            xmlrpc_parser.parse_response(xml)
