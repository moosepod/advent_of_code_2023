from queue import Queue
from typing import Optional
from pydantic import BaseModel, model_validator

class P(BaseModel):
    """ A point """
    x: int = 0
    y: int = 0

    def clone(self):
        return P(x=self.x,y=self.y)
    
    def __hash__(self):
        return hash(f'{self.x}x{self.y}')

    def __add__(self, value):
        # Assume adding a P
        return P(x=self.x+value.x, y=self.y+value.y)

class Polygon(BaseModel):
    verticies: list[P]

    def perimeter(self):
        p = 0

        for i in range(1, len(self.verticies)):
            p1 = self.verticies[i-1]
            p2 = self.verticies[i]
            if p1.y == p2.y:
                p += abs(p1.x - p2.x)
            else:
                p += abs(p1.y - p2.y)

        return p
    
    def area(self) -> int:
        area = 0
        j = len(self.verticies)-1

        for i in range(0,len(self.verticies)):
            #print(i,j,'x',self.verticies[j].x,self.verticies[i].x,self.verticies[j].x + self.verticies[i].x)
            #print(i,j,'y',self.verticies[j].y,self.verticies[i].y,self.verticies[j].y - self.verticies[i].y)
            area += (self.verticies[j].x + self.verticies[i].x) * (self.verticies[j].y - self.verticies[i].y);
            j = i
            
        return area/2

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


RIGHT=P(x=1,y=0)
LEFT=P(x=-1,y=0)
UP=P(x=0,y=-1)
DOWN=P(x=0,y=1)

class Grid(BaseModel):
    size: S
    cells: dict[P, str]
    start: P

    def passable(self, p: P, d: P,from_c: P) -> bool:
        return self.in_bounds(p) and self.cells.get(p,'.') in ('.','x')

    def expanded(self, mapping: dict[P,str], sd: S, default_char='.') -> 'Grid':
        grid = Grid(cells={}, start=P(), size=S(width=self.size.width*sd.width, height=self.size.height*sd.height))
        for x in range(0, self.size.width):
            for y in range(0,self.size.height):
                c = self.cells.get(P(x=x,y=y)) or default_char
                for i in range(0,sd.width):
                    for j in range(0,sd.height):
                        
                        grid.cells[P(x=(x*sd.width)+i,y=(y*sd.height)+j)] = mapping[c][j][i]

        return grid

    def flood_fill(self, p: P, fill_c: str, iteration_max=0):
        frontier = Queue()
        frontier.put(p)
        reached = set()

        count = 0
        while not frontier.empty():
            if iteration_max and count > iteration_max:
                break
            count+=1
            current = frontier.get()
            c = self.cells.get(current,'.')
            if current not in reached:
                if self.passable(current + UP, UP, c):
                    frontier.put(current + UP)
                if self.passable(current + DOWN, DOWN, c):
                    frontier.put(current + DOWN)
                if self.passable(current + RIGHT, RIGHT,c):
                    frontier.put(current + RIGHT)
                if self.passable(current + LEFT, LEFT,c):
                    frontier.put(current + LEFT)
                reached.add(current)
                if self.cells.get(current,'.') == '.':
                    self.cells[current] = fill_c
        self.cells[current] = "!"

    def connect(self, p1: P, p2: P):
        c = self.cells[P1]
        for mapping in MAPPINGS.get(c,()):
            if mapping + p1 == p2:
                return True

        return False

    def in_bounds(self,p: P) -> bool:
        return p.x >=self.start.x and p.y >=self.start.y and p.x < self.size.width and p.y < self.size.height
    
    def connected_points(self, p1: P) -> list:
        points = []
        c = self.cells[p1]
        for mapping in MAPPINGS.get(c,()):
            p2 = p1 + mapping
            if self.in_bounds(p2):
                points.append(p2)

        return points

    def magnitude(self) -> int:
        return self.size.magnitude()

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
  for y in range(-1,grid.size.height+1):
    s = ""
    for x in range(-1,grid.size.width+1):
      c = grid.cells.get(P(x=x,y=y)) or '.'
      #if c == 'O':
      #    c = ' '
      #elif c != '.':
      #    c = 'X'
      s+=c
    print(s)

def find_loop_path(grid: Grid) -> list[P]:
  visited: dict[P,bool] = {grid.start: 0}
  max_depth = 0
  p = grid.start
  to_visit = [*grid.connected_points(p)]

  # use DFS to find the path
  counter = 0
  path = [p]
  while len(to_visit) and counter < 100000:
      counter+=1
      p2 = to_visit[0]#.pop()
      del to_visit[0]
      if not visited.get(p2):
          visited[p2] = True
          #print('Visited',p2,grid.cells[p2],'from',p,visited[p2])
          to_visit.extend([np for np in grid.connected_points(p2) if not visited.get(np)])
          path.append(p2)

  return path
