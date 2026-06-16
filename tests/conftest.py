import pytest
from pathlib import Path


@pytest.fixture
def tmp_csv(tmp_path: Path) -> Path:
    """返回一个临时目录下的 prices.csv 路径（文件尚未创建）。"""
    return tmp_path / "prices.csv"


@pytest.fixture
def tmp_csv_with_header(tmp_path: Path) -> Path:
    """返回一个已写入表头的临时 prices.csv 路径。"""
    p = tmp_path / "prices.csv"
    p.write_text(
        "date,item,unit_price,quantity,unit,on_sale,merchant,note\n",
        encoding="utf-8",
    )
    return p
