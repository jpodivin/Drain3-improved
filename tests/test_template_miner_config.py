# SPDX-License-Identifier: MIT

import os
import tempfile
import unittest

from drain3.template_miner_config import TemplateMinerConfig


class TemplateMinerConfigDefaultsTest(unittest.TestCase):
    def test_default_values(self):
        config = TemplateMinerConfig()
        self.assertEqual("Drain", config.engine)
        self.assertFalse(config.profiling_enabled)
        self.assertEqual(60, config.profiling_report_sec)
        self.assertEqual(5, config.snapshot_interval_minutes)
        self.assertTrue(config.snapshot_compress_state)
        self.assertEqual([], config.drain_extra_delimiters)
        self.assertAlmostEqual(0.4, config.drain_sim_th)
        self.assertEqual(4, config.drain_depth)
        self.assertEqual(100, config.drain_max_children)
        self.assertIsNone(config.drain_max_clusters)
        self.assertEqual([], config.masking_instructions)
        self.assertEqual("<", config.mask_prefix)
        self.assertEqual(">", config.mask_suffix)
        self.assertEqual(3000, config.parameter_extraction_cache_capacity)
        self.assertTrue(config.parametrize_numeric_tokens)


class TemplateMinerConfigLoadTest(unittest.TestCase):
    def test_load_missing_file_keeps_defaults(self):
        config = TemplateMinerConfig()
        config.load("/nonexistent/path/file.ini")
        self.assertEqual("Drain", config.engine)
        self.assertAlmostEqual(0.4, config.drain_sim_th)

    def test_load_partial_config(self):
        content = "[DRAIN]\nsim_th = 0.8\ndepth = 6\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(content)
            f.flush()
            path = f.name

        try:
            config = TemplateMinerConfig()
            config.load(path)
            self.assertAlmostEqual(0.8, config.drain_sim_th)
            self.assertEqual(6, config.drain_depth)
            self.assertFalse(config.profiling_enabled)
            self.assertEqual([], config.masking_instructions)
        finally:
            os.remove(path)

    def test_load_profiling_section(self):
        content = "[PROFILING]\nenabled = True\nreport_sec = 120\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(content)
            f.flush()
            path = f.name

        try:
            config = TemplateMinerConfig()
            config.load(path)
            self.assertTrue(config.profiling_enabled)
            self.assertEqual(120, config.profiling_report_sec)
        finally:
            os.remove(path)

    def test_load_snapshot_section(self):
        content = "[SNAPSHOT]\nsnapshot_interval_minutes = 30\ncompress_state = False\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(content)
            f.flush()
            path = f.name

        try:
            config = TemplateMinerConfig()
            config.load(path)
            self.assertEqual(30, config.snapshot_interval_minutes)
            self.assertFalse(config.snapshot_compress_state)
        finally:
            os.remove(path)

    def test_load_masking_section(self):
        content = (
            "[MASKING]\n"
            'masking = [{"regex_pattern": "\\\\d+", "mask_with": "NUM"}]\n'
            "mask_prefix = [:\n"
            "mask_suffix = :]\n"
            "parameter_extraction_cache_capacity = 500\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(content)
            f.flush()
            path = f.name

        try:
            config = TemplateMinerConfig()
            config.load(path)
            self.assertEqual("[:", config.mask_prefix)
            self.assertEqual(":]", config.mask_suffix)
            self.assertEqual(500, config.parameter_extraction_cache_capacity)
            self.assertEqual(1, len(config.masking_instructions))
        finally:
            os.remove(path)

    def test_load_engine_option(self):
        content = "[DRAIN]\nengine = JaccardDrain\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(content)
            f.flush()
            path = f.name

        try:
            config = TemplateMinerConfig()
            config.load(path)
            self.assertEqual("JaccardDrain", config.engine)
        finally:
            os.remove(path)

    def test_load_extra_delimiters(self):
        content = '[DRAIN]\nextra_delimiters = ["_", "-"]\n'
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(content)
            f.flush()
            path = f.name

        try:
            config = TemplateMinerConfig()
            config.load(path)
            self.assertListEqual(["_", "-"], config.drain_extra_delimiters)
        finally:
            os.remove(path)

    def test_load_parametrize_numeric_tokens_false(self):
        content = "[DRAIN]\nparametrize_numeric_tokens = False\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(content)
            f.flush()
            path = f.name

        try:
            config = TemplateMinerConfig()
            config.load(path)
            self.assertFalse(config.parametrize_numeric_tokens)
        finally:
            os.remove(path)
