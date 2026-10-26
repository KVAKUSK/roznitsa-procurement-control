import pytest

from scripts.source_registry import (
    assert_ready_for_matching,
    expected_allowed_files,
    preflight_unsynced_files,
)


def test_sudarikov_both_files_are_mandatory_sources():
    files = expected_allowed_files()
    assert "Судариков 1.xls" in files
    assert "Судариков 2.xls" in files


def test_general_vostok_is_not_allowed_but_orimi_file_is():
    files = expected_allowed_files()
    assert "Восток.xlsx" not in files
    assert "Прайс Орими.xlsx" in files


def test_missing_allowed_supplier_index_blocks_matching():
    files = expected_allowed_files()
    synced = files - {"Судариков 2.xls"}
    assert preflight_unsynced_files(synced) == {"Судариков 2.xls"}
    with pytest.raises(RuntimeError, match="matching is forbidden"):
        assert_ready_for_matching(files, synced)


def test_complete_registry_allows_matching():
    files = expected_allowed_files()
    assert_ready_for_matching(files, files)
