# Error handling

try {
  assert 1 == 2, "one is not two"
  print "should not print"
} catch err {
  print "handled assert:", err
}

xs = [10, 20, 30]
print "xs[1] =", xs[1]

try {
  print xs[99]
} catch err {
  print "index error:", err
}

print "still running"
