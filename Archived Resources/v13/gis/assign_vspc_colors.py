#!/usr/bin/env python3
"""
V12: Automatically assign colors to VSPCs using HSL-based palette selection.

This version uses a hue-evenly-distributed color palette based on HSL color space
to maximize perceptual color separation before applying geographic constraints.

Color selection reference:
- HSL Color Chart: https://www.quackit.com/css/color/charts/hsl_color_chart.cfm

This script:
1. Reads VSPC locations from GeoJSON
2. Calculates which VSPCs are adjacent (within distance threshold)
3. Uses HSL-based palette with evenly distributed hues (~11.25° increments for 32 colors)
4. Applies graph coloring with geographic constraints
5. Adds color properties to the GeoJSON
6. Creates a color mapping file for use in QGIS
"""

import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import colorsys

def hsl_to_hex(h: float, s: float, l: float) -> str:
    """
    Convert HSL color to hex string.
    
    Args:
        h: Hue in degrees (0-360)
        s: Saturation (0-100)
        l: Lightness (0-100)
    
    Returns:
        Hex color string (e.g., "#FF0000")
    """
    # Convert to 0-1 range for colorsys
    h_norm = (h % 360) / 360.0
    s_norm = s / 100.0
    l_norm = l / 100.0
    
    # Convert HSL to RGB
    r, g, b = colorsys.hls_to_rgb(h_norm, l_norm, s_norm)
    
    # Convert to 0-255 range and format as hex
    r_int = int(round(r * 255))
    g_int = int(round(g * 255))
    b_int = int(round(b * 255))
    
    return f"#{r_int:02X}{g_int:02X}{b_int:02X}"


def generate_hsl_palette(n_colors: int = 32, saturation: float = 100.0, lightness: float = 50.0) -> List[str]:
    """
    Generate a palette of colors evenly distributed around the HSL color wheel.
    
    Args:
        n_colors: Number of colors to generate
        saturation: Saturation percentage (0-100)
        lightness: Lightness percentage (0-100)
    
    Returns:
        List of hex color strings
    """
    palette = []
    hue_increment = 360.0 / n_colors
    
    for i in range(n_colors):
        hue = i * hue_increment
        hex_color = hsl_to_hex(hue, saturation, lightness)
        palette.append(hex_color)
    
    return palette


# V12 HSL-based palette: 32 colors evenly distributed around color wheel
# Using 100% saturation and 50% lightness for maximum vibrancy and distinction
# Hue increments: 360° / 32 = 11.25° per color
HSL_PALETTE = generate_hsl_palette(n_colors=32, saturation=100.0, lightness=50.0)

# Add whites, blacks, and grays to the palette
# White variations
WHITE_GRAY_PALETTE = [
    "#FFFFFF",  # Pure white
    "#F5F5F5",  # Very light gray
    "#E0E0E0",  # Light gray
    "#BDBDBD",  # Medium gray
    "#9E9E9E",  # Dark gray
    "#757575",  # Darker gray
    "#424242",  # Very dark gray
    "#000000",  # Pure black
]

# Combined palette: HSL colors + whites/blacks/grays
FULL_PALETTE = HSL_PALETTE + WHITE_GRAY_PALETTE

# For backward compatibility and as fallback
HIGH_CONTRAST_PALETTE = FULL_PALETTE

def get_hue_family(hue: float) -> str:
    """
    Get color family name based on hue value.
    Groups colors into families based on hue ranges.
    Uses 45° ranges for stricter family separation (8 main families).
    
    Args:
        hue: Hue in degrees (0-360)
    
    Returns:
        Family name string
    """
    hue_norm = hue % 360
    
    # Define hue ranges for color families
    # Using 45° ranges for families (8 main families) - stricter separation
    if hue_norm < 22.5 or hue_norm >= 337.5:
        return "red"
    elif hue_norm < 67.5:
        return "yellow"
    elif hue_norm < 112.5:
        return "green"
    elif hue_norm < 157.5:
        return "cyan"
    elif hue_norm < 202.5:
        return "blue"
    elif hue_norm < 247.5:
        return "purple"
    elif hue_norm < 292.5:
        return "magenta"
    else:  # 292.5-337.5
        return "pink"


def hex_to_hue(hex_color: str) -> float:
    """
    Convert hex color to HSL hue value.
    
    Args:
        hex_color: Hex color string (e.g., "#FF0000")
    
    Returns:
        Hue in degrees (0-360)
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    
    # Convert RGB to HSL
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    
    # Convert hue from 0-1 to 0-360 degrees
    hue_degrees = h * 360.0
    return hue_degrees


# Build color families dynamically based on HSL hue values
# Colors with similar hues (within 45°) are in the same family
# Whites, blacks, and grays get their own families
COLOR_FAMILIES = {}
COLOR_TO_FAMILY = {}

# Assign families to HSL colors
for color in HSL_PALETTE:
    hue = hex_to_hue(color)
    family = get_hue_family(hue)
    
    if family not in COLOR_FAMILIES:
        COLOR_FAMILIES[family] = []
    COLOR_FAMILIES[family].append(color)
    COLOR_TO_FAMILY[color] = family

# Assign families to whites, blacks, and grays
# Each gray shade gets its own family for maximum distinction
for i, color in enumerate(WHITE_GRAY_PALETTE):
    if color == "#FFFFFF":
        family = "white"
    elif color == "#000000":
        family = "black"
    else:
        # Each gray shade is its own family
        family = f"gray_{i}"
    
    if family not in COLOR_FAMILIES:
        COLOR_FAMILIES[family] = []
    COLOR_FAMILIES[family].append(color)
    COLOR_TO_FAMILY[color] = family

# Manual color overrides - specific colors for specific VSPCs
# V13: All colors are hardcoded from v12 final assignments
# Add new overrides here to change specific VSPCs without triggering full recalculation
MANUAL_COLOR_OVERRIDES = {
    "Arapahoe Community College": "#FF0030",
    "Arapahoe County CentrePoint Plaza": "#00CFFF",
    "Arapahoe County Fairgrounds": "#FFFFFF",  # White
    "Arapahoe County Lima Plaza": "#FFEF00",
    "Aurora Center for Active Adults": "#FFFF00",  # Yellow
    "Aurora Public Schools Educational Service Center 4": "#355E3B",  # Hunter/forest green
    "Aurora Public Schools Professional Learning & Conference Center": "#9E9E9E",
    "Beck Recreation Center": "#00FFCF",
    "Bemis Public Library": "#20FF00",
    "Central Recreation Center": "#000000",
    "Cherry Creek School District Instructional Support Facility": "#00FF10",
    "City of Aurora Municipal Center": "#FF6600",  # Bright orange
    "City of Glendale Municipal Building": "#424242",
    "City of Sheridan Municipal Building": "#FFFFFF",  # White
    "Community College of Aurora CentreTech Campus": "#F5F5F5",
    "Community College of Aurora Lowry Campus": "#9370DB",  # Royal purple (lighter, more blue)
    "Cook Park Recreation Center": "#E2C3EC",  # Medium lavender (between light and plum)
    "Englewood Civic Center": "#FFFFFF",
    "Greenwood Village City Hall": "#DF00FF",
    "Heather Gardens": "#FF3000",
    "Kelver Library": "#00FF70",
    "Martin Luther King, Jr. Library": "#FF0000",
    "Mission Viejo Library": "#FFFFFF",
    "Murphy Creek Golf Course": "#BDBDBD",  # Medium gray
    "Parkside Village Retirement Resort": "#5000FF",
    "Pickens Technical College": "#FF00EF",
    "Smoky Hill Library": "#FFA500",  # Light orange
    "Southglenn Library": "#66B3FF",  # Light blue
    "Tallyns Reach Library": "#FF00EF",
    "The Avenue Church": "#00FF40",
    "Trails Recreation Center": "#87CEEB",  # Light blue (sky blue)
    "Vista PEAK": "#FFEF00"
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in miles.
    Uses the Haversine formula.
    """
    R = 3959  # Earth radius in miles
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def build_adjacency_graph(vspcs: List[Dict], distance_threshold: float = 10.0) -> Dict[str, Set[str]]:
    """
    Build an adjacency graph of VSPCs based on geographic proximity.
    Returns a dictionary mapping VSPC name to set of adjacent VSPC names.
    """
    graph = {vspc['properties']['name']: set() for vspc in vspcs}
    
    for i, vspc1 in enumerate(vspcs):
        coords1 = vspc1['geometry']['coordinates']
        lon1, lat1 = coords1[0], coords1[1]
        
        for j, vspc2 in enumerate(vspcs):
            if i >= j:
                continue
            
            coords2 = vspc2['geometry']['coordinates']
            lon2, lat2 = coords2[0], coords2[1]
            
            distance = haversine_distance(lat1, lon1, lat2, lon2)
            
            if distance <= distance_threshold:
                name1 = vspc1['properties']['name']
                name2 = vspc2['properties']['name']
                graph[name1].add(name2)
                graph[name2].add(name1)
    
    return graph


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def color_distance(color1: str, color2: str) -> float:
    """
    Calculate perceptual color distance using weighted Euclidean distance in RGB space.
    Returns a value where larger = more different.
    """
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    
    # Weighted Euclidean distance (weights approximate human color perception)
    # Red and green are more perceptually important
    dr = (r1 - r2) ** 2
    dg = (g1 - g2) ** 2
    db = (b1 - b2) ** 2
    
    # Weighted distance (approximates perceptual difference)
    distance = math.sqrt(2 * dr + 4 * dg + 3 * db)
    return distance


def get_n_hop_neighbors(graph: Dict[str, Set[str]], node: str, n_hops: int = 3) -> Set[str]:
    """Get all neighbors within N hops."""
    if n_hops < 1:
        return set()
    
    all_neighbors = set()
    current_level = {node}
    visited = {node}
    
    for hop in range(n_hops):
        next_level = set()
        for current_node in current_level:
            neighbors = graph.get(current_node, set())
            for neighbor in neighbors:
                if neighbor not in visited:
                    next_level.add(neighbor)
                    visited.add(neighbor)
        all_neighbors.update(next_level)
        current_level = next_level
        if not current_level:
            break
    
    return all_neighbors


def colors_in_same_family(color1: str, color2: str) -> bool:
    """
    Check if two colors are in the same color family based on HSL hue.
    V12: Uses strict hue-based checking - colors within 30° hue are same family.
    Also checks exact family matches for whites/blacks/grays.
    """
    # Get families from HSL-based grouping
    family1 = COLOR_TO_FAMILY.get(color1)
    family2 = COLOR_TO_FAMILY.get(color2)
    
    if family1 and family2:
        # Exact family match - definitely same family
        if family1 == family2:
            return True
        
        # For HSL colors, also check hue distance directly
        # If both are HSL colors (not white/black/gray), check hue difference
        if color1 in HSL_PALETTE and color2 in HSL_PALETTE:
            hue1 = hex_to_hue(color1)
            hue2 = hex_to_hue(color2)
            
            # Calculate circular distance (accounting for wrap-around)
            hue_diff = abs(hue1 - hue2)
            if hue_diff > 180:
                hue_diff = 360 - hue_diff
            
            # If hues are very close (< 15°), consider them same family
            # This catches colors that are visually similar but in different named families
            # Using 15° for very strict separation
            if hue_diff < 15.0:
                return True
        
        # Whites/blacks/grays: only exact family match
        # Different gray shades are different families
        return False
    
    # If colors not in our palette, check if they're very similar
    # This is a fallback for manually assigned colors
    return color_distance(color1, color2) < 50.0


def get_all_vspcs_within_distance(locations: Dict[str, Tuple[float, float]], 
                                   center_name: str, distance_miles: float) -> List[str]:
    """Get all VSPC names within distance_miles of center_name."""
    if center_name not in locations:
        return []
    
    lat1, lon1 = locations[center_name]
    nearby = []
    for name, (lat2, lon2) in locations.items():
        if name != center_name:
            dist = haversine_distance(lat1, lon1, lat2, lon2)
            if dist < distance_miles:
                nearby.append(name)
    return nearby


def get_vspcs_by_rings(locations: Dict[str, Tuple[float, float]], 
                       center_name: str, 
                       immediate_ring: float = 8.0,
                       middle_ring: float = 15.0) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]], List[Tuple[str, float]]]:
    """
    Get VSPCs organized by concentric rings around center_name.
    
    Returns:
        (immediate_ring_vspcs, middle_ring_vspcs, far_ring_vspcs)
        Each is a list of (name, distance) tuples
    """
    if center_name not in locations:
        return [], [], []
    
    lat1, lon1 = locations[center_name]
    immediate = []
    middle = []
    far = []
    
    for name, (lat2, lon2) in locations.items():
        if name == center_name:
            continue
        
        dist = haversine_distance(lat1, lon1, lat2, lon2)
        
        if dist < immediate_ring:
            immediate.append((name, dist))
        elif dist < middle_ring:
            middle.append((name, dist))
        else:
            far.append((name, dist))
    
    return immediate, middle, far


def check_color_constraint_by_ring(color1: str, color2: str, distance: float,
                                   immediate_ring: float = 8.0,
                                   middle_ring: float = 15.0) -> bool:
    """
    Check if two colors violate constraints based on distance ring.
    
    Returns True if colors violate constraints (i.e., should NOT be used together at this distance).
    
    Ring rules (updated to be further out):
    - Immediate ring (< 8mi): Must be different families (strict)
    - Middle ring (8-15mi): Can be same family if colors are very different (moderate)
    - Far ring (> 15mi): Can be same family (relaxed)
    """
    if distance < immediate_ring:
        # Immediate ring: STRICT - no same family allowed
        return colors_in_same_family(color1, color2)
    elif distance < middle_ring:
        # Middle ring: MODERATE - same family OK if colors are very different
        if colors_in_same_family(color1, color2):
            # Same family - check if colors are at least somewhat different
            color_dist = color_distance(color1, color2)
            # If very similar (< 200), still a problem even in middle ring
            return color_dist < 200.0
        return False
    else:
        # Far ring: RELAXED - same family is OK
        return False


def greedy_graph_coloring_with_distance(graph: Dict[str, Set[str]], palette: List[str], 
                                        vspcs: List[Dict],
                                        locations: Dict[str, Tuple[float, float]],
                                        min_color_distance: float = 400.0,
                                        family_separation_miles: float = 20.0,
                                        preassigned: Dict[str, str] = None,
                                        n_hops: int = 3) -> Dict[str, str]:
    """
    Use greedy graph coloring with STRICT color family separation.
    SIMPLIFIED: Adjacent VSPCs (within distance threshold) MUST use different color families.
    No complex ring system - just check direct adjacency.
    
    Args:
        graph: Adjacency graph of VSPCs (directly adjacent pairs)
        palette: Available colors
        vspcs: List of VSPC features
        locations: Dict mapping VSPC name to (lat, lon)
        min_color_distance: Minimum color distance for adjacent VSPCs (not used in simplified version)
        family_separation_miles: Not used - adjacency is determined by graph
        preassigned: Dictionary of VSPC names to colors that are already assigned
        n_hops: Not used in simplified version
    """
    colors = preassigned.copy() if preassigned else {}
    used_colors = set(colors.values())
    
    # Get nodes that still need colors
    all_nodes = set(graph.keys())
    uncolored_nodes = all_nodes - set(colors.keys())
    
    # Sort uncolored nodes by degree (number of neighbors) - color high-degree nodes first
    nodes_by_degree = sorted(uncolored_nodes, key=lambda n: len(graph[n]), reverse=True)
    
    for node in nodes_by_degree:
        # Get directly adjacent neighbors (from graph)
        adjacent_neighbors = graph.get(node, set())
        
        # Get colors used by adjacent neighbors
        neighbor_colors = [colors.get(neighbor) for neighbor in adjacent_neighbors if neighbor in colors and colors.get(neighbor)]
        
        # Get color families used by adjacent neighbors
        neighbor_families = set()
        for neighbor in adjacent_neighbors:
            if neighbor in colors:
                neighbor_color = colors[neighbor]
                neighbor_family = COLOR_TO_FAMILY.get(neighbor_color)
                if neighbor_family:
                    neighbor_families.add(neighbor_family)
        
        # Find the best color that:
        # 1. Is not in the same family as any adjacent neighbor
        # 2. Maximizes distance from neighbor colors
        best_color = None
        max_min_distance = -1
        
        for color in palette:
            # Skip if already used (prefer unique colors)
            if color in used_colors:
                continue
            
            # Get this color's family
            color_family = COLOR_TO_FAMILY.get(color)
            
            # STRICT: Cannot use same family OR same color as any adjacent neighbor
            # Check both exact family match and hue-based similarity
            invalid = False
            for neighbor in adjacent_neighbors:
                if neighbor in colors:
                    neighbor_color = colors[neighbor]
                    # Cannot use exact same color
                    if color == neighbor_color:
                        invalid = True
                        break
                    # Cannot use same family
                    if colors_in_same_family(color, neighbor_color):
                        invalid = True
                        break
            
            if invalid:
                continue
            
            # Calculate minimum distance to any neighbor color (for tie-breaking)
            if neighbor_colors:
                min_dist = min(color_distance(color, nc) for nc in neighbor_colors if nc)
                if min_dist > max_min_distance:
                    max_min_distance = min_dist
                    best_color = color
            else:
                # No adjacent neighbors colored yet - use this color
                best_color = color
                break
        
        if best_color:
            colors[node] = best_color
            used_colors.add(best_color)
        else:
            # Fallback: find any color not in same family as neighbors
            for color in palette:
                if color in used_colors:
                    continue
                
                color_family = COLOR_TO_FAMILY.get(color)
                if color_family and color_family in neighbor_families:
                    continue
                
                colors[node] = color
                used_colors.add(color)
                break
            else:
                # Last resort: use first available color (shouldn't happen with 40 colors)
                for color in palette:
                    if color not in used_colors:
                        colors[node] = color
                        used_colors.add(color)
                        break
    
    return colors


def refine_colors_to_separate_similar(vspcs: List[Dict], colors: Dict[str, str], 
                                     palette: List[str], graph: Dict[str, Set[str]],
                                     locations: Dict[str, Tuple[float, float]],
                                     family_separation_miles: float = 25.0,
                                     similar_color_threshold: float = 400.0,
                                     max_iterations: int = 10,
                                     protected_colors: Set[str] = None) -> Dict[str, str]:
    """
    SIMPLIFIED: Refine color assignments to ensure adjacent VSPCs use different color families.
    Only checks directly adjacent pairs (from graph), not all pairs.
    
    Args:
        protected_colors: Set of VSPC names whose colors should not be changed
    """
    if protected_colors is None:
        protected_colors = set()
    
    colors_refined = colors.copy()
    used_colors = set(colors_refined.values())
    
    for iteration in range(max_iterations):
        # Find problematic pairs: adjacent VSPCs using same color family
        # Use same logic as verification step
        problematic_pairs = []
        seen_pairs = set()  # Avoid duplicate pairs (A-B and B-A)
        
        for name1 in colors_refined:
            if name1 in protected_colors:
                continue
            
            color1 = colors_refined[name1]
            family1 = COLOR_TO_FAMILY.get(color1)
            
            if not family1:
                continue
            
            # Check all adjacent neighbors
            adjacent_neighbors = graph.get(name1, set())
            for name2 in adjacent_neighbors:
                if name2 in protected_colors or name2 not in colors_refined:
                    continue
                
                # Avoid checking same pair twice
                pair_key = tuple(sorted([name1, name2]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                
                color2 = colors_refined[name2]
                family2 = COLOR_TO_FAMILY.get(color2)
                
                # Problem: adjacent VSPCs using same color OR same color family
                # Check for exact same color first, then same family
                if color1 == color2 or colors_in_same_family(color1, color2):
                    # Calculate distance for reporting
                    if name1 in locations and name2 in locations:
                        lat1, lon1 = locations[name1]
                        lat2, lon2 = locations[name2]
                        geo_dist = haversine_distance(lat1, lon1, lat2, lon2)
                        color_dist = color_distance(color1, color2)
                        problematic_pairs.append((name1, name2, color1, color2, family1, geo_dist, color_dist))
        
        if not problematic_pairs:
            if iteration == 0:
                print(f"  ✅ No problematic pairs found - all adjacent VSPCs use different color families!")
            break
        
        # Sort by distance (closest conflicts first - most important to fix)
        problematic_pairs.sort(key=lambda x: x[5])  # Sort by geo_dist
        
        if iteration == 0:
            print(f"  Found {len(problematic_pairs)} adjacent VSPC pairs using same color family")
        
        fixed_this_iteration = 0
        changed_this_iteration = set()
        
        for name1, name2, color1, color2, family, geo_dist, color_dist in problematic_pairs:
            # Skip if already changed
            if name1 in changed_this_iteration:
                continue
            
            # Get adjacent neighbors of name1
            adjacent_neighbors = graph.get(name1, set())
            
            # Try each available color to find best replacement
            best_replacement = None
            best_score = -1
            
            for new_color in palette:
                # Must be different color AND different family from name2 (the conflicting VSPC) - this is the priority
                if new_color == color2:
                    continue
                if colors_in_same_family(new_color, color2):
                    continue
                
                # Cannot use exact same color as any adjacent neighbor
                has_same_color = False
                for neighbor in adjacent_neighbors:
                    if neighbor in colors_refined:
                        neighbor_color = colors_refined[neighbor]
                        if new_color == neighbor_color:
                            has_same_color = True
                            break
                
                if has_same_color:
                    continue
                
                # Count conflicts with other adjacent neighbors (but allow some conflicts if it fixes the main one)
                conflict_count = 0
                for neighbor in adjacent_neighbors:
                    if neighbor in colors_refined and neighbor != name2:
                        neighbor_color = colors_refined[neighbor]
                        if colors_in_same_family(new_color, neighbor_color):
                            conflict_count += 1
                
                # Score: prioritize fixing the main conflict (name2), then minimize other conflicts
                score = 1000.0 - conflict_count * 100.0  # Big bonus for fixing main conflict, penalty for creating others
                
                # Extra weight for distance from name2 (the conflicting VSPC)
                score += color_distance(new_color, color2) * 2.0
                
                # Also maximize distance from other neighbors
                for neighbor in adjacent_neighbors:
                    if neighbor in colors_refined:
                        neighbor_color = colors_refined[neighbor]
                        score += color_distance(new_color, neighbor_color) * 0.5
                
                # Bonus if this color is not currently used (prefer unique colors)
                if new_color not in used_colors or new_color == color1:
                    score += 50.0
                
                if score > best_score:
                    best_score = score
                    best_replacement = new_color
            
            if best_replacement and best_replacement != color1:
                # Update used colors
                old_color_count = sum(1 for c in colors_refined.values() if c == color1)
                if old_color_count == 1 and color1 in used_colors:
                    used_colors.remove(color1)
                if best_replacement not in used_colors:
                    used_colors.add(best_replacement)
                
                colors_refined[name1] = best_replacement
                changed_this_iteration.add(name1)
                fixed_this_iteration += 1
                if iteration == 0:
                    print(f"    Swapped {name1} from {color1} ({family}) to {best_replacement} ({COLOR_TO_FAMILY.get(best_replacement)}) (adjacent to {name2} at {geo_dist:.1f}mi)")
        
        if fixed_this_iteration > 0:
            if iteration == 0:
                print(f"  ✅ Fixed {fixed_this_iteration} problematic color assignments in iteration {iteration + 1}")
            elif iteration < 3:
                print(f"  ✅ Fixed {fixed_this_iteration} more problematic color assignments in iteration {iteration + 1}")
        else:
            if iteration > 0:
                print(f"  No more improvements possible after {iteration + 1} iterations")
            break
    
    return colors_refined


def assign_colors_to_geojson(input_file: Path, output_file: Path, 
                              distance_threshold: float = 10.0,
                              palette_name: str = "extended") -> Dict[str, str]:
    """
    Assign colors to VSPCs in GeoJSON based on geographic proximity.
    Returns a mapping of VSPC name to color.
    """
    # Load GeoJSON
    with open(input_file, 'r') as f:
        geojson = json.load(f)
    
    vspcs = geojson['features']
    
    # Create location lookup
    locations = {}
    for vspc in vspcs:
        name = vspc['properties']['name']
        coords = vspc['geometry']['coordinates']
        locations[name] = (coords[1], coords[0])  # lat, lon
    
    # Build adjacency graph
    print(f"Building adjacency graph (threshold: {distance_threshold} miles)...")
    graph = build_adjacency_graph(vspcs, distance_threshold)
    
    # Count edges
    total_edges = sum(len(neighbors) for neighbors in graph.values()) // 2
    print(f"  Found {total_edges} adjacent VSPC pairs")
    
    # Choose palette
    # V12: Default to full palette (HSL + whites/blacks/grays) for maximum color separation
    if palette_name == "set1":
        palette = [
            "#E41A1C", "#377EB8", "#4DAF4A", "#984EA3", 
            "#FF7F00", "#FFFF33", "#A65628", "#F781BF"
        ]
    elif palette_name == "set3":
        palette = [
            "#8DD3C7", "#FFFFB3", "#BEBADA", "#FB8072",
            "#80B1D3", "#FDB462", "#B3DE69", "#FCCDE5",
            "#D9D9D9", "#BC80BD", "#CCEBC5", "#FFED6F"
        ]
    elif palette_name == "hsl" or palette_name == "extended":
        # V12: Use full palette (HSL + whites/blacks/grays) - default
        palette = FULL_PALETTE
    else:
        # Fallback to full palette
        palette = FULL_PALETTE
    
    print(f"Using {palette_name} palette with {len(palette)} colors")
    
    # Apply manual color overrides first
    print("Applying manual color overrides...")
    color_assignments = {}
    used_colors = set()
    override_count = 0
    
    for vspc_name, override_color in MANUAL_COLOR_OVERRIDES.items():
        # Check if this VSPC exists in our data
        vspc_exists = any(vspc['properties']['name'] == vspc_name for vspc in vspcs)
        if vspc_exists:
            color_assignments[vspc_name] = override_color
            used_colors.add(override_color)
            override_count += 1
            print(f"  ✅ {vspc_name}: {override_color}")
        else:
            print(f"  ⚠️  {vspc_name} not found in data")
    
    if override_count > 0:
        print(f"  Applied {override_count} manual color overrides")
    
    # Check if all VSPCs have colors assigned (all hardcoded)
    all_vspc_names = {vspc['properties']['name'] for vspc in vspcs}
    unassigned = all_vspc_names - set(color_assignments.keys())
    all_hardcoded = len(unassigned) == 0
    
    if unassigned:
        # Some VSPCs still need colors - assign them
        print(f"Assigning colors with simplified constraint:")
        print(f"  - Adjacent VSPCs (within {distance_threshold}mi) MUST use different color families")
        print(f"  - Using {len(palette)} colors ({len(HSL_PALETTE)} HSL + {len(WHITE_GRAY_PALETTE)} whites/blacks/grays)")
        print(f"  - {len(unassigned)} VSPCs still need color assignment")
        
        # Create a modified palette that excludes manually assigned colors
        available_palette = [c for c in palette if c not in used_colors]
        
        # Assign colors for remaining VSPCs with strict family separation
        remaining_colors = greedy_graph_coloring_with_distance(
            graph, available_palette, vspcs, locations,
            min_color_distance=400.0,  # Not used in simplified version
            family_separation_miles=10.0,  # Not used in simplified version
            preassigned=color_assignments,  # Includes existing + manual overrides
            n_hops=1  # Only check direct adjacency (simplified)
        )
        color_assignments.update(remaining_colors)
    else:
        # All VSPCs already have colors (all hardcoded) - skip recalculation
        print(f"  ✅ All {len(color_assignments)} VSPCs have colors assigned (hardcoded)")
        print(f"  ℹ️  No recalculation needed - using hardcoded colors only")
    
    # Verify no duplicates
    color_counts = {}
    for vspc_name, color in color_assignments.items():
        color_counts[color] = color_counts.get(color, 0) + 1
    
    duplicates = {color: count for color, count in color_counts.items() if count > 1}
    if duplicates:
        print(f"  ⚠️  WARNING: Found duplicate color assignments: {duplicates}")
    else:
        print(f"  ✅ All {len(color_assignments)} VSPCs have unique colors")
    
    # Refine to fix any remaining adjacent VSPCs using same color family
    # Skip refinement if all colors are hardcoded (no recalculation needed)
    if not all_hardcoded:
        # Protect manually assigned colors from being changed
        print(f"Refining colors to ensure adjacent VSPCs use different families...")
        protected_vspcs = set(MANUAL_COLOR_OVERRIDES.keys())  # Protect manual overrides
        color_assignments = refine_colors_to_separate_similar(
            vspcs, color_assignments, palette, graph, locations,
            family_separation_miles=10.0,  # Not used in simplified version
            similar_color_threshold=400.0,  # Not used in simplified version
            max_iterations=10,
            protected_colors=protected_vspcs  # Protect manual overrides from being changed
        )
    else:
        # All colors hardcoded - skip refinement
        print(f"  ℹ️  Skipping refinement - all colors are hardcoded")
    
    # Final verification: check for any remaining adjacent VSPCs using same color family
    print("Verifying final color assignments...")
    conflicts = []
    for name1 in color_assignments:
        color1 = color_assignments[name1]
        family1 = COLOR_TO_FAMILY.get(color1)
        
        if not family1:
            continue
        
        # Check all adjacent neighbors
        adjacent_neighbors = graph.get(name1, set())
        for name2 in adjacent_neighbors:
            if name2 not in color_assignments:
                continue
            
            color2 = color_assignments[name2]
            family2 = COLOR_TO_FAMILY.get(color2)
            
            # Problem: adjacent VSPCs using same color OR same color family
            # Check for exact same color first, then same family
            if color1 == color2 or colors_in_same_family(color1, color2):
                if name1 in locations and name2 in locations:
                    lat1, lon1 = locations[name1]
                    lat2, lon2 = locations[name2]
                    geo_dist = haversine_distance(lat1, lon1, lat2, lon2)
                    conflicts.append((name1, name2, color1, color2, family1, geo_dist))
    
    if conflicts:
        print(f"  ⚠️  WARNING: Found {len(conflicts)} remaining adjacent VSPC pairs using same color family:")
        for name1, name2, c1, c2, family, dist in conflicts[:5]:
            print(f"    {name1} ({c1}, {family}) and {name2} ({c2}, {family}) are {dist:.1f} miles apart")
    else:
        print(f"  ✅ No adjacent VSPCs use the same color family!")
    
    # Add colors to GeoJSON properties
    for feature in vspcs:
        vspc_name = feature['properties']['name']
        color = color_assignments.get(vspc_name, palette[0])
        feature['properties']['color'] = color
        feature['properties']['color_hex'] = color
    
    # Save updated GeoJSON
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"  ✅ Updated {len(vspcs)} VSPCs with colors")
    print(f"  ✅ Saved to {output_file.name}")
    
    return color_assignments


def create_color_mapping_file(color_assignments: Dict[str, str], output_file: Path):
    """
    Create a JSON file mapping VSPC names to colors for easy reference.
    """
    with open(output_file, 'w') as f:
        json.dump(color_assignments, f, indent=2, sort_keys=True)
    
    print(f"  ✅ Created color mapping file: {output_file.name}")


def main():
    """Main function."""
    gis_dir = Path(__file__).parent
    input_file = gis_dir / "vspc_locations.geojson"
    output_file = gis_dir / "vspc_locations_colored.geojson"
    mapping_file = gis_dir / "vspc_color_mapping.json"
    
    print("="*60)
    print("AUTOMATIC VSPC COLOR ASSIGNMENT")
    print("="*60)
    print()
    
    if not input_file.exists():
        print(f"❌ Error: {input_file.name} not found!")
        return
    
    # Assign colors (adjust distance_threshold as needed)
    # 10 miles = VSPCs within 10 miles get different colors
    color_assignments = assign_colors_to_geojson(
        input_file=input_file,
        output_file=output_file,
        distance_threshold=10.0,  # Adjust this based on your VSPC distribution
        palette_name="hsl"  # V12: Use HSL-based palette (Options: "set1", "set3", "hsl", "extended")
    )
    
    # Create color mapping file
    create_color_mapping_file(color_assignments, mapping_file)
    
    # Automatically assign precinct colors based on VSPC colors
    print()
    print("="*60)
    print("UPDATING PRECINCT COLORS")
    print("="*60)
    print()
    precinct_script = gis_dir / "assign_precinct_colors.py"
    if precinct_script.exists():
        print("Running precinct color assignment...")
        try:
            result = subprocess.run(
                [sys.executable, str(precinct_script)],
                cwd=str(gis_dir),
                capture_output=False,
                check=True
            )
            print("  ✅ Precinct colors updated successfully")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Warning: Precinct color assignment failed (exit code {e.returncode})")
            print("     You can run assign_precinct_colors.py manually to update precinct colors.")
    else:
        print(f"  ℹ️  {precinct_script.name} not found - skipping precinct color assignment")
        print("     Run assign_precinct_colors.py manually to assign colors to precincts.")
    
    print()
    print("="*60)
    print("USAGE IN QGIS:")
    print("="*60)
    print()
    print("Option 1: Use the colored GeoJSON file")
    print(f"  1. Load {output_file.name} in QGIS")
    print("  2. In Symbology, use 'Categorized' by 'name'")
    print("  3. For each category, set the color to match the 'color' property")
    print()
    print("Option 2: Manual color assignment")
    print(f"  1. Load {input_file.name} in QGIS")
    print(f"  2. Reference {mapping_file.name} for color assignments")
    print("  3. Manually set each VSPC's color in Symbology")
    print()
    print("Precinct colors:")
    print("  - Precinct colors are automatically assigned based on their assigned VSPC")
    print("  - Load precinct_locations_colored.geojson to see colored precincts")
    print("  - Run assign_precinct_colors.py manually if you need to update precinct colors")
    print()
    print("To adjust adjacency threshold, edit distance_threshold in the script.")
    print("To use a different palette, change palette_name (set1, set3, or extended).")


if __name__ == '__main__':
    main()
