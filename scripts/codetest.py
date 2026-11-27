#!/usr/bin/env python3
"""Harder coding test for small models on the PS4.

usage: codetest.py <server-port> <label> <outdir>
Asks a running llama-server (OpenAI API, temp 0, thinking off) for three
functions, extracts the first ```python block, and runs hidden unit tests in a
subprocess with a timeout. Prints one line per task and a total.
"""
import json, os, re, subprocess, sys, tempfile, textwrap, time, urllib.request

PORT, LABEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)

TASKS = {
 "intervals": (
  "Write a Python function merge_intervals(intervals) that takes a list of [start, end] integer pairs "
  "(not necessarily sorted, start <= end) and returns a new list of merged, non-overlapping intervals "
  "sorted by start. Intervals that touch (e.g. [1,2] and [2,3]) must be merged. Do not modify the input. "
  "Reply with only one ```python code block.",
  """
cases = [
 ([], []),
 ([[1,3]], [[1,3]]),
 ([[1,3],[2,6],[8,10],[15,18]], [[1,6],[8,10],[15,18]]),
 ([[1,2],[2,3]], [[1,3]]),
 ([[5,7],[1,2],[3,4]], [[1,2],[3,4],[5,7]]),
 ([[1,10],[2,3],[4,5]], [[1,10]]),
 ([[6,8],[1,9],[2,4],[4,7]], [[1,9]]),
 ([[0,0],[0,0]], [[0,0]]),
 ([[-5,-1],[-2,3]], [[-5,3]]),
]
for inp, want in cases:
    orig = [list(x) for x in inp]
    got = [list(x) for x in merge_intervals(inp)]
    check(got == want and inp == orig, f"{inp} -> {got}, want {want}")
"""),
 "expr": (
  "Write a Python function eval_expr(s) that evaluates an arithmetic expression string containing "
  "non-negative integers, spaces, + - * /, unary minus, and parentheses, with normal precedence and "
  "left-to-right associativity. '/' is true division. Return a float or int. You must NOT use eval, exec, "
  "compile, or the ast module. Reply with only one ```python code block.",
  """
import math
cases = {"1 + 2": 3, "2 * 3 + 4": 10, "2 + 3 * 4": 14, "(2 + 3) * 4": 20, "10 - 4 - 3": 3,
         "8 / 4 / 2": 1, "-3 + 5": 2, "2 * -3": -6, "-(2 + 3) * 2": -10, " 7 ": 7,
         "((1))+((2)*(3))": 7, "1 - -1": 2, "100 / 8": 12.5, "3 - (4 - (5 - 6))": -2}
for s, want in cases.items():
    try: got = eval_expr(s)
    except Exception as e: got = repr(e)
    check(isinstance(got,(int,float)) and math.isclose(got, want), f"{s!r} -> {got}, want {want}")
"""),
 "lru": (
  "Write a Python class LRUCache with __init__(self, capacity), get(self, key) returning the value or -1, "
  "and put(self, key, value). When over capacity, evict the least recently used key. Both get and put "
  "count as a use. Reply with only one ```python code block.",
  """
c = LRUCache(2); c.put(1,1); c.put(2,2)
check(c.get(1) == 1, "get 1")
c.put(3,3); check(c.get(2) == -1, "2 evicted")
c.put(4,4); check(c.get(1) == -1, "1 evicted"); check(c.get(3) == 3, "3 kept"); check(c.get(4) == 4, "4 kept")
c = LRUCache(2); c.put(1,1); c.put(2,2); c.put(1,10); c.put(3,3)
check(c.get(1) == 10, "update counts as use + new value"); check(c.get(2) == -1, "2 evicted after update")
c = LRUCache(1); c.put(1,1); c.put(2,2); check(c.get(1) == -1 and c.get(2) == 2, "cap 1")
c = LRUCache(3)
for i in range(1000): c.put(i, i*i)
check(c.get(999) == 998001 and c.get(996) == -1, "bulk")
"""),
}

HARNESS = """
_pass = _fail = 0
def check(ok, msg):
    global _pass, _fail
    if ok: _pass += 1
    else:
        _fail += 1; print("FAIL", msg)
"""

def ask(prompt):
    body = {"messages": [{"role": "user", "content": prompt}], "temperature": 0, "max_tokens": 1500,
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    t = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=900))
    return r["choices"][0]["message"].get("content") or "", r.get("usage", {}), time.time() - t

total_p = total_n = 0
for name, (prompt, tests) in TASKS.items():
    text, usage, secs = ask(prompt)
    open(f"{OUT}/{LABEL}.{name}.txt", "w").write(text)
    m = re.search(r"```(?:python|py)?\n(.*?)```", text, re.S)
    code = m.group(1) if m else text
    banned = name == "expr" and re.search(r"\b(eval|exec|compile)\s*\(|\bimport ast\b|\bfrom ast\b", code)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code + "\n" + HARNESS + textwrap.dedent(tests) + "\nprint('SCORE', _pass, _pass + _fail)\n")
    try:
        p = subprocess.run([sys.executable, "-I", f.name], capture_output=True, text=True, timeout=20)
        out = p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        out = "TIMEOUT"
    os.unlink(f.name)
    n_tests = tests.count("check(") + (len(eval(tests.split("cases = ")[1].split("\nfor")[0])) - 1 if "cases = " in tests else 0)
    sm = re.search(r"SCORE (\d+) (\d+)", out)
    p_, n_ = (int(sm.group(1)), int(sm.group(2))) if sm else (0, n_tests)
    if banned: p_ = 0
    total_p += p_; total_n += n_
    first_fail = next((l for l in out.splitlines() if l.startswith(("FAIL", "Traceback", "TIMEOUT")) or "Error" in l), "")
    print(f"{LABEL:28s} {name:10s} {p_:2d}/{n_:<2d} {usage.get('completion_tokens','?'):>5} tok {secs:6.1f}s"
          f"{'  BANNED(eval/ast)' if banned else ''}  {first_fail[:90]}")
print(f"{LABEL:28s} TOTAL      {total_p}/{total_n}")
