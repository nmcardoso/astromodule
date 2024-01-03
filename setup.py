from dataclasses import dataclass
from pathlib import Path

import toml
from setuptools import find_packages, setup


@dataclass
class Project:
  name: str
  version: str
  description: str
  author: str
  author_email: str
  maintainer: str
  maintainer_email: str
  install_requires: str
  extras_require: dict
  keywords: list



def load_pyproject_file():
  path = Path(__file__).parent / 'pyproject.toml'
  data = toml.load(path)
  return Project(
    name=data['project']['name'],
    version=data['project']['version'],
    description=data['project']['description'],
    author=data['project']['authors'][0]['name'],
    author_email=data['project']['authors'][0]['email'],
    maintainer=data['project']['maintainers'][0]['name'],
    maintainer_email=data['project']['maintainers'][0]['email'],
    install_requires=data['project']['dependencies'],
    extras_require=data['project']['optional-dependencies'],
    keywords=data['project']['keywords']
  )



def _setup(*args, **kargs):
  project = load_pyproject_file()
  print(project)
  setup(
    name=project.name,
    version=project.version,
    description=project.description,
    long_description=Path('README.md').read_text(),
    long_description_content_type='text/markdown',
    author=project.author,
    author_email=project.author_email,
    maintainer=project.maintainer,
    maintainer_email=project.maintainer_email,
    packages=find_packages(),
    install_requires=project.install_requires,
    extras_require=project.extras_require,
    keywords=project.keywords,
    include_package_data=True,
    package_data={
      'astromodule': []
    },
  )


if __name__ == '__main__':
  _setup()