from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from transfer_windows import check_calendar, _sao_paulo_today, BUNDLED_SAO_PAULO_TZIF
from zoneinfo import ZoneInfoNotFoundError
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
CAL=ROOT/'config/transfer-windows-2026.json'

class CalendarTests(unittest.TestCase):
    def test_bundled_timezone_fallback_on_windows_without_tzdata(self):
        # Emulate Python on Windows without an IANA tzdata installation.
        self.assertTrue(BUNDLED_SAO_PAULO_TZIF.is_file())
        with patch('transfer_windows._system_zoneinfo', side_effect=ZoneInfoNotFoundError()):
            actual = _sao_paulo_today()
            self.assertIsInstance(actual, date)

    def test_duplicate_window_needs_no_system_timezone_database(self):
        with patch('transfer_windows._system_zoneinfo', side_effect=ZoneInfoNotFoundError()):
            with TemporaryDirectory() as t:
                root=Path(t); payload=json.loads(CAL.read_text())
                payload['windows'].append(dict(payload['windows'][0]))
                p=root/'dup.json'; p.write_text(json.dumps(payload))
                with self.assertRaisesRegex(ValueError, 'Duplicate'):
                    check_calendar(p)

    def test_before_end_no_calls(self):
        result=check_calendar(CAL,now=date(2026,2,22))
        self.assertFalse(result['publicationEnabled'])
        self.assertEqual(result['apiCalls'],0)
        self.assertEqual(result['windows'][0]['status'],'not_due')
    def test_exactly_seven_days_after_second_window(self):
        result=check_calendar(CAL,now=date(2026,9,18))
        self.assertEqual(result['windows'][1]['dueDate'],'2026-09-18')
        self.assertEqual(result['windows'][1]['status'],'due_but_publication_blocked_until_release_validation')
    def test_duplicate_window_rejected(self):
        with TemporaryDirectory() as t:
            root=Path(t);payload=json.loads(CAL.read_text())
            payload['windows'].append(dict(payload['windows'][0]));p=root/'dup.json';p.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError,'Duplicate'):
                check_calendar(p)
    def test_unconfirmed_window_not_published(self):
        result=check_calendar(CAL,now=date(2026,10,24))
        self.assertEqual(result['windows'][2]['status'],'calendar_requires_official_confirmation')
    def test_completed_window_not_repeated(self):
        result=check_calendar(CAL,now=date(2026,10,24),completed={'2026-br-main-2'})
        self.assertEqual(result['windows'][1]['status'],'completed')

if __name__=='__main__':unittest.main()
