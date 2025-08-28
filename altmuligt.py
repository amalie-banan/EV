import pandas as pd
import numpy as np
import time
import random

import subprocess
import importlib.util
# 5x5 Puslespil datasæt
# Positioner: 0-4 (top row), 5-9 (second row), osv.
# Kant-brikker har "flat" på ydersiderne
# Farver: blue, red, green, yellow, purple, orange
# in = hunkøn (modtager), out = hankøn (giver)
puzzle_pieces = [
    # Top row (0-4)
    {"id": 0,  "top": "flat", "right": "blue_out",    "bottom": "red_in",    "left": "flat",       "solution_pos": (0, 0)},
    {"id": 1,  "top": "flat", "right": "green_out",   "bottom": "yellow_in", "left": "blue_in",    "solution_pos": (0, 1)},
    {"id": 2,  "top": "flat", "right": "purple_out",  "bottom": "green_in",  "left": "green_in",   "solution_pos": (0, 2)},
    {"id": 3,  "top": "flat", "right": "orange_out",  "bottom": "blue_in",   "left": "purple_in",  "solution_pos": (0, 3)},
    {"id": 4,  "top": "flat", "right": "flat",        "bottom": "red_in",    "left": "orange_in",  "solution_pos": (0, 4)},

    # Second row (5-9)
    {"id": 5,  "top": "red_out",    "right": "yellow_out", "bottom": "purple_in", "left": "flat",      "solution_pos": (1, 0)},
    {"id": 6,  "top": "yellow_out", "right": "blue_out",   "bottom": "orange_in", "left": "yellow_in", "solution_pos": (1, 1)},
    {"id": 7,  "top": "green_out",  "right": "red_out",    "bottom": "yellow_in", "left": "blue_in",   "solution_pos": (1, 2)},
    {"id": 8,  "top": "blue_out",   "right": "green_out",  "bottom": "purple_in", "left": "red_in",    "solution_pos": (1, 3)},
    {"id": 9,  "top": "red_out",    "right": "flat",       "bottom": "orange_in", "left": "green_in",  "solution_pos": (1, 4)},

    # Third row (10-14)
    {"id": 10, "top": "purple_out", "right": "orange_out", "bottom": "blue_in",   "left": "flat",      "solution_pos": (2, 0)},
    {"id": 11, "top": "orange_out", "right": "purple_out", "bottom": "green_in",  "left": "orange_in", "solution_pos": (2, 1)},
    {"id": 12, "top": "yellow_out", "right": "yellow_out", "bottom": "red_in",    "left": "purple_in", "solution_pos": (2, 2)},
    {"id": 13, "top": "purple_out", "right": "blue_out",   "bottom": "orange_in", "left": "yellow_in", "solution_pos": (2, 3)},
    {"id": 14, "top": "orange_out", "right": "flat",       "bottom": "yellow_in", "left": "blue_in",   "solution_pos": (2, 4)},

    # Fourth row (15-19)
    {"id": 15, "top": "blue_out",   "right": "red_out",    "bottom": "green_in",  "left": "flat",      "solution_pos": (3, 0)},
    {"id": 16, "top": "green_out",  "right": "green_out",  "bottom": "purple_in", "left": "red_in",    "solution_pos": (3, 1)},
    {"id": 17, "top": "red_out",    "right": "orange_out", "bottom": "blue_in",   "left": "green_in",  "solution_pos": (3, 2)},
    {"id": 18, "top": "orange_out", "right": "purple_out", "bottom": "red_in",    "left": "orange_in", "solution_pos": (3, 3)},
    {"id": 19, "top": "yellow_out", "right": "flat",       "bottom": "yellow_in", "left": "purple_in", "solution_pos": (3, 4)},

    # Bottom row (20-24)
    {"id": 20, "top": "green_out",  "right": "blue_out",   "bottom": "flat", "left": "flat",      "solution_pos": (4, 0)},
    {"id": 21, "top": "purple_out", "right": "yellow_out", "bottom": "flat", "left": "blue_in",   "solution_pos": (4, 1)},
    {"id": 22, "top": "blue_out",   "right": "red_out",    "bottom": "flat", "left": "yellow_in", "solution_pos": (4, 2)},
    {"id": 23, "top": "red_out",    "right": "yellow_out", "bottom": "flat", "left": "red_in",    "solution_pos": (4, 3)},
    {"id": 24, "top": "yellow_out", "right": "flat",       "bottom": "flat", "left": "yellow_in", "solution_pos": (4, 4)}
]


def generate_and_load_puzzle(size):
    """Generer et puslespil og indlæs det"""
    print(f"Generating {size}x{size} puzzle...")
    
    # Kør generate_puzzle.py med den ønskede størrelse
    # Du skal ændre din generate_puzzle.py til at tage size som parameter
    
    # Alternativt: importér og kør direkte
    spec = importlib.util.spec_from_file_location("generate_puzzle", "generate_puzzle.py")
    gen_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen_module)
    
    # Generer puslespillet
    puzzle_pieces = gen_module.generate_puzzle_dataset(size)
    
    # Verificer det
    if gen_module.verify_puzzle(puzzle_pieces):
        print(f"✓ {size}x{size} puzzle generated successfully!")
        return puzzle_pieces
    else:
        print("✗ Puzzle generation failed!")
        return None

 

def get_opposite(x):
    if x == 'flat':
        return 'flat'
    c, g = x.split("_")
    if g == 'in':
        s = '_out'
    else:
        s = '_in'
    return c+s

 
 
def backtrack_solve(grid, available_pieces, grid_size, position=0):
    if position == grid_size * grid_size:  # Alle positioner fyldt
        return True
    
    #konverter r,c til 
    r, c = position // grid_size, position % grid_size
   # print(f"Trying position ({r},{c}) - {len(available_pieces)} pieces left")
    for piece in available_pieces[:]:  # Kopi af listen
        if is_correct_placement(piece, r, c, grid, grid_size):
         #   print(f"  Placing piece {piece['id']} at ({r},{c})")
            grid[r, c] = piece
            available_pieces.remove(piece)
            
            if backtrack_solve(grid, available_pieces,grid_size, position + 1):
                return True
                 
         #   print(f"  Backtracking from ({r},{c}), removing piece {piece['id']}")
            grid[r, c] = None
            available_pieces.append(piece)
    
    return False

def is_correct_placement(piece, r,c,grid,grid_size):

    top_n = grid[r-1,c] if r > 0 else None
    bottom_n = grid[r+1,c] if r < grid_size-1 else None
    right_n = grid[r,c+1] if c < grid_size-1 else None
    left_n = grid[r,c-1]  if c > 0 else None

    is_correct = (check_correct_placement(piece['top'], top_n, 'bottom', r==0) and
                  check_correct_placement(piece['bottom'], bottom_n, 'top', r==grid_size-1) and
                  check_correct_placement(piece['right'], right_n, 'left', c==grid_size-1) and
                  check_correct_placement(piece['left'], left_n, 'right', c==0))
    return is_correct

def check_correct_placement(piece_side, n, n_side, is_edge):
    if is_edge:
        return piece_side =='flat'
    if n is None:
        return piece_side != 'flat'
    
    return get_opposite(n[n_side]) == piece_side
 
def print_solution(grid, grid_size=5):
    print("\n=== BACKTRACK SOLUTION FOUND ===")
    for r in range(grid_size):
        row_ids = []
        for c in range(grid_size):
            piece = grid[r, c]
            if piece is not None:
                row_ids.append(f"{piece['id']:2d}")
            else:
                row_ids.append("--")
        print(f"Row {r}: [{', '.join(row_ids)}]")

    
 

# Kør backtracking
def solve_puzzle(size):
    print(f"Solving {size}x{size} puzzle...")
    
    if size == 5:
        # Brug dit eksisterende datasæt
        puzzle_pieces = generate_and_load_puzzle(size)
    else:
        # Generer nyt puslespil
        puzzle_pieces = generate_and_load_puzzle(size)
        if puzzle_pieces is None:
            print("Failed to generate puzzle!")
            return
    
    pieces = random.sample(puzzle_pieces, len(puzzle_pieces))
    current_grid = np.full((size, size), None, dtype=object)
    
    start_time = time.time()
    result = backtrack_solve(current_grid, pieces.copy(), grid_size=size)
    end_time = time.time()
    
    if result:
        print_solution(current_grid, size)
        print(f"Solved in {end_time - start_time:.2f} seconds")
    else:
        print("No solution found!")

# Brug det:
solve_puzzle(5)   # Dit eksisterende 5x5
solve_puzzle(10)  # Nyt 10x10 puslespil
 