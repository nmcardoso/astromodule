import re
import secrets
import subprocess
import tempfile
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Literal, Sequence, Tuple, Union

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord, match_coordinates_sky
from astropy.table import Table

from astromodule.io import load_table, save_table

RA_REGEX = re.compile(r'^ra_?\d*$', re.IGNORECASE)
DEC_REGEX = re.compile(r'^dec_?\d*$', re.IGNORECASE)

def _match_regex_against_sequence(
  regex: re.Pattern, 
  columns: Sequence[str]
) -> Tuple[int, str] | None:
  for i, col in enumerate(columns):
    if regex.match(col):
      return i, col
  return None


def _guess_coords_columns(
  df: pd.DataFrame,
  ra: str | None = None,
  dec: str | None = None,
) -> Tuple[str, str]:
  cols = df.columns.to_list()
  if ra is None:
    _, ra = _match_regex_against_sequence(RA_REGEX, cols)
  if dec is None:
    _, dec = _match_regex_against_sequence(DEC_REGEX, cols)
  if ra is None or dec is None:
    raise ValueError(
      "Can't guess RA or DEC columns, please, specify the columns names "
      "via `ra` and `dec` parameters"
    )
  return ra, dec
  

def _load_table(table: str | Path | pd.DataFrame | Table) -> pd.DataFrame:
  if isinstance(table, (str, Path)):
    return load_table(table)
  elif isinstance(table, pd.DataFrame):
    return table
  elif isinstance(table, Table):
    return table.to_pandas()


def sitilts_crossmatch(
  table1: pd.DataFrame | Table | str | Path,
  table2: pd.DataFrame | Table | str | Path,
  ra1: str | None = None,
  dec1: str | None = None,
  ra2: str | None = None,
  dec2: str | None = None,
  radius: float | u.Quantity = 1 * u.arcsec,
  join: Literal['1and2', '1or2', 'all1', 'all2', '1not2', '2not1', '1xor2'] = '1and2',
  find: Literal['all', 'best', 'best1', 'best2'] = 'best',
  fixcols: Literal['dups', 'all', 'none'] = 'dups',
  suffix1: str = '_1',
  suffix2: str = '_2',
  scorecol: str | None = 'xmatch_sep',
  fmt: Literal['fits', 'csv'] = 'fits',
):
  tmpdir = Path(tempfile.gettempdir())
  token = secrets.token_hex(8)
  tb1_path = tmpdir / f'xmatch_in1_{token}.{fmt}'
  tb2_path = tmpdir / f'xmatch_in2_{token}.{fmt}'
  out_path = tmpdir / f'xmatch_out_{token}.{fmt}'
  
  df1 = _load_table(table1)
  df2 = _load_table(table2)
  
  ra1, dec1 = _guess_coords_columns(df1, ra1, dec1)
  ra2, dec2 = _guess_coords_columns(df2, ra2, dec2)
  
  save_table(df1, tb1_path)
  save_table(df2, tb2_path)
  
  if isinstance(radius, u.Quantity):
    radius = int(radius.to(u.arcsec).value)
  else:
    radius = int(radius)
  
  cmd = [
    'stilts',
    'tmatch2',
    'matcher=sky',
    'progress=none',
    'runner=parallel',
    f'ifmt1={fmt}',
    f'ifmt2={fmt}',
    f'ofmt={fmt}',
    'omode=out',
    f'out={str(out_path.absolute())}',
    f'values1={ra1} {dec1}',
    f'values2={ra2} {dec2}',
    f'params={radius}',
    f'join={join}',
    f'find={find}',
    f'fixcols={fixcols}',
    f'suffix1={suffix1}',
    f'suffix2={suffix2}',
    f'scorecol={scorecol or "none"}',
    f'in1={str(tb1_path.absolute())}',
    f'in2={str(tb2_path.absolute())}',
  ]
  
  result = subprocess.run(
    cmd,
    stderr=subprocess.PIPE,
  )
  
  error = result.stderr.decode().strip()
  if error:
    print(error)
    
  tb1_path.unlink()
  tb2_path.unlink()
  
  df_out = load_table(out_path)
  out_path.unlink()
  return df_out



