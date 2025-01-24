import unittest

import pandas as pd
from astropy import units as u

from astromodule.table import crossmatch


class TestCrossMatch(unittest.TestCase):
  def test_valid_data_expected_results(self):
    """
    Given two tables with valid data, it should return a pandas DataFrame 
    with the expected crossmatch results.
    """
    # Initialize the input tables
    table1 = pd.DataFrame({
      'RA': [10.0, 20.0, 30.0],
      'DEC': [45.0, 50.0, 55.0],
      'Name': ['Star1', 'Star2', 'Star3']
    })

    table2 = pd.DataFrame({
      'RA': [15.0, 25.0, 35.0],
      'DEC': [47.0, 52.0, 57.0],
      'Type': ['Galaxy', 'Galaxy', 'Galaxy']
    })

    # Invoke the stilts_crossmatch function
    result = crossmatch(table1, table2, ra1='RA', dec1='DEC', ra2='RA', dec2='DEC', radius=0)

    # Define the expected result
    expected_result = pd.DataFrame()
    
    print(result)
    print(expected_result)

    # Assert the result is equal to the expected result
    pd.testing.assert_frame_equal(result, expected_result)