# ifc4d-gantt - Extract scheduling data from IFC files and generate interactive Gantt charts
# Copyright (C) 2024 Bruno Postle <bruno@postle.net>
#
# This file is part of ifc4d-gantt.
#
# ifc4d-gantt is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ifc4d-gantt is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with ifc4d-gantt.  If not, see <http://www.gnu.org/licenses/>.

import ifcopenshell
import ifcopenshell.util.date
import ifcopenshell.util.sequence
import json
from pathlib import Path
from datetime import timedelta

__version__ = "0.1.0"


class Ifc2Gantt:
    def __init__(self):
        self.file = None
        self.html = None

    def execute(self):
        """Generate HTML Gantt chart from IFC file"""
        work_schedules = self.file.by_type("IfcWorkSchedule")

        if not work_schedules:
            # No schedules found - generate HTML with message
            schedules_html = "<p>No work schedules found in this IFC file.</p>"
            ifc_filename = self._get_ifc_filename()
            html_content = self._get_html_template().format(
                ifc_file=ifc_filename, schedules_html=schedules_html
            )
            with open(self.html, "w") as f:
                f.write(html_content)
            return

        # Extract all schedules
        schedules_data = []
        for work_schedule in work_schedules:
            schedule_data = self._extract_schedule(work_schedule)
            schedules_data.append(schedule_data)

        # Generate HTML output
        self._generate_html(schedules_data)

    def _get_ifc_filename(self):
        """Extract IFC filename from file object"""
        try:
            filename = self.file.wrapped_data.header().file_name_py().get_argument(0)
            return Path(filename).name
        except:
            return "model.ifc"

    def _extract_schedule(self, work_schedule):
        """Extract a single work schedule and its tasks"""
        tasks = []
        self._get_tasks(work_schedule, tasks)

        return {
            "work_schedule": {
                "Name": work_schedule.Name or "Unnamed",
                "id": work_schedule.id(),
                "CreationDate": work_schedule.CreationDate or "",
            },
            "tasks": tasks,
        }

    def _get_tasks(self, element, tasks_list):
        """Recursively extract tasks"""
        if element.is_a("IfcWorkSchedule"):
            rels = element.Controls or []
            for rel in rels:
                for task in rel.RelatedObjects:
                    if task.is_a("IfcTask"):
                        self._get_tasks(task, tasks_list)
        elif element.is_a("IfcTask"):
            task_data = {
                "pID": element.id(),
                "pName": element.Name or "Unnamed",
                "pStart": "",
                "pEnd": "",
                "pClass": "gtaskblue",
                "pLink": "",
                "pMile": 0,
                "pRes": "",
                "pComp": 0,
                "pGroup": 0,
                "pParent": 0,
                "pOpen": 1,
                "pDepend": "",
                "pCaption": "",
                "pNotes": element.Description or "",
            }

            # Extract dates using ifcopenshell utilities
            derived_start = ifcopenshell.util.sequence.derive_date(
                element, "ScheduleStart", is_earliest=True
            )
            derived_finish = ifcopenshell.util.sequence.derive_date(
                element, "ScheduleFinish", is_earliest=True
            )

            if derived_start:
                task_data["pStart"] = derived_start.strftime("%Y-%m-%d")

            if derived_finish:
                task_data["pEnd"] = derived_finish.strftime("%Y-%m-%d")

            # Store duration if available and calculate end date if missing
            if element.TaskTime and element.TaskTime.ScheduleDuration:
                duration = ifcopenshell.util.date.ifc2datetime(
                    element.TaskTime.ScheduleDuration
                )
                task_data["ifcduration"] = f"{duration.days}d"

                # If we have start but no finish, calculate from duration
                if task_data["pStart"] and not task_data["pEnd"] and duration.days > 0:
                    end_date = derived_start + timedelta(days=duration.days)
                    task_data["pEnd"] = end_date.strftime("%Y-%m-%d")

            # Check if parent
            nested_tasks = []
            for rel in element.IsNestedBy or []:
                for subtask in rel.RelatedObjects:
                    if subtask.is_a("IfcTask"):
                        nested_tasks.append(subtask)

            if nested_tasks:
                task_data["pGroup"] = 1

            # Get parent
            for rel in element.Nests or []:
                if rel.RelatingObject.is_a("IfcTask"):
                    task_data["pParent"] = rel.RelatingObject.id()

            tasks_list.append(task_data)

            # Process children
            for nested_task in nested_tasks:
                self._get_tasks(nested_task, tasks_list)

    def _generate_html(self, schedules_data):
        """Generate HTML file with all schedules"""
        ifc_filename = self._get_ifc_filename()

        # Generate sections for each schedule
        schedules_html_parts = []
        for idx, schedule_data in enumerate(schedules_data):
            schedule_name = schedule_data["work_schedule"]["Name"]
            div_id = f"GanttChartDIV_{idx}"

            section_html = f"""
    <div class="schedule-section">
        <h2>{schedule_name}</h2>
        <div id="{div_id}"></div>
        <script>
            var g{idx} = new JSGantt.GanttChart(document.getElementById('{div_id}'), 'week');
            g{idx}.setOptions({{
                vCaptionType: 'Complete',
                vFormat: 'week',
                vShowRes: true,
                vShowDur: true,
                vShowComp: true
            }});
            var tasks{idx} = {json.dumps(schedule_data['tasks'], indent=2)};
            JSGantt.addJSONTask(g{idx}, tasks{idx});
            g{idx}.Draw();
        </script>
    </div>"""
            schedules_html_parts.append(section_html)

        schedules_html = "\n".join(schedules_html_parts)
        html_content = self._get_html_template().format(
            ifc_file=ifc_filename, schedules_html=schedules_html
        )

        with open(self.html, "w") as f:
            f.write(html_content)

    def _get_html_template(self):
        """Return HTML template"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>Gantt Chart - {ifc_file}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/jsgantt-improved@2.1.0/dist/jsgantt.css"/>
    <script src="https://cdn.jsdelivr.net/npm/jsgantt-improved@2.1.0/dist/jsgantt.min.js"></script>
    <style>
        .schedule-section {{
            margin-bottom: 50px;
            page-break-after: always;
        }}
        h1 {{
            margin-top: 20px;
        }}
        h2 {{
            margin-top: 10px;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <h1>Work Schedules - {ifc_file}</h1>
    {schedules_html}
</body>
</html>"""


def main():
    """Entry point for the command-line interface"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: ifc4d-gantt model.ifc [output.html]")
        sys.exit(1)

    ifc_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "gantt.html"

    # Create converter and execute
    converter = Ifc2Gantt()
    converter.file = ifcopenshell.open(ifc_path)
    converter.html = output_path
    converter.execute()

    # Count schedules for output message
    work_schedules = converter.file.by_type("IfcWorkSchedule")
    schedule_count = len(work_schedules)
    print(
        f"Gantt chart generated: {output_path} ({schedule_count} schedule{'s' if schedule_count != 1 else ''})"
    )
