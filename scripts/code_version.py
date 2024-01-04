import re
from pathlib import Path


def get_code_version():
  path = Path(__file__).parent.parent / 'pyproject.toml'
  content = path.read_text()
  match = re.findall(r'version = "(.*)"', content)
  return match[0]


def main():
  print(f'CODE_VERSION={get_code_version()}')
  
  
if __name__ == '__main__':
  main()