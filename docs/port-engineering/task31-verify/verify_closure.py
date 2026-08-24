import sys, json, hashlib
sys.path.insert(0, '.')
from tools.glslcpp import check_corpus, check_semantics

repo = check_corpus._ROOT.resolve()
report = check_semantics.semantic_report(repo)
print('body_success', report.get('body_success'))

# Need typed IR for caustic. Let's look at how check_semantics builds per-program typed objects.
