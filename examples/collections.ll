# Lists, dicts, indexing, loops

xs = [1, 2, 3, 4, 5]
print "len", len(xs)
print "first", xs[0]
print "last", xs[4]

xs[0] = 99
print "mutated", xs[0]

s = 0
for x in xs {
  s = s + x
}
print "sum", s

person = {"name": "Stanley", "role": "builder"}
print person["name"]
print "keys:", keys(person)

for i in range(3) {
  print "i=", i
}

msg = fmt("Hello {}, score={}", "world", 100)
print msg
