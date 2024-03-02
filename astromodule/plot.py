"""
Plotting functions
"""
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid

from astromodule.io import read_image


def simple_image_axis(image: str | Path, ax = None):
  if not ax:
    fig, ax = plt.subplots()
  
  img = read_image(image)
  ax.imshow(img)
  ax.axis('off')
  return ax


def plot_axis_grid(
  images: Sequence[str | Path],
  cols: int, 
  rows: int, 
  width: float = 2.5, 
  height: float = 2.5, 
  size: float = None,
  title: str = None,
  show: bool = False,
  save_path: str | Path = None,
  axes_pad: float = 0.05,
):
  if size:
    width, height = size, size
  fig, axs = plt.subplots(figsize=(width, height))
  axs.axis('off')
  fig.tight_layout(rect=(0, 0, 1, 1), pad=0.15)
  if title:
    plt.title(title)
  grid = ImageGrid(fig, 111, nrows_ncols=(rows, cols), axes_pad=axes_pad)
  for ax, im in zip(grid, images):
    simple_image_axis(im, ax)
  if save_path:
    plt.savefig(save_path)
  if show:
    plt.show()
  return axs


