# SPDX-License-Identifier: MIT

import unittest

from drain3.simple_profiler import NullProfiler, SimpleProfiler, ProfiledSectionStats


class NullProfilerTest(unittest.TestCase):
    def test_start_end_report_are_noop(self):
        profiler = NullProfiler()
        profiler.start_section("x")
        profiler.end_section("x")
        profiler.end_section()
        profiler.report(0)


class SimpleProfilerTest(unittest.TestCase):
    def test_start_and_end_section(self):
        profiler = SimpleProfiler()
        profiler.start_section("a")
        profiler.end_section()
        stats = profiler.section_to_stats["a"]
        self.assertEqual(1, stats.sample_count)
        self.assertGreater(stats.total_time_sec, 0)

    def test_end_section_by_name(self):
        profiler = SimpleProfiler()
        profiler.start_section("a")
        profiler.end_section("a")
        self.assertEqual(1, profiler.section_to_stats["a"].sample_count)

    def test_multiple_samples(self):
        profiler = SimpleProfiler()
        for _ in range(5):
            profiler.start_section("s")
            profiler.end_section()
        self.assertEqual(5, profiler.section_to_stats["s"].sample_count)

    def test_empty_section_name_raises(self):
        profiler = SimpleProfiler()
        with self.assertRaises(ValueError):
            profiler.start_section("")

    def test_double_start_raises(self):
        profiler = SimpleProfiler()
        profiler.start_section("a")
        with self.assertRaises(ValueError):
            profiler.start_section("a")

    def test_end_nonexistent_section_raises(self):
        profiler = SimpleProfiler()
        with self.assertRaises(ValueError):
            profiler.end_section("nonexistent")

    def test_end_without_start_raises(self):
        profiler = SimpleProfiler()
        profiler.start_section("a")
        profiler.end_section("a")
        with self.assertRaises(ValueError):
            profiler.end_section("a")

    def test_end_no_name_no_start_raises(self):
        profiler = SimpleProfiler()
        with self.assertRaises(ValueError):
            profiler.end_section()

    def test_report_respects_period(self):
        output = []
        profiler = SimpleProfiler(printer=output.append, report_sec=9999)
        profiler.start_section("total")
        profiler.end_section()
        profiler.report(9999)
        self.assertEqual(0, len(output))

    def test_report_prints_when_period_elapsed(self):
        output = []
        profiler = SimpleProfiler(printer=output.append)
        profiler.last_report_timestamp_sec = 0
        profiler.start_section("total")
        profiler.end_section()
        profiler.report(0)
        self.assertGreater(len(output), 0)

    def test_report_includes_enclosing_section_percentage(self):
        output = []
        profiler = SimpleProfiler(printer=output.append, enclosing_section_name="total")
        profiler.last_report_timestamp_sec = 0
        profiler.start_section("total")
        profiler.start_section("inner")
        profiler.end_section("inner")
        profiler.end_section("total")
        profiler.report(0)
        text = "\n".join(output)
        self.assertIn("%", text)

    def test_reset_after_sample_count(self):
        profiler = SimpleProfiler(reset_after_sample_count=2)
        for _ in range(3):
            profiler.start_section("s")
            profiler.end_section()
        stats = profiler.section_to_stats["s"]
        self.assertEqual(3, stats.sample_count)
        self.assertEqual(1, stats.sample_count_batch)


class ProfiledSectionStatsTest(unittest.TestCase):
    def test_to_string_without_enclosing(self):
        stats = ProfiledSectionStats("test", sample_count=100, total_time_sec=1.0)
        result = stats.to_string(0, False)
        self.assertIn("test", result)
        self.assertIn("100", result)

    def test_to_string_with_enclosing(self):
        stats = ProfiledSectionStats("test", sample_count=100, total_time_sec=0.5)
        result = stats.to_string(1.0, False)
        self.assertIn("%", result)
        self.assertIn("50.00", result)

    def test_to_string_with_batch_rates(self):
        stats = ProfiledSectionStats(
            "test",
            sample_count=100,
            total_time_sec=1.0,
            sample_count_batch=50,
            total_time_sec_batch=0.5,
        )
        result = stats.to_string(0, True)
        self.assertIn("test", result)

    def test_to_string_zero_time(self):
        stats = ProfiledSectionStats("test", sample_count=10, total_time_sec=0)
        result = stats.to_string(0, False)
        self.assertIn("N/A", result)

    def test_to_string_zero_batch_time(self):
        stats = ProfiledSectionStats(
            "test",
            sample_count=10,
            total_time_sec=1.0,
            sample_count_batch=5,
            total_time_sec_batch=0,
        )
        result = stats.to_string(0, True)
        self.assertIn("N/A", result)
