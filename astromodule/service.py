import concurrent.futures
import secrets
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Sequence
from urllib.parse import urlencode

import pandas as pd
import requests
import tqdm

from astromodule.io import (PathOrFile, batch_download_file, download_file,
                            write_table)
from astromodule.utils import append_query_params


class ImagingService(ABC):
  def __init__(self, image_format):
    self.image_format = image_format


  @abstractmethod
  def cutout(self, ra: float, dec: float, save_path: Path):
    pass


  @abstractmethod
  def batch_cutout(self, ra: List[float], dec: List[float], save_path: List[Path]):
    pass


  def _download_rgb(
    self,
    ra: float,
    dec: float,
    save_path: Path,
    width: int = 256,
    height: int = 256,
    scale: float = 0.55,
    opt: str = ''
  ):
    image_url = append_query_params(self.imaging_url, {
      'ra': ra,
      'dec': dec,
      'width': width,
      'height': height,
      'scale': scale,
      'opt': opt
    })
    download_file(image_url, save_path)


  def _batch_download_rgb(
    self,
    ra: Sequence[float],
    dec: Sequence[float],
    save_path: Sequence[Path],
    workers: int = None,
    **kwargs
  ):
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
      futures = []

      for i in range(len(ra)):
        futures.append(executor.submit(
          self.download_rgb,
          ra=ra[i],
          dec=dec[i],
          save_path=save_path[i],
          **kwargs
        ))

      for _ in tqdm.tqdm(
        concurrent.futures.as_completed(futures),
        total=len(futures),
        unit=' file'
      ):
        pass





class TapService:
  def __init__(self, url):
    self.url = url
    self.http_client = requests.Session()

  def sync_query(self, query: str, save_path: PathOrFile):
    params = {
      'request': 'doQuery',
      'version': 1.0,
      'lang': 'ADQL',
      'phase': 'run',
      'format': 'csv',
      'query': query
    }
    req_url = self.url + '?' + urlencode(params)
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    download_file(req_url, save_path, replace=True, http_client=self.http_client)

  def batch_sync_query(
    self,
    queries: Sequence[str],
    save_paths: PathOrFile | Sequence[PathOrFile],
    join_outputs: bool = False,
    workers: int = 3
  ):
    params = {
      'request': 'doQuery',
      'version': 1.0,
      'lang': 'ADQL',
      'phase': 'run',
      'format': 'csv'
    }
    urls = [self.url + '?' + urlencode({**params, 'query': q}) for q in queries]

    save_paths_aux = save_paths
    if join_outputs:
      tmp_folder = Path(tempfile.gettempdir()) / f'tap_{secrets.token_hex(3)}'
      tmp_folder.mkdir(parents=True)
      save_paths_aux = [tmp_folder / f'{i}.csv' for i in range(len(queries))]

    batch_download_file(
      urls,
      save_path=save_paths_aux,
      http_client=self.http_client,
      workers=workers
    )

    if join_outputs:
      combined_csv = pd.concat([
        pd.read_csv(f, comment='#') for f in tmp_folder.glob('*.csv')
      ])
      save_paths = Path(save_paths)
      save_paths.parent.mkdir(parents=True, exist_ok=True)
      write_table(combined_csv, save_paths)