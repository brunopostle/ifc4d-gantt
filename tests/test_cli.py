"""Tests for CLI functionality"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from ifc4d_gantt import main


class TestCLI:
    """Tests for command-line interface"""

    def test_main_no_arguments_exits(self):
        """Test that main() exits with error when no arguments provided"""
        with patch("sys.argv", ["ifc4d_gantt"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_main_with_ifc_file(self, tmp_path):
        """Test main() with IFC file and default output"""
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
        mock_file.wrapped_data.header.file_name.name = "test.ifc"

        with patch("sys.argv", ["ifc4d_gantt", "test.ifc"]):
            with patch("ifc4d_gantt.ifcopenshell.open", return_value=mock_file):
                with patch("builtins.open", create=True) as mock_open:
                    with patch("builtins.print") as mock_print:
                        # Mock the file write
                        mock_open.return_value.__enter__.return_value.write = Mock()
                        main()

                        # Check success message was printed
                        mock_print.assert_called_once()
                        assert "gantt.html" in str(mock_print.call_args)
                        assert "1 schedule" in str(mock_print.call_args)

    def test_main_with_custom_output_file(self, tmp_path):
        """Test main() with custom output filename"""
        # Mock work schedule
        mock_schedule = Mock()
        mock_schedule.Name = "Test Schedule"
        mock_schedule.id.return_value = 123
        mock_schedule.CreationDate = ""
        mock_schedule.Controls = []
        mock_schedule.is_a.side_effect = lambda x: x == "IfcWorkSchedule"

        # Mock file
        mock_file = Mock()
        mock_file.by_type.return_value = [mock_schedule]
        mock_file.wrapped_data.header.file_name.name = "test.ifc"

        with patch("sys.argv", ["ifc4d_gantt", "test.ifc", "custom.html"]):
            with patch("ifc4d_gantt.ifcopenshell.open", return_value=mock_file):
                with patch("builtins.open", create=True) as mock_open:
                    with patch("builtins.print"):
                        mock_open.return_value.__enter__.return_value.write = Mock()
                        main()

                        # Check custom filename was used
                        assert any(
                            "custom.html" in str(call)
                            for call in mock_open.call_args_list
                        )

    def test_main_no_work_schedules(self):
        """Test main() generates HTML even when no work schedules found"""
        # Mock file with no schedules
        mock_file = Mock()
        mock_file.by_type.return_value = []
        mock_file.wrapped_data.header.file_name.name = "test.ifc"

        with patch("sys.argv", ["ifc4d_gantt", "test.ifc"]):
            with patch("ifc4d_gantt.ifcopenshell.open", return_value=mock_file):
                with patch("builtins.open", create=True) as mock_open:
                    with patch("builtins.print") as mock_print:
                        mock_open.return_value.__enter__.return_value.write = Mock()
                        main()

                        # Should still write HTML file
                        assert any(
                            "gantt.html" in str(call)
                            for call in mock_open.call_args_list
                        )
                        # Should print with 0 schedules
                        assert "0 schedule" in str(mock_print.call_args)

    def test_main_generates_valid_html(self):
        """Test that main() generates valid HTML output"""
        # Mock task
        mock_task = Mock()
        mock_task.is_a.side_effect = lambda x: x == "IfcTask"
        mock_task.Name = "Task 1"
        mock_task.Description = "Test note"
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
        mock_schedule.CreationDate = ""
        mock_schedule.Controls = [mock_rel]
        mock_schedule.is_a.side_effect = lambda x: x == "IfcWorkSchedule"

        # Mock file
        mock_file = Mock()
        mock_file.by_type.return_value = [mock_schedule]
        mock_file.wrapped_data.header.file_name.name = "test.ifc"

        written_content = []

        def capture_write(content):
            written_content.append(content)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            with patch("sys.argv", ["ifc4d_gantt", "test.ifc", output_path]):
                with patch("ifc4d_gantt.ifcopenshell.open", return_value=mock_file):
                    with patch(
                        "ifc4d_gantt.ifcopenshell.util.sequence.derive_date",
                        return_value=None,
                    ):
                        with patch("builtins.print"):
                            main()

            # Read the generated file
            with open(output_path, "r") as f:
                html_output = f.read()

            assert "<!DOCTYPE html>" in html_output
            assert "Test Schedule" in html_output
            assert "Task 1" in html_output
            assert "JSGantt" in html_output
            assert "jsgantt-improved" in html_output
        finally:
            Path(output_path).unlink()

    def test_main_multiple_schedules(self):
        """Test main() with multiple work schedules"""
        # Mock schedules
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

        # Mock file
        mock_file = Mock()
        mock_file.by_type.return_value = [mock_schedule_1, mock_schedule_2]
        mock_file.wrapped_data.header.file_name.name = "test.ifc"

        with patch("sys.argv", ["ifc4d_gantt", "test.ifc"]):
            with patch("ifc4d_gantt.ifcopenshell.open", return_value=mock_file):
                with patch("builtins.open", create=True) as mock_open:
                    with patch("builtins.print") as mock_print:
                        mock_open.return_value.__enter__.return_value.write = Mock()
                        main()

                        # Should print with 2 schedules (plural)
                        assert "2 schedules" in str(mock_print.call_args)
