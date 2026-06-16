"""Tests for the small acmt001.xml helper modules.

Covers register_namespaces, generate_updated_xml_file_path,
write_xml_to_file (indent_xml + write_xml_to_file) and xml_to_string.
"""

import os
import xml.etree.ElementTree as et

from acmt001.xml.generate_updated_xml_file_path import (
    generate_updated_xml_file_path,
)
from acmt001.xml.register_namespaces import register_namespaces
from acmt001.xml.write_xml_to_file import indent_xml, write_xml_to_file
from acmt001.xml.xml_to_string import xml_to_string


class TestRegisterNamespaces:
    def test_registers_default_namespace(self):
        register_namespaces("acmt.001.001.08")
        root = et.Element(
            "{urn:iso:std:iso:20022:tech:xsd:acmt.001.001.08}Document"
        )
        serialized = et.tostring(root, encoding="unicode")
        # Default namespace registered -> no ns0: prefix.
        assert "ns0:" not in serialized
        assert "acmt.001.001.08" in serialized

    def test_registers_xsi_prefix(self):
        register_namespaces("acmt.022.001.04")
        root = et.Element("Document")
        child = et.SubElement(
            root,
            "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
        )
        child.text = "x"
        serialized = et.tostring(root, encoding="unicode")
        assert "xsi:" in serialized


class TestGenerateUpdatedXmlFilePath:
    def test_replaces_filename_with_message_type(self):
        result = generate_updated_xml_file_path(
            "/tmp/work/template.xml", "acmt.007.001.05"
        )
        assert result == os.path.join("/tmp/work", "acmt.007.001.05.xml")

    def test_no_directory_component(self):
        result = generate_updated_xml_file_path(
            "template.xml", "acmt.001.001.08"
        )
        assert result == "acmt.001.001.08.xml"

    def test_uses_message_type_not_original_name(self):
        result = generate_updated_xml_file_path(
            "/data/original.xml", "acmt.024.001.04"
        )
        assert result.endswith("acmt.024.001.04.xml")
        assert "original" not in result


class TestIndentXml:
    def test_indent_leaf_element(self):
        elem = et.Element("root")
        indent_xml(elem)
        # Leaf element at level 0 should not get a tail.
        assert elem.tail is None or elem.tail == ""

    def test_indent_with_children(self):
        root = et.Element("root")
        et.SubElement(root, "child1").text = "value1"
        et.SubElement(root, "child2").text = "value2"
        indent_xml(root)
        assert root.text is not None
        assert "\n" in root.text

    def test_indent_preserves_existing_text(self):
        root = et.Element("root")
        child = et.SubElement(root, "child")
        child.text = "keep this"
        indent_xml(root)
        assert child.text == "keep this"

    def test_indent_nested(self):
        root = et.Element("root")
        parent = et.SubElement(root, "parent")
        et.SubElement(parent, "child").text = "deep"
        indent_xml(root)
        assert "  " in parent.text

    def test_indent_multiple_levels(self):
        root = et.Element("a")
        b = et.SubElement(root, "b")
        c = et.SubElement(b, "c")
        d = et.SubElement(c, "d")
        d.text = "leaf"
        indent_xml(root, level=0)
        assert "\n" in d.tail

    def test_indent_empty_children(self):
        root = et.Element("root")
        et.SubElement(root, "empty1")
        et.SubElement(root, "empty2")
        indent_xml(root)
        # Empty children at level 1 should get tails.
        for child in root:
            assert child.tail is not None


class TestWriteXmlToFile:
    def test_write_simple(self, tmp_path):
        root = et.Element("Document")
        child = et.SubElement(root, "Header")
        child.text = "test"
        out = tmp_path / "output.xml"
        write_xml_to_file(str(out), root)
        content = out.read_text(encoding="utf-8")
        assert "<?xml" in content
        assert "<Document>" in content
        assert "<Header>test</Header>" in content

    def test_write_preserves_structure(self, tmp_path):
        root = et.Element("root")
        parent = et.SubElement(root, "parent")
        et.SubElement(parent, "child1").text = "a"
        et.SubElement(parent, "child2").text = "b"
        out = tmp_path / "tree.xml"
        write_xml_to_file(str(out), root)
        content = out.read_text(encoding="utf-8")
        assert "<child1>a</child1>" in content
        assert "<child2>b</child2>" in content

    def test_write_with_attributes(self, tmp_path):
        root = et.Element("root")
        child = et.SubElement(root, "amount", Ccy="EUR")
        child.text = "100.00"
        out = tmp_path / "attr.xml"
        write_xml_to_file(str(out), root)
        content = out.read_text(encoding="utf-8")
        assert 'Ccy="EUR"' in content
        assert "100.00" in content


class TestXmlToString:
    def test_basic_conversion(self):
        root = et.Element("Document")
        child = et.SubElement(root, "Body")
        child.text = "content"
        result = xml_to_string(root)
        assert result.startswith("<?xml")
        assert "<Document>" in result
        assert "<Body>content</Body>" in result
        assert result.endswith("\n")

    def test_without_declaration(self):
        root = et.Element("root")
        result = xml_to_string(root, include_declaration=False)
        assert not result.startswith("<?xml")
        assert "<root" in result

    def test_with_declaration_only_once(self):
        root = et.Element("root")
        result = xml_to_string(root, include_declaration=True)
        assert result.count("<?xml") == 1

    def test_trailing_newline(self):
        root = et.Element("root")
        result = xml_to_string(root)
        assert result.endswith("\n")

    def test_complex_tree(self):
        root = et.Element("Document")
        grp = et.SubElement(root, "GrpHdr")
        et.SubElement(grp, "MsgId").text = "MSG001"
        et.SubElement(grp, "NbOfTxs").text = "1"
        result = xml_to_string(root)
        assert "<MsgId>MSG001</MsgId>" in result
        assert "<NbOfTxs>1</NbOfTxs>" in result
