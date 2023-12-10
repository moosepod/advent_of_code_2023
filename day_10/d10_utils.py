from typing import Optional
from pydantic import BaseModel, model_validator

class P(BaseModel):
    """ A point """
    x: int = 0
    y: int = 0
    z: int = 0

    def __hash__(self):
        return hash(f'{self.x}x{self.y}x{self.z}')

    def __add__(self, value):
        # Assume adding a P
        return P(x=self.x+value.x, y=self.y+value.y, z=self.z+value.z)
        
class S(BaseModel):
    """A size. Not really different than point, but keeps var names separate"""
    width: int
    height: int

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

MAPPINGS = {"|": (P(x=0,y=-1),P(x=0,y=1)),
            "-": (P(x=1,y=0),P(x=-1,y=0)),
            "L": (P(x=1,y=0),P(x=0,y=-1)),
            "J": (P(x=-1,y=0),P(x=0,y=-1)),
            "7": (P(x=-1,y=0),P(x=0,y=1)),
            "F": (P(x=1,y=0),P(x=0,y=1))}

class Grid(BaseModel):
    size: S
    cells: dict[P, str]
    start: P

    def connect(self, p1: P, p2: P):
        c = self.cells[P1]
        for mapping in MAPPINGS.get(c,()):
            if mapping + p1 == p2:
                return True

        return False

    def in_bounds(self,p: P) -> bool:
        return p.x >=0 and p.y >=0 and p.x < self.size.width and p.y < self.size.height
    
    def connected_points(self, p1: P) -> list:
        points = []
        c = self.cells[p1]
        for mapping in MAPPINGS.get(c,()):
            p2 = p1 + mapping
            if self.in_bounds(p2):
                points.append(p2)

        return points

def load_grid(path: str) -> Grid:
  cells = {}
  width,height = 0,0
  start = P()
  with open(path,'r') as f:
    for y, row in enumerate(f.read().split("\n")):
      if row:
        width = len(row)
        height +=1 
        for x, col in enumerate(row.strip()):
          p = P(x=x,y=y)
          if col == 'S':
              start = p
          cells[p] = col

  return Grid(size=S(width=width,height=height),cells=cells, start=start)


def dump_grid(grid: Grid):
  print("Starting at",grid.start)
  for y in range(0,grid.size.height):
    s = ""
    for x in range(0,grid.size.width):
      s+=grid.cells.get(P(x=x,y=y)) or '.'
    print(s)

