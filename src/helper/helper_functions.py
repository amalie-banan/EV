import math

def create_octagon_coords(center_x, center_y, radius):
        coords = []
        # 8 punkter for oktagon (45 grader mellem hver)
        for i in range(8):
            angle = i * (2 * math.pi / 8)  # 45 grader = π/4 radianer
            x = center_x + int(radius * math.cos(angle))
            y = center_y + int(radius * math.sin(angle))
            coords.append((x, y))
        
        return coords

# Alternativt: Gør Sjælland lidt mindre og mere aflang
def create_elliptical_octagon(center_x, center_y, radius_x, radius_y):
    """Skaber en aflang oktagon"""
    coords = []
    import math
    
    for i in range(8):
        angle = i * (2 * math.pi / 8)
        x = center_x + int(radius_x * math.cos(angle))
        y = center_y + int(radius_y * math.sin(angle))
        coords.append((x, y))
    
    return coords

# Aflang Sjælland (mere realistisk form)
def draw_line_points(x1, y1, x2, y2):
    """Tegner alle punkter langs en linje mellem to punkter"""
    points = []
    
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    
    # Bestem retning
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    
    err = dx - dy
    x, y = x1, y1
    
    while True:
        points.append((x, y))
        
        if x == x2 and y == y2:
            break
            
        e2 = 2 * err
        
        if e2 > -dy:
            err -= dy
            x += sx
            
        if e2 < dx:
            err += dx
            y += sy
    
    return points

def create_elliptical_octagon_outline_precise(center_x, center_y, radius_x, radius_y, rotation_degrees=0):
    """Skaber elliptisk oktagon med alle kantpunkter og rotation"""
    import math
    
    # Konverter grader til radianer
    rotation_rad = math.radians(rotation_degrees)
    
    # Find de 8 hjørner med rotation
    corners = []
    for i in range(8):
        angle = i * (2 * math.pi / 8)
        
        # Beregn position før rotation
        x_before = radius_x * math.cos(angle)
        y_before = radius_y * math.sin(angle)
        
        # Anvend rotation
        x_rotated = x_before * math.cos(rotation_rad) - y_before * math.sin(rotation_rad)
        y_rotated = x_before * math.sin(rotation_rad) + y_before * math.cos(rotation_rad)
        
        # Flyt til det rigtige centrum
        x = center_x + int(x_rotated)
        y = center_y + int(y_rotated)
        corners.append((x, y))
    
    # Tegn alle linjer mellem hjørnerne
    all_points = []
    
    for i in range(len(corners)):
        start = corners[i]
        end = corners[(i + 1) % len(corners)]
        
        line_points = draw_line_points(start[0], start[1], end[0], end[1])
        all_points.extend(line_points)
    
    # Fjern dubletter
    return list(set(all_points))
 
def get_cells_inside_outline_scanline(outline_coordinates, grid_width, grid_height):
    """Finder celler indenfor outline ved hjælp af scanline"""
    
    if not outline_coordinates:
        return []
    
    outline_set = set(outline_coordinates)
    inside_cells = []
    
    # Find bounding box
    min_x = min(coord[0] for coord in outline_coordinates)
    max_x = max(coord[0] for coord in outline_coordinates)
    min_y = min(coord[1] for coord in outline_coordinates)
    max_y = max(coord[1] for coord in outline_coordinates)
    
    print(f"Bounding box: ({min_x},{min_y}) to ({max_x},{max_y})")
    
    # For hver række
    for y in range(max(0, min_y), min(grid_height, max_y + 1)):
        # Find alle outline-punkter på denne række
        outline_x_coords = []
        for x, outline_y in outline_coordinates:
            if outline_y == y:
                outline_x_coords.append(x)
        
        if len(outline_x_coords) >= 2:
            outline_x_coords.sort()
            
            # Find par af outline-punkter og fyld mellem dem
            for i in range(0, len(outline_x_coords) - 1, 2):
                start_x = outline_x_coords[i]
                end_x = outline_x_coords[i + 1] if i + 1 < len(outline_x_coords) else outline_x_coords[-1]
                
                # Fyld mellem start_x og end_x (eksklusiv outline-punkterne selv)
                for x in range(start_x + 1, end_x):
                    if 0 <= x < grid_width and (x, y) not in outline_set:
                        inside_cells.append((x, y))
    
    print(f"Scanline found {len(inside_cells)} cells")
    return inside_cells