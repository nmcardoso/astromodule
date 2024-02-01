"""
Hyperparameter data model useful for standardizing the training loop of
machine learning applications.
"""


import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Sequence, Union

import optuna

L = logging.getLogger(__name__)


class HyperParameter(ABC):
  """
  This abstract class is the generic representation of a hyperparmaeter 
  and can be used on any model of Machine Learning or Deep Learning.
  This data model is designed to be a ``optuna`` wrapper,
  In this way, it is possible to implement a model training function without
  worry about how hyperparimeters are obtained.That is, it is possible
  Get the hyperparimeters automatically by the ``optuna`` library
  or predefined (manual) form with the same code.
  """
  def __init__(self):
    self._trial = None
    self.last_value = None
    self.attrs = {}
    
  @abstractmethod
  def suggest(self, trial: optuna.trial.FrozenTrial = None):
    """
    Used to recover the value of the hyperparmeter as defined by the
    concrete class.The concrete class can implement a logic based
    in Auto-ML using the ``optuna`` library or predefined values.
    The training function of the model should call this method to obtain the
    hyperparmeter value.

    Parameters
    ----------
    trial: optuna.trial.FrozenTrial, optional
      An instance of the ``optuna`` trial, by default none
    """
    pass

  def set_attr(self, key, value):
    self.attrs[key] = value

  def set_trial(self, trial: optuna.trial.FrozenTrial):
    self._trial = trial

  def to_dict(self, show_name: bool = False) -> dict:
    """
    A hyperparmeter can be defined from various attributes.
    This method expresses the hyperparmeter in the form of a python dictionary.

    Parameters
    ----------
    Show_Name: BOOL, OPTIONAL
      ``True`` if the `HyperParmeter` name should be included, in this case, a 
      pair key-value ``name: <hyperparameter-name>`` will be included, else,
      only hyperparmeter attributes will be included. By default ``False``

    Return
    -------
    dict
      Representation of the hyperparmeter in the form of python dictionary
    """
    if show_name:
      return self.attrs
    else:
      copy = self.attrs.copy()
      copy.pop('name')
      return copy

  def clear_last_value(self):
    """
    Sets ``last_value`` attribute to ``None``
    """
    self.last_value = None

  @staticmethod
  def from_dict(params: dict):
    """
    Creates a concrete instance of hyperparmeter from a dictionary of the
    python

    Parameters
    ----------
    params : dict
      A python dictionary that can be properly transformed into a concrete 
      hyperparmeter instance.

    Returns
    -------
    HyperParameter
      A concrete instance of hyperparmeter
    """
    t = params.pop('type')
    if t == 'categorical':
      E = CategoricalHyperParameter
    elif t == 'float':
      E = FloatHyperParameter
    elif t == 'int':
      E = IntHyperParameter
    elif t == 'constant':
      E = ConstantHyperParameter
    return E(**params)



class CategoricalHyperParameter(HyperParameter):
  """
  Concrete class that represents a hyperparimeter of the categorical type

  Parameters
  ----------
  name: str
    The hyperparâmeter identification name, must be unique.
  choices: Sequence[Any]
    A list-like object of categorical values
  """
  def __init__(self, name: str, choices: Sequence[Any]):
    super(CategoricalHyperParameter, self).__init__()
    self.set_attr('name', name)
    self.set_attr('choices', choices)

  def suggest(self, trial: optuna.trial.FrozenTrial = None) -> Any:
    _trial = trial or self._trial
    self.last_value = _trial.suggest_categorical(**self.attrs)
    return self.last_value



class FloatHyperParameter(HyperParameter):
  def __init__(
    self,
    name: str,
    low: float,
    high: float,
    step: float = None,
    log: bool = False
  ):
    super(FloatHyperParameter, self).__init__()
    self.set_attr('name', name)
    self.set_attr('low', low)
    self.set_attr('high', high)
    self.set_attr('step', step)
    self.set_attr('log', log)

  def suggest(self, trial: optuna.trial.FrozenTrial = None) -> float:
    _trial = trial or self._trial
    self.last_value = _trial.suggest_float(**self.attrs)
    return self.last_value



class IntHyperParameter(HyperParameter):
  def __init__(
    self,
    name: str,
    low: int,
    high: int,
    step: int = 1,
    log: bool = False
  ):
    super(IntHyperParameter, self).__init__()
    self.set_attr('name', name)
    self.set_attr('low', low)
    self.set_attr('high', high)
    self.set_attr('step', step)
    self.set_attr('log', log)

  def suggest(self, trial: optuna.trial.FrozenTrial = None) -> int:
    _trial = trial or self._trial
    self.last_value = _trial.suggest_int(**self.attrs)
    return self.last_value



class ConstantHyperParameter(HyperParameter):
  def __init__(self, name: str, value: Any):
    super(ConstantHyperParameter, self).__init__()
    self.set_attr('name', name)
    self.set_attr('value', value)
    self.last_value = value

  def suggest(self, trial: optuna.trial.FrozenTrial = None) -> Any:
    return self.attrs['value']


class HP:
  """
  A utilitary factory class that produces concretes `HyperParameter` instances
  according to its types. Used for convenience, to avoid importing and
  instantiating each type of hyperparmeter separately.

  Returns
  -------
  Hyperparameter
    A concrete instance of hyperparmeter.
  """ 
  @staticmethod
  def cat(name: str, choices: Sequence) -> CategoricalHyperParameter:
    return CategoricalHyperParameter(name, choices)


  @staticmethod
  def const(name: str, value: Any) -> ConstantHyperParameter:
    return ConstantHyperParameter(name, value)


  @staticmethod
  def num(
    name: str,
    low: Union[float, int],
    high: Union[float, int],
    step: Union[float, int] = None,
    log: bool = False,
    dtype: Union[float, int] = float
  ) -> Union[FloatHyperParameter, IntHyperParameter]:
    if dtype == float:
      return FloatHyperParameter(name, low, high, step, log)
    else:
      return IntHyperParameter(name, low, high, step, log)



class HyperParameterSet:
  """
  Represents a set of concretes `HyperParameter` instances and 
  handles the registration and access of hyperparameters.
  
  Parameters
  ----------
  *args: HyperParameter
    Any `HyperParameter` instance created by `HP` factory

  See Also
  --------
  astromodule.hp.HyperParameter
  astromodule.hp.CategoricalHyperParameter
  astromodule.hp.IntHyperParameter
  astromodule.hp.FloatHyperParameter
  astromodule.hp.ConstantHyperParameter
  astromodule.hp.HP
  """
  def __init__(self, *args: HyperParameter, verbose: bool = True):
    self.verbose = verbose
    self.hps = {}
    self._trial: optuna.trial.Trial = None

    for hp in args:
      if isinstance(hp, HyperParameter):
        name = hp.attrs['name']
        self.hps[name] = hp
      elif isinstance(hp, dict):
        pass
      
      
  @classmethod
  def from_dict(cls, d: Dict[str, Any]):
    hp_list = []
    for k, v in d.items():
      hp_list.append(ConstantHyperParameter(k, v))
    return HyperParameterSet(*hp_list)


  def concat(self, hyperparameters: Sequence[Union[dict, HyperParameter]]):
    """
    Parses a sequence of dictionaries that represents the hyperparameters

    Parameters
    ----------
    hyperparameters: array-like of dictionaries or array-like of `HyperParameter`
      The list of hyperparameters that will be added to this
      hyperparameters set
    """
    for hp in hyperparameters:
      if type(hp) == dict:
        name = hp['name']
        self.hps.update({ name: HyperParameter.from_dict(hp) })
      else:
        name = hp.attrs['name']
        self.hps.update({ name: hp })


  def get(
    self,
    name: str,
    trial: optuna.trial.FrozenTrial = None,
    default: Any = None,
    regex: bool = False,
  ) -> Any:
    """
    Get the value of a hyperparameter identified by its name.
    For hyperparameters different than ConstantHyperParameter, this method
    will use optuna's seggest api

    Parameters
    ----------
    name: str
      The hyperparamer name
    
    trial: optuna.trial.FrozenTrial
      The optuan trial instance
    
    default: Any
      Default value returned if the specified hyperparameter name wasn't found
      
    regex : bool
      When interpret ``name`` parameter as a regex and get all matches as a dict

    Returns
    -------
    Any
      The hyperparameter value

    See Also
    --------
    astromodule.hp.HyperParameter.suggest
    """
    if regex:
      reg = re.compile(name)
      matched_keys = filter(reg.match, self.hps.keys())
      return {k: self.hps[k].suggest(trial) for k in matched_keys}
    
    if not name in self.hps:
      if self.verbose:
        L.warning(f'Hyperparameter {name} not found! Returning default value: {str(default)}')
      return default

    return self.hps[name].suggest(trial)


  def set_trial(self, trial: optuna.trial.FrozenTrial):
    """
    Sets the optuna's trial for all hyperparameter in this set

    Parameters
    ----------
    trial: optuna.trial.FrozenTrial
      The trial that will be added
    """
    self._trial = trial
    for hp in self.hps.values():
      hp.set_trial(trial)


  def to_values_dict(self):
    """
    Returns a dict representation of this hyperparameters set with hp name
    as dict key and last optuna's suggested value as dict value
    """
    return { name: hp.last_value for name, hp in self.hps.items() }


  def clear_values_dict(self):
    """
    Clear ``last_value`` property of the `HyperParameter`, relevant when training
    with conditional hyperparameters
    """
    for hp in self.hps.values():
      hp.clear_last_value()
      
      
  def check_missing_hp(self, hps: Sequence[str]) -> List[str]:
    """
    Checks if all elements in a given list is in hyperparameters set

    Parameters
    ----------
    hps : Sequence[str]
      A list of hyperparameters name that must include the hyperparameters set

    Returns
    -------
    List[str]
      A list of missing hyperparameters
    """
    missing = []
    for hp in hps:
      if hp not in self:
        missing.append(hp)
    return missing
  
  
  def __contains__(self, key: str):
    """
    Checks if the hyperparameter set contains a hp identified by the given key

    Parameters
    ----------
    key : str
      The hyperparameter name

    Returns
    -------
    bool
      `True` if the set contains a hyperparameter with a given key,
      `False` otherwise.
    """
    return any(e == key for e in self.hps.keys())
  
  
  def __iadd__(self, hp: HyperParameter):
    hp.set_trial(self._trial)
    self.hps.update({hp.attrs.get('name'): hp})
    return self
  
  
  def add(self, hp: HyperParameter):
    self += hp
  
  
if __name__ == '__main__':
  hps = HyperParameterSet(
    HP.const('mlp_validation_fraction', 0.2),
    HP.const('mlp_early_stopping', True),
    HP.const('mlp_n_iter_no_change', 10),
    verbose=False,
  )
  hps += HP.const('A', 2)
  print(hps.hps)
  print(hps.get(r'mlp_*', regex=True))