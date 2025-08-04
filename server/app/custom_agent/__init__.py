import pandas as pd
from ..constants import (
    RENT_CSV,
    SALE_CSV
)

def load_data():
    """Load rental and sales data from CSV files."""
    rent_data = get_rent_data()
    sale_data = get_sale_data()
    return rent_data, sale_data

def get_rent_data():
    """Get rental data."""
    return pd.read_csv(RENT_CSV)


def get_sale_data():
    """Get sales data."""
    return pd.read_csv(SALE_CSV)
