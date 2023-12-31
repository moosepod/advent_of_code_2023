""" Create the scaffolding for a day of AOC """

import os
import argparse

def scaffold_day(day: int):
    print(f"Setting up day {day}")
    dir_path = f"day_{day}"
    if os.path.exists(dir_path):
        print(f"{dir_path} already exists")
        return
    print(f"...creating directory at {dir_path}")
    os.mkdir(dir_path)

    path = os.path.join(dir_path, f"aoc_2023_day_{day}.org")
    print(f"...creating template at {path}")
    with open(path, "w") as f:
        f.write(aoc_template(day))
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("day", help="Day of AOC")
    args = parser.parse_args()
    day = int(args.day)
    if day < 1 or day > 25:
        print(f"Day of {args.day} must be in range 1 to 25 inclusive") 
    scaffold_day(day)
    
def aoc_template(day: int) -> str:
    return f"""
* AOC 2023 Day {day}

** Initialize 
#+BEGIN_SRC elisp
  (pyvenv-activate "~/projects/project_venv/")
  ; This is needed to make sure python indentation isn't messed up
  (setq org-src-preserve-indentation t)
#+END_SRC

** Day {day} star 1
*** Problem statement
*** Solution
#+BEGIN_SRC python :results output
import re
def star_1(path: str) -> int:
  with open(path,'r') as f:
     pass
  return 0
  
print("Star 1:",star_1("sample.txt"))

#+END_SRC

** Day {day} star 2
*** Problem statement
*** Solution
#+BEGIN_SRC python :results output
def star_2(path: str) -> int:
  with open(path,'r') as f:
     pass
  return 0
  
print("Star 2:", star_2("sample.txt"))
#+END_SRC

"""
    
if __name__ == "__main__":
    main()
