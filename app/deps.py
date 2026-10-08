# app/deps.py
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

from app.graph.builder import build_graph

import os
os.makedirs("data", exist_ok=True)
_conn = sqlite3.connect("data/checkpoints.db", check_same_thread=False)

_checkpointer = SqliteSaver(_conn)
graph = build_graph(checkpointer=_checkpointer)