# LlmLang error-handling examples (language level)

print "=== 1. Assert success ==="
assert 1 + 1 == 2, "math broken"
print "assert ok"

print "=== 2. try/catch around assert failure ==="
try {
  assert 1 == 2, "expected inequality demo"
  print "should not reach"
} catch err {
  print fmt("caught: {}", err)
}

print "=== 3. try/catch around bad index ==="
xs = [10, 20]
try {
  print xs[99]
} catch err {
  print fmt("index error handled: {}", err)
}

print "=== 4. Soft confidence branch (not an exception) ==="
model m { system: "brief" temperature: 0.1 }
ans = m("hello")
if conf(ans) > 0.95 {
  print "very high confidence"
} elif conf(ans) > 0.5 {
  print "acceptable confidence — proceed"
} else {
  print "low confidence — escalate"
}

print "=== 5. Safe recovery path ==="
try {
  val = py("1/0")
  print val
} catch err {
  print "python error recovered"
  val = 0
}
print fmt("val={}", val)

print "=== error_handling.ll complete ==="
