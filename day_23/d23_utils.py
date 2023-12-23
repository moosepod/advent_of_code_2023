from typing import Optional
from pydantic import BaseModel, model_validator
from queue import Queue

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

    def __lt__(self,value):
        return self.x < value.x or self.y < value.y
    
    def __eq__(self, value):
        return self.x == value.x and self.y == value.y and self.z == value.z
    
    def clone(self) -> 'P':
        return P(x=self.x,y=self.y,z=self.z)
        
class S(BaseModel):
    """A size. Not really different than point, but keeps var names separate"""
    width: int = 0
    height: int = 0
    depth: int = 0

    def magnitude(self) -> int:
        return self.width * self.height * self.depth

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

EMPTY = 0
END = 3

import heapq

class PriorityQueue:
    """ From https://www.redblobgames.com/pathfinding/a-star/implementation.html#python-dijkstra """
    def __init__(self):
        self.elements: list[tuple[float, T]] = []
    
    def empty(self) -> bool:
        return not self.elements
    
    def put(self, item: P, priority: float):
        heapq.heappush(self.elements, (priority, item))
    
    def get(self) -> P:
        return heapq.heappop(self.elements)[1]

class Grid(BaseModel):
    """ Pathfinding adapted from https://www.redblobgames.com/pathfinding/a-star/introduction.html """
    size: S
    cells: dict[P, int]
    blocked: list

    def points(self) -> list[P]:
        for x in range(0, self.size.width):
            for y in range(0,self.size.height):
                yield P(x=x,y=y)

    def is_blocked(self, p: P) -> bool:
        return self.cells.get(p,0) in self.blocked or not self.in_bounds(p)

    def neighbors(self,p: P) -> list[P]:
        for d in (UP,DOWN,LEFT,RIGHT):
            if not self.is_blocked(p + d):
                yield p + d

    def neighbors_with_max(self,p: P,came_from: dict, max_d: int) -> list[P]:
        for d in (UP,DOWN,LEFT,RIGHT):
            if not self.is_blocked(p + d):
                path_sum = P()
                t = p
                for i in range(0,max_d):
                    if came_from.get(t):
                        path_sum += t - came_from.get(t)
                        t = came_from.get(t)

                if abs(path_sum.x) < max_d and abs(path_sum.y) < max_d:
                    yield p + d
    
    def bfs(self, start: P, end: P) -> list[P]:
        """ Look for path from start to end. If end reached, return it """
        frontier = Queue()
        frontier.put(start.clone())
        reached = set()
        reached.add(start.clone())

        while not frontier.empty():
            p = frontier.get()
            for n in self.neighbors(p):
                if n == end:
                    return [p]

                if n not in reached:
                    frontier.put(n)
                    reached.add(n)

        return []

    def bfs_distances(self, start: P) -> dict:
        """ Look for path from start to end. If end reached, return it """
        frontier = Queue()
        frontier.put((start.clone(),0))
        reached = set()
        reached.add(start.clone())
        distances = {}

        while not frontier.empty():
            p,d = frontier.get()
            for n in self.neighbors(p):
                if n not in reached:
                    distances[n] = d+1
                    frontier.put((n,d+1))
                    reached.add(n)

        return distances

    def bfs_max_distance(self, start: P, max_distance: int, at_distance: dict) -> int:
        """ Look for path from start to end. If end reached, return it. Stop after max distance. Return count. """
        frontier = Queue()
        frontier.put((start.clone(),0))
        count = 0

        while not frontier.empty():
            p,d = frontier.get()
            if d == max_distance:
                if not at_distance.get(p):
                    count += 1
                    at_distance[p] = "O"
                continue

            for n in self.neighbors(p):
                if n not in at_distance:
                    frontier.put((n,d+1))

        return count
    
    def find_path(self, came_from: dict, end: P) -> list[P]:
        p = end
        path = []
        while p:
            path.append(came_from[p])
            p = came_from[p]

        return path

    def dijkstra_pathfind(self, start: P, end: P) -> list[P]:
        """ Look for path from start to end using a modified dijkstra (uniform cost search) """
        frontier = PriorityQueue()
        frontier.put(start, 0)
        came_from = {start: None}
        cost_so_far = {start: 0}

        while not frontier.empty():
            current = frontier.get()

            if current == end:
                return self.find_path(came_from, end)

            for n in self.neighbors(current):
                new_cost = cost_so_far[current] + self.cells.get(n,0)
                if n not in cost_so_far or new_cost < cost_so_far[n]:
                    cost_so_far[n] = new_cost
                    frontier.put(n, new_cost)
                    came_from[n] = current

        return []

    def dijkstra_pathfind_with_max(self, start: P, end: P,max_d:int ) -> list[P]:
        """ Look for path from start to end using a modified dijkstra (uniform cost search)
        Modified so max_d steps in a straight line counts as blocked
        """
        frontier = PriorityQueue()
        frontier.put(start, 0)
        came_from = {start: None}
        cost_so_far = {start: 0}

        while not frontier.empty():
            current = frontier.get()

            if current == end:
                return self.find_path(came_from, end)

            for n in self.neighbors_with_max(current, came_from, max_d):
                new_cost = cost_so_far[current] + self.cells.get(n,0)
                if n not in cost_so_far or new_cost < cost_so_far[n]:
                    cost_so_far[n] = new_cost
                    frontier.put(n, new_cost)
                    came_from[n] = current

        return []

    def bfs_pathfind(self, start: P, end: P) -> list[P]:
        """ Look for path from start to end. If found, return it.
            Uses early exit."""
        frontier = Queue()
        frontier.put(start.clone())
        came_from = dict()
        came_from[start.clone()] = None

        while not frontier.empty():
            p = frontier.get()
            for n in self.neighbors(p):
                if n == end:
                    came_from[n] = p
                    return self.find_path(came_from, end)

                if n not in came_from:
                    frontier.put(n)
                    came_from[n] = p

        return []

    def find_first_value(self, c: str) -> P | None:
        for y in range(0,self.size.height):
            for x in range(0,self.size.width):
                p = P(x=x,y=y)
                if self.cells.get(p) == c:
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
          cells[p] = col
        y+=1

  return Grid(size=S(width=width,height=height),cells=cells, blocked=[])

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

def dump_grid_x(grid: Grid):
  s = ""
  for z in range(grid.size.depth,-1,-1):
    for x in range(0,grid.size.width):
        c = None
        for y in range(0,grid.size.height):
            p = P(x=x,y=y,z=z)
            if z == 0:
                s+="-"
                c="-"
                break
            c = grid.cells.get(p)
            if c:
                s+=chr(c+64)
                break
        if not c:
            s+="."
    s+=f" {z}\n"
  print(s)

def dump_grid_y(grid: Grid):
  s = ""
  for z in range(grid.size.depth,-1,-1):
      for y in range(0,grid.size.height):
        c = None
        for x in range(0,grid.size.width):
            p = P(x=x,y=y,z=z)
            if z == 0:
                s+="-"
                c="-"
                break
            
            c = grid.cells.get(p)
            if c:
                s+=chr(c+64)
                break
        if not c:
            s+="."
      s+=f" {z}\n"
  print(s)
