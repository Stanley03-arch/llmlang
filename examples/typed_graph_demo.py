#!/usr/bin/env python3
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library.typed_ports import demo_typed_graph, graph_from_dense
from library.durable import run_dense_durable

print("=== typed graph demo ===")
print(json.dumps(demo_typed_graph(), indent=2))
print("\n=== from dense ===")
g = graph_from_dense("T project_stats path=. | T search_code query=CallResult | L summarize")
print(g.to_mermaid())
print(g.check())
print("\n=== durable ===")
print(json.dumps(run_dense_durable("T calculator expression=2+2 | T now"), indent=2, default=str))
