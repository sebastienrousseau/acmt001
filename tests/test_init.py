"""Tests for the acmt001 package public exports."""

import acmt001


class TestPackageExports:
    def test_version(self):
        assert acmt001.__version__ == "0.0.1"

    def test_all_names_present(self):
        for name in acmt001.__all__:
            assert hasattr(acmt001, name), f"missing export: {name}"

    def test_main_is_callable(self):
        assert callable(acmt001.main)

    def test_process_files_is_callable(self):
        assert callable(acmt001.process_files)

    def test_generate_xml_string_is_callable(self):
        assert callable(acmt001.generate_xml_string)

    def test_exception_exports(self):
        from acmt001.exceptions import (
            AccountValidationError,
            DataSourceError,
        )

        assert acmt001.AccountValidationError is AccountValidationError
        assert acmt001.DataSourceError is DataSourceError

    def test_exceptions_are_exception_subclasses(self):
        assert issubclass(acmt001.AccountValidationError, Exception)
        assert issubclass(acmt001.DataSourceError, Exception)
