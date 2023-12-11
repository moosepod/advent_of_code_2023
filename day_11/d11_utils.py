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

    def __eq__(self, value):
        return self.x == value.x and self.y == value.y and self.z == value.z
    
    def clone(self) -> 'P':
        return P(x=self.x,y=self.y,z=self.z)
        
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

MAPPINGS = {"|": (P(x=0,y=-1),P(x=0,y=1)),
            "-": (P(x=1,y=0),P(x=-1,y=0)),
            "L": (P(x=1,y=0),P(x=0,y=-1)),
            "J": (P(x=-1,y=0),P(x=0,y=-1)),
            "7": (P(x=-1,y=0),P(x=0,y=1)),
            "F": (P(x=1,y=0),P(x=0,y=1))}

class Grid(BaseModel):
    size: S
    cells: dict[P, str]
    distance_cache: dict[str,int] = {}
    cell_sizes: dict[P, str]

    def connect(self, p1: P, p2: P):
        c = self.cells[P1]
        for mapping in MAPPINGS.get(c,()):
            if mapping + p1 == p2:
                return True

        return False

    def in_bounds(self,p: P) -> bool:
        return p.x >=0 and p.y >=0 and p.x < self.size.width and p.y < self.size.height

    def find(self, c: str) -> list[P]:
        r = []

        for y in range(0, self.size.height):
            for x in range(0, self.size.width):
                p = P(x=x,y=y)
                if self.cells[p] == c:
                    r.append(p)

        return r

    def grid_distance(self, p1: P, p2: P) -> int:
        d = 0

        p = p1.clone()
        
        toggle = True
        while p != p2:
            if self.distance_cache.get((p,p2)) != None:
                return d + self.distance_cache[(p,p2)]

            dir_x = 0
            dir_y = 0

            if p.x != p2.x:
                dir_x = 1 if p2.x - p.x > 0 else -1

            if p.y != p2.y:
                dir_y = 1 if p2.y - p.y > 0 else -1

            if dir_x == 0 and dir_y == 0:
                break
            
            s = self.cell_sizes[p]

            #print('1',p,s)

            if dir_y == 0:
                d += s.width
                p.x += dir_x
            elif dir_x == 0:
                d += s.height
                p.y += dir_y
            else:
                if toggle:
                    d += s.width 
                    p.x += dir_x
                else:
                    d+= s.height
                    p.y += dir_y
                toggle = not toggle

            #print('2',p,d,dir_x,dir_y)
            #print()

        self.distance_cache[(p,p2)] = d
        
        return d
                
    def connected_points(self, p1: P) -> list:
        points = []
        c = self.cells[p1]
        for mapping in MAPPINGS.get(c,()):
            p2 = p1 + mapping
            if self.in_bounds(p2):
                points.append(p2)

        return points

    def insert_column(self, at_x: int, c: str):
        self.size.width += 1
        for x in range(self.size.width-1, at_x, -1):
            for y in range(0,self.size.height):
                self.cells[P(x=x,y=y)] = self.cells[P(x=x-1, y=y)]
        for y in range(0,self.size.height):
            self.cells[P(x=at_x,y=y)] = c

    def insert_row(self, at_y: int, c: str):
        self.size.height += 1
        for y in range(self.size.height-1, at_y, -1):
            for x in range(0,self.size.width):
                self.cells[P(x=x,y=y)] = self.cells[P(x=x, y=y-1)]
        for x in range(0,self.size.width):
            self.cells[P(x=x,y=at_y)] = c

    def expand_size(self, s: int):        
        for x in range(0, self.size.width):
            for y in range(0, self.size.height):
                self.cell_sizes[P(x=x,y=y)] = S(width=1,height=1)

        for x in range(0,self.size.width):
            if len([True for y in range(0,self.size.height) if not self.cells.get(P(x=x, y=y)) == '#']) == self.size.height:
                for y in range(0,self.size.height):
                    self.cell_sizes[P(x=x,y=y)].width = s

        for y in range(0, self.size.height):
            if len([True for x in range(0,self.size.width) if not self.cells.get(P(x=x, y=y)) == '#']) == self.size.width:
                for x in range(0,self.size.width):
                    self.cell_sizes[P(x=x,y=y)].height = s
        
    def expand(self):
        x = 0
        while x < self.size.width:
            if len([True for y in range(0,self.size.height) if not self.cells.get(P(x=x, y=y)) == '#']) == self.size.height:
                self.insert_column(x,'.')
                x+=1
            x+=1

        y = 0
        while y < self.size.height:
            if len([True for x in range(0,self.size.width) if not self.cells.get(P(x=x, y=y)) == '#']) == self.size.width:
                self.insert_row(y,'.')
                y+=1
            y+=1

    def magnitude(self) -> int:
        return self.size.magnitude()

def load_grid(path: str) -> Grid:
  cells = {}
  width,height = 0,0

  with open(path,'r') as f:
    for y, row in enumerate(f.read().split("\n")):
      if row:
        width = len(row)
        height +=1 
        for x, col in enumerate(row.strip()):
          p = P(x=x,y=y)
          cells[p] = col

  return Grid(size=S(width=width,height=height),cells=cells,cell_sizes={})


def dump_grid(grid: Grid):
  for y in range(0,grid.size.height):
    s = ""
    for x in range(0,grid.size.width):
      c = grid.cells.get(P(x=x,y=y)) or '.'
      s+=c
    print(s)

