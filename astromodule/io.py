import re
from io import StringIO
from pathlib import Path

import astropy
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.table import Table


def load_tdat(path: str | Path) -> pd.DataFrame:
  """
  Loads a tdat table. Transportable Database Aggregate Table (TDAT) is a data
  structure created by NASA's Heasarc project. For more information, see [TDAT]_

  Parameters
  ----------
  path : str | Path
    Path to the table to read

  Returns
  -------
  pd.DataFrame
    The table as a pandas dataframe
    
  References
  ----------
  .. [TDAT] Transportable Database Aggregate Table (TDAT) Format.
      `<https://heasarc.gsfc.nasa.gov/docs/software/dbdocs/tdat.html>`_
  """
  path = Path(path)
  content = path.read_text()
  header = re.findall(r'line\[1\] = (.*)', content)[0].replace(' ', '|')
  data = content.split('<DATA>\n')[-1].split('<END>')[0].replace('|\n', '\n')
  tb = header + '\n' + data
  df = pd.read_csv(StringIO(tb), sep='|')
  return df

def load_fits(path: str | Path) -> pd.DataFrame:
  """
  Loads a fits table

  Parameters
  ----------
  path : str | Path
    Path to the table to read

  Returns
  -------
  pd.DataFrame
    The table as a pandas dataframe
  """
  with fits.open(path) as hdul:
    table_data = hdul[1].data
    table = Table(data=table_data)
    return table.to_pandas()

def load_csv(path: str | Path) -> pd.DataFrame:
  """
  Loads a csv table. ASCII tables with columns delimited by a comma.

  Parameters
  ----------
  path : str | Path
    Path to the table to read

  Returns
  -------
  pd.DataFrame
    The table as a pandas dataframe
  """
  return pd.read_csv(path)

def load_tsv(path: str | Path) -> pd.DataFrame:
  """
  Loads a tsv table. ASCII tables with columns delimited by a white character,
  e.g. space or tab.

  Parameters
  ----------
  path : str | Path
    Path to the table to read

  Returns
  -------
  pd.DataFrame
    The table as a pandas dataframe
  """
  return pd.read_csv(path, delim_whitespace=True)

def load_parquet(path: str | Path) -> pd.DataFrame:
  """
  Loads a parquet table

  Parameters
  ----------
  path : str | Path
    Path to the table to read

  Returns
  -------
  pd.DataFrame
    The table as a pandas dataframe
  """
  return pd.read_parquet(path)

def load_table(path: str | Path) -> pd.DataFrame:
  """
  This function tries to detect the table type comparing the file extension and
  returns a pandas dataframe of the loaded table.
  
  Supported table types:
  
  - Fits tables: .fit, .fits, .fz
  - ASCII tables: .csv, .tsv, .dat
  - Heasarc tables: .tdat
  - Arrow tables: .parquet

  Parameters
  ----------
  path : str | Path
    Path to the table to read

  Returns
  -------
  pd.DataFrame
    The table as a pandas dataframe

  Raises
  ------
  ValueError
    Raises an error if the file extension can not be detected
  """
  func_map = {
    '.fit': load_fits,
    '.fits': load_fits,
    '.fz': load_fits,
    '.csv': load_csv,
    '.tsv': load_tsv,
    '.dat': load_tsv,
    '.parquet': load_parquet,
    '.tdat': load_tdat,
  }
  
  path = Path(path)
  load_func = func_map.get(path.suffix)
  if load_func is None:
    raise ValueError(
      'Can not infer the load function for this table based on suffix. '
      'Please, use a specific loader.'
    )
  return load_func(path)