import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Sequence

import graphviz


class PipelineStage(ABC):
  _artifacts: Dict[str, Path] = {}
  _outputs: Dict[str, Any] = {}
  name: str = 'Unamed Stage'
  requires: Sequence[str] = []
  produces: Sequence[str] = []
  
  @abstractmethod
  def run(self):
    pass
  
  def set_output(self, key: str, value: Any):
    PipelineStage._outputs[key] = value
    
  def get_output(self, key: str) -> Any:
    return PipelineStage._outputs.get(key)
  
  def register_artifact(self, key: str, path: str | Path):
    PipelineStage._artifacts[key] = Path(path)
    
  def get_artifact(self, key: str) -> Path:
    return PipelineStage._artifacts.get(key)



class Pipeline:
  def __init__(self, *stages: PipelineStage):
    self.stages = stages
    
  def run(self):
    if not self.validate():
      print('Aborting pipeline execution due to validation fail')
      return 
    
    for i, stage in enumerate(self.stages, 1):
      print(f'[{i} / {len(self.stages)}] Stage {stage.name}')
      stage.run()
      print()
      
  def validate(self) -> bool:
    all_resources = set()
    problems = []
    for i, stage in enumerate(self.stages, 1):
      missing_req = set(stage.requires) - all_resources
      if len(missing_req) > 0:
        problems.append({'stage_index': i, 'stage_name': stage.name, 'missing_req': missing_req})
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
  
  
if __name__ == '__main__':
  class Stage1(PipelineStage):
    name = 'Stage 1'
    produces = ['super_frame']
    
    def run(self):
      self.set_output('frame', [0, 1, 2])
    
  class Stage2(PipelineStage):
    name = 'Stage 2'
    requires = ['super_frame']
    
    def run(self):
      print(self.get_output('frame'))
    
  p = Pipeline(Stage1(), Stage2())
  # p.plot()
  # print(p)
  # p.run()
  p.validate()