"""
Distance transformation
"""


from typing import Sequence

from astropy import units as u
from astropy.cosmology import FlatLambdaCDM, Planck18


def arcsec2mpc(
  distance: float | u.Quantity | Sequence[float | u.Quantity], 
  z: float | Sequence[float], 
  cosmology: FlatLambdaCDM = Planck18
):
  """
  Converts arcsecs to Mpc at a given redshift using the specified cosmology
  This function can be used to convert a single distance or multiple distances 
  with a single call.

  Parameters
  ----------
  distance: float or Quantity
    The distance in arcsec to be converted. This argument accepts a float variable 
    or an array-like object (python list, numpy array, pandas series) of floats.
    If a float or sequence of floats is passed, this function interprets it
    as a arcsec unit. If a quantity is passed, this funcion convert the given
    unit (e.g. arcmin or deg) to arcsec. Therefore, if a Quantity object is
    passed, there is no need to convert it.
  z: float or Sequence[float]
    The redshift. This argument can be a single redshift, so this function 
    considers that all distances are in the same redshift, or a sequence of
    redshift of same number of elements of the sequence passed in distance 
    argument, so this function considers that the i-th distance is at i-th
    redshift.
  cosmology: FlatLambdaCDM, optional.
    An astropy cosmology. This function uses Planck 2018 cosmology as default
    with parameters from Planck Collaboration (2020) Table 2 (TT, TE, EE
    + lowE + lensing + BAO) [#P18]_. That is also possible to use a custom
    cosmology, passing a FlatLambdaCDM instance or any cosmology realizations
    from astropy package [#AR]_.

  Returns
  -------
  Quantity
    The converted distance in Mpc
    
  References
  ----------
  .. [#P18] Planck Collaboration, et. al. (2020). Planck 2018 results. VI.
      Cosmological parameters. Astronomy \& Astrophysics, 641, A6.
      `<https://ui.adsabs.harvard.edu/abs/2020A%26A...641A...6P/abstract>`_
  .. [#AR] Included Cosmology Realizations - Astropy Documentation
      `<https://docs.astropy.org/en/stable/cosmology/realizations.html>`_
  """
  if isinstance(distance, u.Quantity):
    distance = distance.to(u.arcec)
  else:
    distance *= u.arcsec

  return cosmology.kpc_proper_per_arcmin(z).to(u.Mpc/u.arcsec)*(distance)


def mpc2arcsec(
  distance: float | u.Quantity | Sequence[float | u.Quantity], 
  z: float | Sequence[float], 
  cosmology: FlatLambdaCDM = Planck18
):
  """
  Converts Mpc to arcsecs at a given redshif using the specified cosmology
  This function can be used to convert a single distance or multiple distances 
  with a single call.

  Parameters
  ----------
  distance: float or Quantity
    The distance in Mpc to be converted. This argument accepts a float variable 
    or an array-like object (python list, numpy array, pandas series) of floats.
    If a float or sequence of floats is passed, this function interprets it
    as a Mpc unit. If a quantity is passed, this funcion convert the given
    unit to Mpc. Therefore, if a Quantity object is passed, there is no 
    need to convert it.
  z: float or Sequence[float]
    The redshift. This argument can be a single redshift, so this function 
    considers that all distances are in the same redshift, or a sequence of
    redshift of same number of elements of the sequence passed in distance 
    argument, so this function considers that the i-th distance is at i-th
    redshift.
  cosmology: FlatLambdaCDM, optional
    An astropy cosmology. This function uses Planck 2018 cosmology as default
    with parameters from Planck Collaboration (2020) Table 2 (TT, TE, EE
    + lowE + lensing + BAO) [#P18]_. That is also possible to use a custom
    cosmology, passing a FlatLambdaCDM instance or any cosmology realizations
    from astropy package [#AR]_.

  Returns
  -------
  Quantity
    The converted distance in arcsec
  
  References
  ----------
  .. [#P18] Planck Collaboration, et. al. (2020). Planck 2018 results. VI.
      Cosmological parameters. Astronomy \& Astrophysics, 641, A6.
      `<https://ui.adsabs.harvard.edu/abs/2020A%26A...641A...6P/abstract>`_
  .. [#AR] Included Cosmology Realizations - Astropy Documentation
      `<https://docs.astropy.org/en/stable/cosmology/realizations.html>`_
  """
  if isinstance(distance, u.Quantity):
    distance = distance.to(u.Mpc)
  else:
    distance *= u.Mpc
    
  return cosmology.arcsec_per_kpc_proper(z).to(u.arcsec/u.Mpc)*(distance)



if __name__ == '__main__':
  print(arcsec2mpc(2.3, 0.03))
  print(arcsec2mpc([2.3, 4.4], 0.03))
  print(arcsec2mpc([2.3, 4.4], [0.3, 0.03]))