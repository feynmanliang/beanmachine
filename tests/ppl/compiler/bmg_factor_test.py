# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import unittest

from beanmachine.ppl.compiler.bm_graph_builder import BMGraphBuilder
from beanmachine.ppl.compiler.gen_bmg_cpp import to_bmg_cpp
from beanmachine.ppl.compiler.gen_bmg_graph import to_bmg_graph
from beanmachine.ppl.compiler.gen_bmg_python import to_bmg_python
from beanmachine.ppl.compiler.gen_dot import to_dot


def tidy(s: str) -> str:
    return "\n".join(c.strip() for c in s.strip().split("\n")).strip()


class BMGFactorTest(unittest.TestCase):
    def test_bmg_factor(self) -> None:

        bmg = BMGraphBuilder()
        pos1 = bmg.add_pos_real(2.0)
        real1 = bmg.add_real(3.0)
        prob1 = bmg.add_probability(0.4)
        dist1 = bmg.add_normal(real1, pos1)
        x = bmg.add_sample(dist1)
        x_sq = bmg.add_multiplication(x, x)
        bmg.add_exp_product(x, prob1, x_sq)
        bmg.add_observation(x, 7.0)
        observed = to_dot(bmg, label_edges=False)
        expected = """
digraph "graph" {
  N0[label=3.0];
  N1[label=2.0];
  N2[label=Normal];
  N3[label=Sample];
  N4[label=0.4];
  N5[label="*"];
  N6[label=ExpProduct];
  N7[label="Observation 7.0"];
  N0 -> N2;
  N1 -> N2;
  N2 -> N3;
  N3 -> N5;
  N3 -> N5;
  N3 -> N6;
  N3 -> N7;
  N4 -> N6;
  N5 -> N6;
}
"""
        self.maxDiff = None
        self.assertEqual(expected.strip(), observed.strip())

        observed = to_bmg_graph(bmg).graph.to_string()
        expected = """
Node 0 type 1 parents [ ] children [ 2 ] real 3
Node 1 type 1 parents [ ] children [ 2 ] positive real 2
Node 2 type 2 parents [ 0 1 ] children [ 3 ] unknown
Node 3 type 3 parents [ 2 ] children [ 5 5 6 ] real 7
Node 4 type 1 parents [ ] children [ 6 ] probability 0.4
Node 5 type 3 parents [ 3 3 ] children [ 6 ] real 0
Node 6 type 4 parents [ 3 4 5 ] children [ ] unknown
"""
        self.assertEqual(tidy(expected), tidy(observed))

        observed = to_bmg_python(bmg).code

        expected = """
from beanmachine import graph
from torch import tensor
g = graph.Graph()
n0 = g.add_constant_real(3.0)
n1 = g.add_constant_pos_real(2.0)
n2 = g.add_distribution(
  graph.DistributionType.NORMAL,
  graph.AtomicType.REAL,
  [n0, n1],
)
n3 = g.add_operator(graph.OperatorType.SAMPLE, [n2])
n4 = g.add_constant_probability(0.4)
n5 = g.add_operator(graph.OperatorType.MULTIPLY, [n3, n3])
n6 = g.add_factor(
  graph.FactorType.EXP_PRODUCT,
  [n3, n4, n5],
)
g.observe(n3, 7.0)
"""
        self.assertEqual(expected.strip(), observed.strip())

        observed = to_bmg_cpp(bmg).code

        expected = """
graph::Graph g;
uint n0 = g.add_constant_real(3.0);
uint n1 = g.add_constant_pos_real(2.0);
uint n2 = g.add_distribution(
  graph::DistributionType::NORMAL,
  graph::AtomicType::REAL,
  std::vector<uint>({n0, n1}));
uint n3 = g.add_operator(
  graph::OperatorType::SAMPLE, std::vector<uint>({n2}));
uint n4 = g.add_constant_probability(0.4);
uint n5 = g.add_operator(
  graph::OperatorType::MULTIPLY, std::vector<uint>({n3, n3}));
uint n6 = g.add_factor(
  graph::FactorType::EXP_PRODUCT,
  std::vector<uint>({n3, n4, n5}));
g.observe(n3, 7.0);
"""
        self.assertEqual(expected.strip(), observed.strip())
