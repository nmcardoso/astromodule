"""
This module performs requests to `splus.cloud <https://splus.cloud>`_ server 
over https

Features
--------
* Download a single rgb image colored using Lupton or Trilogy method
* Donwload a single fits image of single band
* Fast batch download of rgb images using multiprocessing
* Fast batch download of fits images using multiprocessing
* Single async database query
* Fast batch database queries using multiprocessing

Authors
-------
Natanael Magalhães Cardoso <`natanael.net <https://natanael.net>`_>
"""

import concurrent.futures
import os
import secrets
import tempfile
from datetime import datetime, timedelta
from functools import wraps
from io import BufferedIOBase, BytesIO, RawIOBase
from multiprocessing import Lock
from pathlib import Path
from time import sleep
from typing import Callable, List, Literal, Union
from urllib.parse import urljoin, urlparse

import requests
import tqdm

from astromodule.io import download_file, write_table
from astromodule.table import concat_tables

BASE_URL = 'https://splus.cloud/api/'
LOGIN_ROUTE = 'auth/login'
LUPTON_ROUTE = 'get_lupton_image/{ra}/{dec}/{size}/{r_band}/{g_band}/{b_band}/{stretch}/{Q}'
TRILOGY_ROUTE = 'get_image/{ra}/{dec}/{size}/{r_band}-{g_band}-{b_band}/{noise}/{saturation}'
FITS_ROUTE = 'get_cut/{ra}/{dec}/{size}/{band}'
PUBLIC_TAP_ROUTE = '/public-TAP/tap/async/'
PRIVATE_TAP_ROUTE = '/tap/tap/async/'
SPLUS_USER = os.environ.get('SPLUS_USER')
SPLUS_PASS = os.environ.get('SPLUS_PASS')



def update_authorization(f: Callable):
  """
  Decorator that can be placed on functions that needs S-PLUS authentication
  This decorator will update authorization token before the function call if 
  needed

  Parameters
  ----------
  f: the function that will be decorated

  Returns
  -------
  Callable
    The decorated function
  """
  @wraps(f)
  def wrapper(*args, **kwargs):
    this: SplusService = args[0]
    updated = this.update_token()
    if updated:
      this.client.headers.update({
        'Authorization': f'Token {this.token["value"]}'
      })
    return f(*args, **kwargs)
  return wrapper



class SplusService:
  """
  This service class interacts with splus.cloud server over https

  Parameters
  ----------
  username: str (optional)
    The username used in splus.cloud authentication, defaults to ``SPLUS_USER``
    environment variable
  password: str (optional)
    The password used in splus.cloud authentication, defaults to ``SPLUS_PASS``
    environment variable
  """
  _lock: Lock = Lock()


  def __init__(self, username: str = SPLUS_USER, password: str = SPLUS_PASS):
    self.credentials = {
      'username': username,
      'password': password
    }
    self.token: dict = None
    self.token_duration = timedelta(hours=1)
    self.client = requests.Session()


  def update_token(self) -> bool:
    """
    Updates splus.cloud authorization token

    Returns
    -------
    bool
      ``True`` if the token was updated and ``False`` otherwise
    """
    now = datetime.now()
    if self.token is None or self.token['timestamp'] < (now - self.token_duration):
      with SplusService._lock:
        if self.token is None or self.token['timestamp'] < (now - self.token_duration):
          resp = self.client.post(
            self._get_url(LOGIN_ROUTE),
            json=self.credentials
          )
          if resp.status_code == 200:
            if 'application/json' in resp.headers['Content-Type']:
              resp_body = resp.json()
              if 'token' in resp_body:
                self.token = {
                  'value': resp_body['token'],
                  'timestamp': datetime.now()
                }
                return True # updated
    return False # using cache


  def download_lupton_rgb(
    self,
    ra: float,
    dec: float,
    save_path: Union[str, Path],
    replace: bool = False,
    size: int = 128,
    r_band: str = 'I',
    g_band: str = 'R',
    b_band: str = 'G',
    stretch: Union[int, float] = 3,
    Q: Union[int, float] = 8
  ):
    """
    Downloads a single Lupton RGB image based on object posistion, this method
    accepts arguments to customize Lupton's parameters

    Parameters
    ----------
    ra: float
      The right ascension in degrees
    dec: float
      The declination in degrees
    save_path: str or Path
      The path where the file will be saved
    replace: bool (optional)
      This method checks if a file exists in ``save_path`` location before the
      download. If this parameters is ``True`` and a file exists in ``save_path``
      location, this method will ovewrite the existing file. If this parameter
      is ``False`` and a file exists in ``save_path`` location, this method will
      skip the download
    size: int (optional)
      The image size in pixels
    r_band: str (optional)
      The S-PLUS band that will be mapped as R channel of the RGB image
    g_band: str (optional)
      The S-PLUS band that will be mapped as G channel of the RGB image
    b_band: str (optional)
      The S-PLUS band that will be mapped as B channel of the RGB image
    stretch: int or float (optional)
      The ``stretch`` parameter of Lupton's formula
    Q: int or float (optional)
      The ``Q`` parameter of Lupton's formula
    """
    self._download_image(
      LUPTON_ROUTE,
      save_path=save_path,
      replace=replace,
      ra=str(ra),
      dec=str(dec),
      size=str(size),
      r_band=str(r_band),
      g_band=str(g_band),
      b_band=str(b_band),
      stretch=str(stretch),
      Q=str(Q)
    )


  def download_trilogy_rgb(
    self,
    ra: float,
    dec: float,
    save_path: Union[str, Path],
    replace: bool = False,
    size: int = 128,
    r_band: List[str] = ['R', 'I', 'F861', 'Z'],
    g_band: List[str] = ['G', 'F515', 'F660'],
    b_band: List[str] = ['U', 'F378', 'F395', 'F410', 'F430'],
    noise: float = 0.15,
    saturation: float = 0.15
  ):
    """
    Downloads a single Trilogy RGB image based on object posistion, this method
    accepts arguments to customize Trilogy parameters

    Parameters
    ----------
    ra: float
      The right ascension in degrees
    dec: float
      The declination in degrees
    save_path: str or Path
      The path where the file will be saved
    replace: bool (optional)
      This method checks if a file exists in ``save_path`` location before the
      download. If this parameters is ``True`` and a file exists in ``save_path``
      location, this method will ovewrite the existing file. If this parameter
      is ``False`` and a file exists in ``save_path`` location, this method will
      skip the download
    size: int (optional)
      The image size in pixels
    r_band: str (optional)
      The S-PLUS band that will be mapped as R channel of the RGB image
    g_band: str (optional)
      The S-PLUS band that will be mapped as G channel of the RGB image
    b_band: str (optional)
      The S-PLUS band that will be mapped as B channel of the RGB image
    noise: int or float (optional)
      The ``noise`` parameter of Trilogy algorithm
    saturation: int or float (optional)
      The ``saturation`` parameter of Trilogy algorithm
    """
    self._download_image(
      TRILOGY_ROUTE,
      ra=ra,
      dec=dec,
      save_path=save_path,
      replace=replace,
      size=size,
      r_band=','.join(r_band),
      g_band=','.join(g_band),
      b_band=','.join(b_band),
      noise=noise,
      saturation=saturation
    )


  def download_fits(
    self,
    ra: float,
    dec: float,
    save_path: Union[str, Path],
    replace: bool = False,
    size: int = 128,
    band: str = 'R'
  ):
    """
    Downloads a single FITS image based on object posistion

    Parameters
    ----------
    ra: float
      The right ascension in degrees
    dec: float
      The declination in degrees
    save_path: str or Path
      The path where the file will be saved
    replace: bool (optional)
      This method checks if a file exists in ``save_path`` location before the
      download. If this parameters is ``True`` and a file exists in ``save_path``
      location, this method will ovewrite the existing file. If this parameter
      is ``False`` and a file exists in ``save_path`` location, this method will
      skip the download
    size: int (optional)
      The image size in pixels
    band: str (optional)
      The S-PLUS band of the fits file
    """
    self._download_image(
      FITS_ROUTE,
      ra=ra,
      dec=dec,
      save_path=save_path,
      replace=replace,
      size=size,
      band=band
    )


  def batch_image_download(
    self,
    ra: List[float],
    dec: List[float],
    save_path: List[Union[str, Path]],
    img_type: Literal['trilogy', 'lupton', 'fits'] = 'lupton',
    workers: int = None,
    **kwargs
  ):
    """
    Downloads a single Lupton RGB image based on object posistion, this method
    accepts arguments to customize Lupton's parameters

    Parameters
    ----------
    ra: list of float
      A list of right ascension in degrees
    dec: list of float
      A list of declination in degrees
    save_path: list of str or list of Path
      A list of paths where the file will be saved
    img_type: str (optional)
      One of: ``lupton``, ``trilogy`` or ``fits``.
      Defaults to ``lupton``
    workers: int (optional)
      The  number of parallel processes that will be spawned. Default to a
      single process
    kwargs: Any (optional)
      Any optional parameter of :meth:`.download_lupton_rgb` if ``img_type='lupton'``,
      or  any optional parameter of :meth:`.download_trilogy_rgb`
      if ``img_type='trilogy'`` or any optional parameter of
      :meth:`.download_fits` if ``img_type='fits'``.
      These parameters must have the same type as the mentioned functions,
      i.e. pass a single value instead of a list of values and all images
      will be downloaded with the same parameter

    Examples
    --------
      >>> ra = [172.4, 193.9, 63.3]
      >>> dec = [0.42, 2.63, -1.24]
      >>> paths = ['fig1.png', 'fig2.png', 'fig3.png']
      >>> service.batch_image_download(ra, dec, paths, 'trilogy',
      ...                             size=256, noise=0.2, saturation=0.2)
    """
    assert len(ra) == len(dec) == len(save_path)

    if img_type == 'fits':
      download_function = self.download_fits
    elif img_type == 'lupton':
      download_function = self.download_lupton_rgb
    elif img_type == 'trilogy':
      download_function = self.download_trilogy_rgb

    download_args = [
      {'ra': _ra, 'dec': _dec, 'save_path': Path(_save_path), **kwargs}
      for _ra, _dec, _save_path in zip(ra, dec, save_path)
    ]

    self._batch_download(
      download_function=download_function,
      download_args=download_args,
      workers=workers
    )


  @update_authorization
  def query(
    self,
    sql: str,
    save_path: Union[str, Path],
    replace: bool = False,
    scope: Literal['public', 'private'] = 'public',
    table = None,
    fmt: str = 'text/csv'
  ):
    """
    Sends a single query to splus.cloud database

    Parameters
    ----------
    sql: str
      The sql query string
    save_path: str or Path
      The path where the query output will be saved
    repalace: bool (optional)
      This method checks if a file exists in ``save_path`` location before the
      download. If this parameters is ``True`` and a file exists in ``save_path``
      location, this method will ovewrite the existing file. If this parameter
      is ``False`` and a file exists in ``save_path`` location, this method will
      skip the download. Default to ``False``
    scope: str (optional)
      The splus.cloud scope. Can be ``public`` or ``private``. Use ``private`` only
      if you are assigned as collaborator. Defaults to ``public``
    fmt: str (optional)
      The mimi-type of query output. Defaults to ``text/csv``

    Examples
    --------
      >>> service.query('SELECT TOP 10 * FROM dr1.all_dr1', 'query.csv')
    """
    params = {
      'request': 'doQuery',
      'version': '1.0',
      'lang': 'ADQL',
      'phase': 'run',
      'query': sql,
      'format': fmt,
    }
    
    if scope == 'public':
      url = self._get_url(PUBLIC_TAP_ROUTE)
    else:
      url = self._get_url(PRIVATE_TAP_ROUTE)

    if table is None:
      resp = self.client.post(
        url,
        params=params,
        headers={
          'Accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      )
    else:
      params['upload'] = 'upload,param:uplTable'
      file = BytesIO()
      write_table(table, file, fmt='votable')
      resp = self.client.post(
        url,
        params=params,
        files={'uplTable': file},
        headers={
          'Accept': 'application/json',
        },
      )

    if resp.status_code == 200:
      self._track_tap_job(url=resp.url, save_path=save_path, replace=replace)


  def batch_query(
    self,
    sql: List[str],
    save_path: List[Union[str, Path]],
    join: bool = False,
    replace: bool = False,
    scope: Literal['public', 'private'] = 'public',
    fmt: str = 'text/csv',
    workers: int = None
  ):
    """
    Sends a batch of queries to splus.cloud database

    Parameters
    ----------
    sql: list of str
      The sql query string
    save_path: list of str or list of Path
      The path where the query output will be saved
    join: bool (optional)
      Join all tables
    repalace: bool (optional)
      This method checks if a file exists in ``save_path`` location before the
      download. If this parameters is ``True`` and a file exists in ``save_path``
      location, this method will ovewrite the existing file. If this parameter
      is ``False`` and a file exists in ``save_path`` location, this method will
      skip the download. Default to ``False``
    scope: str (optional)
      The splus.cloud scope. Can be ``public`` or ``private``. Use ``private`` only
      if you are assigned as collaborator. Defaults to ``public``
    fmt: str (optional)
      The mime-type of query output. Defaults to ``text/csv``
    workers: int (optional)
      The number of parallel processes that will be spawned. Defaults to 1
    """
    if join:
      final_path = Path(save_path)
      save_path = [
        Path(tempfile.gettempdir()) / f'spluslib_{secrets.token_hex(8)}.csv'
        for _ in range(len(sql))
      ]
    
    args = [
      {
        'sql': _sql,
        'save_path': _save_path,
        'replace': replace,
        'scope': scope,
        'fmt': fmt
      }
      for _sql, _save_path in zip(sql, save_path)
    ]

    self._batch_download(
      download_function=self.query,
      download_args=args,
      workers=workers
    )
    
    if join:
      df = concat_tables(save_path, comment='#')
      write_table(df, final_path)
      
      
  @update_authorization
  def download_field(
    self, 
    field: str, 
    output: str | Path | BufferedIOBase | RawIOBase,
    band: Literal['R', 'G', 'I', 'U', 'Z', 'F378', 'F395', 'F410', 'F430', 'F515', 'F660', 'F861'] = 'R', 
    weight_image: bool = False,
  ):
    payload = {
      'band': band,
      'dr': None,
      'fieldname': field,
      'weight': '1' if weight_image else 0
    }
    
    resp = self.client.post(
      url='https://splus.cloud/api/download_frame',
      json=payload
    )
    
    if isinstance(output, (str, Path)):
      output = Path(output)
      output.mkdir(parents=True, exist_ok=True)
      output.write_bytes(resp.content)
    elif isinstance(output, (BufferedIOBase, RawIOBase)):
      output.write(resp.content)
    


  def _get_url(self, route: str, params: dict = {}) -> str:
    """
    Get the full url based on params
    """
    return urljoin(BASE_URL, route.format(**params))


  @update_authorization
  def _track_tap_job(self, url: str, save_path: Union[str, Path], replace: bool):
    """
    Tracks the async query status in splus.cloud database

    Parameters
    ----------
    url: str
      The job url
    save_path: str or Path
      The path where the query output will be saved
    repalace: bool (optional)
      This method checks if a file exists in ``save_path`` location before the
      download. If this parameters is ``True`` and a file exists in ``save_path``
      location, this method will ovewrite the existing file. If this parameter
      is ``False`` and a file exists in ``save_path`` location, this method will
      skip the download. Default to ``False``
    """
    while True:
      resp = self.client.get(url, headers={'Accept': 'application/json'})

      if resp.status_code == 200:
        data = resp.json()
        destruction_time = datetime.fromisoformat(data['destruction'][:-1] + '+00:00')
        now = datetime.now(destruction_time.tzinfo)

        if data['phase'] == 'EXECUTING' and destruction_time > now:
          sleep(5)
        elif data['phase'] == 'COMPLETED':
          result_url = urlparse(data['results'][0]['href'])
          result_url = result_url._replace(netloc='splus.cloud').geturl()
          download_file(
            url=result_url,
            save_path=save_path,
            replace=replace,
            http_client=self.client
          )
          break
        elif data['phase'] == 'ERROR':
          message = data['error'].get('message', '')
          print(message)
          break
        else:
          break
      else:
        print(f'Status code: {resp.status_code}')
        break


  @update_authorization
  def _download_image(
    self,
    route: str,
    save_path: Union[str, Path],
    replace: bool = False,
    **kwargs
  ):
    """
    Generic download method for splus.cloud images
    This method performs a generic two stages download, required by splus.cloud

    Parameters
    ----------
    route: str
      The image request route
    save_path: str or Path
      The path where the file will be saved
    replace: bool (optional)
      This method checks if a file exists in ``save_path`` location before the
      download. If this parameters is ``True`` and a file exists in ``save_path``
      location, this method will ovewrite the existing file. If this parameter
      is ``False`` and a file exists in ```save_path`` location, this method will
      skip the download. Default to ``False``
    """
    if not replace and save_path.exists():
      return

    # Stage 1 request
    url = self._get_url(route, kwargs)
    resp = self.client.get(url)

    if resp.status_code == 200:
      if 'application/json' in resp.headers['Content-Type']:
        resp_body = resp.json()
        file_url = self._get_url(resp_body['filename'])
        # Stage 2 request
        download_file(
          file_url,
          save_path=save_path,
          replace=replace,
          http_client=self.client
        )


  def _batch_download(
    self,
    download_function: Callable,
    download_args: List[dict],
    workers: int = None
  ):
    """
    Generic batch download method.
    This method receives a donwload function and perform a multi-theread
    execution

    Parameters
    ----------
    download_function: function
      The download function that will spawned in multiple threads
    download_args: list of dict
      The list of parameters of `download_function`
    workers: int (optional)
      The number of parallel processes that will be spawned, defaults to ``None``
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
      futures = []
      download_function = download_function or download_file

      for i in range(len(download_args)):
        futures.append(executor.submit(
          download_function,
          **download_args[i]
        ))

      for future in tqdm.tqdm(
        concurrent.futures.as_completed(futures),
        total=len(futures),
        unit=' files'
      ):
        try:
          future.result()
        except Exception:
          pass






# class TableDr4Dual(Entity):
#   _name = 'dr4_dual'
#   RA = SplusColumn('RA')
#   DEC = SplusColumn('DEC')
#   photoz = SplusColumn('photoz')
    

# class DR4Schema(Entity):
#   _name = 'DR4'
#   dr4_dual = TableDr4Dual()

# class SplusClass(Entity):
#   _name = 'SPLUS'
#   DR4 = DR4Schema()
  

# Splus = SplusClass()
# Splus._config(Splus)

# sql = """
# SELECT {','.join(tables)} 
# FROM 
# """

# tb = Splus.DR4.dr4_dual
# print(
#   (tb.RA.between(3, 5) & tb.DEC.between(-4, -12) & (tb.photoz < 0.1)) |
#   (tb.photoz > 0.4)
# )




if __name__ == '__main__':
  s = SplusService()
  ra = [11.5933851, 11.8345742, 11.9053378, 12.1397573, 12.3036425]
  dec = [-1.0180862, -0.8710110, -0.8707459, -0.7373196, -0.4088959]
  path1 = ['1.png', '2.png', '3.png', '4.png', '5.png']
  path2 = ['01.png', '02.png', '03.png', '04.png', '05.png']
  path3 = ['1.fits', '2.fits', '3.fits', '4.fits', '5.fits']
  # s.batch_image_download(ra, dec, path1, img_type='lupton', workers=3, replace=True)
  # s.batch_image_download(ra, dec, path2, img_type='trilogy', workers=3, replace=True)
  # s.batch_image_download(ra, dec, path3, img_type='fits', workers=3, replace=True)


  sql = 'SELECT TOP 100 ID, RA, DEC FROM dr3.all_dr3 where id like \'%HYDRA%\''
  sql = """
  SELECT TOP 10 * 
  FROM "dr4_dual"."dr4_dual_r" AS r 
  JOIN TAP_UPLOAD.upload AS upl ON 1=CONTAINS(
    POINT('ICRS', r.ra, r.dec), CIRCLE('ICRS', upl.RA, upl.DEC, 0.00027)
  )
  """
  # path4 = [f'table{i}.csv' for i in range(10)]
  path4 = 'table0.csv'
  # s.query(sql, save_path=path4, replace=True, table=pd.DataFrame({'ra': ra, 'dec': dec}))