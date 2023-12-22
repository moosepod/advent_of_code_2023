from typing import Optional
from pydantic import BaseModel, model_validator
from queue import Queue

class P(BaseModel):
    """ A point """
    x: int = 0
    y: int = 0

    def __hash__(self):
        return hash(f'{self.x}x{self.y}')

    def __add__(self, value):
        # Assume adding a P
        return P(x=self.x+value.x, y=self.y+value.y)

    def __sub__(self, value):
        # Assume adding a P
        return P(x=self.x-value.x, y=self.y-value.y)

    def __mul__(self,value):
        # Assume multiplying by int
        return P(x=self.x*value, y=self.y*value)

    def __lt__(self,value):
        return self.x < value.x or self.y < value.y
    
    def __eq__(self, value):
        if value == None:
            return False
        
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

    def get_with_priority(self) -> tuple[float,P]:
        return heapq.heappop(self.elements)

class Grid(BaseModel):
    """ Pathfinding adapted from https://www.redblobgames.com/pathfinding/a-star/introduction.html """
    size: S
    cells: dict[P, int]
    blocked: list

    def is_blocked(self, p: P) -> bool:
        return self.cells.get(p,0) in self.blocked or not self.in_bounds(p)

    def neighbors(self,p: P) -> list[P]:
        for d in (UP,DOWN,LEFT,RIGHT):
            if not self.is_blocked(p + d):
                yield p + d

    def neighbors_with_direction(self,p: P) -> list[tuple[P,P]]:
        for d in (UP,DOWN,LEFT,RIGHT):
            if not self.is_blocked(p + d):
                yield (p + d,d)

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

    def points(self) -> list[P]:
        for x in range(0, self.size.width):
            for y in range(0,self.size.height):
                yield P(x=x,y=y)
                
    def dijkstra_k_shortest_paths(self, s: P, t: P, K: int) -> list[P]:
        """ https://en.wikipedia.org/wiki/K_shortest_path_routing """
        P = []
        B = PriorityQueue()
        B.put([s],0)
        count = {p: 0 for p in self.points()}

        while not B.empty() and count[t] < K:
            C, p_u = B.get_with_priority()
            u = p_u[-1]
            if count[u] >= K:
                continue
            count[u] += 1
            if u == t:
                P.append([x for x in p_u])
            for v in self.neighbors(u):
                np = [p for p in p_u]
                np.append(v)
                B.put(np, C + (self.cells.get(v,0)+1))
                    
        return P

    def dijkstra_max_length(self, s: P, t: P, L: int) -> list[P]:
        """ Run dijkstras with no path longer than L """
        B = PriorityQueue()
        B.put([s],0)
        visited = set()
        visited.add(s)

        while not B.empty():
            C, p_u = B.get_with_priority()
            u = p_u[-1]
            if u == t:
                return p_u
            for v in self.neighbors(u):
                np = [p for p in p_u]
                np.append(v)

                if below_max_length(np, L) and v not in visited:
                    B.put(np, C + (self.cells.get(v,0)+1))
                    visited.add(v)
                    
        return []

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

    def find_path(self, came_from: dict, end: P) -> list[P]:
        p = end
        path = []
        while p:
            path.append(came_from[p])
            p = came_from[p]

        return path

    def find_path_with_directions(self, came_from: dict, end: P) -> list[tuple[P,P]]:
        p = end
        path = []
        while p:
            path.append(came_from[p])
            p,d = came_from[p]

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

    def dijkstra_pathfind_with_max(self, start: P, end: P,max_d:int ) -> list[P] | None:
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

        return None

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

    def greedy_best_first_search(self, start: P, end: P, heuristic) -> list[P]:
        frontier = PriorityQueue()
        frontier.put(start, 0)
        came_from = {start: None}

        while not frontier.empty():
            current = frontier.get()

            for n in self.neighbors(current):
                if n == end:
                    came_from[n] = current
                    return self.find_path(came_from, end)
                    
                if n not in came_from:
                    priority = heuristic(end, n)
                    frontier.put(n,priority)
                    came_from[n] = current
                
        return []

    def a_star(self, start: P, end: P, heuristic) -> list[P]:
        frontier = PriorityQueue()
        frontier.put(start, 0)
        came_from = {start: None}
        cost_so_far = {start: 0}

        while not frontier.empty():
            current = frontier.get()

            for n in self.neighbors(current):
                if n == end:
                    came_from[n] = current
                    return self.find_path(came_from, end)

                new_cost = cost_so_far[current] + self.cells[n]
                    
                if n not in cost_so_far or new_cost < cost_so_far[n]:
                    cost_so_far[n] = new_cost
                    priority = new_cost + heuristic(end, n)
                    frontier.put(n,priority)
                    came_from[n] = current
                
        return []

    def is_straight_path(self, p: P, d: P, current: P, came_from: dict, max_straight: int) -> bool:
        i = 0
        while i < max_straight:
            if not came_from.get(current):
                return False
            np, nd = came_from.get(current)
            if nd != d:
                return False
            d = nd
            p = np
            i+=1

        return True
        
        
    def a_star_with_max_straight(self, start: P, end: P, heuristic, max_straight: int) -> list[P]:
        frontier = PriorityQueue()
        frontier.put((start,RIGHT),0 )
        came_from = {start: (None, None)}
        cost_so_far = {start: 0}

        while not frontier.empty():
            current, current_d = frontier.get()

            for n,d in self.neighbors_with_direction(current):
                if n == end:
                    came_from[n] = (current, d)
                    return self.find_path_with_directions(came_from, end)

                new_cost = cost_so_far[current] + self.cells[n]
                if self.is_straight_path(n, d, current, came_from, max_straight):
                    new_cost = 10000000
                    
                if n not in cost_so_far or new_cost < cost_so_far[n]:
                    cost_so_far[n] = new_cost
                    h_val = heuristic(end, n)
                    priority = new_cost + h_val
                    frontier.put((n,d),priority)
                    came_from[n] = (current,d)
                
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

def manhattan_distance(p1: P, p2: P) -> int:
    return abs(p1.x -p2.x) + abs(p1.y - p2.y)

def d_to_c(d: P) -> str:
    if not d:
        return 'x'
    
    if d == RIGHT:
        return ">"

    if d == LEFT:
        return "<"

    if d == UP:
        return "^"

    if d == DOWN:
        return "v"

    return "x"

def below_max_length(path: list[P], L: int)->bool:
    if len(path) <= L:
        return True

    for i in range(L,len(path)):
        dx = 0
        dy = 0
        for j in range(1,L):
            dx += (path[i].x - path[i-j].x)
            dy += (path[i].y - path[i-j].y)
            print(i,j,dx,dy,path[i],path[i-j])

        if abs(dx) > L or abs(dy) > L:
            return False

    return True
