# QGIS Setup Guide - Step by Step Instructions

This guide will walk you through loading and styling your VSPC and precinct data in QGIS so you can visualize the distributions on a map.

## Prerequisites

- QGIS installed on your computer (download from https://qgis.org if needed)
- The GeoJSON files in this `gis/` directory

## Quick Reference: Which Files to Use

- **`vspc_locations_colored.geojson`** - VSPC locations with assigned colors (recommended)
- **`vspc_locations.geojson`** - Basic VSPC locations (if you need uncolored version)
- **`precinct_locations_colored.geojson`** - Precinct locations with colors matching assigned VSPCs (recommended)
- **`precinct_locations.geojson`** - Basic precinct locations (if you need uncolored version)

**Note**: Historical files like `precinct_locations_colored.geojson` are preserved in `Archived Resources/v11/gis/` if needed for reference.

## Understanding QGIS Projects

**One Project = Everything You Need**

A QGIS project (saved as a `.qgz` file) contains:
- **All your layers** (VSPC locations, precinct locations, base maps, etc.)
- **All your styling** (colors, sizes, labels for each layer)
- **Multiple print layouts** (different map views - VSPC only, precincts only, both, etc.)
- **All your settings** (zoom levels, layer visibility, etc.)

**You only need ONE project** - you can create multiple print layouts within that same project for different views.

**Think of it like this:**
- **Project** = Your entire workspace (like a PowerPoint file)
- **Layers** = Your data (like slides with content)
- **Print Layouts** = Different map views/export formats (like different slide designs)

**Save your project early and often!** (Project menu → Save As)

---

## Step 1: Open QGIS

1. Launch QGIS Desktop
2. You'll see a blank map canvas

---

## Step 2: Add a Base Map (Optional but Recommended)

Having a base map helps you see where things are located geographically.

1. In the **Browser** panel (left side), expand **XYZ Tiles**
2. Right-click on **XYZ Tiles** and select **New Connection**
3. Enter:
   - **Name**: OpenStreetMap
   - **URL**: `https://tile.openstreetmap.org/{z}/{x}/{y}.png`
4. Click **OK**
5. Double-click **OpenStreetMap** to add it to your map

**Note**: You'll see a very zoomed-out view of the whole world - this is normal! Once you add your VSPC and precinct layers in the next steps, you can zoom to them to see your area (Arapahoe County, Colorado).

---

## Step 2b: Add Arapahoe County Border (Optional)

Adding the county border helps define the geographic extent of your data.

1. **Add the shapefile**:
   - **Layer** menu → **Add Layer** → **Add Vector Layer**
   - Navigate to `gis/County_Boundary_SHAPE_WGS/`
   - Select `County_Boundary_WGS.shp`
   - Click **Add**

2. **Handle Coordinate System Transformation** (if prompted):
   - QGIS may show a dialog asking you to select a transformation
   - Select the transformation with the best accuracy (usually "1 meter" accuracy)
   - Click **OK**

3. **Style the boundary**:
   - Right-click the county boundary layer → **Properties** → **Symbology**
   - **Fill color**: Set to transparent
   - **Stroke color**: Set to dark color (black or dark blue)
   - **Stroke width**: Set to `1.0` or `1.5`
   - Click **OK**

4. **Position the layer**: Drag it to the bottom of the Layers panel so it appears behind your points

**Tip**: Right-click the layer → **Zoom to Layer** to see the full county extent.

---

## Step 3: Add VSPC Locations

1. Go to **Layer** menu → **Add Layer** → **Add Vector Layer**
   - OR click the **Add Vector Layer** button (looks like a folder with a green plus)
2. In the dialog:
   - **Source Type**: Select **File**
   - Click the **...** button next to **Vector Dataset(s)**
   - Navigate to this `gis/` directory
   - Select `vspc_locations.geojson`
3. Click **Add**
4. The VSPC points should now appear on your map as small dots

---

## Step 4: Style VSPC Locations

1. In the **Layers** panel (bottom left), right-click on `vspc_locations`
2. Select **Properties** (or double-click the layer)
3. Go to the **Symbology** tab (left sidebar)
4. At the top, change from **Single Symbol** to **Categorized**
5. In the **Column** dropdown, select **name**
6. Click **Classify** button
7. You'll see each VSPC gets a different color
8. Click **OK**

**Optional: Make VSPC points larger and add labels:**

**To change size for ALL VSPCs at once:**
- In the **Symbology** tab, click on the first symbol in the list
- Hold **Shift** and click on the last symbol (this selects all symbols)
- Right-click on the selected symbols and choose **Change Symbol**
- In the **Symbol Selector** dialog, in the symbol tree on the left, expand **Marker** and click **Simple Marker**
- On the right, change **Size** to `5` or `6` (if current is 2, this will make them 2.5-3x larger)
- Click **OK** to close symbol editor
- **Result**: All VSPCs will now use this size

**Alternative method:**
- Look at the top of the Symbology panel for a **Change** button (next to the symbol preview)
- Click it and follow the same steps above

**To add labels to ALL VSPCs at once:**
- Go to **Labels** tab (left sidebar)
- Check **Single labels** (this enables labels for the entire layer)
- **Label with**: Select **name** (this shows the VSPC name for all points)
- **Font**: Increase size to `10` or `12`
- **Placement**: Select **Offset from symbol bounds**
- Click **OK**

**Note**: You only need to do this once - it applies to all VSPCs automatically. You don't need to add labels individually for each VSPC.

---

### Use a High-Contrast Color Ramp

**Option 1: Automated Color Assignment (Recommended)**

Use the automated script to assign colors based on geographic proximity:

1. **Run the color assignment script**:
   ```bash
   cd gis/
   python3 assign_vspc_colors.py
   ```
   This creates `vspc_locations_colored.geojson` with colors assigned using graph coloring to ensure adjacent VSPCs get different colors.

2. **Load the colored GeoJSON in QGIS**:
   - Load `vspc_locations_colored.geojson` instead of `vspc_locations.geojson`
   - Right-click the layer → **Properties** → **Symbology** tab
   
   **Recommended: Categorized with Data-Defined Colors (Best of Both Worlds)**
   - Change to **Categorized** → select **name** → click **Classify** (this creates all the categories)
   - **Select all categories**: Click the first category, then Shift+click the last category (or Ctrl+A / Cmd+A)
   - With all categories selected, click any symbol to open Symbol Settings
   - In Symbol Settings, find the **Color** property → click the **ε (epsilon)** button
   - Select **Field type: string** → choose **color** field
   - Click **OK** to close Symbol Settings, then **OK** again to close Layer Properties
   - This gives you both correct colors from the GeoJSON AND a categorized legend!
   
   **Alternative: Single Symbol (Simpler, No Legend)**
   - Keep it as **Single Symbol** (default)
   - Click the **symbol preview** → **Color** → **ε** button → **Field type: string** → choose **color** field
   - Click **OK** twice
   - Colors will be correct, but no legend with VSPC names

**Option 2: Manual Reordering (If you prefer manual control)**

Colors are assigned based on the **order of categories** in the symbology list (default is alphabetical):

1. In the **Symbology** tab, change to **Categorized** and select **name** column
2. **Before clicking Classify**, manually reorder categories:
   - Categories appear in alphabetical order by default
   - **Drag categories up/down** to reorder them
   - Put geographically adjacent VSPCs far apart in the list
3. Click **Classify** - colors will be assigned based on the new order
4. Apply a ColorBrewer ramp (Set3 or Paired) as described in Option 1

**Tip**: The automated script uses graph coloring to ensure all VSPCs within 10 miles get different colors, which is more reliable than manual reordering.

---

## Step 5: Add Precinct Locations

1. Go to **Layer** menu → **Add Layer** → **Add Vector Layer**
2. Navigate to `gis/` directory
3. Select `precinct_locations_colored.geojson` (recommended - includes colors and VSPC assignment data)
   - Or use `precinct_locations.geojson` if you need the basic version without colors
4. Click **Add**
5. **Note**: The colored file includes VSPC assignment data - you can color-code precincts by their assigned VSPC (see Step 7)

---

## Step 6: Style Precinct Locations by Size (Based on Voter Count)

**Tip - Add Layer Twice for Easy Toggling**: You can add the same layer twice and style them differently, then toggle between views:
1. Add `precinct_locations_colored.geojson` a second time using **Add Vector Layer** (it will appear as "precinct_locations_colored (2)")
2. Style the first layer with size by voters (this section)
3. Style the second layer with color by VSPC (Step 7)
4. Rename them: Right-click each layer → **Rename Layer** → "Precincts by Size" and "Precincts by VSPC"
5. Show/hide layers using the eye icon to instantly switch between views

This will make larger precincts (more voters) appear as larger circles.

1. Right-click `precinct_locations_colored` → **Properties**
2. Go to **Symbology** tab
3. Change from **Single Symbol** to **Graduated**
4. **Column**: Select **voters** (this is the voter count field)
5. **Method**: Select **Size**
6. **Mode**: Select **Equal Interval** or **Natural Breaks**
7. **Classes**: Set to `5` (this creates 5 size categories)
8. Click **Classify**
9. Adjust the size range using the **Size Range** section:
   - You'll see two fields: **Size from** and **to**
   - **Size from**: Change to `3` or `4` (this sets the smallest precinct size)
   - **to**: Change to `12` or `15` (this sets the largest precinct size)
   - The symbols in the classes table will automatically update to show the new size range
   - All precincts will scale proportionally between these min and max sizes
10. Click **OK**

**Add precinct numbers as labels:**
1. Right-click `precinct_locations_colored` → **Properties**
2. Go to **Labels** tab
3. Check **Single labels**
4. **Label with**: Select **precinct** (this shows the precinct number)
5. **Font**: Set size to `8` or `9`
6. **Placement**: Select **Offset from symbol bounds**
7. **Buffer**: Check **Draw text buffer** (helps text stand out)
   - Set **Size** to `1.5`
   - Set **Color** to white
8. Click **OK**

---

## Step 7: Color Precincts by Assigned VSPC

To see which precincts are assigned to which VSPCs:

**Note**: If you followed the tip in Step 6 and added the layer twice, style the second layer (precinct_locations_colored (2)) with this approach, then you can toggle between size and color views.

1. Right-click `precinct_locations_colored` (or the second instance if you added it twice) → **Properties**
2. Go to **Symbology** tab
3. Change to **Categorized**
4. **Column**: Select **assigned_vspc**
5. Click **Classify**
6. QGIS will automatically assign a different color to each VSPC category (all precincts assigned to the same VSPC get the same color)

**To match precinct colors to VSPC colors:**

**If you used the automated color assignment script:**

1. Reference `vspc_color_mapping.json` for the exact color for each VSPC
2. In the precinct layer's **Symbology** tab, for each VSPC category:
   - Click on the category's symbol
   - Change the **Fill color** to match the color from the mapping file for that VSPC
   - You only need to do this once per VSPC category (32 times), not per precinct
3. All precincts in that category will automatically get the same color

**If you used manual color assignment:**

**Option 1: Recreate the same ramp (if you didn't manually adjust VSPC colors)**

1. In the precinct layer's **Symbology** tab, click the **Color ramp** dropdown
2. Click **All Color Ramps...** → **Create New Color Ramp...** → **Catalog: ColorBrewer**
3. Select the **exact same palette** you used for VSPCs (e.g., **Set3**)
4. Set it to the **exact same number of colors** (e.g., 12)
5. Click **OK**, then click **Classify** again
6. Colors should match because both layers use the same ramp with the same category order

**Option 2: Manually match colors (if you adjusted VSPC colors)**

If you manually adjusted any VSPC colors, you'll need to manually match precinct colors:
1. Use your screenshot/notes from Step 4 showing which color each VSPC has
2. In the precinct layer's **Symbology** tab, for each VSPC category:
   - Click on the category's symbol
   - Change the **Fill color** to match the color used for that VSPC
   - You only need to do this once per VSPC category (32 times), not per precinct
3. All precincts in that category will automatically get the same color

**Note**: If you manually adjust a VSPC color later, precincts will NOT automatically update. You'll need to manually change the matching precinct category color to keep them synchronized.

**Optional - Adjust symbol size:**
- Select all symbols (Shift+click first to last)
- Right-click → **Change Symbol**
- Click **Simple Marker**
- Change **Size** to `6` or `8` (uniform size for all)
- Click **OK**

7. Click **OK** to apply

**Result**: All precincts will be automatically colored based on their assigned VSPC. Precincts assigned to the same VSPC will share the same color, making it easy to see the distribution visually.

---

## Step 8: Organize Your Layers

You can reorder and organize layers:

1. In the **Layers** panel, drag layers up/down to reorder
2. **Recommended order** (top to bottom):
   - `precinct_locations_colored` (precincts with assignment data, on top)
   - `vspc_locations` (VSPC points)
   - County boundary (if added)
   - Base map (bottom)

3. **Show/Hide layers**: Click the eye icon next to layer names
4. **Rename layers**: Right-click → **Rename Layer**

---

## Step 9: Highlight Reassigned Precincts

To see which precincts were reassigned from their nearest VSPC:

1. Right-click `precinct_locations_colored` → **Properties**
2. Go to **Symbology** tab
3. Change to **Categorized**
4. **Column**: Select **reassigned**
5. Click **Classify**
6. You'll see two categories: `True` and `False`
7. Click on the `True` symbol:
   - **Simple Marker**
   - Change **Fill color** to bright red or orange
   - Change **Size** to `10` or `12` (make them stand out)
8. Click on the `False` symbol:
   - Change **Fill color** to light gray or blue
   - Change **Size** to `4` or `5`
9. Click **OK**

---

## Step 10: Create Printable Maps

**Save your project first**: **Project** menu → **Save As** → Save as `vspc_precinct_maps.qgz`

### Create a Print Layout

1. **Set up your map view** in the main QGIS window:
   - Show/hide layers as needed (click the eye icon)
   - Right-click on the layer you want to focus on → **Zoom to Layer**

2. **Create a new print layout**:
   - **Project** menu → **New Print Layout**
   - Name it (e.g., "VSPC Locations")
   - Click **OK**

3. **Add the map**:
   - Click **Add Map** button
   - Click and drag on the page to create the map area

4. **Auto-fit the map**:
   - Click on the map in the layout to select it
   - In **Item Properties** panel (right side), find **Extent** section
   - Click **Set to map canvas extent** or choose **Fit to content**

5. **Add title and legend**:
   - Click **Add Label** for title
   - Click **Add Legend** to show what the symbols mean
   - Position them as needed

6. **Set page size** (optional):
   - **Layout** menu → **Page Setup**
   - Choose **Letter**, **Tabloid**, or **A4**
   - **Landscape** orientation often works better for maps

7. **Export**:
   - **Layout** menu → **Export as PDF** (or **Export as Image**)
   - Set resolution to `300` DPI for printing
   - Save with a descriptive name

**Tip**: You can create multiple layouts in the same project for different views (VSPC only, precincts only, both, etc.). Each layout can have different layers, zoom levels, and styling.

---

## Quick Tips

### Zoom and Pan
- **Zoom in**: Mouse wheel up, or **Zoom In** tool
- **Zoom out**: Mouse wheel down, or **Zoom Out** tool
- **Pan**: Click and drag with **Pan Map** tool
- **Zoom to layer**: Right-click layer → **Zoom to Layer**

### Find a Specific Precinct or VSPC
1. Click **Select Features** tool (looks like a cursor with a box)
2. Click on a point on the map
3. The feature will be highlighted
4. Check the **Attributes** panel (bottom) to see details

### Measure Distances
1. Click **Measure Line** tool (ruler icon)
2. Click on map to start, click again to add points, double-click to finish
3. Distance shows in the status bar

### Save Your Project

**IMPORTANT: Save your project to keep all your work!**

- **First time**: **Project** menu → **Save As** → Save as `vspc_precinct_maps.qgz`
- **After changes**: **Project** menu → **Save** (or Ctrl+S / Cmd+S)
- **Reopening**: **Project** menu → **Open** → Select your `.qgz` file

This saves all layers, styling, layouts, and settings. Exported PDF/image files are separate.

---

## Recommended Layer Combinations

**Overview**: `precinct_locations_colored` (colored by assigned_vspc) + `vspc_locations` + county boundary + base map

**Reassigned Precincts**: `precinct_locations_colored` (colored by reassigned) + `vspc_locations` + county boundary + base map

**Size Analysis**: `precinct_locations_colored` (size by voters) + `vspc_locations` + county boundary + base map

---

## Troubleshooting

**Points don't appear:**
- Check if you're zoomed in too far or too far out
- Right-click layer → **Zoom to Layer**
- Check layer visibility (eye icon)

**Labels overlap:**
- In **Labels** tab → **Placement** → Try **Around point** or **Over point**
- Reduce label font size
- Use **Label with** a shorter field (like precinct number instead of name)

**Colors are hard to see:**
- In **Symbology**, click on symbols to change colors
- Use bright, contrasting colors
- Add outlines to symbols (in **Simple Marker** → **Stroke style**)

**Map is too cluttered:**
- Hide layers you don't need (click eye icon)
- Reduce label font sizes
- Use fewer size categories in graduated symbology

**Printed map looks different from screen:**
- Colors may appear different when printed
- Use darker colors for better print contrast
- Test print before printing many copies
- Consider printing in grayscale if color isn't critical

**Text is too small when printed:**
- Increase font sizes in Labels (add 2-4 points)
- Increase symbol sizes
- Use bold fonts for better readability

---

## Next Steps

Once you're comfortable with the basics:
- Create multiple map views for different analyses
- Export maps as images or PDFs
- Use the **Identify Features** tool to click on points and see all their attributes
- Experiment with different color schemes and symbol styles
- Create template layouts you can reuse for different data views
