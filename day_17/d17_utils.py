from typing import Optional
from pydantic import BaseModel, model_validator

class P(BaseModel):
    """ A point """
    x: int = 0
    y: int = 0

    def __hash__(self):
        return hash(f'{self.x}x{self.y}')

    def __add__(self, value):
        # Assume adding a P
        return P(x=self.x+value.x, y=self.y+value.y)

    def __mul__(self,value):
        # Assume multiplying by int
        return P(x=self.x*value, y=self.y*value)
    
    def __eq__(self, value):
        return self.x == value.x and self.y == value.y
    
    def clone(self) -> 'P':
        return P(x=self.x,y=self.y)
        
class S(BaseModel):
    """A size. Not really different than point, but keeps var names separate"""
    width: int
    height: int

    def magnitude(self) -> int:
        return self.width * self.height

class R(BaseModel):
    """ A range with a/b inclusive""" 
    a: int 
    b: int

    def overlap(self, r: 'R') -> bool:
        return max(self.a, r.a) <= min(self.b, r.b)

    def intersection(self, r: 'R') -> Optional['R']:
        new_a = max(self.a, r.a)
        new_b = min(self.b, r.b)
        if new_a <= new_b:
            return R(a=new_a,b=new_b)
        return None

    def __sub__(self, value) -> Optional['R']:
        if type(value) == R:
            return self.intersection(value)

        raise ValueError("Can only subtract a R from an R")

    def __add__(self, value) -> 'R':
        return R(a=self.a + value, b=self.b+value)

    def __contains__(self, value) -> bool:
        if type(value) == R:
            return self.overlap(value)
            
        try:
            x = int(value)
            return x >= self.a and x <= self.b
        except ValueError:
            return False
        
    @model_validator(mode='after')
    def check_ordering(self) -> 'R':
        if self.a > self.b:
            raise ValueError(f"a [{self.a}] is greater than b [{self.b}]")

        return self

RIGHT=P(x=1,y=0)
LEFT=P(x=-1,y=0)
UP=P(x=0,y=-1)
DOWN=P(x=0,y=1)

class Grid(BaseModel):
    size: S
    cells: dict[P, int]

    def is_blocked(self, p: P) -> bool:
        return self.cells.get(p,0) != 0
    
    def bfs(self, start: P, end: P) -> list[P]:
        frontier = [start]
        reached = {}

        while frontier:
            p = frontier.pop()
            if p == end:
                return [p]
            if p == start or (not self.is_blocked(p) and not reached.get(p)):
                reached[p] = True
                frontier.append(p + UP)
                frontier.append(p + DOWN)
                frontier.append(p + LEFT)
                frontier.append(p + RIGHT)

        return []
            
    def find_first_value(self, v: int) -> P | None:
        for y in range(0,self.size.height):
            for x in range(0,self.size.width):
                p = P(x=x,y=y)
                if self.cells.get(p) == v:
                    return p
        return None
    
    def in_bounds(self,p: P) -> bool:
        return p.x >=0 and p.y >=0 and p.x < self.size.width and p.y < self.size.height

    def magnitude(self) -> int:
        return self.size.magnitude()

def load_grid(path: str) -> Grid:
  with open(path,'r') as f:
      return load_grid_from_str(f.read())

def load_grid_from_str(s: str) -> Grid:
  cells = {}
  width,height = 0,0

  y = 0
  for row in s.split("\n"):
      if row.strip():
        width = len(row)
        height +=1 
        for x, col in enumerate(row.strip()):
          p = P(x=x,y=y)
          cells[p] = int(col)
        y+=1

  return Grid(size=S(width=width,height=height),cells=cells)

def dump_grid_s(grid: Grid, path: dict) -> str:
  s = ""
  for y in range(0,grid.size.height):
    for x in range(0,grid.size.width):
        p = P(x=x,y=y)
        c = path.get(p) or str(grid.cells.get(p)) or '.'
        s+=c
    s+="\n"
  return s

def dump_grid(grid: Grid, path: dict):
    print(dump_grid_s(grid, path))

