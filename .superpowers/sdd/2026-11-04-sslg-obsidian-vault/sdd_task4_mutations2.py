"""Mutation harness for the four Task 4 test guards added after the review.

Each mutation simulates a regression the review measured as surviving all nine
tests. A guard is real only if the suite fails under its mutation.
"""
import io
import unittest

import tools.tests.test_sslg_navigation as T

RESULTS = []


def run(label):
    suite = unittest.TestLoader().loadTestsFromModule(T)
    result = unittest.TextTestRunner(verbosity=0, stream=io.StringIO()).run(suite)
    caught = len(result.errors) + len(result.failures)
    RESULTS.append((label, caught))


def restore():
    import importlib
    importlib.reload(T)


ORIG_QUEUE = T.render_review_queue
ORIG_TIMELINE = T.render_timeline
ORIG_HOME = T.render_home


def only_first_reason(data):
    text = ORIG_QUEUE(data)
    out, seen_block = [], 0
    for line in text.splitlines():
        if line.startswith("  - "):
            seen_block += 1
            if seen_block > 1:
                continue
        else:
            seen_block = 0
        out.append(line)
    return "\n".join(out) + "\n"


def status_only(data):
    stripped = {**data,
                "records": [{**r, "review_reasons": []} for r in data["records"]
                            if r.get("status") != "needs-review"] + [r for r in data["records"]
                                                                     if r.get("status") == "needs-review"],
                "activities": [{**a, "review_reasons": []} for a in data["activities"]
                               if a.get("status") != "needs-review"] + [a for a in data["activities"]
                                                                        if a.get("status") == "needs-review"]}
    return ORIG_QUEUE(stripped)


def unsorted_timeline(data):
    text = ORIG_TIMELINE(data)
    rows = [line for line in text.splitlines() if line.startswith("| 20")]
    reordered = iter(sorted(rows, reverse=True))
    return "\n".join(next(reordered) if line.startswith("| 20") else line for line in text.splitlines()) + "\n"


def home_without_member_links(data):
    return "\n".join(line for line in ORIG_HOME(data).splitlines()
                     if "[[03 Governance/" not in line and "[[04 External" not in line) + "\n"


run("baseline")

T.render_review_queue = only_first_reason
run("truncate to first reason")
T.render_review_queue = ORIG_QUEUE

T.render_review_queue = status_only
run("status-only queue inclusion")
T.render_review_queue = ORIG_QUEUE

T.render_timeline = unsorted_timeline
run("unsorted timeline rows")
T.render_timeline = ORIG_TIMELINE

T.render_home = home_without_member_links
run("home collection member links deleted")
T.render_home = ORIG_HOME

for label, caught in RESULTS:
    print(f"{label}: failing tests = {caught}")
