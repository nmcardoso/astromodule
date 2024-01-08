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


def table_knn(
  left: str | Path | pd.DataFrame | Table,
  right: str | Path | pd.DataFrame | Table,
  nthneighbor: int = 1,
  left_ra: str = 'ra',
  left_dec: str = 'dec',
  right_ra: str = 'ra',
  right_dec: str = 'dec',
) -> Tuple[np.ndarray, np.ndarray]:
  left_df = _load_table(left)
  right_df = _load_table(right)
  
  left_coords = SkyCoord(
    ra=left_df[left_ra].values,
    dec=left_df[left_dec].values, 
    unit=u.deg,
  )
  right_coords = SkyCoord(
    ra=right_df[right_ra].values,
    dec=right_df[right_dec].values,
    unit=u.deg,
  )
  
  idx, d, _ = match_coordinates_sky(
    left_coords,
    right_coords,
    nthneighbor=nthneighbor
  )

  return np.array(idx), np.array(d)


def crossmatch(
  left: str | Path | pd.DataFrame | Table,
  right: str | Path | pd.DataFrame | Table,
  radius: float | u.Quantity = 1*u.arcsec,
  join: Literal['inner', 'left'] = 'inner',
  nthneighbor: int = 1,
  left_ra: str | None = None,
  left_dec: str | None = None,
  left_columns: Sequence[str] | None = None,
  right_ra: str | None = None,
  right_dec: str | None = None,
  right_columns: Sequence[str] | None = None,
  include_sep: bool = True,
):
  left_df = _load_table(left)
  left_ra, left_dec = _guess_coords_columns(left_df, left_ra, left_dec)
  right_df = _load_table(right)
  right_ra, right_dec = _guess_coords_columns(right_df, right_ra, right_dec)
  
  idx, d = table_knn(
    left_df, 
    right_df, 
    nthneighbor=nthneighbor, 
    left_ra=left_ra,
    left_dec=left_dec,
    right_ra=right_ra,
    right_dec=right_dec,
  )
  
  if isinstance(radius, u.Quantity):
    radius = radius.to(u.deg).value
  else:
    radius = u.Quantity(radius, unit=u.arcsec).to(u.deg).value

  mask = d < radius

  left_idx = mask.nonzero()[0]
  right_idx = idx[mask]
  
  if left_columns is not None:
    left_df = left_df[left_columns].copy()
  if right_columns is not None:
    right_df = right_df[right_columns].copy()
  
  if join == 'inner':
    left_masked_df = left_df.iloc[left_idx]
    right_masked_df = right_df.iloc[right_idx]
    match_df = left_masked_df.copy(deep=True)
    for col in right_masked_df.columns.to_list():
      if not col in match_df.columns:
        match_df[col] = right_masked_df[col].to_numpy()
        # TODO: include a flag "replace" in this method to indicate if t2 must
        # replace or not t1 columns. This implementation consider replace=False.
    if include_sep:
      match_df['xmatch_sep'] = d[mask]
  elif join == 'left':
    right_masked_df = right_df.iloc[right_idx]
    cols = [col for col in right_masked_df.columns if col not in left_df.columns]
    match_df = left_df.copy(deep=True)
    match_df.loc[left_idx, cols] = right_masked_df[cols].values
    if include_sep:
      match_df.loc[left_idx, 'xmatch_sep'] = d[mask]
  return match_df

  # left_df_masked = left_df.iloc[primary_idx]
  # right_df_masked = right_df.iloc[secondary_idx]

  # left_df_subsample = left_df_masked[left_columns].copy() \
  #   if left_columns is not None else left_df_masked.copy()
  # right_df_subsample = right_df_masked[right_columns].copy() \
  #   if right_columns.columns is not None else right_df_masked.copy()

  # for col in right_df_subsample.columns.tolist():
  #   left_df_subsample[col] = right_df_subsample[col].to_numpy()
  #   # TODO: include a flag "replace" in this method to indicate if t2 must
  #   # replace or not t1 columns. This implementation consider replace=True.

  # r = CrossMatchResult()
  # r.distance = d[mask]
  # r.primary_idx = primary_idx
  # r.secondary_idx = secondary_idx
  # r.table = df1_subsample
  


@dataclass
class DropDuplicatesResult:
  df: pd.DataFrame
  distances: np.ndarray
  n_iterations: int
  drop_count: int

  
def drop_duplicates(
  table: str | Path | pd.DataFrame | Table,
  radius: float | u.Quantity = 1*u.arcsec,
  ra: str | None = None,
  dec: str | None = None,
  columns: Sequence[str] | None = None,
  max_iterations: int = 20,
) -> DropDuplicatesResult:
  if isinstance(radius, u.Quantity):
    radius = radius.to(u.deg).value
  else:
    radius = u.Quantity(radius, unit=u.arcsec).to(u.deg).value
  
  df = _load_table(table)
  ra, dec = _guess_coords_columns(df, ra, dec)
  df_coords = df[[ra, dec]].copy(deep=True)
  total_drop_count = 0
  drop_count = -1
  iteration = 0
  
  while (drop_count != 0 and iteration <= max_iterations):
    print(drop_count, iteration)
    idx, d = table_knn(
      df_coords, 
      df_coords, 
      left_ra=ra, 
      left_dec=dec, 
      right_ra=ra, 
      right_dec=dec, 
      nthneighbor=2
    )

    mask = d < radius
    primary_idx = mask.nonzero()[0]
    secondary_idx = idx[mask]
    removed_idx = []

    for pid, sid in zip(primary_idx, secondary_idx):
      if sid not in removed_idx:
        removed_idx.append(pid)

    del_mask = np.isin(idx, removed_idx, invert=True).nonzero()[0]
    len_copy_df = len(df_coords)
    df_coords = df_coords.iloc[del_mask].copy()
    
    drop_count = len_copy_df - len(df_coords)
    total_drop_count += drop_count
    iteration += 1
  
  d = d[del_mask]
  final_df = df.iloc[df_coords.index]
  if columns is not None:
    final_df = final_df[columns]
  
  return DropDuplicatesResult(
    df=final_df,
    distances=d,
    n_iterations=iteration,
    drop_count=total_drop_count
  )



  
def stilts_crossmatch(
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
) -> pd.DataFrame:
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



def stilts_unique(
  table: pd.DataFrame | Table | str | Path,
  radius: float | u.Quantity,
  action: Literal['identify', 'keep0', 'keep1', 'wide2', 'wideN'] = 'keep1',
  ra: str | None = None,
  dec: str | None = None,
  fmt: Literal['fits', 'csv'] = 'fits',
) -> pd.DataFrame:
  tmpdir = Path(tempfile.gettempdir())
  token = secrets.token_hex(8)
  in_path = tmpdir / f'xmatch_in_{token}.{fmt}'
  out_path = tmpdir / f'xmatch_out_{token}.{fmt}'
  
  df = _load_table(table)
  
  ra, dec = _guess_coords_columns(df, ra, dec)
  
  save_table(df, in_path)
  
  if isinstance(radius, u.Quantity):
    radius = int(radius.to(u.arcsec).value)
  else:
    radius = int(radius)
    
  cmd = [
    'stilts',
    'tmatch1',
    'matcher=sky',
    f'params={radius}',
    f'values={ra} {dec}',
    f'action={action}',
    'progress=none',
    'runner=parallel',
    f'ifmt={fmt}',
    'omode=out',
    f'ofmt={fmt}',
    f'out={str(out_path.absolute())}',
    f'in={str(in_path.absolute())}',
  ]
  
  result = subprocess.run(
    cmd,
    stderr=subprocess.PIPE,
  )
  
  error = result.stderr.decode().strip()
  if error:
    print(error)
    
  in_path.unlink()
  
  df_out = load_table(out_path)
  out_path.unlink()
  return df_out


if __name__ == '__main__':
  pass
