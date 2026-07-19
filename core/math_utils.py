import math
import mathutils

def get_perpendicular_2d(p1, p2):
    """Return a normalized 2D perpendicular vector to the line p1->p2 (Z=0)."""
    v = mathutils.Vector((p2.x - p1.x, p2.y - p1.y, 0.0))
    if v.length == 0:
        return mathutils.Vector((0, 1, 0))
    v.normalize()
    return mathutils.Vector((-v.y, v.x, 0.0))

def offset_line_2d(p1, p2, offset):
    """Offset line p1->p2 by 'offset' distance."""
    perp = get_perpendicular_2d(p1, p2)
    return (p1 + perp * offset, p2 + perp * offset)

def line_intersection_2d(p1, p2, p3, p4):
    """Find 2D intersection of line (p1, p2) and (p3, p4)."""
    # Intersection of two infinite lines
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    x3, y3 = p3.x, p3.y
    x4, y4 = p4.x, p4.y
    
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-6:
        # Lines are parallel
        return None
        
    intersect_x = ((x1*y2 - y1*x2)*(x3 - x4) - (x1 - x2)*(x3*y4 - y3*x4)) / denom
    intersect_y = ((x1*y2 - y1*x2)*(y3 - y4) - (y1 - y2)*(x3*y4 - y3*x4)) / denom
    
    return mathutils.Vector((intersect_x, intersect_y, p1.z))
