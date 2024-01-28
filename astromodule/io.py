"""
Input/Output operations
"""

import bz2
import concurrent.futures
import re
from io import BufferedIOBase, RawIOBase, StringIO, TextIOBase
from pathlib import Path
from typing import Any, BinaryIO, Callable, Dict, Sequence

import numpy as np
import pandas as pd
import requests
from astropy.io import fits, votable
from astropy.table import Table
from tqdm import tqdm

RANDOM_SEED = 42
PathOrFile = str | Path | BufferedIOBase | RawIOBase | TextIOBase
TableLike = Table | pd.DataFrame

def read_table(
  path: TableLike | PathOrFile,
  fmt: str | None = None,
  columns: Sequence[str] | None = None,
  low_memory: bool = False,
  comment: str | None = None,
  na_values: Sequence[str] | Dict[str, Sequence[str]] = None,
  keep_default_na: bool = True,
  na_filter: bool = True,
) -> pd.DataFrame:
  """
  This function tries to detect the table type comparing the file extension and
  returns a pandas dataframe of the loaded table.
  
  Supported table types:
  
    =============== ===========================
    Table Type      Extensions
    =============== ===========================
    Fits            .fit, .fits, .fz
    Votable         .vo, .vot, .votable, .xml
    ASCII           .csv, .tsv, .dat
    Heasarc         .tdat
    Arrow           .parquet, .feather
    =============== ===========================

  Parameters
  ----------
  path : str or Path
    Path to the table to be read.
  
  fmt : str | None
    Specify the file format manually to avoid inference by file extension. This
    parameter can be used to force a specific parser for the given file.
  
  columns : Sequence[str] | None
    If specified, only the column names in list will be loaded. Can be used to
    reduce memory usage.
  
  low_memory : bool
    Internally process the file in chunks, resulting in lower memory use while 
    parsing, but possibly mixed type inference. To ensure no mixed types either 
    set False, or specify the type with the dtype parameter. Note that the 
    entire file is read into a single DataFrame regardless, use the chunksize 
    or iterator parameter to return the data in chunks. (Only valid with C parser).
    
    .. note::
      Used only for ASCII tables, ignored by other types of tables.
  
  comment : str | None
    Character indicating that the remainder of line should not be parsed. 
    If found at the beginning of a line, the line will be ignored altogether. 
    This parameter must be a single character. Like empty lines 
    (as long as ``skip_blank_lines=True``), fully commented lines are ignored 
    by the parameter header but not by skiprows. For example, if ``comment='#'``, 
    parsing ``#empty\\na,b,c\\n1,2,3`` with ``header=0`` will result in 
    ``'a,b,c'`` being treated as the header.
    
    .. note::
      Used only for ASCII tables, ignored by other types of tables.
  
  na_values: Hashable, Iterable of Hashable or dict of {HashableIterable}
    Additional strings to recognize as ``NA``/``NaN``. If ``dict`` passed, specific 
    per-column ``NA`` values. By default the following values are interpreted 
    as `NaN`: “ “, “#N/A”, “#N/A N/A”, “#NA”, “-1.#IND”, “-1.#QNAN”, “-NaN”, 
    “-nan”, “1.#IND”, “1.#QNAN”, “<NA>”, “N/A”, “NA”, “NULL”, “NaN”, “None”, 
    “n/a”, “nan”, “null “.
    
    .. note::
      Used only for ASCII tables, ignored by other types of tables.
  
  keep_default_na : bool 
    Whether or not to include the default ``NaN`` values when parsing the data. 
    Depending on whether ``na_values`` is passed in, the behavior is as follows:

    - If ``keep_default_na`` is ``True``, and ``na_values`` are specified, 
      `na_values` is appended to the default NaN values used for parsing.
    - If ``keep_default_na`` is ``True``, and ``na_values`` are not specified, only the 
      default ``NaN`` values are used for parsing.
    - If ``keep_default_na`` is ``False``, and ``na_values`` are specified, only 
      the ``NaN`` values specified na_values are used for parsing.
    - If ``keep_default_na`` is ``False``, and ``na_values`` are not specified, 
      no strings will be parsed as ``NaN``.

    Note that if ``na_filter`` is passed in as ``False``, the ``keep_default_na`` and 
    ``na_values`` parameters will be ignored.
    
    .. note::
      Used only for ASCII tables, ignored by other types of tables.
  
  na_filter : bool
    Detect missing value markers (empty strings and the value of ``na_values``). 
    In data without any ``NA`` values, passing ``na_filter=False`` can improve the 
    performance of reading a large file.
    
    .. note::
      Used only for ASCII tables, ignored by other types of tables.

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
  is_file_like = False
  if isinstance(path, (str, Path)):
    path = Path(path)
    fmt = fmt or path.suffix
  elif isinstance(path, pd.DataFrame):
    return path
  elif isinstance(path, Table):
    df = path.to_pandas()
    if columns:
      df = df[columns]
    return df
  elif isinstance(path, (RawIOBase, BufferedIOBase, TextIOBase)):
    is_file_like = True
  
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
    if is_file_like: raise ValueError('Not implemented for file-like objects')
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


def write_table(data: TableLike, path: PathOrFile, fmt: str | None = None):
  if isinstance(path, str):
    fmt = fmt or Path(path).suffix
    Path(path).parent.mkdir(parents=True, exist_ok=True)
  elif isinstance(path, Path):
    fmt = fmt or path.suffix
    path.parent.mkdir(parents=True, exist_ok=True)
    path = str(path.absolute())
  
  if isinstance(data, Table):
    data = data.to_pandas()
  
  if fmt.startswith('.'):
    fmt = fmt[1:]
  
  if fmt in ('fit', 'fits'):
    Table.from_pandas(data).write(path, overwrite=True, format='fits')
  elif fmt == 'csv':
    data.to_csv(path, index=False)
  elif fmt == 'parquet':
    data.to_parquet(path, index=False)
  elif fmt == 'dat':
    data.to_csv(path, index=False, sep=' ')
  elif fmt == 'tsv':
    data.to_csv(path, index=False, sep='\t')
  elif fmt == 'html':
    data.to_html(path, index=False)
  elif fmt == 'feather':
    data.to_feather(path, index=False)
  elif fmt in ('vo', 'vot', 'votable', 'xml'):
    t = Table.from_pandas(data)
    votable.writeto(t, path)
    
    

def compress_fits(
  file: PathOrFile,
  compress_type: str = 'HCOMPRESS_1',
  hcomp_scale: int = 3,
  quantize_level: int = 10,
  quantize_method: int = -1,
  ext: int = 0,
  save_path: str | Path = None,
  replace: bool = True,
):
  hdul = fits.open(file)

  if ext >= len(hdul):
    raise ValueError(f'Trying to access ext {ext}, max ext is {len(hdul)-1}')

  if save_path.exists() and not replace:
    return None

  comp = None

  try:
    comp = fits.CompImageHDU(
      data=hdul[ext].data,
      header=hdul[ext].header,
      compression_type=compress_type,
      hcomp_scale=hcomp_scale,
      quantize_level=quantize_level,
      quantize_method=quantize_method,
      dither_seed=RANDOM_SEED,
    )
    if save_path:
      comp.writeto(
        save_path,
        overwrite=replace,
      )
  except OSError as e:
    pass

  return comp



def download_file(
  url: str,
  save_path: str | Path,
  replace: bool = False,
  http_client: requests.Session = None,
  extract: bool = False,
  return_bytes: bool = False,
) -> bytes | None:
  save_path = Path(save_path)

  if not replace and save_path.exists():
    return None

  http_client = http_client or requests

  if not save_path.parent.exists():
    save_path.parent.mkdir(parents=True, exist_ok=True)

  r = http_client.get(url, allow_redirects=True)

  if r.status_code == 200:
    if extract:
      file_bytes = bz2.decompress(r.content)
    else:
      file_bytes = r.content

    if return_bytes:
      return file_bytes

    with open(str(save_path.resolve()), 'wb') as f:
      f.write(file_bytes)

  return None


def parallel_function_executor(
  func: Callable,
  params: Sequence[Dict[str, Any]] = [],
  workers: int = 2,
  unit: str = 'it'
):
  with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
    futures = []

    for i in range(len(params)):
      futures.append(executor.submit(
        func,
        **params[i]
      ))

    for future in tqdm(
      concurrent.futures.as_completed(futures),
      total=len(futures),
      unit=unit
    ):
      try:
        future.result()
      except Exception as e:
        pass


def batch_download_file(
  urls: Sequence[str],
  save_path: Sequence[str] | Sequence[Path],
  replace: bool = False,
  http_client: requests.Session = None,
  workers: int = 2,
):
  params = [
    {
      'url': _url,
      'save_path': Path(_save_path),
      'replace': replace,
      'http_client': http_client
    }
    for _url, _save_path in zip(urls, save_path)
  ]
  parallel_function_executor(download_file, params, workers=workers, unit='file')


if __name__ == '__main__':
  df = pd.DataFrame({'RA': [193.20100, 193.31000], 'DEC': [-15.43320, -15.38000]})
  write_table(df, 'test.xml')