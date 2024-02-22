"""
High-level interface to Legacy Survey data
"""


from io import BytesIO
from pathlib import Path
from typing import List, Literal, Sequence, Tuple, Union

import pandas as pd
import requests
from astropy import units as u
from astropy.table import Table

from astromodule.adql import AdqlColumn, AdqlDatabase, AdqlSchema, AdqlTable
from astromodule.io import (PathOrFile, TableLike, compress_fits,
                            download_file, parallel_function_executor,
                            read_table)
from astromodule.table import guess_coords_columns
from astromodule.tap import TapService
from astromodule.utils import append_query_params, iauname, iauname_path

LEGACY_RGB_URL = 'https://www.legacysurvey.org/viewer/jpeg-cutout'
LEGACY_RGB_URL_DEV = 'https://www.legacysurvey.org/viewer-dev/jpeg-cutout'
LEGACY_FITS_URL = 'https://www.legacysurvey.org/viewer/fits-cutout'
LEGACY_FITS_URL_DEV = 'https://www.legacysurvey.org/viewer-dev/fits-cutout'
LEGACY_TAP_SYNC_DR10 = 'https://datalab.noirlab.edu/tap/sync'


# mag_r | pixscale
# 14-15 | 0.45
# 15-16 | 0.35
# 16-17 | 0.3
# 17-18 | 0.2


class LS10Tractor(AdqlTable):
  release = AdqlColumn('release')
  brickid = AdqlColumn('brickid')
  brickname = AdqlColumn('brickname')
  objid = AdqlColumn('objid')
  brick_primary = AdqlColumn('brick_primary')
  maskbits = AdqlColumn('maskbits')
  fitbits = AdqlColumn('fitbits')
  type = AdqlColumn('type')
  ra = AdqlColumn('ra')
  dec = AdqlColumn('dec')
  ra_ivar	= AdqlColumn('ra_ivar')
  dec_ivar = AdqlColumn('dec_ivar')
  bx = AdqlColumn('bx')
  by = AdqlColumn('by')
  nobs_g = AdqlColumn('nobs_g') 
  nobs_r = AdqlColumn('nobs_r')
  nobs_i = AdqlColumn('nobs_i')
  nobs_z = AdqlColumn('nobs_z')
  nobs_w1	= AdqlColumn('nobs_w1')
  nobs_w2	= AdqlColumn('nobs_w2')
  nobs_w3	= AdqlColumn('nobs_w3')
  nobs_w4	= AdqlColumn('nobs_w4')
  rchisq_g = AdqlColumn('rchisq_g')
  rchisq_r = AdqlColumn('rchisq_r')
  rchisq_i = AdqlColumn('rchisq_i')
  rchisq_z = AdqlColumn('rchisq_z')
  rchisq_w1 = AdqlColumn('rchisq_w1')
  rchisq_w2 = AdqlColumn('rchisq_w2')
  rchisq_w3 = AdqlColumn('rchisq_w3')
  rchisq_w4 = AdqlColumn('rchisq_w4')
  mag_g = AdqlColumn('mag_g')
  mag_r = AdqlColumn('mag_r')
  mag_i = AdqlColumn('mag_i')
  mag_z = AdqlColumn('mag_z')
  mag_w1 = AdqlColumn('mag_w1')
  mag_w2 = AdqlColumn('mag_w2')
  mag_w3 = AdqlColumn('mag_w3')
  mag_w4 = AdqlColumn('mag_w4')

class LS10(AdqlSchema):
  tractor = LS10Tractor()

class LegacyClass(AdqlDatabase):
  DR10 = LS10()


Legacy = LegacyClass()
Legacy.config()


class LegacyService(TapService):
  """
  High-level Legacy Survey API interface
  
  Parameters
  ----------
  replace: bool, optional
    Replace file if exists in ``save_path`` location
  
  width: float, optional
    Stamp width.
  
  height: float, optional
    Stamp height.
  
  pixscale: float, optional
    Pixel scale of the sky.
  
  bands: str, optional
    Image bands
  
  layer: str, optional
    Legacy Survey image layer.
  
  use_dev: bool, optional
    Use the dev env of Legacy Cutout API
  
  fmt: str, optional
    File format. One of: ``jpg`` or ``fits``
  
  compress_fits: bool, optional
    Compress the downloaded fits stamp to ``fits.fz``
  
  workers: int, optional
    Maximum spawned threads when `batch_cutout` is called
  """
  def __init__(
    self,
    replace: bool = False,
    width: float = 256,
    height: float = 256,
    pixscale: float = 0.27,
    bands: str = 'grz',
    layer: str = 'ls-dr10',
    use_dev: bool = False,
    fmt: Literal['jpg', 'fits'] = 'jpg',
    compress_fits: bool = False,
    compress_type: str = 'HCOMPRESS_1',
    hcomp_scale: int = 3,
    quantize_level: int = 10,
    quantize_method: int = -1,
    workers: int = 3,
  ):
    super().__init__(LEGACY_TAP_SYNC_DR10)
    self.replace = replace
    self.width = width
    self.height = height
    self.pixscale = pixscale
    self.bands = bands
    self.layer = layer
    self.use_dev = use_dev
    self.fmt = fmt
    self.workers = workers
    self.compress_fits = compress_fits
    self.compress_type = compress_type
    self.hcomp_scale = hcomp_scale
    self.quantize_level = quantize_level
    self.quantize_method = quantize_method
    self.http_client = requests.Session()


  def cutout(
    self,
    ra: float,
    dec: float,
    save_path: Path = None,
    base_path: str | Path = '',
    mag_r: float = None,
  ) -> None:
    """
    Downloads a single Legacy Survey object RGB stamp defined by RA and DEC.

    Parameters
    ----------
    ra: float
      Right ascension of the object.
    dec: float
      Declination of the object.
    save_path: pathlib.Path, optional
      Path where downloaded file will be stored.
    base_path: str, pathlib.Path, optional
      The path that will be appended at beggining of every paths if ``save_path``
      is ``None``.
    """
    if self.fmt == 'jpg':
      url = LEGACY_RGB_URL_DEV if self.use_dev else LEGACY_RGB_URL
    else:
      url = LEGACY_FITS_URL_DEV if self.use_dev else LEGACY_FITS_URL

    if save_path is None:
      save_path = iauname_path(
        iaunames=iauname(ra=ra, dec=dec),
        prefix=Path(base_path),
        suffix=f'.{self.fmt}'
      )

    pixscale = self.get_pixscale(mag_r) if mag_r is not None else self.pixscale

    image_url = append_query_params(url, {
      'ra': ra,
      'dec': dec,
      'width': self.width,
      'height': self.height,
      'pixscale': pixscale,
      'bands': self.bands,
      'layer': self.layer
    })

    content = download_file(
      url=image_url,
      save_path=save_path,
      http_client=self.http_client,
      replace=self.replace,
      return_bytes=self.compress_fits,
    )

    if self.compress_fits:
      compress_fits(
        file=BytesIO(content),
        compress_type=self.compress_type,
        hcomp_scale=self.hcomp_scale,
        quantize_level=self.quantize_level,
        quantize_method=self.quantize_method,
        ext=0,
        save_path=save_path,
        replace=self.replace,
      )


  def batch_cutout(
    self,
    ra: Sequence[float],
    dec: Sequence[float],
    save_path: Sequence[Path] = None,
    base_path: str | Path = '',
    mag_r: Sequence[float] = None,
  ) -> Tuple[List[Path], List[Path]]:
    """
    Downloads a list of objects defined by RA and DEC coordinates.

    The ``ra``, ``dec`` and ``save_path`` lists are mandatory and
    must have same length.

    Parameters
    ----------
    ra: List[float]
      The list of RA coordinates of the desired objects.
    dec: List[float]
      The list of DEC coordinates of the desired objects.
    save_path: List[Path], optional
      The list of path where files should be saved.
    base_path: str, Path, optional
      The path that will be appended at beggining of every paths if ``save_path``
      is ``None``.
    """
    if save_path is None:
      save_path = iauname_path(
        iaunames=iauname(ra=ra, dec=dec),
        prefix=Path(base_path),
        suffix=f'.{self.fmt}'
      )

    if mag_r is None:
      params = [
        {
          'ra': _ra,
          'dec': _dec,
          'save_path': _save_path,
        }
        for _ra, _dec, _save_path in zip(ra, dec, save_path)
      ]
    else:
      params = [
        {
          'ra': _ra,
          'dec': _dec,
          'save_path': _save_path,
          'mag_r': _mag_r,
        }
        for _ra, _dec, _save_path, _mag_r in zip(ra, dec, save_path, mag_r)
      ]

    parallel_function_executor(
      self.cutout,
      params=params,
      workers=self.workers,
      unit='file'
    )

    success = [p for p in save_path if p.exists()]
    error = [p for p in save_path if not p.exists()]
    return success, error


  def get_pixscale(self, mag_r: float | Sequence[float]) -> float | Sequence[float]:
    if isinstance(mag_r, list):
      return [self.get_pixscale(m) for m in mag_r]

    if   14 <= mag_r < 15: return 0.45
    elif 15 <= mag_r < 16: return 0.35
    elif 16 <= mag_r < 17: return 0.3
    elif 17 <= mag_r < 18: return 0.2
    
    
  def crossmatch(
    self, 
    table: TableLike | PathOrFile, 
    columns: Sequence[str] | Sequence[AdqlColumn], 
    radius: float | u.Quantity,
    save_path: str | Path,
    ra_col: str = None,
    dec_col: str = None,
    where: AdqlColumn = None,
    workers: int = 3,
  ):
    query_template = """
    SELECT TOP 1 {columns}, 
      POWER(ra - ({ra}), 2) + POWER(dec - ({dec}), 2) AS ls_separation
    FROM ls_dr10.tractor
    WHERE 
      ra BETWEEN {ra_min} AND {ra_max} AND 
      dec BETWEEN {dec_min} AND {dec_max} AND
      mag_r BETWEEN 10 AND 23
    ORDER BY ls_separation ASC
    """.strip()
    df = read_table(table)
    ra_col, dec_col = guess_coords_columns(df, ra_col, dec_col)
    tb = Legacy.DR10.tractor
    queries = []
    
    if isinstance(radius, u.Quantity):
      radius = radius.to(u.deg).value
    else:
      radius = (radius * u.arcsec).to(u.deg).value
      
    for i, row in df.iterrows():
      ra = row[ra_col]
      dec = row[dec_col]
      # match_cond = (
      #   tb.ra.between(ra - radius, ra + radius) & 
      #   tb.dec.between(dec - radius, dec + radius)
      # )
      # where = where & match_cond if where is not None else match_cond
      query = query_template.format(
        columns=','.join([str(c) for c in columns]), 
        ra_min=ra-radius,
        ra_max=ra+radius,
        dec_min=dec-radius,
        dec_max=dec+radius,
        ra=ra,
        dec=dec,
      )
      queries.append(query)
    self.batch_sync_query(
      queries=queries, 
      save_paths=save_path, 
      join_outputs=True, 
      workers=workers
    )
    


if __name__ == '__main__':
  # ls = LegacyService(workers=6)
  # ls.batch_download_legacy_rgb(
  #   ra=[185.1458 + dx/2 for dx in range(20)],
  #   dec=[12.8624 + dy/2 for dy in range(20)],
  #   save_path=[Path(f'test/{i}.jpg') for i in range(20)]
  # )
  
  ls = LegacyService()
  df = pd.DataFrame(({'ra':[184.4924, 184.4922], 'dec': [7.2737, 7.1862]}))
  ls.crossmatch(df, ['mag_r', 'mag_g', 'mag_i', 'mag_z'], 3, 'test.csv')
