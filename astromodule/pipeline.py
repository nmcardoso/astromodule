"""
Simple implementation of a linear pipeline with multiprocessing support
"""

import tempfile
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Sequence

import graphviz

from astromodule.io import parallel_function_executor


class PipelineStorage:
  """
  The storage used share resources between pipeline stage
  
  Attributes
  ----------
  outputs: dict
    The ``output`` data
  
  artifacts: dict
    The ``artifact`` data
  """
  def __init__(self):
    self._outputs = {}
    self._artifacts = {}
    
  def set_output(self, key: str, value: Any):
    """
    Stores an output ``value`` identified by a ``key``

    Parameters
    ----------
    key : str
      The output identifier
    value : Any
      The output value
    """
    self._outputs[key] = value
    
  def get_output(self, key: str) -> Any:
    """
    Retrieve an output ``value`` identified by a ``key``

    Parameters
    ----------
    key : str
      The output identifier
    """
    return self._outputs.get(key)
  
  def set_artifact(self, key: str, path: str | Path):
    """
    Stores an artifact ``path`` identified by a ``key``

    Parameters
    ----------
    key : str
      The artifact identifier
    path : str | Path
      The artifact path
    """
    self._artifacts[key] = Path(path)
    
  def get_artifact(self, key: str) -> Path:
    """
    Retrieve an artifact ``path`` identified by a ``key``

    Parameters
    ----------
    key : str
      The artifact identifier
    """
    return self._artifacts.get(key)



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
  requires: Sequence[str] = []
  """
  A list of all resorces required by this pipeline stage. It's includes all
  ``outputs`` and ``artifacts`` accessed by this stage using 
  `PipelineStage.get_output` or `PipelineStage.get_artifact`.
  """
  produces: Sequence[str] = []
  """
  A list of all resorces produced by this pipeline stage. It's includes all
  ``outputs`` and ``artifacts`` produced by this stage using 
  `PipelineStage.set_output` or `PipelineStage.set_artifact` 
  that can be accessed by another via `PipelineStage.get_output` or
  `PipelineStage.get_artifact`.
  """
  
  @abstractmethod
  def run(self):
    """
    All concrete class of `PipelineStage` must implement this method.
    This method is called by `Pipeline.run` and `Pipeline.map_run` when
    executing the pipeline.
    
    .. warning ::
      This method does not receives any parameter, since the `Pipeline`
      can not handle it.
    
    See also
    --------
    astomodule.pipeline.Pipeline.run
    astomodule.pipeline.Pipeline.map_run
    """
    pass
  
  @property
  def storage(self) -> PipelineStorage:
    return self._storage
  
  @storage.setter
  def storage(self, pipe_storage: PipelineStorage):
    self._storage = pipe_storage
  
  def set_output(self, key: str, value: Any):
    """
    Stores a output data that will be shared between all pipeline stages

    Parameters
    ----------
    key : str
      The output identifier
    value : Any
      The value that will be stored
    """
    self.storage.set_output(key, value)
    
  def get_output(self, key: str) -> Any:
    """
    Access the output identified by ``key`` that was produced by a 
    previous stage.

    Parameters
    ----------
    key : str
      The output identifier

    Returns
    -------
    Any
      The value stored
    """
    return self.storage.get_output(key)
  
  def set_artifact(self, key: str, path: str | Path):
    """
    Stores an artifact ``path`` identified by a ``key``

    Parameters
    ----------
    key : str
      The artifact identifier
    path : str | Path
      The artifact path
    """
    self.storage.set_artifact(key, path)
    
  def get_artifact(self, key: str) -> Path:
    """
    Retrieve an artifact ``path`` identified by a ``key``

    Parameters
    ----------
    key : str
      The artifact identifier
    """
    return self.storage.get_artifact(key)



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
  def __init__(self, *stages: PipelineStage, verbose: bool = True):
    self.verbose = verbose
    self.storage = PipelineStorage()
    self.stages = [deepcopy(s) for s in stages]
    for stage in self.stages:
      stage.storage = self.storage
    
  def run(self, validate: bool = True):
    """
    Validates and executes all stages of the pipeline

    Parameters
    ----------
    validate : bool, optional
      If True, a pipeline requirements validation will be performed using
      `validate` method. If `False`, the validation will be skiped, 
      by default True
    
    See Also
    --------
    astromodule.pipeline.Pipeline.validate
    """
    if not self.validate() and validate:
      if self.verbose:
        print('Aborting pipeline execution due to validation fail')
      return 
    
    for i, stage in enumerate(self.stages, 1):
      if self.verbose:
        print(f'[{i} / {len(self.stages)}] Stage {stage.name}')
      
      stage.run()
      
      if self.verbose:
        print()
      
  def validate(self) -> bool:
    """
    Validates the pipeline by checking whether all requirements for all 
    stages are satisfied

    Returns
    -------
    bool
      ``True`` if all stages can retrieve the required resources (outputs
      and artifacts) correctly, ``False`` otherwise.
    """
    all_resources = set()
    problems = []
    for i, stage in enumerate(self.stages, 1):
      missing_req = set(stage.requires) - all_resources
      if len(missing_req) > 0:
        problems.append({
          'stage_index': i, 
          'stage_name': stage.name, 
          'missing_req': missing_req
        })
      all_resources = all_resources.union(stage.produces)
      
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
      
  def __repr__(self):
    p = [f'{i}. {s.name}' for i, s in enumerate(self.stages, 1)]
    p = '\n'.join(p)
    p = f'Pipeline:\n{p}'
    return p
  
  def __add__(self, other: Any):
    if isinstance(other, PipelineStage):
      return Pipeline(*self.stages, other)
    elif isinstance(other, Pipeline):
      return Pipeline(*self.stages, *other.stages)
    
  def _pipe_executor(self, key: str, data: Any):
    p = Pipeline(*self.stages, verbose=False)
    p.storage.set_output(key, data)
    p.run(validate=False)
    del p
    
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
    Thus, the pipeline is executed ``n`` times, where ``n` is the size of 
    the ``array`` vector.
    For each of the ``n`` executions, the pipeline creates an output with 
    identifier ``key`` whose value is the element of the vector.

    Parameters
    ----------
    key : str
      The identifier that identifies a element of ``array`` vector and can
      be accessed by a pipeline stage using `PipelineStage.get_output`.
    array : Sequence[Any]
      The data that will be mapped to pipeline
    workers : int, optional
      The number of parallel proccesses that will be spawned, by default 2
    validate : bool, optional
      If True, a pipeline requirements validation will be performed using
      `validate` method. If `False`, the validation will be skiped, 
      by default True
        
    See also
    --------
    astromodule.pipeline.Pipeline.run
    astromodule.pipeline.Pipeline.validate
    
    References
    ----------
    .. [#MapReduce] MapReduce - Wikipedia
      `<https://en.wikipedia.org/wiki/MapReduce>`_
    """
    if not self.validate() and validate:
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


  
if __name__ == '__main__':
  import random
  import time
  class Stage1(PipelineStage):
    name = 'Stage 1'
    produces = ['super_frame']
    
    def run(self):
      self.set_output('frame', self.get_output('pipe') * 2)
      time.sleep(random.random())
    
  class Stage2(PipelineStage):
    name = 'Stage 2'
    requires = ['super_frame']
    
    def run(self):
      print(self.get_output('frame'))
      time.sleep(random.random())
    
  p = Pipeline(Stage1(), Stage2())
  # p.plot()
  # print(p)
  # p.run()
  # p.validate()
  p.map_run('pipe', [1, 2, 3, 4, 5, 6], workers=2)