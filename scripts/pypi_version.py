import os

import requests


def get_pypi_version():
  if os.environ.get('DEPLOY_ENV', 'test').lower() == 'test':
    url = 'https://test.pypi.org/pypi/astromodule/json'
  else:
    url = 'https://pypi.org/pypi/astromodule/json'
    
  resp = requests.get(url)
  data = resp.json()
  version = data['info']['version']
  return version



def main():
  print(f'PYPI_VERSION={get_pypi_version()}')


if __name__ == '__main__':
  main()