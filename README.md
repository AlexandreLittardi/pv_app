# Updated build — 28 September 2026

Read **LIRE_MOI_FR.md** for setup, compact navigation, Energy / BESS, economic comparisons and engineering limitations. **CHANGELOG_FR.md** maps the reported issues to their corrections. The original interface guide follows; historical energy screens retain some Italian labels.

**28 September guide update:** Home now contains a compact recent-project history and two guide tabs, **How it works** and **Formulas**. The equations are rendered with Matplotlib mathtext and checked against the implementation. The full revised note is `docs/technical_note_updated.pdf`, accessible through the button on Home. Install the new `matplotlib` dependency using `pip install -r requirements.txt`. Toolbar tabs and the workspace selector are both available; zoom has small −/reset/+ buttons, and the roof image import is under Home > Project. Energy / BESS has its own summary workspace without the roof canvas.

In **Electrical single-line diagram → Site wiring → Detailed wiring editor…**, edit the actual string/MPPT, DC, AC, battery-port and grid wiring schedule for the open project. Save it with the project, preview/export the current vector SVG, or preview/export the wiring CSV. One DEYE MC-L522 connects two clusters to the BAT ports of the first two 125 kVA hybrid inverters; the third remains PV-only. A second battery cabinet requires a manufacturer-approved connection diagram, and missing cable/protection ratings remain explicit open checks.

# PV Layout and Stringing — English interface

Run with Python 3.10 or newer:

```bash
python -m pip install -r requirements.txt
python main.py
```

This package includes the quick-start tutorial, formula reference and engineering calculation guide in the **Home** tab, plus an English interface throughout the supplied modules. The formula function `SUM()` is available alongside the existing `SOMME()` spelling.

The saved JSON schema, equipment field names, zone alignment values and existing formula variable names are retained so earlier project files remain readable. Equipment column headings and alignment controls are translated only for display.

This checkpoint covers the general section, Home, Installation area, and Layout & Blocks. In Layout & Blocks, Shift-click panels to add or remove them from the selection; enter tilt (0–90°) and azimuth (0–<360°, north=0°, east=90°), then apply to the selected panels. With no selection, applying updates the default orientation for all panels and clears individual overrides. Selection outlines are pink. Panel orientations and the consecutive numbering preference are saved in the project JSON. Simulation uses each panel's saved orientation for energy calculations.

The Stringing toolbar is ordered Export, Generate, Configuration, String actions, Active string, Zoom. Configuration stores the minimum and maximum number of panels per string and direction in the JSON project. The left panel shows all strings and their ordered panels as a tree; select a panel to move or remove it, or drag it within its string. Hover over an assigned panel on the drawing to read its full string label. The status bar reports total string length.

MPPT assignment has a left-hand inverter/MPPT/string tree and a toolbar ordered MPPT actions, current string, CSV export, configuration, Zoom. The MPPT actions menu distributes or clears assignments and dims unselected strings. CSV export includes each nonempty string, its block and MPPT assignment, ordered panel numbers, and cable length and routing information when available.

The Paths tab has been removed. Installation area now includes polygon drawing, selection, and deletion, plus scale and distance measurements in its measurement menu. Cabling contains cable paths and gathering point tools. Polygon and cable path drawing can still be finished with a right-click; polygon outlines can be moved after choosing Select / move polygon.

Shadow uses the generic term "obstacle" in the interface. Changes to its solar, obstacle, and module settings recalculate the preview automatically after a short pause; the Calculate buttons have been removed. The simulation heatmap supports mouse drag panning and zoom. After running a multi-day simulation, the Chart button displays its actual results as bars or a line, with a choice of produced or lost energy and the number of hours per plotted point. Production, unshaded potential, and loss totals are highlighted, and the module specifications are saved in the project.

The Spreadsheet tab has a searchable variable explorer in the side panel and a compact File / Charts / Tools / Zoom toolbar. The formula bar shows and edits the selected cell's raw value. The File menu imports and exports semicolon-delimited CSV with formulas intact; Charts draws bars or a line for a numeric column; Zoom scales the grid. Additional variables expose estimated clear-sky irradiance, shade, simulation energy and installed panel area. The structured equipment sheet remains available under the explorer. These irradiance figures are simplified clear-sky estimates rather than measured weather values.

The Electrical single-line diagram has a Custom links menu offering solid, dashed, dotted and dash-dot connections. Electrical data opens a dialog for module STC Pmax, Voc, Vmp, Isc, Imp and optional nominal inverter AC kW. The diagram can show estimated per-string voltages and DC power, MPPT ranges and summed parallel currents, and total assigned DC power per inverter. Specifications, visibility and link styles are saved with the project. Enter nominal inverter AC power in kW separately: a kVA rating cannot be used as kW without a power factor. MPPT voltage ranges highlight different string lengths; they are not a validation of the inverter's allowed operating range.

The Cabling tab now groups cable paths, gathering points, string routing and zoom in its toolbar. The side panel contains a per-string route inventory (including unavailable routes and lengths), a drawn-path list, a DC voltage-drop calculator and project notes. Selecting a route highlights it on the roof. Routes can be exported to CSV, and the longest calculated length can be copied into the sizing form. The calculator uses the configured maximum voltage-drop percentage, picks from listed standard cross-sections up to 240 mm² and preserves the inputs in the project. The calculation checks voltage drop only; ampacity, temperature, installation method and protection still require engineering review.
