"""
High-level interface for data access using Table Access Protocol (TAP)
"""


import secrets
import tempfile
from pathlib import Path
from typing import List, Union
from urllib.parse import quote, urlencode

import pandas as pd
import requests

from astromodule.io import batch_download_file, download_file, write_table
from astromodule.table import concat_tables


class TapService:
  def __init__(self, url):
    self.url = url
    self.http_client = requests.Session()

  def sync_query(self, query: str, save_path: Union[str, Path]):
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
    queries: List[str],
    save_paths: List[str] | List[Path] | str | Path,
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
      combined_df = concat_tables(tmp_folder.glob('*.csv'), comment='#')
      write_table(combined_df, save_paths)





if __name__ == '__main__':
  tap = TapService('https://datalab.noirlab.edu/tap/sync')
  tap.sync_query('select top 10 psfdepth_g, psfdepth_r from ls_dr9.tractor where ra between 230.2939-0.0013 and 230.2939+0.0013 and dec between 29.7714-0.0013 and 29.7714+0.0013')
  tap.sync_query('select top 10 psfdepth_g, psfdepth_r from ls_dr9.tractor where ra between 230.2939-0.0013 and 230.2939+0.0013 and dec between 29.7714-0.0013 and 29.7714+0.0013')
