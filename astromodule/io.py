import re
from io import StringIO
from pathlib import Path
from typing import Dict, Sequence

import astropy
import numpy as np
import pandas as pd
from astropy.io import fits, votable
from astropy.table import Table


def load_table(
  path: str | Path, 
  columns: Sequence[str] | None = None,
  low_memory: bool = False,
  fmt: str | None = None,
  comment: str | None = None,
  na_values: Sequence[str] | Dict[str, Sequence[str]] = None,
  keep_default_na: bool = True,
  na_filter: bool = True,
) -> pd.DataFrame:
  """
  This function tries to detect the table type comparing the file extension and
  returns a pandas dataframe of the loaded table.
  
  Supported table types:
  
  - Fits tables: .fit, .fits, .fz
  - Votable: .vo, .vot, .votable, .xml
  - ASCII tables: .csv, .tsv, .dat
  - Heasarc tables: .tdat
  - Arrow tables: .parquet, .feather

  Parameters
  ----------
  path : str | Path
    Path to the table to be read.
  columns : Sequence[str] | None
    If specified, only the column names in list will be loaded. Can be used to
    reduce memory usage.
  low_memory : bool
    Internally process the file in chunks, resulting in lower memory use while 
    parsing, but possibly mixed type inference. To ensure no mixed types either 
    set False, or specify the type with the dtype parameter. Note that the 
    entire file is read into a single DataFrame regardless, use the chunksize 
    or iterator parameter to return the data in chunks. (Only valid with C parser).
  fmt : str | None
    Specify the file format manually to avoid inference by file extension. This
    parameter can be used to force a specific parser for the given file.
  comment : str | None
    Character indicating that the remainder of line should not be parsed. 
    If found at the beginning of a line, the line will be ignored altogether. 
    This parameter must be a single character. Like empty lines 
    (as long as skip_blank_lines=True), fully commented lines are ignored 
    by the parameter header but not by skiprows. For example, if comment='#', 
    parsing #empty\na,b,c\n1,2,3 with header=0 will result in 'a,b,c' being 
    treated as the header.
  na_values: Hashable, Iterable of Hashable or dict of {HashableIterable}
    Additional strings to recognize as `NA`/`NaN`. If `dict` passed, specific 
    per-column `NA` values. By default the following values are interpreted 
    as `NaN`: “ “, “#N/A”, “#N/A N/A”, “#NA”, “-1.#IND”, “-1.#QNAN”, “-NaN”, 
    “-nan”, “1.#IND”, “1.#QNAN”, “<NA>”, “N/A”, “NA”, “NULL”, “NaN”, “None”, 
    “n/a”, “nan”, “null “.
  keep_default_na : bool 
    Whether or not to include the default `NaN` values when parsing the data. 
    Depending on whether `na_values` is passed in, the behavior is as follows:

    - If `keep_default_na` is `True`, and `na_values` are specified, 
    `na_values` is appended to the default NaN values used for parsing.
    - If `keep_default_na` is `True`, and `na_values` are not specified, only the 
    default `NaN` values are used for parsing.
    - If `keep_default_na` is `False`, and `na_values` are specified, only 
    the `NaN` values specified na_values are used for parsing.
    - If `keep_default_na` is `False`, and `na_values` are not specified, 
    no strings will be parsed as `NaN`.

    Note that if `na_filter` is passed in as `False`, the `keep_default_na` and 
    `na_values` parameters will be ignored.
  na_filter : bool
    Detect missing value markers (empty strings and the value of `na_values`). 
    In data without any `NA` values, passing `na_filter=False` can improve the 
    performance of reading a large file.

  Notes
  -----
  The Transportable Database Aggregate Table (TDAT) type is a data structure 
  created by NASA's Heasarc project and a very simple parser was implemented
  in this function due to lack of support in packages like pandas and astropy. 
  For more information, see [#TDAT]_

  Returns
  -------
  pd.DataFrame
    The table as a pandas dataframe

  Raises
  ------
  ValueError
    Raises an error if the file extension can not be detected
    
  References
  ----------
  .. [#TDAT] Transportable Database Aggregate Table (TDAT) Format.
      `<https://heasarc.gsfc.nasa.gov/docs/software/dbdocs/tdat.html>`_
  """
  path = Path(path)
  fmt = fmt or path.suffix
  if fmt.startswith('.'):
    fmt = fmt[1:]

  if fmt in ('fit', 'fits', 'fz'):
    with fits.open(path) as hdul:
      table_data = hdul[1].data
      table = Table(data=table_data)
      df = table.to_pandas()
      if columns:
        df = df[columns]
      return df
  elif fmt in ('dat', 'tsv'):
    return pd.read_csv(
      path, 
      delim_whitespace=True, 
      usecols=columns, 
      low_memory=low_memory,
      comment=comment,
      na_values=na_values,
      keep_default_na=keep_default_na,
      na_filter=na_filter,
    )
  elif fmt == 'csv':
    return pd.read_csv(
      path, 
      usecols=columns, 
      low_memory=low_memory,
      comment=comment,
      na_values=na_values,
      keep_default_na=keep_default_na,
      na_filter=na_filter,
    )
  elif fmt == 'parquet':
    return pd.read_parquet(
      path, 
      columns=columns,
    )
  elif fmt == 'feather':
    return pd.read_feather(
      path, 
      columns=columns
    )
  elif fmt == 'tdat':
    path = Path(path)
    content = path.read_text()
    header = re.findall(r'line\[1\] = (.*)', content)[0].replace(' ', '|')
    data = content.split('<DATA>\n')[-1].split('<END>')[0].replace('|\n', '\n')
    tb = header + '\n' + data
    return pd.read_csv(
      StringIO(tb), 
      sep='|', 
      usecols=columns, 
      low_memory=low_memory
    )
  elif fmt in ('vo', 'vot', 'votable', 'xml'):
    result = votable.parse_single_table(path)
    table = result.to_table(use_names_over_ids=True)
    # table = result.get_first_table().to_table(use_names_over_ids=True)
    df = table.to_pandas()
    if columns:
      df = df[columns]
    return df

  raise ValueError(
    'Can not infer the load function for this table based on suffix. '
    'Please, use a specific loader.'
  )


def save_table(data: pd.DataFrame, path: str | Path):
  path = Path(path)
  if path.suffix in ('.fit', '.fits'):
    Table.from_pandas(data).write(path, overwrite=True)
  elif path.suffix == '.csv':
    data.to_csv(path, index=False)
  elif path.suffix == '.parquet':
    data.to_parquet(path, index=False)
  elif path.suffix == '.dat':
    data.to_csv(path, index=False, sep=' ')
  elif path.suffix == '.tsv':
    data.to_csv(path, index=False, sep='\t')
  elif path.suffix == '.html':
    data.to_html(path, index=False)
  elif path.suffix == '.feather':
    data.to_feather(path, index=False)