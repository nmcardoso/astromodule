import tempfile
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Sequence

import graphviz

from astromodule.io import parallel_function_executor


class PipelineStorage:
  def __init__(self):
    self._outputs = {}
    self._artifacts = {}
    
  def set_output(self, key: str, value: Any):
    self._outputs[key] = value
    
  def get_output(self, key: str) -> Any:
    return self._outputs.get(key)
  
  def set_artifact(self, key: str, path: str | Path):
    self._artifacts[key] = Path(path)
    
  def get_artifact(self, key: str) -> Path:
    return self._artifacts.get(key)



class PipelineStage(ABC):
  name: str = 'Unamed Stage'
  requires: Sequence[str] = []
  produces: Sequence[str] = []
  
  @abstractmethod
  def run(self):
    pass
  
  @property
  def storage(self) -> PipelineStorage:
    return self._storage
  
  @storage.setter
  def storage(self, pipe_storage: PipelineStorage):
    self._storage = pipe_storage
  
  def set_output(self, key: str, value: Any):
    self.storage.set_output(key, value)
    
  def get_output(self, key: str) -> Any:
    return self.storage.get_output(key)
  
  def set_artifact(self, key: str, path: str | Path):
    self.storage.set_artifact(key, path)
    
  def get_artifact(self, key: str) -> Path:
    return self.storage.get_artifact(key)



class Pipeline:
  def __init__(self, *stages: PipelineStage, verbose: bool = True):
    self.verbose = verbose
    self.storage = PipelineStorage()
    self.stages = [deepcopy(s) for s in stages]
    for stage in self.stages:
      stage.storage = self.storage
    
  def run(self, validate: bool = True):
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
    
  def parallel_run(
    self, 
    key: str, 
    array: Sequence[Any], 
    workers: int = 2, 
    validate: bool = True
  ):
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
  p.parallel_run('pipe', [1, 2, 3, 4, 5, 6], workers=2)