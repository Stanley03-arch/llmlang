# Tools demo

print "Available tools:", tools()

r = calc("17 * 3 + 1")
print "calc:", r

t = now("%Y-%m-%d")
print "today (UTC):", t

msg = upper("hello llmlang")
print msg

j = json_parse('{"name": "Stanley", "score": 42}')
print "json ok?", j
print "parsed:", j

# try/catch around a bad calc
try {
  bad = calc("not math")
  print bad
} catch err {
  print "caught:", err
}
