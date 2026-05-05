# SPDX-License-Identifier: MIT

import os
import tempfile
import unittest

from drain3.file_persistence import FilePersistence
from drain3.memory_buffer_persistence import MemoryBufferPersistence


class FilePersistenceTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.file_path = os.path.join(self.tmpdir, "state.bin")

    def tearDown(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
        os.rmdir(self.tmpdir)

    def test_load_returns_none_when_file_missing(self):
        p = FilePersistence(self.file_path)
        self.assertIsNone(p.load_state())

    def test_save_and_load(self):
        p = FilePersistence(self.file_path)
        data = b"some state data"
        p.save_state(data)
        self.assertEqual(data, p.load_state())

    def test_save_overwrites(self):
        p = FilePersistence(self.file_path)
        p.save_state(b"first")
        p.save_state(b"second")
        self.assertEqual(b"second", p.load_state())

    def test_save_empty_bytes(self):
        p = FilePersistence(self.file_path)
        p.save_state(b"")
        self.assertEqual(b"", p.load_state())

    def test_save_binary_data(self):
        p = FilePersistence(self.file_path)
        data = bytes(range(256))
        p.save_state(data)
        self.assertEqual(data, p.load_state())


class MemoryBufferPersistenceTest(unittest.TestCase):
    def test_initial_state_is_none(self):
        p = MemoryBufferPersistence()
        self.assertIsNone(p.load_state())

    def test_save_and_load(self):
        p = MemoryBufferPersistence()
        data = b"hello"
        p.save_state(data)
        self.assertEqual(data, p.load_state())

    def test_save_overwrites(self):
        p = MemoryBufferPersistence()
        p.save_state(b"first")
        p.save_state(b"second")
        self.assertEqual(b"second", p.load_state())

    def test_save_empty_bytes(self):
        p = MemoryBufferPersistence()
        p.save_state(b"")
        self.assertEqual(b"", p.load_state())
