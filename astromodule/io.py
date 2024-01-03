import re
from io import StringIO
from pathlib import Path

import astropy
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.table import Table


def load_tdat(path: str | Path) -> pd.DataFrame:
  path = Path(path)
  content = path.read_text()
  header = re.findall(r'line\[1\] = (.*)', content)[0].replace(' ', '|')
  data = content.split('<DATA>\n')[-1].split('<END>')[0].replace('|\n', '\n')
  tb = header + '\n' + data
  df = pd.read_csv(StringIO(tb), sep='|')
  return df

def load_fits(path: str | Path) -> pd.DataFrame:
  with fits.open(path) as hdul:
    table_data = hdul[1].data
    table = Table(data=table_data)
    return table.to_pandas()

def load_csv(path: str | Path) -> pd.DataFrame:
  return pd.read_csv(path)

def load_tsv(path: str | Path) -> pd.DataFrame:
  return pd.read_csv(path, delim_whitespace=True)

def load_parquet(path: str | Path) -> pd.DataFrame:
  return pd.read_parquet(path)

def load_table(path: str | Path) -> pd.DataFrame:
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