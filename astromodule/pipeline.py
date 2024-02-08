"""
Simple implementation of a linear pipeline with multiprocessing support
"""

import inspect
import tempfile
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Sequence

import graphviz

from astromodule.io import parallel_function_executor
from astromodule.utils import filter_dict


class PipelineStorage:
  """
  The storage used share resources between pipeline stage
  
  Attributes
  ----------
  storage: dict
    The data shared across pipeline stages
  """
  def __init__(self):
    self._storage = {}
    
  def write(self, key: str, value: Any):
    """
    Stores ``value`` identified by a ``key``

    Parameters
    ----------
    key : str
      The data identifier
    value : Any
      The data value
    """
    self._storage[key] = value
    
  def write_many(self, **data):
    """
    Stores ``value`` identified by a ``key`` in ``data``

    Parameters
    ----------
    **data: Any
      The data to be stored
    """
    for key, value in data.items():
      self._storage[key] = value
    
  def read(self, key: str) -> Any:
    """
    Retrieve the ``value`` identified by a ``key``

    Parameters
    ----------
    key : str
      The data identifier
    """
    return self._storage.get(key)
    
  def read_many(self, keys: Sequence[str]) -> Dict[str, Any]:
    """
    Retrieve the ``values`` identified by ``keys``

    Parameters
    ----------
    keys : Sequence[str]
      The data identifiers
    """
    return filter_dict(self._storage, keys)



class PipelineStage(ABC):
  """
  Base class for all pipeline stages
  
  Attributes
  ----------
  storage: PipelineStorage
    The pipeline storage. All resources of the pipeline are shared between 
    stages using this object. The `Pipeline` class creates this object
    during instantiation
    
  See Also
  --------
  astromodule.pipeline.Pipeline
  """
  
  name: str = 'Unnamed Stage'
  """Unique name that identifies a stage inside a pipeline"""
  requirements: Sequence[str] = []
  """
  A list of all resorces required by this pipeline stage. It's includes all
  shared data required by this stage using `get_data` or `run` arguments
  """
  products: Sequence[str] = []
  """
  A list of all resorces produced by this pipeline stage. It's includes all
  shared data produced by this stage using `set_data` 
  that can be accessed by another via `get_data` 
  or `run` arguments
  """
  
  @abstractmethod
  def run(self):
    """
    All concrete class of `PipelineStage` must implement this method.
    This method is called by `Pipeline.run` and `Pipeline.map_run` when
    executing the pipeline.
    
    .. note ::
      This method receives all needed data via
    
    See also
    --------
    astromodule.pipeline.Pipeline.run
    astromodule.pipeline.Pipeline.map_run
    """
    pass
  
  @property
  def storage(self) -> PipelineStorage:
    """
    The pipeline shared storage object

    Returns
    -------
    PipelineStorage
      The pipeline storage
    """
    return self._storage
  
  @storage.setter
  def storage(self, pipe_storage: PipelineStorage):
    """
    The pipeline shared storage object

    Parameters
    ----------
    pipe_storage : PipelineStorage
      A pipeline storage object
    """
    self._storage = pipe_storage
  
  def set_data(self, key: str, value: Any):
    """
    Stores shared data ``value`` identified by a ``key``

    Parameters
    ----------
    key : str
      The data identifier
    
    value : Any
      The data value
    """
    self.storage.write(key, value)
    
  def get_data(self, key: str) -> Path:
    """
    Retrieve shared data identified by a ``key``

    Parameters
    ----------
    key : str
      The data identifier
    """
    return self.storage.read(key)



class Pipeline:
  """
  A simple linear pipeline implementation with mapping and multiprocessing
  support.
  
  Parameters
  ----------
  *stages: PipelineStage
    The stages of the pipeline
  
  verbose: bool, optional
    The verbosity flag, by default True.
    
  Attributes
  ----------
  storage: PipelineStorage
    The object used to share resources between all pipeline stages
    
  See Also
  --------
  astromodule.pipeline.PipelineStorage
  astromodule.pipeline.PipelineStage
  """
  def __init__(
    self, 
    *stages: PipelineStage, 
    verbose: bool = True, 
    req_list: Sequence[str] = None,
  ):
    self.verbose = verbose
    self.storage = PipelineStorage()
    self.stages = [deepcopy(s) for s in stages]
    
    for stage in self.stages:
      stage.storage = self.storage
    
    if not req_list:
      req_list = self.extract_stages_requirements()
    self.set_stages_requirements(req_list)
    self._req_list = req_list
  
  
  def set_stages_requirements(self, requirements: Sequence[str]):
    """
    Sets ``requirements`` attribute for all pipeline stages

    Parameters
    ----------
    requirements : Sequence[str]
      A list-like object of same size as pipeline stages. Each element of 
      this list is another list of required resources keys.
    """
    for stage, req in zip(self.stages, requirements):
      stage.requirements = req
      
      
  def extract_stages_requirements(self) -> Sequence[str]:
    """
    Use code inspection to find required resources based in the assignature
    of `PipelineStage.run` method.

    Returns
    -------
    Sequence[str]
      A list of resources keys for each pipeline stage.
      
    See Also
    --------
    astromodule.pipeline.PipelineStage.run
    """
    all_reqs = []
    for stage in self.stages:
      reqs = list(inspect.signature(stage.run).parameters.keys())
      all_reqs.append(reqs)
    return all_reqs
  
    
  def run(self, validate: bool = True):
    """
    Validates and executes all stages of the pipeline

    Parameters
    ----------
    validate : bool, optional
      If `True`, a pipeline requirements validation will be performed using
      `validate` method. If `False`, the validation will be skiped, 
      by default True
    
    See Also
    --------
    astromodule.pipeline.Pipeline.validate
    """
    if validate and not self.validate():
      if self.verbose:
        print('Aborting pipeline execution due to validation fail')
      return 
    
    for i, stage in enumerate(self.stages, 1):
      if self.verbose:
        print(f'[{i} / {len(self.stages)}] Stage {stage.name}')
      
      kwargs = self.storage.read_many(stage.requirements)
      outputs = stage.run(**kwargs)
      if isinstance(outputs, dict):
        self.storage.write_many(**outputs)
      
      if self.verbose:
        print()
        
        
  def map_run(
    self, 
    key: str, 
    array: Sequence[Any], 
    workers: int = 2, 
    validate: bool = True
  ):
    """
    Validates and executes all pipeline steps in a similar way to the `run` 
    method, but using multiprocessing.
    This method has a similar implementation to MapReduce [#MapReduce]_, 
    in which a function is applied to all elements of a vector.
    In this case, the function is the pipeline itself and the vector 
    is specified by the ``array`` parameter.
    Thus, the pipeline is executed ``n`` times, where ``n`` is the size of 
    the ``array`` vector.
    For each execution, the pipeline creates an storage output with 
    identifier ``key`` whose value is the element of the vector that can
    be accessed via `PipelineStage.get_output`.

    Parameters
    ----------
    key : str
      The identifier for an element of ``array`` that can
      be accessed by a pipeline stage using `PipelineStage.get_output`.
    
    array : Sequence[Any]
      The data that will be mapped to pipeline
    
    workers : int, optional
      The number of parallel proccesses that will be spawned, by default 2
    
    validate : bool, optional
      If `True`, a pipeline requirements validation will be performed using
      `validate` method. If `False`, the validation will be skiped, 
      by default True
        
    See also
    --------
    astromodule.pipeline.Pipeline.run
    astromodule.pipeline.Pipeline.validate
    astromodule.pipeline.PipelineStage.get_output
    
    References
    ----------
    .. [#MapReduce] MapReduce - Wikipedia
      `<https://en.wikipedia.org/wiki/MapReduce>`_
    """
    if validate and not self.validate(ignore=[key]):
      if self.verbose:
        print('Aborting pipeline execution due to validation fail')
      return 
    
    params = [{'key': key, 'data': d} for d in array]
    parallel_function_executor(
      func=self._pipe_executor, 
      params=params, 
      workers=workers, 
      unit='jobs'
    )
      
      
  def validate(self, ignore: Sequence[str] = []) -> bool:
    """
    Validates the pipeline by checking whether all requirements for all 
    stages are satisfied
    
    Parameters
    ----------
    ignore : Sequence[str], optional
      Keys to ignore, by default []

    Returns
    -------
    bool
      `True` if all stages can retrieve the required resources (outputs
      and artifacts) correctly, `False` otherwise.
    """
    all_resources = set(ignore)
    problems = []
    for i, stage in enumerate(self.stages, 1):
      missing_req = set(stage.requirements) - all_resources
      if len(missing_req) > 0:
        problems.append({
          'stage_index': i, 
          'stage_name': stage.name, 
          'missing_req': missing_req
        })
      all_resources = all_resources.union(stage.products)
      
    if len(problems) > 0:
      print('Missing requirements:')
      for problem in problems:
        print(f'\t{problem["stage_index"]}. {problem["stage_name"]}')
        print(*[f'\t\t- {r}' for r in problem['missing_req']], sep='\n')
      return False
    return True
  
  
  def plot(self):
    """
    Plot the pipeline graph

    Returns
    -------
    graphviz
      A graphviz object containig the pipeline digraph that can be displayed
      in Jupyter Notebook
    """
    dot = graphviz.Digraph('Pipeline')
    for i, stage in enumerate(self.stages, 1):
      dot.node(str(i), f'{i}. {stage.name}')
    for i in range(1, len(self.stages)):
      dot.edge(str(i), str(i+1))
    dot.view(directory=tempfile.gettempdir(), cleanup=True)
    return dot
      
      
  def __repr__(self) -> str:
    """
    String object representation

    Returns
    -------
    str
      The object representation
    """
    p = [f'{i}. {s.name}' for i, s in enumerate(self.stages, 1)]
    p = '\n'.join(p)
    p = f'Pipeline:\n{p}'
    return p
  
  
  def __add__(self, other: PipelineStage) -> 'Pipeline':
    """
    Overcharge of the ``+`` operator that implements concatenation of
    pipelines or concatenation of a pipeline and a stage

    Parameters
    ----------
    other : Pipeline or PipelineStage
      The pipeline or stage that will be concatenated

    Returns
    -------
    Pipeline
      The resultant pipeline
    """
    if isinstance(other, PipelineStage):
      return Pipeline(*self.stages, other)
    elif isinstance(other, Pipeline):
      return Pipeline(*self.stages, *other.stages)
    
    
  def _pipe_executor(self, key: str, data: Any):
    """
    Wrapper function that create a new pipeline instance and execute it to
    ensure isolation of different pipelines in parallel execution

    Parameters
    ----------
    key : str
      The resource name (identifier) that will be accessible to pipeline stages
    data : Any
      The value of the mapped resource
    """
    pipe = Pipeline(*self.stages, verbose=False, req_list=self._req_list)
    pipe.storage.write(key, data)
    pipe.run(validate=False)
    del pipe


  
if __name__ == '__main__':
  import random
  import time
  class Stage1(PipelineStage):
    name = 'Stage 1'
    products = ['frame']
    
    def run(self, pipe = None):
      time.sleep(random.random())
      return {
        'frame': pipe * 2
      }
    
  class Stage2(PipelineStage):
    name = 'Stage 2'
    
    def run(self, frame):
      print(frame)
      time.sleep(random.random())
    
  p = Pipeline(Stage1(), Stage2())
  # p.plot()
  # print(p)
  # p.run()
  # p.validate()
  p.map_run('pipe', [1, 2, 3, 4, 5, 6], workers=2)