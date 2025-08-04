import pandas as pd
from ..constants import (
    RENT_CSV,
    SALE_CSV
)
import os
import logging

def load_data():
    """Load rental and sales data from CSV files."""
    rent_data = get_rent_data()
    sale_data = get_sale_data()
    return rent_data, sale_data

def get_rent_data():
    """Get rental data."""
    # Ensure the directory exists
    if not os.path.exists(os.path.dirname(RENT_CSV)):
        os.makedirs(os.path.dirname(RENT_CSV))
    # Load the CSV file into a DataFrame
    if not os.path.isfile(RENT_CSV):
        logging.error(f"Rent data file not found: {RENT_CSV}")
        raise FileNotFoundError(f"Rent data file not found: {RENT_CSV}")
    

    return pd.read_csv(RENT_CSV)


def get_sale_data():
    """Get sales data."""

    # Ensure the directory exists
    if not os.path.exists(os.path.dirname(SALE_CSV)):
        os.makedirs(os.path.dirname(SALE_CSV))
    # Load the CSV file into a DataFrame
    if not os.path.isfile(SALE_CSV):
        logging.error(f"Sale data file not found: {SALE_CSV}")
        raise FileNotFoundError(f"Sale data file not found: {SALE_CSV}")
    

    return pd.read_csv(SALE_CSV)
