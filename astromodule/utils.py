"""
Utility module
"""


from pathlib import Path
from typing import Any, Sequence

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord


def iauname(
  ra: float | np.ndarray,
  dec: float | np.ndarray
) -> str | Sequence[str]:
  """
  Receives the angular position(s) of the object(s) and returns IAU2000 name(s)

  Parameters
  ----------
  ra: float or array of float
    The right ascension of the object(s).
  dec: float or array of float
    The declination of the object(s).

  Example
  --------
  >>> iauname(187.70592, 12.39112)
  'J123049.42+122328.03'

  Returns
  -------
  str or list of str
    The formated IAU name of the object(s)
  """
  coord = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
  ra_str = coord.ra.to_string(unit=u.hourangle, sep='', precision=2, pad=True)
  dec_str = coord.dec.to_string(sep='', precision=1, alwayssign=True, pad=True)
  if isinstance(ra_str, np.ndarray):
    r = [f'J{_ra_str}{_dec_str}' for _ra_str, _dec_str in zip(ra_str, dec_str)]
  else:
    r = f'J{ra_str}{dec_str}'
  return r



def iauname_path(
  iaunames: str | Sequence[str] = None,
  ra: float | Sequence[float] = None,
  dec: float | Sequence[float] = None,
  prefix: str | Path = '',
  suffix: str = '',
  flat: bool = False,
  return_str: bool = False,
) -> Path | Sequence[Path]:
  """
  Calculate the nested path for a given iauname

  Parameters
  ----------
  iaunames: str, List[str], optional
    Object iauname. The iauname or RA and DEC must be passed, if ``iaunames`` is
    ``None``, this function computes the iauname using the ``ra`` and ``dec``
    parameters
  ra: float, List[float], optional
    Object RA, used only if ``iaunames`` is ``None``
  dec: float, List[float], optional
    Object DEC, used only if ``iaunames`` is ``None``
  prefix: str, Path, optional
    Path that will be prepended at the begin of all paths
  suffix: str, optional
    Suffix that will be appended at the end of all paths
  flat: bool, optional
    Create the flat path with all files inside a same parent folder. This is
    not recomended for big datasets
  return_str: bool, optional
    Cast all paths to string before returning

  Example
  -------
  iaunames_path('J123049.42+122328.03', '.png')
  Path('J123/J123049.42+122328.03.png')

  Returns
  -------
  Path, List[Path]
    The iauname path
  """
  if iaunames is None:
    iaunames = iauname(ra, dec)

  if flat:
    mapping = lambda x:  Path(prefix) / (x + suffix)
  else:
    mapping = lambda x: Path(prefix) / x[:4] / (x + suffix)

  prep_output = lambda x: str(x) if return_str else x

  if isinstance(iaunames, str):
    return prep_output(mapping(iaunames))
  else:
    return [prep_output(mapping(x)) for x in iaunames]
  
  
  
def append_query_params(url: str, query_params: dict) -> str:
  index = url.find('?')
  new_url = ''

  query_string = '&'.join([f'{k}={v}' for (k, v) in query_params.items()])

  if index > -1:
    base = url[:index]
    rest = url[index:] + '&' + query_string
    new_url = base + rest
  else:
    new_url = url + '?' + query_string

  return new_url



def filter_dict(obj: dict, mask: Sequence[Any]):
  return {k: v for k, v in obj.items() if k in mask}