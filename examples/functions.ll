# User-defined functions

def double(x) {
  return x * 2
}

def greet(name) {
  print "Hello,", name
  return name
}

print double(21)
greet("Stanley")

xs = [1, 2, 3, 4]
s = 0
for x in xs {
  s = s + x
}
print "sum =", s
print "len =", len(xs)
