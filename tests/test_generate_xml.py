"""Tests for acmt001.xml.generate_xml across all 34 acmt message types."""

import pytest

from acmt001.constants import valid_xml_types
from acmt001.xml.generate_xml import (
    _build_context,
    _build_record,
    generate_xml,
    generate_xml_string,
)


class TestGenerateXmlStringAllTypes:
    """Every supported message type renders XSD-valid XML from a record."""

    @pytest.mark.message_compat
    @pytest.mark.parametrize("message_type", valid_xml_types)
    def test_generates_valid_xml(
        self, message_type, sample_record, template_path, schema_path
    ):
        xml = generate_xml_string(
            [sample_record],
            message_type,
            template_path(message_type),
            schema_path(message_type),
        )
        assert xml.strip().startswith("<?xml") or xml.strip().startswith(
            "<Document"
        )
        assert message_type in xml
        # The first record's msg_id surfaces in the rendered document.
        assert sample_record["msg_id"] in xml

    @pytest.mark.smoke
    def test_account_opening_instruction_contents(
        self, sample_record, template_path, schema_path
    ):
        version = "acmt.001.001.08"
        xml = generate_xml_string(
            [sample_record],
            version,
            template_path(version),
            schema_path(version),
        )
        assert version in xml
        assert sample_record["msg_id"] in xml

    def test_batch_records_render(
        self, sample_records, template_path, schema_path
    ):
        version = "acmt.001.001.08"
        xml = generate_xml_string(
            sample_records,
            version,
            template_path(version),
            schema_path(version),
        )
        # First record drives the single-subject header fields.
        assert sample_records[0]["msg_id"] in xml


class TestGenerateXmlStringErrors:
    """Error branches in generate_xml_string."""

    def test_invalid_message_type_raises(
        self, sample_record, template_path, schema_path
    ):
        with pytest.raises(ValueError, match="Invalid XML message type"):
            generate_xml_string(
                [sample_record],
                "acmt.999.001.01",
                template_path("acmt.001.001.08"),
                schema_path("acmt.001.001.08"),
            )

    def test_empty_data_raises(self, template_path, schema_path):
        with pytest.raises(ValueError, match="empty"):
            generate_xml_string(
                [],
                "acmt.001.001.08",
                template_path("acmt.001.001.08"),
                schema_path("acmt.001.001.08"),
            )

    def test_invalid_template_path_raises(self, sample_record, schema_path):
        with pytest.raises(ValueError, match="Invalid template path"):
            generate_xml_string(
                [sample_record],
                "acmt.001.001.08",
                "../../../etc/passwd",
                schema_path("acmt.001.001.08"),
            )

    def test_invalid_schema_path_raises(self, sample_record, template_path):
        with pytest.raises(ValueError, match="Invalid schema path"):
            generate_xml_string(
                [sample_record],
                "acmt.001.001.08",
                template_path("acmt.001.001.08"),
                "../../../etc/shadow",
            )

    def test_failed_xsd_validation_raises_runtime_error(
        self, sample_record, template_path, schema_path, monkeypatch
    ):
        """Rendered XML that fails XSD validation raises RuntimeError."""
        import acmt001.xml.generate_xml as gx

        version = "acmt.001.001.08"
        monkeypatch.setattr(
            gx, "validate_xml_string_via_xsd", lambda *_a, **_k: False
        )
        with pytest.raises(RuntimeError, match="failed validation"):
            generate_xml_string(
                [sample_record],
                version,
                template_path(version),
                schema_path(version),
            )


class TestGenerateXmlFile:
    """generate_xml writes the rendered document into the working directory."""

    @pytest.mark.integration
    def test_writes_file_into_work_dir(
        self, sample_record, staged_message, work_dir
    ):
        version = "acmt.007.001.05"
        tpl, xsd = staged_message(version)
        generate_xml([sample_record], version, tpl, xsd)
        out = work_dir / f"{version}.xml"
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert version in content
        assert sample_record["msg_id"] in content


class TestGenerateXmlOutputGuards:
    """Output-path safety branches in generate_xml."""

    def test_output_outside_working_directory_raises(
        self, sample_record, staged_message, work_dir, monkeypatch
    ):
        """Output resolves outside the (relocated) cwd and is rejected."""
        import acmt001.xml.generate_xml as gx

        version = "acmt.001.001.08"
        tpl, xsd = staged_message(version)

        # Relocate cwd to a sibling temp dir so the output path (computed
        # next to the template) falls outside it.
        elsewhere = work_dir.parent / "elsewhere"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)

        # validate_path would otherwise reject the template (outside cwd);
        # make it a transparent pass-through so we reach the cwd guard.
        monkeypatch.setattr(gx, "validate_path", lambda p, **kw: str(p))

        with pytest.raises(ValueError, match="outside working directory"):
            gx.generate_xml([sample_record], version, tpl, xsd)

    def test_output_path_validation_failure_raises(
        self, sample_record, staged_message, work_dir, monkeypatch
    ):
        """A failure validating the output path surfaces as ValueError."""
        import acmt001.xml.generate_xml as gx

        version = "acmt.001.001.08"
        tpl, xsd = staged_message(version)

        real_validate = gx.validate_path
        calls = {"n": 0}

        def fake_validate(path, **kwargs):
            # First two calls validate template + schema (let them pass);
            # the third validates the output path -> force a failure.
            calls["n"] += 1
            if calls["n"] >= 3:
                raise RuntimeError("boom")
            return real_validate(path, **kwargs)

        monkeypatch.setattr(gx, "validate_path", fake_validate)

        with pytest.raises(ValueError, match="Path validation failed"):
            gx.generate_xml([sample_record], version, tpl, xsd)


class TestContextHelpers:
    """Unit coverage for the flat-record projection helpers."""

    def test_build_record_fills_missing_with_empty(self):
        record = _build_record({"msg_id": "X"})
        assert record["msg_id"] == "X"
        # Unknown-for-this-row fields default to empty strings.
        assert record["account_id"] == ""

    def test_build_record_ignores_unknown_keys(self):
        record = _build_record({"msg_id": "X", "not_a_field": "drop"})
        assert "not_a_field" not in record

    def test_build_context_exposes_records_list(self):
        data = [{"msg_id": "A"}, {"msg_id": "B"}]
        context = _build_context(data)
        assert context["msg_id"] == "A"
        assert len(context["records"]) == 2
        assert context["records"][1]["msg_id"] == "B"
