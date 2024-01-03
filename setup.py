from pathlib import Path

from setuptools import find_packages, setup

setup(
  name='astromodule',
  version='0.0.1',
  description='Astronomical Utilities',
  long_description=Path('README.md').read_text(),
  long_description_content_type='text/markdown',
  author='Natanael Magalhães Cardoso',
  author_email='contact@natanael.net',
  maintainer='Natanael Magalhães Cardoso',
  maintainer_email='contact@natanael.net',
  packages=find_packages(),
  include_package_data=True,
  package_data={
    'astromodule': []
  },
  install_requires=[
    'wheel',
    'numpy>=1.21.6',
    'pandas>=1.3.5',
    'scikit-learn>=1.0.2',
    'tqdm>=4.64.1',
    'requests>=2.23',
    'Pillow>=7.1.2',
    'astropy>=5.2',
    'matplotlib',
    'seaborn',
  ],
  extras_require={
    'docs': [
      'Jinja2>=3.1',
      'sphinx',
      'sphinxcontrib-napoleon',
      'sphinx_copybutton',
      'sphinx-astropy',
      'sphinx-gallery',
      'sphinx-automodapi',
      'numpydoc',
      'furo',
      'pydata-sphinx-theme',
      'ipykernel',
    ]
  },
  keywords=[
    'astronomy', 
    'astronomical databases', 
    'machine learning', 
    'data science'
  ],
)
