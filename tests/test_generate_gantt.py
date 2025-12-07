"""Unit tests for ifc4d_gantt package"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from ifc4d_gantt import Ifc2Gantt


class TestIfc2Gantt:
    """Tests for Ifc2Gantt class"""

    def test_no_work_schedules_generates_empty_html(self):
        """Test that converter generates message when no work schedules exist"""
        mock_file = Mock()
        mock_file.by_type.return_value = []
        mock_file.wrapped_data.header.return_value.file_name_py.return_value.get_argument.return_value = "test.ifc"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            converter = Ifc2Gantt()
            converter.file = mock_file
            converter.html = output_path
            converter.execute()

            # Read generated HTML
            with open(output_path, "r") as f:
                html = f.read()

            assert "No work schedules found in this IFC file" in html
        finally:
            Path(output_path).unlink()

    def test_basic_work_schedule_extraction(self):
        """Test extraction of basic work schedule information"""
        # Mock work schedule
        mock_schedule = Mock()
        mock_schedule.Name = "Test Schedule"
        mock_schedule.id.return_value = 123
        mock_schedule.CreationDate = "2025-01-01"
        mock_schedule.Controls = []
        mock_schedule.is_a.side_effect = lambda x: x == "IfcWorkSchedule"

        # Mock file
        mock_file = Mock()
        mock_file.by_type.return_value = [mock_schedule]
        mock_file.wrapped_data.header.return_value.file_name_py.return_value.get_argument.return_value = "test.ifc"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            converter = Ifc2Gantt()
            converter.file = mock_file
            converter.html = output_path
            converter.execute()

            # Read generated HTML
            with open(output_path, "r") as f:
                html = f.read()

            assert "Test Schedule" in html
            assert "test.ifc" in html
        finally:
            Path(output_path).unlink()

    def test_task_extraction_with_dates(self):
        """Test extraction of task with time data"""
        from datetime import datetime

        # Mock task
        mock_task = Mock()
        mock_task.is_a.side_effect = lambda x: x == "IfcTask"
        mock_task.Name = "Task 1"
        mock_task.Description = "Test task"
        mock_task.id.return_value = 456
        mock_task.TaskTime = None
        mock_task.IsNestedBy = []
        mock_task.Nests = []

        # Mock relationship
        mock_rel = Mock()
        mock_rel.RelatedObjects = [mock_task]

        # Mock work schedule
        mock_schedule = Mock()
        mock_schedule.Name = "Test Schedule"
        mock_schedule.id.return_value = 123
        mock_schedule.CreationDate = "2025-01-01"
        mock_schedule.Controls = [mock_rel]
        mock_schedule.is_a.side_effect = lambda x: x == "IfcWorkSchedule"

        # Mock file
        mock_file = Mock()
        mock_file.by_type.return_value = [mock_schedule]
        mock_file.wrapped_data.header.return_value.file_name_py.return_value.get_argument.return_value = "test.ifc"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            # Mock derive_date to return dates
            with patch(
                "ifc4d_gantt.ifcopenshell.util.sequence.derive_date"
            ) as mock_derive:
                mock_derive.side_effect = [
                    datetime(2025, 1, 15),  # Start date
                    datetime(2025, 1, 20),  # Finish date
                ]

                converter = Ifc2Gantt()
                converter.file = mock_file
                converter.html = output_path
                converter.execute()

                # Read generated HTML
                with open(output_path, "r") as f:
                    html = f.read()

                assert "Task 1" in html
                assert "Test task" in html
                assert "2025-01-15" in html
                assert "2025-01-20" in html
        finally:
            Path(output_path).unlink()

    def test_nested_task_hierarchy(self):
        """Test extraction of parent-child task relationships"""
        # Mock child task
        mock_child = Mock()
        mock_child.is_a.side_effect = lambda x: x == "IfcTask"
        mock_child.Name = "Child Task"
        mock_child.Description = ""
        mock_child.id.return_value = 789
        mock_child.TaskTime = None
        mock_child.IsNestedBy = []

        mock_child_nests = Mock()
        mock_child_nests.RelatingObject = Mock()
        mock_child_nests.RelatingObject.is_a.return_value = True
        mock_child_nests.RelatingObject.id.return_value = 456
        mock_child.Nests = [mock_child_nests]

        # Mock nested relationship
        mock_nested_rel = Mock()
        mock_nested_rel.RelatedObjects = [mock_child]

        # Mock parent task
        mock_parent = Mock()
        mock_parent.is_a.side_effect = lambda x: x == "IfcTask"
        mock_parent.Name = "Parent Task"
        mock_parent.Description = ""
        mock_parent.id.return_value = 456
        mock_parent.TaskTime = None
        mock_parent.IsNestedBy = [mock_nested_rel]
        mock_parent.Nests = []

        # Mock relationship
        mock_rel = Mock()
        mock_rel.RelatedObjects = [mock_parent]

        # Mock work schedule
        mock_schedule = Mock()
        mock_schedule.Name = "Test Schedule"
        mock_schedule.id.return_value = 123
        mock_schedule.CreationDate = "2025-01-01"
        mock_schedule.Controls = [mock_rel]
        mock_schedule.is_a.side_effect = lambda x: x == "IfcWorkSchedule"

        # Mock file
        mock_file = Mock()
        mock_file.by_type.return_value = [mock_schedule]
        mock_file.wrapped_data.header.return_value.file_name_py.return_value.get_argument.return_value = "test.ifc"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            with patch(
                "ifc4d_gantt.ifcopenshell.util.sequence.derive_date", return_value=None
            ):
                converter = Ifc2Gantt()
                converter.file = mock_file
                converter.html = output_path
                converter.execute()

                # Read generated HTML
                with open(output_path, "r") as f:
                    html = f.read()

                assert "Parent Task" in html
                assert "Child Task" in html
                # Verify pGroup is 1 for parent (has children)
                assert '"pGroup": 1' in html
        finally:
            Path(output_path).unlink()

    def test_unnamed_elements_get_default_name(self):
        """Test that unnamed elements get 'Unnamed' as default"""
        mock_schedule = Mock()
        mock_schedule.Name = None
        mock_schedule.id.return_value = 123
        mock_schedule.CreationDate = ""
        mock_schedule.Controls = []
        mock_schedule.is_a.side_effect = lambda x: x == "IfcWorkSchedule"

        mock_file = Mock()
        mock_file.by_type.return_value = [mock_schedule]
        mock_file.wrapped_data.header.return_value.file_name_py.return_value.get_argument.return_value = "test.ifc"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            converter = Ifc2Gantt()
            converter.file = mock_file
            converter.html = output_path
            converter.execute()

            # Read generated HTML
            with open(output_path, "r") as f:
                html = f.read()

            assert "Unnamed" in html
        finally:
            Path(output_path).unlink()

    def test_multiple_schedules(self):
        """Test extraction of multiple work schedules"""
        mock_schedule_1 = Mock()
        mock_schedule_1.Name = "Schedule 1"
        mock_schedule_1.id.return_value = 1
        mock_schedule_1.CreationDate = ""
        mock_schedule_1.Controls = []
        mock_schedule_1.is_a.side_effect = lambda x: x == "IfcWorkSchedule"

        mock_schedule_2 = Mock()
        mock_schedule_2.Name = "Schedule 2"
        mock_schedule_2.id.return_value = 2
        mock_schedule_2.CreationDate = ""
        mock_schedule_2.Controls = []
        mock_schedule_2.is_a.side_effect = lambda x: x == "IfcWorkSchedule"

        mock_file = Mock()
        mock_file.by_type.return_value = [mock_schedule_1, mock_schedule_2]
        mock_file.wrapped_data.header.return_value.file_name_py.return_value.get_argument.return_value = "test.ifc"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            converter = Ifc2Gantt()
            converter.file = mock_file
            converter.html = output_path
            converter.execute()

            # Read generated HTML
            with open(output_path, "r") as f:
                html = f.read()

            assert "Schedule 1" in html
            assert "Schedule 2" in html
            assert "GanttChartDIV_0" in html
            assert "GanttChartDIV_1" in html
        finally:
            Path(output_path).unlink()
