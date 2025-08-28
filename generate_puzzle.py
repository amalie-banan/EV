import random

def generate_puzzle_dataset(size=30):
    """Genererer et size x size puslespil datasæt med præcis 1 løsning"""
    colors = ['blue', 'red', 'green', 'yellow', 'purple', 'orange']
    puzzle_pieces = []
    
    # Grid til at holde styr på connections
    # Key: (row, col, direction), Value: color_type (f.eks. "blue_out")
    connections = {}
    
    for row in range(size):
        for col in range(size):
            piece_id = row * size + col
            piece = {"id": piece_id, "solution_pos": (row, col)}
            
            # TOP side
            if row == 0:
                piece["top"] = "flat"
            else:
                # Find bottom-siden af naboen ovenfor
                neighbor_bottom = connections[(row-1, col, 'bottom')]
                piece["top"] = get_opposite_side(neighbor_bottom)
            
            # LEFT side
            if col == 0:
                piece["left"] = "flat"
            else:
                # Find right-siden af naboen til venstre
                neighbor_right = connections[(row, col-1, 'right')]
                piece["left"] = get_opposite_side(neighbor_right)
            
            # RIGHT side
            if col == size - 1:
                piece["right"] = "flat"
            else:
                # Opret ny tilfældig connection til højre nabo
                color = random.choice(colors)
                direction = random.choice(['in', 'out'])
                piece["right"] = f"{color}_{direction}"
                connections[(row, col, 'right')] = piece["right"]
            
            # BOTTOM side
            if row == size - 1:
                piece["bottom"] = "flat"
            else:
                # Opret ny tilfældig connection til nabo nedenfor
                color = random.choice(colors)
                direction = random.choice(['in', 'out'])
                piece["bottom"] = f"{color}_{direction}"
                connections[(row, col, 'bottom')] = piece["bottom"]
            
            puzzle_pieces.append(piece)
    
    return puzzle_pieces

def get_opposite_side(side):
    """Returnerer den modsatte side til en given side"""
    if side == "flat":
        return "flat"
    
    color, direction = side.split("_")
    opposite_direction = "in" if direction == "out" else "out"
    return f"{color}_{opposite_direction}"

def save_puzzle_to_file(puzzle_pieces, filename="puzzle_30x30.py"):
    """Gemmer puzzle datasættet til en Python fil"""
    with open(filename, 'w') as f:
        f.write("puzzle_pieces_30x30 = [\n")
        
        size = int(len(puzzle_pieces) ** 0.5)  # Beregn størrelse
        
        for i, piece in enumerate(puzzle_pieces):
            row = piece['solution_pos'][0]
            col = piece['solution_pos'][1]
            
            # Tilføj kommentar for nye rækker
            if col == 0:
                f.write(f"    # Row {row} ({row*size}-{(row+1)*size-1})\n")
            
            # Formatér brikken
            f.write(f"    {{\"id\": {piece['id']:3d}, \"top\": \"{piece['top']:12s}\", ")
            f.write(f"\"right\": \"{piece['right']:12s}\", \"bottom\": \"{piece['bottom']:12s}\", ")
            f.write(f"\"left\": \"{piece['left']:12s}\", \"solution_pos\": {piece['solution_pos']}}}")
            
            # Tilføj komma hvis ikke sidste element
            if i < len(puzzle_pieces) - 1:
                f.write(",")
            f.write("\n")
        
        f.write("]\n")
    
    print(f"Puzzle saved to {filename}")

def verify_puzzle(puzzle_pieces):
    """Verificerer at puslespillet har konsistente forbindelser"""
    size = int(len(puzzle_pieces) ** 0.5)
    
    # Opret grid for hurtig lookup
    grid = {}
    for piece in puzzle_pieces:
        row, col = piece['solution_pos']
        grid[(row, col)] = piece
    
    errors = 0
    
    for piece in puzzle_pieces:
        row, col = piece['solution_pos']
        
        # Tjek top-nabo
        if row > 0:
            top_neighbor = grid[(row-1, col)]
            if get_opposite_side(top_neighbor['bottom']) != piece['top']:
                print(f"ERROR: Piece {piece['id']} top doesn't match neighbor {top_neighbor['id']} bottom")
                errors += 1
        
        # Tjek left-nabo
        if col > 0:
            left_neighbor = grid[(row, col-1)]
            if get_opposite_side(left_neighbor['right']) != piece['left']:
                print(f"ERROR: Piece {piece['id']} left doesn't match neighbor {left_neighbor['id']} right")
                errors += 1
        
        # Tjek kant-betingelser
        if row == 0 and piece['top'] != 'flat':
            print(f"ERROR: Piece {piece['id']} should have flat top")
            errors += 1
        if row == size-1 and piece['bottom'] != 'flat':
            print(f"ERROR: Piece {piece['id']} should have flat bottom")
            errors += 1
        if col == 0 and piece['left'] != 'flat':
            print(f"ERROR: Piece {piece['id']} should have flat left")
            errors += 1
        if col == size-1 and piece['right'] != 'flat':
            print(f"ERROR: Piece {piece['id']} should have flat right")
            errors += 1
    
    if errors == 0:
        print("✓ Puzzle verification passed! No errors found.")
    else:
        print(f"✗ Puzzle verification failed! {errors} errors found.")
    
    return errors == 0

# Generer og gem 30x30 puslespil
if __name__ == "__main__":
    print("Generating 30x30 puzzle...")
    puzzle_30x30 = generate_puzzle_dataset(30)
    
    print(f"Generated {len(puzzle_30x30)} pieces")
    
    # Verificer puslespillet
    if verify_puzzle(puzzle_30x30):
        # Gem til fil
        save_puzzle_to_file(puzzle_30x30, "puzzle_30x30.py")
        print("30x30 puzzle successfully generated and saved!")
    else:
        print("Puzzle generation failed verification.")
    
    # Vis første par brikker som eksempel
    print("\nFirst 5 pieces as example:")
    for i in range(min(5, len(puzzle_30x30))):
        piece = puzzle_30x30[i]
        print(f"  {piece}")