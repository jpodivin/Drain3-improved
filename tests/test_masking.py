# SPDX-License-Identifier: MIT

import unittest

from drain3.masking import MaskingInstruction, LogMasker, RegexMaskingInstruction


class MaskingInstructionTest(unittest.TestCase):
    def test_pattern_property(self):
        mi = MaskingInstruction(r"\d+", "NUM")
        self.assertEqual(r"\d+", mi.pattern)

    def test_mask_with_attribute(self):
        mi = MaskingInstruction(r"\d+", "NUM")
        self.assertEqual("NUM", mi.mask_with)

    def test_mask_replaces_matches(self):
        mi = MaskingInstruction(r"\d+", "NUM")
        result = mi.mask("abc 123 def 456", "<", ">")
        self.assertEqual("abc <NUM> def <NUM>", result)

    def test_mask_no_match(self):
        mi = MaskingInstruction(r"\d+", "NUM")
        result = mi.mask("no digits here", "<", ">")
        self.assertEqual("no digits here", result)

    def test_mask_empty_prefix_suffix(self):
        mi = MaskingInstruction(r"\d+", "NUM")
        result = mi.mask("test 42", "", "")
        self.assertEqual("test NUM", result)

    def test_regex_masking_instruction_alias(self):
        self.assertIs(RegexMaskingInstruction, MaskingInstruction)


class LogMaskerTest(unittest.TestCase):
    def test_empty_instructions(self):
        masker = LogMasker([], "<", ">")
        self.assertEqual("hello 123", masker.mask("hello 123"))
        self.assertEqual(0, len(masker.mask_names))

    def test_multiple_instructions_applied_in_order(self):
        mi1 = MaskingInstruction(r"\d+\.\d+\.\d+\.\d+", "IP")
        mi2 = MaskingInstruction(r"\d+", "NUM")
        masker = LogMasker([mi1, mi2], "<", ">")
        result = masker.mask("host 192.168.1.1 port 8080")
        self.assertEqual("host <IP> port <NUM>", result)

    def test_mask_names(self):
        mi1 = MaskingInstruction(r"a", "X")
        mi2 = MaskingInstruction(r"b", "Y")
        mi3 = MaskingInstruction(r"c", "X")
        masker = LogMasker([mi1, mi2, mi3], "", "")
        self.assertCountEqual(["X", "Y"], masker.mask_names)

    def test_instructions_by_mask_name_missing(self):
        masker = LogMasker([], "", "")
        result = masker.instructions_by_mask_name("nonexistent")
        self.assertEqual(0, len(result))

    def test_mask_with_custom_prefix_suffix(self):
        mi = MaskingInstruction(r"\d+", "N")
        masker = LogMasker([mi], "{{", "}}")
        result = masker.mask("test 42 end")
        self.assertEqual("test {{N}} end", result)


class MaskingTest(unittest.TestCase):
    def test_instructions_by_mask_name(self):
        instructions = []
        a = MaskingInstruction(r"a", "1")
        instructions.append(a)
        b = MaskingInstruction(r"b", "1")
        instructions.append(b)
        c = MaskingInstruction(r"c", "2")
        instructions.append(c)
        d = MaskingInstruction(r"d", "3")
        instructions.append(d)
        x = MaskingInstruction(r"x", "something else")
        instructions.append(x)
        y = MaskingInstruction(r"y", "something else")
        instructions.append(y)
        masker = LogMasker(instructions, "", "")
        self.assertCountEqual(["1", "2", "3", "something else"], masker.mask_names)
        self.assertCountEqual([a, b], masker.instructions_by_mask_name("1"))
        self.assertCountEqual([c], masker.instructions_by_mask_name("2"))
        self.assertCountEqual([d], masker.instructions_by_mask_name("3"))
        self.assertCountEqual(
            [x, y], masker.instructions_by_mask_name("something else")
        )

    def test_mask(self):
        s = "D9 test 999 888 1A ccc 3"
        mi = MaskingInstruction(
            r"((?<=[^A-Za-z0-9])|^)([\-\+]?\d+)((?=[^A-Za-z0-9])|$)", "NUM"
        )
        masker = LogMasker([mi], "<!", "!>")
        masked = masker.mask(s)
        self.assertEqual("D9 test <!NUM!> <!NUM!> 1A ccc <!NUM!>", masked)
