class Question:
  def config(self, name: str):
    self.name = name
    ans_keys = [ans for ans in self.__class__.__dict__ if ans.isupper()]
    self.answers = [getattr(self, ans) for ans in ans_keys]
    for ans in self.answers:
      ans.question = self
    return self
  
  @property
  def t(self):
    return self.name



class Answer:
  def __init__(self, name: str):
    self.name = name
    self._question = None
    
  @property
  def question(self):
    return self._question
  
  @question.setter
  def question(self, q: Question):
    self._question = q
  
  @property
  def vt(self) -> str:
    return str(self)
  
  @property
  def fr(self) -> str:
    return str(self) + '_fraction'
  
  @property
  def db(self) -> str:
    return str(self) + '_debiased'
  
  def __str__(self) -> str:
    return self.question.name + '_' + self.name
  
  def __repr__(self) -> str:
    return str(self)



class Questions:
  class SmothOrFeatured(Question):
    SMOOTH = Answer('smooth')
    FEATURED_OR_DISK = Answer('featured-or-disk')
    ARTIFACT = Answer('artifact')
    
  class DiskEdgeOn(Question):
    YES = Answer('yes')
    NO = Answer('no')

  class HasSpiralArms(Question):
    YES = Answer('yes')
    NO = Answer('no')

  class Bar(Question):
    STRONG = Answer('strong')
    WEAK = Answer('weak')
    NO = Answer('no')

  class BulgeSize(Question):
    DOMINANT = Answer('dominant')
    LARGE = Answer('large')
    MODERATE = Answer('moderate')
    SMALL = Answer('small')
    NONE = Answer('none')

  class HowRounded(Question):
    ROUND = Answer('round')
    IN_BETWEEN = Answer('in-between')
    CIGAR_SHAPED = Answer('cigar-shaped')
      
  class EdgeOnBulge(Question):
    BOXY = Answer('boxy')
    NONE = Answer('none')
    ROUNDED = Answer('rounded')
      
  class SpiralWinding(Question):
    TIGHT = Answer('tight')
    MEDIUM = Answer('medium')
    LOOSE = Answer('loose')
      
  class SpiralArmCount(Question):
    ONE = Answer('1')
    TWO = Answer('2')
    THREE = Answer('3')
    FOUR = Answer('4')
    MORE_THAN_4 = Answer('more-than-4')
    CANT_TELL = Answer('cant-tell')
    
  class Merging(Question):
    NONE = Answer('none')
    MINOR_DISTURBANCE = Answer('minor-disturbance')
    MAJOR_DISTURBANCE = Answer('major-disturbance')
    MERGER = Answer('merger')
    
  class BarGZ(Question):
    YES = Answer('yes')
    NO = Answer('no')
  
  class BulgeSizeGZ(Question):
    DOMINANT = Answer('dominant')
    OBVIOUS = Answer('obvious')
    NONE = Answer('none')
    
  class HowRoundedGZ(Question):
    COMPLETELY = Answer('completely')
    IN_BETWEEN = Answer('in-between')
    CIGAR_SHAPED = Answer('cigar-shaped')
    
  class SpiralArmCountGZ(Question):
    ONE = Answer('1')
    TWO = Answer('2')
    THREE = Answer('3')
    FOUR = Answer('4')
    MORE_THAN_4 = Answer('more-than-4')
    
  class MergingGZ(Question):
    NEITHER = Answer('neither')
    TIDAL_DEBRIS = Answer('tidal-debris')
    BOTH = Answer('both')
    MERGER = Answer('merger')



class GD5:
  SMOOTH_OR_FEATURED = Questions.SmothOrFeatured().config('smooth-or-featured-dr5')
  DISK_EDGE_ON = Questions.DiskEdgeOn().config('disk-edge-on-dr5')
  HAS_SPIRAL_ARMS = Questions.HasSpiralArms().config('has-spiral-arms-dr5')
  BAR = Questions.Bar().config('bar-dr5')
  BULGE_SIZE = Questions.BulgeSize().config('bulge-size-dr5')
  HOW_ROUNDED = Questions.HowRounded().config('how-rounded-dr5')
  EDGE_ON_BULGE = Questions.EdgeOnBulge().config('edge-on-bulge-dr5')
  SPIRAL_WINDING = Questions.SpiralWinding().config('spiral-winding-dr5')
  SPIRAL_ARM_COUNT = Questions.SpiralArmCount().config('spiral-arm-count-dr5')
  MERGING = Questions.Merging().config('merging-dr5')



class GD8:
  SMOOTH_OR_FEATURED = Questions.SmothOrFeatured().config('smooth-or-featured-dr8')
  DISK_EDGE_ON = Questions.DiskEdgeOn().config('disk-edge-on-dr8')
  HAS_SPIRAL_ARMS = Questions.HasSpiralArms().config('has-spiral-arms-dr8')
  BAR = Questions.Bar().config('bar-dr8')
  BULGE_SIZE = Questions.BulgeSize().config('bulge-size-dr8')
  HOW_ROUNDED = Questions.HowRounded().config('how-rounded-dr8')
  EDGE_ON_BULGE = Questions.EdgeOnBulge().config('edge-on-bulge-dr8')
  SPIRAL_WINDING = Questions.SpiralWinding().config('spiral-winding-dr8')
  SPIRAL_ARM_COUNT = Questions.SpiralArmCount().config('spiral-arm-count-dr8')
  MERGING = Questions.Merging().config('merging-dr8')
  
  
  
class GD12:
  SMOOTH_OR_FEATURED = Questions.SmothOrFeatured().config('smooth-or-featured-dr12')
  DISK_EDGE_ON = Questions.DiskEdgeOn().config('disk-edge-on-dr12')
  HAS_SPIRAL_ARMS = Questions.HasSpiralArms().config('has-spiral-arms-dr12')
  BAR = Questions.BarGZ().config('bar-dr12')
  BULGE_SIZE = Questions.BulgeSizeGZ().config('bulge-size-dr12')
  HOW_ROUNDED = Questions.HowRoundedGZ().config('how-rounded-dr12')
  EDGE_ON_BULGE = Questions.EdgeOnBulge().config('edge-on-bulge-dr12')
  SPIRAL_WINDING = Questions.SpiralWinding().config('spiral-winding-dr12')
  SPIRAL_ARM_COUNT = Questions.SpiralArmCountGZ().config('spiral-arm-count-dr12')
  MERGING = Questions.MergingGZ().config('merging-dr12')
  
  
class DESI:
  SMOOTH_OR_FEATURED = Questions.SmothOrFeatured().config('smooth-or-featured')
  DISK_EDGE_ON = Questions.DiskEdgeOn().config('disk-edge-on')
  HAS_SPIRAL_ARMS = Questions.HasSpiralArms().config('has-spiral-arms')
  BAR = Questions.Bar().config('bar')
  BULGE_SIZE = Questions.BulgeSize().config('bulge-size')
  HOW_ROUNDED = Questions.HowRounded().config('how-rounded')
  EDGE_ON_BULGE = Questions.EdgeOnBulge().config('edge-on-bulge')
  SPIRAL_WINDING = Questions.SpiralWinding().config('spiral-winding')
  SPIRAL_ARM_COUNT = Questions.SpiralArmCount().config('spiral-arm-count')
  MERGING = Questions.Merging().config('merging')



if __name__ == '__main__':
  print(GD12.SPIRAL_ARM_COUNT)