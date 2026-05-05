# SPDX-License-Identifier: MIT

import unittest

from drain3.drain import LogCluster
from drain3.jaccard_drain import JaccardDrain


class JaccardDrainSeqDistanceTest(unittest.TestCase):
    def test_identical_sequences(self):
        model = JaccardDrain()
        sim, params = model.get_seq_distance(["a", "b"], ["a", "b"], False)
        self.assertAlmostEqual(1.0, sim)
        self.assertEqual(0, params)

    def test_empty_sequences(self):
        model = JaccardDrain()
        sim, params = model.get_seq_distance([], [], False)
        self.assertAlmostEqual(1.0, sim)
        self.assertEqual(0, params)

    def test_no_overlap(self):
        model = JaccardDrain()
        sim, params = model.get_seq_distance(["a", "b"], ["c", "d"], False)
        self.assertAlmostEqual(0.0, sim)
        self.assertEqual(0, params)

    def test_with_param_str_include(self):
        model = JaccardDrain()
        sim, params = model.get_seq_distance(
            ["a", "<*>"], ["a", "x"], include_params=True
        )
        self.assertEqual(1, params)
        self.assertGreater(sim, 0)

    def test_with_param_str_exclude(self):
        model = JaccardDrain()
        sim, params = model.get_seq_distance(
            ["a", "<*>"], ["a", "x"], include_params=False
        )
        self.assertEqual(1, params)

    def test_gain_caps_at_one(self):
        model = JaccardDrain()
        sim, _ = model.get_seq_distance(["a"], ["a"], False)
        self.assertLessEqual(sim, 1.0)


class JaccardDrainCreateTemplateTest(unittest.TestCase):
    def test_same_length_different_tokens(self):
        model = JaccardDrain(param_str="*")
        result = model.create_template(["a", "b", "c"], ["a", "x", "c"])
        self.assertListEqual(["a", "*", "c"], result)

    def test_same_length_identical(self):
        model = JaccardDrain(param_str="*")
        result = model.create_template(["a", "b"], ["a", "b"])
        self.assertListEqual(["a", "b"], result)

    def test_different_length_seq1_longer(self):
        model = JaccardDrain(param_str="*")
        result = model.create_template(["a", "b", "c", "d"], ["a", "c"])
        self.assertIn("a", result)
        self.assertIn("c", result)
        self.assertEqual(4, len(result))

    def test_different_length_seq2_longer(self):
        model = JaccardDrain(param_str="*")
        result = model.create_template(["a"], ["a", "b", "c"])
        self.assertEqual(3, len(result))


class JaccardDrainMatchTest(unittest.TestCase):
    def test_match_never(self):
        model = JaccardDrain()
        model.add_log_message("hello world test")
        result = model.match("hello world test", full_search_strategy="never")
        self.assertIsNotNone(result)

    def test_match_always(self):
        model = JaccardDrain()
        model.add_log_message("hello world test")
        result = model.match("hello world test", full_search_strategy="always")
        self.assertIsNotNone(result)

    def test_match_fallback(self):
        model = JaccardDrain()
        model.add_log_message("hello world test")
        result = model.match("hello world test", full_search_strategy="fallback")
        self.assertIsNotNone(result)

    def test_match_invalid_strategy_raises(self):
        model = JaccardDrain()
        with self.assertRaises(AssertionError):
            model.match("hello", full_search_strategy="invalid")

    def test_match_no_match(self):
        model = JaccardDrain()
        model.add_log_message("aaa bbb ccc")
        result = model.match("xxx yyy zzz", full_search_strategy="never")
        self.assertIsNone(result)


class JaccardDrainEmptyLogTest(unittest.TestCase):
    def test_add_empty_message(self):
        model = JaccardDrain()
        cluster, change_type = model.add_log_message("")
        self.assertEqual("cluster_created", change_type)
        self.assertEqual("", cluster.get_template())

    def test_add_empty_message_twice(self):
        model = JaccardDrain()
        model.add_log_message("")
        cluster, change_type = model.add_log_message("")
        self.assertEqual("none", change_type)


class DrainTest(unittest.TestCase):
    def test_add_shorter_than_depth_message(self):
        model = JaccardDrain(depth=4)
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
        model = JaccardDrain()
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
        model = JaccardDrain(
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
        model = JaccardDrain(max_clusters=1)
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
        model = JaccardDrain(max_clusters=2, depth=4, param_str="*")  # sim_th=0.75
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
            print(cluster.get_template())

        self.assertListEqual(list(map(str.strip, expected)), actual)
        self.assertEqual(4, model.get_total_cluster_size())

    def test_max_clusters_lru_single_leaf_node(self):
        """When all templates end up in the same leaf node and the max number of
        clusters is reached, then clusters are removed according to the lru
        policy.
        """
        model = JaccardDrain(max_clusters=2, depth=4, param_str="*")
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
        model = JaccardDrain()
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

    def test_match_token_with_different_length(self):
        model = JaccardDrain()
        res = model.add_log_message("check pass; user unknown")
        print(res[0])

        res = model.add_log_message("check pass; user Lisa")
        print(res[0])

        res = model.add_log_message("check pass; user li Sa")
        print(res[0])

        res = model.add_log_message("session opened for user cyrus by (uid=0)")
        print(res[0])

        res = model.add_log_message("session closed for user cyrus")
        print(res[0])

        c: LogCluster = model.match("check pass; user boris")
        self.assertEqual(1, c.cluster_id)

        c: LogCluster = model.match("session opened for user cyrus by (uid=1)")
        self.assertEqual(2, c.cluster_id)

        c: LogCluster = model.match("nothing")
        self.assertIsNone(c)


if __name__ == "__main__":
    pass
