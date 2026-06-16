"""Tests for acmt001.compliance (SWIFT silent rejection prevention)."""

from acmt001.compliance.swift_charset import (
    SWIFT_X_CHARSET,
    ComplianceReport,
    ComplianceViolation,
    cleanse_data,
    cleanse_data_with_report,
    cleanse_string,
    enforce_field_lengths,
    validate_swift_charset,
)

# --- SWIFT X Character Set ---


class TestSwiftXCharset:
    def test_ascii_letters_allowed(self):
        for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
            assert c in SWIFT_X_CHARSET

    def test_digits_allowed(self):
        for c in "0123456789":
            assert c in SWIFT_X_CHARSET

    def test_special_chars_allowed(self):
        for c in "/-?:().,'+{} ":
            assert c in SWIFT_X_CHARSET

    def test_emoji_not_allowed(self):
        assert "🏦" not in SWIFT_X_CHARSET

    def test_umlaut_not_allowed(self):
        assert "ü" not in SWIFT_X_CHARSET

    def test_at_sign_not_allowed(self):
        assert "@" not in SWIFT_X_CHARSET


# --- validate_swift_charset ---


class TestValidateSwiftCharset:
    def test_clean_string_returns_empty(self):
        assert validate_swift_charset("Hello World 123") == []

    def test_detects_umlaut(self):
        violations = validate_swift_charset("Müller")
        assert len(violations) == 1
        assert violations[0] == (1, "ü")

    def test_detects_multiple_violations(self):
        violations = validate_swift_charset("Ünö@corp")
        assert len(violations) == 3  # Ü, ö, @

    def test_empty_string(self):
        assert validate_swift_charset("") == []

    def test_all_swift_chars_pass(self):
        swift_str = "ABCxyz 012/-?:().,'+{}"
        assert validate_swift_charset(swift_str) == []


# --- cleanse_string ---


class TestCleanseString:
    def test_clean_string_unchanged(self):
        assert cleanse_string("Hello World") == "Hello World"

    def test_umlaut_transliteration(self):
        assert cleanse_string("Müller") == "Mueller"
        assert cleanse_string("Böhm") == "Boehm"
        assert cleanse_string("Süß") == "Suess"

    def test_accented_chars(self):
        result = cleanse_string("café résumé")
        assert validate_swift_charset(result) == []

    def test_currency_symbols(self):
        assert cleanse_string("€100") == "EUR100"
        assert cleanse_string("£50") == "GBP50"

    def test_trademark_replaced(self):
        result = cleanse_string("Corp™")
        assert "™" not in result
        assert validate_swift_charset(result) == []

    def test_ampersand_replaced(self):
        result = cleanse_string("A & B")
        assert "&" not in result
        assert validate_swift_charset(result) == []

    def test_at_sign_replaced(self):
        result = cleanse_string("user@email")
        assert "@" not in result

    def test_result_is_swift_compliant(self):
        test_strings = [
            "Müller & Söhne™",
            "Ñoño café",
            "user@corp.com",
            "100€ — paid",
            "résumé [draft]",
        ]
        for s in test_strings:
            result = cleanse_string(s)
            assert validate_swift_charset(result) == []


# --- enforce_field_lengths ---


class TestEnforceFieldLengths:
    def test_short_fields_unchanged(self):
        row = {"msg_id": "MSG001", "account_owner_name": "Test"}
        corrected, violations = enforce_field_lengths(row)
        assert corrected == row
        assert violations == []

    def test_truncates_long_msg_id(self):
        row = {"msg_id": "X" * 50}
        corrected, violations = enforce_field_lengths(row)
        assert len(corrected["msg_id"]) == 35
        assert len(violations) == 1
        assert violations[0].violation_type == "field_length"
        assert violations[0].field == "msg_id"

    def test_truncates_long_owner_name(self):
        row = {"account_owner_name": "A" * 200}
        corrected, _ = enforce_field_lengths(row)
        assert len(corrected["account_owner_name"]) == 140

    def test_account_id_max_34(self):
        row = {"account_id": "X" * 40}
        corrected, _ = enforce_field_lengths(row)
        assert len(corrected["account_id"]) == 34

    def test_bic_max_11(self):
        row = {"account_servicer_bic": "X" * 15}
        corrected, _ = enforce_field_lengths(row)
        assert len(corrected["account_servicer_bic"]) == 11

    def test_additional_info_max_350(self):
        row = {"additional_info": "Z" * 500}
        corrected, _ = enforce_field_lengths(row)
        assert len(corrected["additional_info"]) == 350

    def test_unknown_fields_not_touched(self):
        row = {"custom_field": "X" * 1000}
        corrected, violations = enforce_field_lengths(row)
        assert corrected["custom_field"] == "X" * 1000
        assert violations == []

    def test_none_values_skipped(self):
        row = {"msg_id": None}
        corrected, violations = enforce_field_lengths(row)
        assert corrected["msg_id"] is None
        assert violations == []

    def test_custom_max_lengths(self):
        row = {"msg_id": "ABCDEFGHIJ"}
        corrected, violations = enforce_field_lengths(row, {"msg_id": 5})
        assert corrected["msg_id"] == "ABCDE"
        assert len(violations) == 1


# --- cleanse_data ---


class TestCleanseData:
    def _row(self, **overrides):
        row = {
            "msg_id": "MSG001",
            "account_owner_name": "Acme Corp",
            "org_full_legal_name": "Acme Corporation GmbH",
        }
        row.update(overrides)
        return row

    def test_clean_data_unchanged(self):
        result = cleanse_data([self._row()])
        assert result[0]["account_owner_name"] == "Acme Corp"

    def test_cleanses_unicode_names(self):
        result = cleanse_data(
            [self._row(account_owner_name="Müller & Söhne™")]
        )
        assert "ü" not in result[0]["account_owner_name"]
        assert "™" not in result[0]["account_owner_name"]
        assert validate_swift_charset(result[0]["account_owner_name"]) == []

    def test_truncates_long_msg_id(self):
        result = cleanse_data([self._row(msg_id="X" * 50)])
        assert len(result[0]["msg_id"]) == 35

    def test_both_charset_and_length(self):
        result = cleanse_data(
            [self._row(account_owner_name="Ä" * 200)]
        )
        assert len(result[0]["account_owner_name"]) <= 140
        assert validate_swift_charset(result[0]["account_owner_name"]) == []

    def test_empty_data(self):
        assert cleanse_data([]) == []

    def test_multiple_rows(self):
        data = [
            self._row(account_owner_name="Böhm"),
            self._row(org_full_legal_name="García SL"),
        ]
        result = cleanse_data(data)
        assert len(result) == 2
        assert "ö" not in result[0]["account_owner_name"]
        assert "í" not in result[1]["org_full_legal_name"]

    def test_disable_charset_cleansing(self):
        result = cleanse_data(
            [self._row(account_owner_name="Müller")], cleanse_charset=False
        )
        assert result[0]["account_owner_name"] == "Müller"

    def test_disable_length_enforcement(self):
        result = cleanse_data(
            [self._row(msg_id="X" * 50)], enforce_lengths=False
        )
        assert len(result[0]["msg_id"]) == 50

    def test_non_string_text_field_skipped(self):
        # value that is falsy / non-str should be left intact
        result = cleanse_data([self._row(account_owner_name=None)])
        assert result[0]["account_owner_name"] is None


# --- cleanse_data_with_report ---


class TestCleanseDataWithReport:
    def test_clean_data_report(self):
        data = [
            {
                "msg_id": "MSG001",
                "account_owner_name": "Test Corp",
                "org_full_legal_name": "Other Corp",
            }
        ]
        _, report = cleanse_data_with_report(data)
        assert report.is_clean
        assert report.rows_processed == 1
        assert report.rows_modified == 0

    def test_dirty_data_report(self):
        data = [
            {
                "msg_id": "X" * 50,
                "account_owner_name": "Müller™",
                "org_full_legal_name": "Test",
            }
        ]
        _, report = cleanse_data_with_report(data)
        assert not report.is_clean
        assert report.rows_modified == 1
        assert report.violation_count >= 2  # charset + length

    def test_report_summary_clean(self):
        data = [
            {
                "msg_id": "OK",
                "account_owner_name": "Clean",
                "org_full_legal_name": "Clean",
            }
        ]
        _, report = cleanse_data_with_report(data)
        assert "SWIFT-compliant" in report.summary()

    def test_report_summary_dirty(self):
        data = [{"msg_id": "X" * 50, "account_owner_name": "Müller"}]
        _, report = cleanse_data_with_report(data)
        summary = report.summary()
        assert "violation" in summary.lower() or "modified" in summary.lower()

    def test_charset_only_modification(self):
        data = [{"account_owner_name": "Müller"}]
        result, report = cleanse_data_with_report(data, enforce_lengths=False)
        assert result[0]["account_owner_name"] == "Mueller"
        assert report.rows_modified == 1
        assert any(v.violation_type == "charset" for v in report.violations)

    def test_empty_data_clean_report(self):
        _, report = cleanse_data_with_report([])
        assert report.is_clean
        assert report.rows_processed == 0
        assert report.rows_modified == 0


# --- ComplianceViolation / ComplianceReport ---


class TestComplianceViolation:
    def test_repr(self):
        v = ComplianceViolation(
            field="account_owner_name",
            violation_type="charset",
            original_value="Müller",
        )
        assert "account_owner_name" in repr(v)
        assert "charset" in repr(v)


class TestComplianceReport:
    def test_add_and_counts(self):
        report = ComplianceReport()
        assert report.is_clean
        report.add(
            ComplianceViolation(
                field="msg_id",
                violation_type="field_length",
                original_value="X" * 50,
            )
        )
        assert not report.is_clean
        assert report.violation_count == 1


# --- Unicode edge cases ---


class TestUnicodeEdgeCases:
    def test_cjk_characters_removed(self):
        result = cleanse_string("Payment 支払い")
        assert validate_swift_charset(result) == []

    def test_mixed_scripts(self):
        result = cleanse_string("ABC αβγ 123")
        assert "ABC" in result
        assert "123" in result
        assert validate_swift_charset(result) == []

    def test_combining_diacritics(self):
        import unicodedata

        decomposed = unicodedata.normalize("NFD", "é")
        result = cleanse_string(decomposed)
        assert validate_swift_charset(result) == []

    def test_zero_width_characters(self):
        result = cleanse_string("Hello​World")
        assert validate_swift_charset(result) == []

    def test_all_transliteration_entries(self):
        from acmt001.compliance.swift_charset import _TRANSLITERATION

        for char in _TRANSLITERATION:
            result = cleanse_string(char)
            assert validate_swift_charset(result) == []

    def test_long_transliteration_chain(self):
        from acmt001.compliance.swift_charset import _TRANSLITERATION

        s = "".join(_TRANSLITERATION.keys())
        result = cleanse_string(s)
        assert validate_swift_charset(result) == []
