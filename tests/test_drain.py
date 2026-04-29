# SPDX-License-Identifier: MIT

import io
import unittest

from drain3.drain import Drain, DrainBase, LogCluster, LogClusterCache, Node


class LogClusterTest(unittest.TestCase):
    def test_get_template(self):
        cluster = LogCluster(["hello", "world"], 1)
        self.assertEqual("hello world", cluster.get_template())

    def test_get_template_empty(self):
        cluster = LogCluster([], 1)
        self.assertEqual("", cluster.get_template())

    def test_str_representation(self):
        cluster = LogCluster(["a", "b"], 42)
        s = str(cluster)
        self.assertIn("42", s)
        self.assertIn("a b", s)
        self.assertIn("size=1", s)

    def test_initial_size_is_one(self):
        cluster = LogCluster(["x"], 1)
        self.assertEqual(1, cluster.size)

    def test_tokens_stored_as_tuple(self):
        cluster = LogCluster(["a", "b", "c"], 1)
        self.assertIsInstance(cluster.log_template_tokens, tuple)


class LogClusterCacheTest(unittest.TestCase):
    def test_missing_key_returns_none(self):
        cache = LogClusterCache(maxsize=10)
        self.assertIsNone(cache[999])

    def test_get_bypasses_eviction(self):
        cache = LogClusterCache(maxsize=2)
        c1 = LogCluster(["a"], 1)
        c2 = LogCluster(["b"], 2)
        cache[1] = c1
        cache[2] = c2
        result = cache.get(1)
        self.assertEqual(c1, result)

    def test_get_nonexistent_returns_none(self):
        cache = LogClusterCache(maxsize=10)
        self.assertIsNone(cache.get(999))


class NodeTest(unittest.TestCase):
    def test_initial_state(self):
        node = Node()
        self.assertEqual({}, node.key_to_child_node)
        self.assertEqual([], node.cluster_ids)


class DrainBaseTest(unittest.TestCase):
    def test_depth_below_three_raises(self):
        with self.assertRaises(ValueError):
            Drain(depth=2)

    def test_depth_exactly_three(self):
        model = Drain(depth=3)
        self.assertEqual(3, model.log_cluster_depth)

    def test_has_numbers_true(self):
        self.assertTrue(DrainBase.has_numbers("abc123"))

    def test_has_numbers_false(self):
        self.assertFalse(DrainBase.has_numbers("abcdef"))

    def test_has_numbers_empty(self):
        self.assertFalse(DrainBase.has_numbers(""))

    def test_unlimited_clusters_uses_dict(self):
        model = Drain(max_clusters=None)
        self.assertIsInstance(model.id_to_cluster, dict)

    def test_limited_clusters_uses_cache(self):
        model = Drain(max_clusters=10)
        self.assertIsInstance(model.id_to_cluster, LogClusterCache)

    def test_clusters_property(self):
        model = Drain()
        model.add_log_message("hello")
        model.add_log_message("world")
        self.assertEqual(2, len(model.clusters))

    def test_get_content_as_tokens_basic(self):
        model = Drain()
        tokens = model.get_content_as_tokens("hello world")
        self.assertListEqual(["hello", "world"], list(tokens))

    def test_get_content_as_tokens_strips(self):
        model = Drain()
        tokens = model.get_content_as_tokens("  hello  ")
        self.assertListEqual(["hello"], list(tokens))

    def test_get_content_as_tokens_extra_delimiters(self):
        model = Drain(extra_delimiters=["_", "-"])
        tokens = model.get_content_as_tokens("hello_world-test")
        self.assertListEqual(["hello", "world", "test"], list(tokens))

    def test_get_total_cluster_size(self):
        model = Drain()
        model.add_log_message("a b c")
        model.add_log_message("a b d")
        model.add_log_message("x y z")
        self.assertEqual(3, model.get_total_cluster_size())

    def test_get_clusters_ids_for_seq_len_existing(self):
        model = Drain()
        model.add_log_message("a b c")
        ids = model.get_clusters_ids_for_seq_len(3)
        self.assertGreater(len(ids), 0)

    def test_get_clusters_ids_for_seq_len_nonexistent(self):
        model = Drain()
        model.add_log_message("a b c")
        ids = model.get_clusters_ids_for_seq_len(99)
        self.assertEqual(0, len(ids))

    def test_fast_match_no_clusters(self):
        model = Drain()
        result = model.fast_match([], ["a", "b"], 0.5, False)
        self.assertIsNone(result)

    def test_fast_match_skips_evicted_clusters(self):
        model = Drain(max_clusters=1)
        model.add_log_message("a b c")
        model.add_log_message("x y z")
        result = model.fast_match([1], ["a", "b", "c"], 1.0, False)
        self.assertIsNone(result)


class DrainTest(unittest.TestCase):
    def test_add_shorter_than_depth_message(self):
        model = Drain(depth=4)
        res = model.add_log_message("hello")
        print(res[1])
        print(res[0])
        self.assertEqual(res[1], "cluster_created")

        res = model.add_log_message("hello")
        print(res[1])
        print(res[0])
        self.assertEqual(res[1], "none")

        res = model.add_log_message("otherword")
        print(res[1])
        print(res[0])
        self.assertEqual(res[1], "cluster_created")

        self.assertEqual(2, len(model.id_to_cluster))

    def test_add_log_message(self):
        model = Drain()
        entries = str.splitlines(
            """
            Dec 10 07:07:38 LabSZ sshd[24206]: input_userauth_request: invalid user test9 [preauth]
            Dec 10 07:08:28 LabSZ sshd[24208]: input_userauth_request: invalid user webmaster [preauth]
            Dec 10 09:12:32 LabSZ sshd[24490]: Failed password for invalid user ftpuser from 0.0.0.0 port 62891 ssh2
            Dec 10 09:12:35 LabSZ sshd[24492]: Failed password for invalid user pi from 0.0.0.0 port 49289 ssh2
            Dec 10 09:12:44 LabSZ sshd[24501]: Failed password for invalid user ftpuser from 0.0.0.0 port 60836 ssh2
            Dec 10 07:28:03 LabSZ sshd[24245]: input_userauth_request: invalid user pgadmin [preauth]
            """
        )
        expected = str.splitlines(
            """
            Dec 10 07:07:38 LabSZ sshd[24206]: input_userauth_request: invalid user test9 [preauth]
            Dec 10 <*> LabSZ <*> input_userauth_request: invalid user <*> [preauth]
            Dec 10 09:12:32 LabSZ sshd[24490]: Failed password for invalid user ftpuser from 0.0.0.0 port 62891 ssh2
            Dec 10 <*> LabSZ <*> Failed password for invalid user <*> from 0.0.0.0 port <*> ssh2
            Dec 10 <*> LabSZ <*> Failed password for invalid user <*> from 0.0.0.0 port <*> ssh2
            Dec 10 <*> LabSZ <*> input_userauth_request: invalid user <*> [preauth]
            """
        )
        actual = []

        for entry in entries:
            cluster, change_type = model.add_log_message(entry)
            actual.append(cluster.get_template())

        self.assertListEqual(list(map(str.strip, expected)), actual)
        self.assertEqual(8, model.get_total_cluster_size())

    def test_add_log_message_sim_75(self):
        """When `sim_th` is set to 75% then only certain log entries match.

        In this test similarity threshold is set to 75% which makes the model
        less aggressive in grouping entries into clusters. In particular, it
        only finds clusters for "Failed password" entries.
        """
        model = Drain(
            depth=4,
            sim_th=0.75,
            max_children=100,
        )
        entries = str.splitlines(
            """
            Dec 10 07:07:38 LabSZ sshd[24206]: input_userauth_request: invalid user test9 [preauth]
            Dec 10 07:08:28 LabSZ sshd[24208]: input_userauth_request: invalid user webmaster [preauth]
            Dec 10 09:12:32 LabSZ sshd[24490]: Failed password for invalid user ftpuser from 0.0.0.0 port 62891 ssh2
            Dec 10 09:12:35 LabSZ sshd[24492]: Failed password for invalid user pi from 0.0.0.0 port 49289 ssh2
            Dec 10 09:12:44 LabSZ sshd[24501]: Failed password for invalid user ftpuser from 0.0.0.0 port 60836 ssh2
            Dec 10 07:28:03 LabSZ sshd[24245]: input_userauth_request: invalid user pgadmin [preauth]
            """
        )
        expected = str.splitlines(
            """
            Dec 10 07:07:38 LabSZ sshd[24206]: input_userauth_request: invalid user test9 [preauth]
            Dec 10 07:08:28 LabSZ sshd[24208]: input_userauth_request: invalid user webmaster [preauth]
            Dec 10 09:12:32 LabSZ sshd[24490]: Failed password for invalid user ftpuser from 0.0.0.0 port 62891 ssh2
            Dec 10 <*> LabSZ <*> Failed password for invalid user <*> from 0.0.0.0 port <*> ssh2
            Dec 10 <*> LabSZ <*> Failed password for invalid user <*> from 0.0.0.0 port <*> ssh2
            Dec 10 07:28:03 LabSZ sshd[24245]: input_userauth_request: invalid user pgadmin [preauth]
            """
        )
        actual = []

        for entry in entries:
            cluster, change_type = model.add_log_message(entry)
            actual.append(cluster.get_template())

        self.assertListEqual(list(map(str.strip, expected)), actual)
        self.assertEqual(8, model.get_total_cluster_size())

    def test_max_clusters(self):
        """Verify model respects the max_clusters option.

        Key difference between this and other tests is that with `max_clusters`
        set to 1 model is capable of keeping track of a single cluster at a
        time. Consequently, when log stream switched form the A format to the B
        and back model doesn't recognize it and returnes a new template with no
        slots.
        """
        model = Drain(max_clusters=1)
        entries = str.splitlines(
            """
            A format 1
            A format 2
            B format 1
            B format 2
            A format 3
            """
        )
        expected = str.splitlines(
            """
            A format 1
            A format <*>
            B format 1
            B format <*>
            A format 3
            """
        )
        actual = []

        for entry in entries:
            cluster, change_type = model.add_log_message(entry)
            actual.append(cluster.get_template())

        self.assertListEqual(list(map(str.strip, expected)), actual)
        self.assertEqual(1, model.get_total_cluster_size())

    def test_max_clusters_lru_multiple_leaf_nodes(self):
        """When all templates end up in different nodes and the max number of
        clusters is reached, then clusters are removed according to the lru
        policy.
        """
        model = Drain(max_clusters=2, depth=4, param_str="*")  # sim_th=0.75
        entries = [
            "A A A",
            "A A B",
            "B A A",
            "B A B",
            "C A A",
            "C A B",
            "B A A",
            "A A A",
        ]
        expected = [
            # lru: []
            "A A A",
            # lru: ["A A A"]
            "A A *",
            # lru: ["A A *"]
            "B A A",
            # lru: ["B A A", "A A *"]
            "B A *",
            # lru: ["B A *", "A A *"]
            "C A A",
            # lru: ["C A A", "B A *"]
            "C A *",
            # lru: ["C A *", "B A *"]
            "B A *",
            # Message "B A A" was normalized because the template "B A *" is
            # still present in the cache.
            # lru: ["B A *", "C A *"]
            "A A A",
            # Message "A A A" was not normalized because the template "C A A"
            # pushed out the template "A A *" from the cache.
            # lru: ["A A A", "C A *"]
        ]
        actual = []

        for entry in entries:
            cluster, _ = model.add_log_message(entry)
            actual.append(cluster.get_template())

        self.assertListEqual(list(map(str.strip, expected)), actual)
        self.assertEqual(4, model.get_total_cluster_size())

    def test_max_clusters_lru_single_leaf_node(self):
        """When all templates end up in the same leaf node and the max number of
        clusters is reached, then clusters are removed according to the lru
        policy.
        """
        model = Drain(max_clusters=2, depth=4, param_str="*")
        entries = [
            "A A A",
            "A A B",
            "A B A",
            "A B B",
            "A C A",
            "A C B",
            "A B A",
            "A A A",
        ]
        expected = [
            # lru: []
            "A A A",
            # lru: ["A A A"]
            "A A *",
            # lru: ["A A *"]
            "A B A",
            # lru: ["B A A", "A A *"]
            "A B *",
            # lru: ["B A *", "A A *"]
            "A C A",
            # lru: ["C A A", "B A *"]
            "A C *",
            # lru: ["C A *", "B A *"]
            "A B *",
            # Message "B A A" was normalized because the template "B A *" is
            # still present in the cache.
            # lru: ["B A *", "C A *"]
            "A A A",
            # Message "A A A" was not normalized because the template "C A A"
            # pushed out the template "A A *" from the cache.
            # lru: ["A A A", "C A *"]
        ]
        actual = []

        for entry in entries:
            cluster, _ = model.add_log_message(entry)
            actual.append(cluster.get_template())

        self.assertListEqual(list(map(str.strip, expected)), actual)
        # self.assertEqual(5, model.get_total_cluster_size())

    def test_match_only(self):
        model = Drain()
        res = model.add_log_message("aa aa aa")
        print(res[0])

        res = model.add_log_message("aa aa bb")
        print(res[0])

        res = model.add_log_message("aa aa cc")
        print(res[0])

        res = model.add_log_message("xx yy zz")
        print(res[0])

        c: LogCluster = model.match("aa aa tt")
        self.assertEqual(1, c.cluster_id)

        c: LogCluster = model.match("xx yy zz")
        self.assertEqual(2, c.cluster_id)

        c: LogCluster = model.match("xx yy rr")
        self.assertIsNone(c)

        c: LogCluster = model.match("nothing")
        self.assertIsNone(c)

    def test_create_template(self):
        model = Drain(param_str="*")

        seq1 = ["aa", "bb", "dd"]
        seq2 = ["aa", "bb", "cc"]

        # test for proper functionality
        template = model.create_template(seq1, seq2)
        self.assertListEqual(["aa", "bb", "*"], template)

        template = model.create_template(seq1, seq1)
        self.assertListEqual(seq1, template)

        # Test for equal lengths input vectors
        self.assertRaises(AssertionError, model.create_template, seq1, ["aa"])

    def test_get_seq_distance_identical(self):
        model = Drain()
        sim, params = model.get_seq_distance(["a", "b"], ["a", "b"], False)
        self.assertAlmostEqual(1.0, sim)
        self.assertEqual(0, params)

    def test_get_seq_distance_completely_different(self):
        model = Drain()
        sim, params = model.get_seq_distance(["a", "b"], ["c", "d"], False)
        self.assertAlmostEqual(0.0, sim)
        self.assertEqual(0, params)

    def test_get_seq_distance_with_param_exclude(self):
        model = Drain()
        sim, params = model.get_seq_distance(
            ["a", "<*>"], ["a", "x"], include_params=False
        )
        self.assertAlmostEqual(0.5, sim)
        self.assertEqual(1, params)

    def test_get_seq_distance_with_param_include(self):
        model = Drain()
        sim, params = model.get_seq_distance(
            ["a", "<*>"], ["a", "x"], include_params=True
        )
        self.assertAlmostEqual(1.0, sim)
        self.assertEqual(1, params)

    def test_get_seq_distance_empty(self):
        model = Drain()
        sim, params = model.get_seq_distance([], [], False)
        self.assertAlmostEqual(1.0, sim)
        self.assertEqual(0, params)

    def test_add_empty_log_message(self):
        model = Drain()
        cluster, change_type = model.add_log_message("")
        self.assertEqual("cluster_created", change_type)
        self.assertEqual("", cluster.get_template())

    def test_add_empty_log_message_twice(self):
        model = Drain()
        model.add_log_message("")
        cluster, change_type = model.add_log_message("")
        self.assertEqual("none", change_type)

    def test_match_never_strategy(self):
        model = Drain()
        model.add_log_message("hello world")
        result = model.match("hello world", full_search_strategy="never")
        self.assertIsNotNone(result)

    def test_match_always_strategy(self):
        model = Drain()
        model.add_log_message("hello world")
        result = model.match("hello world", full_search_strategy="always")
        self.assertIsNotNone(result)

    def test_match_fallback_strategy(self):
        model = Drain()
        model.add_log_message("hello world")
        result = model.match("hello world", full_search_strategy="fallback")
        self.assertIsNotNone(result)

    def test_match_invalid_strategy_raises(self):
        model = Drain()
        with self.assertRaises(AssertionError):
            model.match("hello", full_search_strategy="invalid")

    def test_match_no_match_returns_none(self):
        model = Drain()
        model.add_log_message("hello world")
        result = model.match(
            "completely different message here", full_search_strategy="never"
        )
        self.assertIsNone(result)

    def test_print_tree(self):
        model = Drain()
        model.add_log_message("hello world")
        model.add_log_message("hello earth")
        sio = io.StringIO()
        model.print_tree(file=sio)
        sio.seek(0)
        output = sio.read()
        self.assertIn("<root>", output)
        self.assertIn("<L=2>", output)

    def test_print_tree_max_clusters(self):
        model = Drain()
        for i in range(10):
            model.add_log_message(f"msg{i} content")
        sio = io.StringIO()
        model.print_tree(file=sio, max_clusters=2)
        sio.seek(0)
        output = sio.read()
        self.assertIn("<root>", output)

    def test_add_log_message_cluster_template_changed(self):
        model = Drain()
        model.add_log_message("hello world")
        cluster, change_type = model.add_log_message("hello earth")
        self.assertEqual("cluster_template_changed", change_type)
        self.assertEqual("hello <*>", cluster.get_template())

    def test_parametrize_numeric_tokens_disabled(self):
        model = Drain(parametrize_numeric_tokens=False)
        model.add_log_message("error code 123")
        model.add_log_message("error code 456")
        cluster, _ = model.add_log_message("error code 789")
        self.assertIn("<*>", cluster.get_template())

    def test_custom_param_str(self):
        model = Drain(param_str="??")
        model.add_log_message("hello world")
        cluster, _ = model.add_log_message("hello earth")
        self.assertEqual("hello ??", cluster.get_template())
