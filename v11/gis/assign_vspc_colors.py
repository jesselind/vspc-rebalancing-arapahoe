#!/usr/bin/env python3
"""
Automatically assign colors to VSPCs based on geographic proximity using graph coloring.
Ensures that geographically adjacent VSPCs get different colors.

This script:
1. Reads VSPC locations from GeoJSON
2. Calculates which VSPCs are adjacent (within distance threshold)
3. Uses graph coloring to assign colors ensuring adjacent VSPCs are different
4. Adds color properties to the GeoJSON
5. Creates a color mapping file for use in QGIS
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Set, Tuple

# High-contrast palette with maximum visual distinction
# Colors chosen to maximize perceptual distance between adjacent colors
HIGH_CONTRAST_PALETTE = [
    "#E41A1C",  # red
    "#377EB8",  # blue
    "#4DAF4A",  # green
    "#984EA3",  # purple
    "#FF7F00",  # orange
    "#FFFF33",  # yellow
    "#A65628",  # brown
    "#F781BF",  # pink
    "#1F78B4",  # dark blue
    "#33A02C",  # dark green
    "#E31A1C",  # bright red
    "#FB9A99",  # light red
    "#6A3D9A",  # dark purple
    "#B15928",  # dark orange
    "#000000",  # black
    "#FFFFFF",  # white (will use light gray instead)
    "#FFD700",  # gold
    "#00CED1",  # dark turquoise
    "#FF1493",  # deep pink
    "#32CD32",  # lime green
    "#8B0000",  # dark red
    "#0000CD",  # medium blue
    "#FF4500",  # orange red
    "#228B22",  # forest green
    "#8B008B",  # dark magenta
    "#FF6347",  # tomato
    "#00FA9A",  # medium spring green
    "#1E90FF",  # dodger blue
    "#DC143C",  # crimson
    "#00FF00",  # lime
    "#FF00FF",  # magenta
    "#00FFFF",  # cyan
]

# Replace white with light gray for visibility
HIGH_CONTRAST_PALETTE[15] = "#CCCCCC"  # light gray instead of white

# Define color families - colors in the same family should NEVER be geographically close
# Made families smaller and more distinct to allow better geographic separation
COLOR_FAMILIES = {
    "red_bright": ["#E41A1C", "#E31A1C", "#DC143C"],
    "red_dark": ["#8B0000"],
    "red_light": ["#FB9A99"],
    "red_orange": ["#FF6347", "#FF4500"],
    "blue_bright": ["#377EB8", "#1F78B4", "#1E90FF"],
    "blue_dark": ["#0000CD"],
    "blue_cyan": ["#00CED1", "#00FFFF"],
    "green_bright": ["#4DAF4A", "#32CD32", "#00FF00"],
    "green_dark": ["#33A02C", "#228B22"],
    "green_light": ["#00FA9A"],
    "purple_dark": ["#984EA3", "#6A3D9A", "#8B008B"],
    "purple_bright": ["#FF00FF"],
    "orange": ["#FF7F00", "#B15928"],
    "yellow_gold": ["#FFFF33", "#FFD700"],
    "brown": ["#A65628"],
    "pink": ["#F781BF", "#FF1493"],
    "black": ["#000000"],
    "gray": ["#CCCCCC"],
}

# Reverse mapping: color -> family
COLOR_TO_FAMILY = {}
for family, colors in COLOR_FAMILIES.items():
    for color in colors:
        COLOR_TO_FAMILY[color] = family

# Manual color overrides - specific colors for specific VSPCs
MANUAL_COLOR_OVERRIDES = {}


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
    """Check if two colors are in the same color family - STRICT: only exact family matches."""
    family1 = COLOR_TO_FAMILY.get(color1)
    family2 = COLOR_TO_FAMILY.get(color2)
    if family1 and family2:
        # Only exact family match counts as "same family"
        if family1 == family2:
            return True
        # Also check if they're in the same base family (e.g., both red variants) AND very similar
        base_family1 = family1.split('_')[0] if '_' in family1 else family1
        base_family2 = family2.split('_')[0] if '_' in family2 else family2
        if base_family1 == base_family2:
            # Same base family - check if colors are very similar (within 100 distance)
            if color_distance(color1, color2) < 100.0:
                return True
    # If not in defined families, only consider very similar (within 100)
    return color_distance(color1, color2) < 100.0


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


def greedy_graph_coloring_with_distance(graph: Dict[str, Set[str]], palette: List[str], 
                                        vspcs: List[Dict],
                                        locations: Dict[str, Tuple[float, float]],
                                        min_color_distance: float = 400.0,
                                        family_separation_miles: float = 20.0,
                                        preassigned: Dict[str, str] = None,
                                        n_hops: int = 3) -> Dict[str, str]:
    """
    Use greedy graph coloring with strict color family separation.
    Ensures colors in the same family are never geographically close.
    
    Args:
        graph: Adjacency graph of VSPCs
        palette: Available colors
        vspcs: List of VSPC features
        locations: Dict mapping VSPC name to (lat, lon)
        min_color_distance: Minimum color distance for adjacent VSPCs
        family_separation_miles: Minimum miles between colors in same family
        preassigned: Dictionary of VSPC names to colors that are already assigned
        n_hops: Number of hops to check for neighbors
    """
    colors = preassigned.copy() if preassigned else {}
    used_colors = set(colors.values())
    
    # Get nodes that still need colors
    all_nodes = set(graph.keys())
    uncolored_nodes = all_nodes - set(colors.keys())
    
    # Sort uncolored nodes by degree (number of neighbors) - color high-degree nodes first
    nodes_by_degree = sorted(uncolored_nodes, key=lambda n: len(graph[n]), reverse=True)
    
    for node in nodes_by_degree:
        if node not in locations:
            continue
        
        lat1, lon1 = locations[node]
        
        # Get all neighbors to check (N-hop neighbors)
        neighbors_to_check = get_n_hop_neighbors(graph, node, n_hops)
        
        # Get colors used by all neighbors to check
        neighbor_colors = [colors.get(neighbor) for neighbor in neighbors_to_check if neighbor in colors and colors.get(neighbor)]
        
        # Find the best color (farthest from all neighbor colors and not in same family as nearby colors)
        best_color = None
        max_min_distance = -1
        
        for color in palette:
            # Never reuse a color that's already assigned
            if color in used_colors:
                continue
            
            # Check if this color is in the same family as any nearby VSPC
            invalid = False
            for neighbor in neighbors_to_check:
                if neighbor in colors:
                    neighbor_color = colors[neighbor]
                    if colors_in_same_family(color, neighbor_color):
                        # Check geographic distance
                        if neighbor in locations:
                            lat2, lon2 = locations[neighbor]
                            geo_dist = haversine_distance(lat1, lon1, lat2, lon2)
                            if geo_dist < family_separation_miles:
                                invalid = True
                                break
            
            if invalid:
                continue
            
            # Check ALL already-assigned VSPCs within family_separation_miles (not just neighbors)
            nearby_all = get_all_vspcs_within_distance(locations, node, family_separation_miles)
            for other_node in nearby_all:
                if other_node in colors:
                    other_color = colors[other_node]
                    if colors_in_same_family(color, other_color):
                        invalid = True
                        break
            
            if invalid:
                continue
            
            # Calculate minimum distance to any neighbor color
            if neighbor_colors:
                min_dist = min(color_distance(color, nc) for nc in neighbor_colors if nc)
                if min_dist < min_color_distance:
                    continue  # Too similar to a neighbor
                if min_dist > max_min_distance:
                    max_min_distance = min_dist
                    best_color = color
            else:
                # No neighbors colored yet, but still check all assigned colors for family conflicts
                has_family_conflict = False
                nearby_all = get_all_vspcs_within_distance(locations, node, family_separation_miles)
                for other_node in nearby_all:
                    if other_node in colors:
                        other_color = colors[other_node]
                        if colors_in_same_family(color, other_color):
                            has_family_conflict = True
                            break
                
                if not has_family_conflict:
                    best_color = color
                    break
        
        if best_color:
            colors[node] = best_color
            used_colors.add(best_color)
        else:
            # Fallback: find color with maximum distance from neighbors and no family conflicts
            best_fallback = None
            best_fallback_score = -1
            
            for color in palette:
                if color in used_colors:
                    continue
                
                # Check family conflicts with all nearby VSPCs
                has_conflict = False
                nearby_all = get_all_vspcs_within_distance(locations, node, family_separation_miles)
                for other_node in nearby_all:
                    if other_node in colors:
                        other_color = colors[other_node]
                        if colors_in_same_family(color, other_color):
                            has_conflict = True
                            break
                
                if has_conflict:
                    continue
                
                # Score based on distance from neighbors
                if neighbor_colors:
                    min_dist = min(color_distance(color, nc) for nc in neighbor_colors if nc)
                    if min_dist > best_fallback_score:
                        best_fallback_score = min_dist
                        best_fallback = color
                else:
                    best_fallback = color
                    break
            
            if best_fallback:
                colors[node] = best_fallback
                used_colors.add(best_fallback)
            else:
                # Last resort: use first available color
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
    Aggressively refine color assignments to ensure color families are geographically separated.
    Checks ALL pairs, not just adjacent ones.
    
    Args:
        protected_colors: Set of VSPC names whose colors should not be changed
    """
    if protected_colors is None:
        protected_colors = set()
    
    colors_refined = colors.copy()
    # Track used colors but allow reuse if needed
    used_colors = set(colors_refined.values())
    
    for iteration in range(max_iterations):
        # Find ALL problematic pairs: colors in same family that are geographically close
        problematic_pairs = []
        
        for i, (name1, color1) in enumerate(colors_refined.items()):
            if name1 not in locations or name1 in protected_colors:
                continue
            lat1, lon1 = locations[name1]
            
            for name2, color2 in list(colors_refined.items())[i+1:]:
                if name2 not in locations:
                    continue
                lat2, lon2 = locations[name2]
                
                # Check if colors are in the same family OR very similar
                if colors_in_same_family(color1, color2) or color_distance(color1, color2) < similar_color_threshold:
                    geo_dist = haversine_distance(lat1, lon1, lat2, lon2)
                    if geo_dist < family_separation_miles:
                        # This is a problem - same family colors too close
                        color_dist = color_distance(color1, color2)
                        badness = (family_separation_miles - geo_dist) + (similar_color_threshold - color_dist)
                        problematic_pairs.append((name1, name2, color1, color2, geo_dist, color_dist, badness))
        
        if not problematic_pairs:
            if iteration == 0:
                print(f"  ✅ No problematic pairs found - all color families are well separated!")
            break
        
        # Sort by badness (worst first)
        problematic_pairs.sort(key=lambda x: x[6], reverse=True)
        
        if iteration == 0:
            print(f"  Found {len(problematic_pairs)} pairs with same-family or similar colors within {family_separation_miles} miles")
        
        fixed_this_iteration = 0
        changed_this_iteration = set()
        
        for name1, name2, color1, color2, geo_dist, color_dist, badness in problematic_pairs:
            # Skip if already changed
            if name1 in changed_this_iteration:
                continue
            
            lat1, lon1 = locations[name1]
            
            # Find all VSPCs within family_separation_miles
            nearby_vspcs = []
            for name, (lat, lon) in locations.items():
                if name != name1:
                    dist = haversine_distance(lat1, lon1, lat, lon)
                    if dist < family_separation_miles:
                        nearby_vspcs.append((name, colors_refined.get(name), dist))
            
            # Try each available color to find best replacement
            best_replacement = None
            best_score = -1
            valid_colors_found = 0
            
            for new_color in palette:
                # Allow reusing colors if they don't create conflicts
                # (We have 32 VSPCs and 32 colors, so some reuse may be necessary)
                
                # Check if this color is in same family as any nearby VSPC
                invalid = False
                for nearby_name, nearby_color, nearby_geo_dist in nearby_vspcs:
                    if nearby_color and colors_in_same_family(new_color, nearby_color):
                        invalid = True
                        break
                
                if invalid:
                    continue
                
                # Also check all other assigned colors for family conflicts
                for other_name, other_color in colors_refined.items():
                    if other_name == name1:
                        continue
                    if colors_in_same_family(new_color, other_color):
                        if other_name in locations:
                            lat2, lon2 = locations[other_name]
                            geo_dist_check = haversine_distance(lat1, lon1, lat2, lon2)
                            if geo_dist_check < family_separation_miles:
                                invalid = True
                                break
                
                if invalid:
                    continue
                
                # Score: maximize distance from nearby colors, especially name2
                score = 0
                for nearby_name, nearby_color, nearby_geo_dist in nearby_vspcs:
                    if nearby_color:
                        dist = color_distance(new_color, nearby_color)
                        # Weight by proximity - closer neighbors matter more
                        weight = 1.0 / (nearby_geo_dist + 0.1)
                        score += dist * weight
                
                # Extra weight for distance from name2 (the conflicting VSPC)
                dist_to_name2 = color_distance(new_color, color2)
                score += dist_to_name2 * 3.0
                
                # Bonus if this color is not currently used (prefer unique colors)
                if new_color not in used_colors or new_color == color1:
                    score += 100.0
                
                if score > best_score:
                    best_score = score
                    best_replacement = new_color
                    valid_colors_found += 1
            
            # If no valid replacement found for name1, try name2 instead
            if not best_replacement or best_replacement == color1:
                # Try swapping name2 instead
                if name2 not in changed_this_iteration and name2 not in protected_colors:
                    lat2, lon2 = locations[name2]
                    nearby_vspcs2 = []
                    for name, (lat, lon) in locations.items():
                        if name != name2:
                            dist = haversine_distance(lat2, lon2, lat, lon)
                            if dist < family_separation_miles:
                                nearby_vspcs2.append((name, colors_refined.get(name), dist))
                    
                    best_replacement2 = None
                    best_score2 = -1
                    
                    for new_color in palette:
                        if new_color == color2:
                            continue
                        
                        invalid = False
                        for nearby_name, nearby_color, nearby_geo_dist in nearby_vspcs2:
                            if nearby_color and colors_in_same_family(new_color, nearby_color):
                                invalid = True
                                break
                        
                        if invalid:
                            continue
                        
                        for other_name, other_color in colors_refined.items():
                            if other_name == name2:
                                continue
                            if colors_in_same_family(new_color, other_color):
                                if other_name in locations:
                                    lat_o, lon_o = locations[other_name]
                                    geo_dist_check = haversine_distance(lat2, lon2, lat_o, lon_o)
                                    if geo_dist_check < family_separation_miles:
                                        invalid = True
                                        break
                        
                        if invalid:
                            continue
                        
                        score = 0
                        for nearby_name, nearby_color, nearby_geo_dist in nearby_vspcs2:
                            if nearby_color:
                                dist = color_distance(new_color, nearby_color)
                                weight = 1.0 / (nearby_geo_dist + 0.1)
                                score += dist * weight
                        
                        dist_to_name1 = color_distance(new_color, color1)
                        score += dist_to_name1 * 3.0
                        
                        if new_color not in used_colors or new_color == color2:
                            score += 100.0
                        
                        if score > best_score2:
                            best_score2 = score
                            best_replacement2 = new_color
                    
                    if best_replacement2 and best_replacement2 != color2:
                        old_color_count = sum(1 for c in colors_refined.values() if c == color2)
                        if old_color_count == 1 and color2 in used_colors:
                            used_colors.remove(color2)
                        if best_replacement2 not in used_colors:
                            used_colors.add(best_replacement2)
                        
                        colors_refined[name2] = best_replacement2
                        changed_this_iteration.add(name2)
                        fixed_this_iteration += 1
                        if iteration == 0:
                            print(f"    Swapped {name2} from {color2} to {best_replacement2} (was {geo_dist:.1f}mi from {name1} with similar color)")
                        continue
            
            if best_replacement and best_replacement != color1:
                # Update used colors (track but allow reuse)
                old_color_count = sum(1 for c in colors_refined.values() if c == color1)
                if old_color_count == 1 and color1 in used_colors:
                    used_colors.remove(color1)
                if best_replacement not in used_colors:
                    used_colors.add(best_replacement)
                
                colors_refined[name1] = best_replacement
                changed_this_iteration.add(name1)
                fixed_this_iteration += 1
                if iteration == 0:
                    print(f"    Swapped {name1} from {color1} to {best_replacement} (was {geo_dist:.1f}mi from {name2} with similar color, found {valid_colors_found} valid alternatives)")
            elif iteration == 0 and fixed_this_iteration < 5:
                # Debug: show why we couldn't fix this one
                print(f"    ⚠️  Could not find valid replacement for {name1} (conflict with {name2} at {geo_dist:.1f}mi)")
        
        if fixed_this_iteration > 0:
            if iteration == 0:
                print(f"  ✅ Fixed {fixed_this_iteration} problematic color assignments in iteration {iteration + 1}")
            elif iteration < 3:  # Print first few iterations
                print(f"  ✅ Fixed {fixed_this_iteration} more problematic color assignments in iteration {iteration + 1}")
        else:
            if iteration > 0:
                print(f"  No more improvements possible after {iteration + 1} iterations")
            break  # No improvements this iteration, stop
    
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
    else:
        palette = HIGH_CONTRAST_PALETTE
    
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
    
    # Assign colors using strict family separation
    # Family separation: colors in same family must be at least 15 miles apart
    # This ensures color families are well separated while being achievable with 32 VSPCs
    family_separation_miles = 15.0
    print(f"Assigning colors with strict family separation ({family_separation_miles} miles minimum between same-family colors)...")
    
    # Create a modified palette that excludes manually assigned colors
    available_palette = [c for c in palette if c not in used_colors]
    
    # Assign colors for remaining VSPCs with strict family separation
    remaining_colors = greedy_graph_coloring_with_distance(
        graph, available_palette, vspcs, locations,
        min_color_distance=400.0,  # Very strict threshold
        family_separation_miles=family_separation_miles,
        preassigned=color_assignments,
        n_hops=3  # Check 3-hop neighbors
    )
    color_assignments.update(remaining_colors)
    
    # Verify no duplicates
    color_counts = {}
    for vspc_name, color in color_assignments.items():
        color_counts[color] = color_counts.get(color, 0) + 1
    
    duplicates = {color: count for color, count in color_counts.items() if count > 1}
    if duplicates:
        print(f"  ⚠️  WARNING: Found duplicate color assignments: {duplicates}")
    else:
        print(f"  ✅ All {len(color_assignments)} VSPCs have unique colors")
    
    # Aggressively refine to separate color families geographically
    print(f"Refining colors to ensure color families are geographically separated (checking all pairs within {family_separation_miles} miles)...")
    color_assignments = refine_colors_to_separate_similar(
        vspcs, color_assignments, palette, graph, locations,
        family_separation_miles=family_separation_miles,
        similar_color_threshold=400.0,  # Very strict: same family or very similar
        max_iterations=10,  # More iterations to catch all problems
        protected_colors=set()  # No protection - algorithm can refine all colors
    )
    
    # Final verification: check for any remaining same-family conflicts
    print("Verifying final color assignments...")
    conflicts = []
    for i, (name1, color1) in enumerate(color_assignments.items()):
        if name1 not in locations:
            continue
        lat1, lon1 = locations[name1]
        for name2, color2 in list(color_assignments.items())[i+1:]:
            if name2 not in locations:
                continue
            if colors_in_same_family(color1, color2):
                lat2, lon2 = locations[name2]
                geo_dist = haversine_distance(lat1, lon1, lat2, lon2)
                if geo_dist < family_separation_miles:
                    conflicts.append((name1, name2, color1, color2, geo_dist))
    
    if conflicts:
        print(f"  ⚠️  WARNING: Found {len(conflicts)} remaining same-family conflicts:")
        for name1, name2, c1, c2, dist in conflicts[:5]:
            print(f"    {name1} ({c1}) and {name2} ({c2}) are {dist:.1f} miles apart")
    else:
        print(f"  ✅ No same-family color conflicts within {family_separation_miles} miles!")
    
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
        palette_name="extended"  # Options: "set1", "set3", "extended"
    )
    
    # Create color mapping file
    create_color_mapping_file(color_assignments, mapping_file)
    
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
    print("To adjust adjacency threshold, edit distance_threshold in the script.")
    print("To use a different palette, change palette_name (set1, set3, or extended).")


if __name__ == '__main__':
    main()
