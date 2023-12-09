from pydantic import BaseModel, model_validator

class P(BaseModel):
    """ A point """
    x: int
    y: int
    z: int = 0

class R(BaseModel):
    """ A range with a/b inclusive""" 
    a: int 
    b: int

    def overlap(self, r: 'R') -> bool:
        return max(self.a, r.a) <= min(self.b, r.b) 

    def __contains__(self, value) -> bool:
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
