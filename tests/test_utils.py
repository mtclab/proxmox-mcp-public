from __future__ import annotations

from proxmox_mcp.utils import extract_data, extract_upid


class TestExtractUpid:
    def test_none_returns_na(self):
        assert extract_upid(None) == "N/A"

    def test_string_passthrough(self):
        assert extract_upid("UPID:pve:123:456") == "UPID:pve:123:456"

    def test_empty_string_returns_na(self):
        assert extract_upid("") == "N/A"

    def test_dict_with_data_key(self):
        assert extract_upid({"data": "UPID:pve:789:012"}) == "UPID:pve:789:012"

    def test_dict_with_data_none_returns_na(self):
        assert extract_upid({"data": None}) == "N/A"

    def test_dict_with_data_empty_string_returns_na(self):
        assert extract_upid({"data": ""}) == "N/A"

    def test_dict_without_data_key(self):
        assert extract_upid({"status": "OK"}) == "{'status': 'OK'}"

    def test_dict_data_is_int(self):
        assert extract_upid({"data": 42}) == "42"

    def test_int_returns_str(self):
        assert extract_upid(42) == "42"

    def test_zero_returns_str(self):
        assert extract_upid(0) == "0"

    def test_false_returns_str(self):
        assert extract_upid(False) == "False"

    def test_list_returns_str(self):
        assert extract_upid([1, 2]) == "[1, 2]"


class TestExtractData:
    def test_none_returns_none(self):
        assert extract_data(None) is None

    def test_string_passthrough(self):
        assert extract_data("hello") == "hello"

    def test_dict_with_data_key(self):
        assert extract_data({"data": "value"}) == "value"

    def test_dict_without_data_key(self):
        result = extract_data({"status": "OK"})
        assert result == {"status": "OK"}

    def test_dict_data_is_none(self):
        assert extract_data({"data": None}) is None

    def test_dict_data_is_empty_string(self):
        assert extract_data({"data": ""}) == ""

    def test_dict_data_is_int(self):
        assert extract_data({"data": 42}) == 42

    def test_int_passthrough(self):
        assert extract_data(42) == 42

    def test_false_passthrough(self):
        assert extract_data(False) is False

    def test_list_passthrough(self):
        assert extract_data([1, 2, 3]) == [1, 2, 3]
