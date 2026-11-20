"""Regression checks for equation attachments in packaged C++ run reports."""

from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from rotary_melter.Paths import PROJECT_ROOT
from rotary_melter.Reporting import export_result


class PackagedReportingTests(unittest.TestCase):
    def test_native_export_links_both_catalogues_and_preserves_source_bytes(self):
        catalogues = {
            'EQUATIONS.md': 'CPP_CALCULATION_EQUATIONS.md',
            'CALCULATION_EQUATIONS.md': 'CALCULATION_EQUATIONS.md',
        }
        original_links = re.compile(r'\]\(((?:\.\./(?:native|rotary_melter)/|history/)[^)]+)\)')
        temporary_root = PROJECT_ROOT / '.autodev'
        temporary_root.mkdir(exist_ok=True)

        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            root = Path(directory)
            resources = root / 'bundle'
            (resources / 'docs').mkdir(parents=True)
            expected_catalogues = {}
            for output_name, catalogue_name in catalogues.items():
                original = PROJECT_ROOT / 'docs' / catalogue_name
                shutil.copyfile(original, resources / 'docs' / catalogue_name)
                expected = set()
                for link in original_links.findall(original.read_text(encoding='utf-8')):
                    relative = link[3:] if link.startswith('../') else 'docs/' + link
                    expected.add('source/' + relative)
                    source = relative.split('#', 1)[0]
                    packaged = ('native_sources/' + source.removeprefix('native/')
                                if source.startswith('native/') else 'reference_sources/' + source)
                    destination = resources / packaged
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(PROJECT_ROOT / source, destination)
                self.assertTrue(expected, catalogue_name)
                expected_catalogues[output_name] = expected

            with patch.object(sys, 'frozen', True, create=True), \
                    patch.object(sys, '_MEIPASS', str(resources), create=True):
                folder = export_result({'engine': {'name': 'Rotary Melter C++'}}, root / 'run')

            report = (folder / 'RUN_REPORT.md').read_text(encoding='utf-8')
            self.assertIn('](EQUATIONS.md)', report)
            main = (folder / 'EQUATIONS.md').read_text(encoding='utf-8')
            self.assertIn('](CALCULATION_EQUATIONS.md)', main)
            for output_name, expected in expected_catalogues.items():
                with self.subTest(catalogue=output_name):
                    exported = (folder / output_name).read_text(encoding='utf-8')
                    self.assertFalse(original_links.search(exported))
                    self.assertEqual(set(re.findall(r'\]\((source/[^)]+)\)', exported)), expected)
                    for link in expected:
                        path = link.split('#', 1)[0]
                        self.assertEqual((folder / path).read_bytes(),
                                         (PROJECT_ROOT / path.removeprefix('source/')).read_bytes(), path)
