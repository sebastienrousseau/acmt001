# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Coverage-guided fuzzing of the text entry points with Atheris.

Every function here takes text a caller supplies: the IBAN, BIC and LEI
validators, the SWIFT character-set check and cleanser, and XML-string
validation against a bundled XSD. Each must answer with its documented
result and never raise; anything else is a crash libFuzzer reports and
minimises. The cleanser is also held to its contract: its output passes
the character-set check.

Run (Linux x86_64, Python 3.12)::

    pip install --require-hashes -r requirements/fuzz.txt
    pip install --no-deps --no-build-isolation -e .
    python fuzz/fuzz_inputs.py fuzz/corpus -max_total_time=60
"""

import contextlib
import io
import sys
from pathlib import Path

import atheris

with atheris.instrument_imports():
    import acmt001
    from acmt001.compliance.swift_charset import (
        cleanse_string,
        validate_swift_charset,
    )
    from acmt001.validation.bic_validator import validate_bic_format
    from acmt001.validation.iban_validator import (
        validate_iban_checksum,
        validate_iban_format,
    )
    from acmt001.validation.lei_validator import (
        validate_lei_checksum,
        validate_lei_format,
    )
    from acmt001.xml.validate_via_xsd import validate_xml_string_via_xsd

VERSION = "acmt.001.001.08"
XSD = str(
    Path(acmt001.__file__).parent / "templates" / VERSION / f"{VERSION}.xsd"
)
VALIDATORS = (
    validate_iban_format,
    validate_iban_checksum,
    validate_bic_format,
    validate_lei_format,
    validate_lei_checksum,
)


def _check_identifiers(text: str) -> None:
    for validator in VALIDATORS:
        ok, message = validator(text)
        assert isinstance(ok, bool) and isinstance(message, str)


def _check_charset(text: str) -> None:
    assert isinstance(validate_swift_charset(text), list)
    assert validate_swift_charset(cleanse_string(text)) == []


def _check_xml(text: str) -> None:
    # The validator prints why a document was rejected; keep the
    # fuzzer's output readable.
    with contextlib.redirect_stdout(io.StringIO()):
        assert isinstance(validate_xml_string_via_xsd(text, XSD), bool)


def test_one_input(data: bytes) -> None:
    """Drive every text entry point with one fuzzer input."""
    fdp = atheris.FuzzedDataProvider(data)
    target = fdp.ConsumeIntInRange(0, 2)
    text = fdp.ConsumeUnicodeNoSurrogates(8192)
    (_check_identifiers, _check_charset, _check_xml)[target](text)


def main() -> None:
    """Hand the harness to libFuzzer."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
