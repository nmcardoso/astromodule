class AdqlColumn:
  def __init__(self, name):
    self._name = name
    self._table = None
    
  def __gt__(self, other):
    return AdqlColumn(f'({self._name} > {str(other)})')
  
  def __lt__(self, other):
    return AdqlColumn(f'({self._name} < {str(other)})')
  
  def __ge__(self, other):
    return AdqlColumn(f'({self._name} >= {str(other)})')
  
  def __le__(self, other):
    return AdqlColumn(f'({self._name} <= {str(other)})')
  
  def __eq__(self, other):
    return AdqlColumn(f'({self._name} = {str(other)})')
  
  def __ne__(self, other):
    return AdqlColumn(f'({self._name} != {str(other)})')
  
  def __or__(self, other):
    return AdqlColumn(f'({self._name} OR {str(other)})')
  
  def __and__(self, other):
    return AdqlColumn(f'({self._name} AND {str(other)})')
  
  def __add__(self, other):
    return AdqlColumn(f'({self._name} + {str(other)})')
  
  def __sub__(self, other):
    return AdqlColumn(f'({self._name} - {str(other)})')
  
  def __mul__(self, other):
    return AdqlColumn(f'({self._name} * {str(other)})')
  
  def __truediv__(self, other):
    return AdqlColumn(f'({self._name} / {str(other)})')
  
  def __mod__(self, other):
    return AdqlColumn(f'({self._name} % {str(other)})')
  
  def __pow__(self, other):
    return AdqlColumn(f'(POWER({self._name}, {str(other)}))')
  
  def __neg__(self):
    return AdqlColumn(f'(-{self._name})')
  
  def __pos__(self):
    return AdqlColumn(f'(+{self._name})')
  
  def __pos__(self):
    return AdqlColumn(f'(NOT({self._name}))')
  
  def between(self, first, second):
    return AdqlColumn(f'({self._name} BETWEEN {str(first)} AND {str(second)})')
  
  def like(self, other):
    return AdqlColumn(f"({self._name} LIKE '{str(other)}')")

  def __str__(self) -> str:
    return self._name
    
  def set_table(self, table):
    self._table = table
    
  def get_table(self):
    return self._table
  
  def get_name(self):
    return self._name
    
    
    
class AdqlTable:
  # def join(self, table: 'AdqlTable'):
  #   return AdqlTable()
  
  def __str__(self):
    return self._name
  
  def set_schema(self, schema):
    self._schema = schema
  
  def get_schema(self):
    return self._schema
  
  def get_name(self):
    return self._name
  
  def config(self):
    cols = [v for k, v in self.__class__.__dict__.items() if not k.startswith('_')]
    for col in cols:
      col.set_table(self)




class AdqlSchema:
  def get_name(self):
    return self._name
  
  def config(self):
    tables = [v for k, v in self.__class__.__dict__.items() if not k.startswith('_')]
    for table in tables:
      table.set_schema(self)
      table.config()
      
      

class AdqlDatabase:
  def config(self):
    schemas = [v for k, v in self.__class__.__dict__.items() if not k.startswith('_')]
    for schema in schemas:
      schema.config()