# ifc4d-gantt

Extract scheduling data from IFC (Industry Foundation Classes) files and generate interactive Gantt charts.

This tool reads BIM (Building Information Modeling) files containing project schedules and converts them into standalone HTML files with interactive Gantt chart visualizations using JSGantt-improved.

## Installation

Install from source:

```bash
git clone https://github.com/brunopostle/ifc4d-gantt.git
cd ifc4d-gantt
pip install .
```

## Usage

### Command Line

```bash
ifc4d-gantt model.ifc [output.html]
```

If no output filename is provided, the tool generates `gantt.html` in the current directory.

### As a Library

```python
import ifcopenshell
from ifc4d_gantt import Ifc2Gantt

# Create converter
converter = Ifc2Gantt()
converter.file = ifcopenshell.open('model.ifc')
converter.html = 'output.html'

# Generate Gantt chart
converter.execute()
```

## Requirements

- Python 3.9 or later
- ifcopenshell 0.8.1 or later

## Features

- Extracts `IfcWorkSchedule` and `IfcTask` entities from IFC files
- Preserves task hierarchies (parent-child relationships)
- Includes task timing information (start dates, end dates, durations)
- Generates self-contained HTML files with embedded visualization
- Uses JSGantt-improved for interactive chart rendering

## License

This project is licensed under the GNU Lesser General Public License v3.0 or later (LGPL-3.0-or-later). See the LICENSE file for details.

## Author

Bruno Postle <bruno@postle.net>

## Repository

https://github.com/brunopostle/ifc4d-gantt
