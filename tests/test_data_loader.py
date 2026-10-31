from io import BytesIO

import pandas as pd
import pytest

from app.services.data_loader import SUPPORTED_EXTENSIONS, load_dataset


class NamedBytesIO(BytesIO):
    def __init__(self, content: bytes, name: str):
        super().__init__(content)
        self.name = name


def test_load_csv_returns_dataframe():
    file = NamedBytesIO(b"sales,profit\n100,20\n200,40\n", "data.csv")
    result = load_dataset(file)
    assert isinstance(result, pd.DataFrame)
    assert result.to_dict("list") == {"sales": [100, 200], "profit": [20, 40]}


def test_load_csv_preserves_duplicate_headers():
    file = NamedBytesIO(b"sales,sales\n100,20\n200,40\n", "duplicate.csv")
    result = load_dataset(file)
    assert list(result.columns) == ["sales", "sales"]


def test_load_csv_preserves_blank_header():
    file = NamedBytesIO(b",sales\nx,10\ny,20\n", "blank_header.csv")
    result = load_dataset(file)
    assert list(result.columns) == ["", "sales"]


def test_load_csv_supports_utf8_bom():
    file = NamedBytesIO("\ufeffname,sales\nCafe,10\n".encode("utf-8"), "bom.csv")
    result = load_dataset(file)
    assert list(result.columns) == ["name", "sales"]
    assert result.iloc[0]["name"] == "Cafe"


def test_load_csv_falls_back_for_legacy_encoding():
    file = NamedBytesIO("name\nCaf\xe9\n".encode("latin-1"), "legacy.csv")
    result = load_dataset(file)
    assert result.iloc[0]["name"] == "Café"


def test_load_csv_rewinds_file_before_reading():
    file = NamedBytesIO(b"sales\n100\n", "data.csv")
    file.read(5)
    result = load_dataset(file)
    assert result.iloc[0, 0] == 100


def test_load_json_returns_dataframe():
    file = NamedBytesIO(b'[{"sales":100},{"sales":200}]', "data.json")
    result = load_dataset(file)
    assert result["sales"].tolist() == [100, 200]


def test_load_excel_returns_dataframe():
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame({"sales": [100, 200]}).to_excel(writer, index=False)
    file = NamedBytesIO(buffer.getvalue(), "data.xlsx")
    result = load_dataset(file)
    assert result["sales"].tolist() == [100, 200]


def test_load_csv_empty_file_has_clear_error():
    file = NamedBytesIO(b"", "empty.csv")
    with pytest.raises(ValueError, match="empty"):
        load_dataset(file)


def test_load_csv_header_only_returns_empty_dataframe():
    file = NamedBytesIO(b"sales,profit\n", "header_only.csv")
    result = load_dataset(file)
    assert result.empty
    assert list(result.columns) == ["sales", "profit"]


def test_unsupported_extension_has_clear_error():
    file = NamedBytesIO(b"data", "data.txt")
    with pytest.raises(ValueError, match="Unsupported file format"):
        load_dataset(file)


def test_missing_filename_has_clear_error():
    file = BytesIO(b"sales\n100\n")
    with pytest.raises(ValueError, match="filename"):
        load_dataset(file)


def test_path_input_is_supported(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("sales\n100\n", encoding="utf-8")
    result = load_dataset(path)
    assert result["sales"].tolist() == [100]


def test_malformed_csv_has_clear_error():
    file = NamedBytesIO(b'a,b\n"unterminated,2\n', "broken.csv")
    with pytest.raises(ValueError, match="Unable to parse CSV"):
        load_dataset(file)


def test_supported_extensions_include_existing_and_new_formats():
    assert {".csv", ".xlsx", ".xls", ".json", ".parquet"} == SUPPORTED_EXTENSIONS


def test_parquet_missing_optional_engine_has_actionable_error(monkeypatch):
    import app.services.data_loader as loader

    def fail_read_parquet(_file):
        raise ImportError("missing parquet engine")

    monkeypatch.setattr(loader.pd, "read_parquet", fail_read_parquet)
    file = NamedBytesIO(b"placeholder", "data.parquet")
    with pytest.raises(ValueError, match="Parquet support requires"):
        load_dataset(file)
