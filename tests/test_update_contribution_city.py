import json
import unittest
import xml.etree.ElementTree as ET
from datetime import date

from scripts.update_contribution_city import CalendarParser, render, render_data


class CalendarParserTests(unittest.TestCase):
    def test_parses_dates_levels_and_counts_from_github_calendar(self):
        source = '''
        <table>
          <td class="ContributionCalendar-day" data-date="2026-10-20" data-level="4">
            <tool-tip>5 contributions on Tuesday, October 20th.</tool-tip>
          </td>
          <td class="ContributionCalendar-day" data-date="2026-10-21" data-level="0">
            <tool-tip>No contributions on Wednesday, October 21st.</tool-tip>
          </td>
        </table>
        '''
        parser = CalendarParser()
        parser.feed(source)

        self.assertEqual(
            parser.days,
            [(date(2026, 10, 20), 4, 5), (date(2026, 10, 21), 0, 0)],
        )


class ContributionCityRenderTests(unittest.TestCase):
    def setUp(self):
        self.days = [
            (date(2026, 10, 20), 3, 4),
            (date(2026, 10, 21), 0, 0),
            (date(2026, 10, 22), 2, 2),
        ]

    def test_data_export_uses_the_same_real_calendar_values(self):
        payload = json.loads(render_data(self.days))

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["source"], "GitHub public contribution calendar")
        self.assertIn("may exclude private activity", payload["day_semantics"])
        self.assertEqual(
            payload["days"],
            [
                {"date": "2026-10-20", "level": 3, "count": 4},
                {"date": "2026-10-21", "level": 0, "count": 0},
                {"date": "2026-10-22", "level": 2, "count": 2},
            ],
        )

    def test_data_export_sorts_dates_chronologically(self):
        unsorted = [self.days[2], self.days[0], self.days[1]]
        payload = json.loads(render_data(unsorted))

        self.assertEqual(
            [item["date"] for item in payload["days"]],
            ["2026-10-20", "2026-10-21", "2026-10-22"],
        )

    def test_static_city_still_renders_valid_svg_with_trustworthy_totals(self):
        svg = render(self.days)
        root = ET.fromstring(svg)

        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertIn("generated from 6 public GitHub contributions", svg)
        self.assertIn("across 2 active days", svg)


if __name__ == "__main__":
    unittest.main()
