# Parallel model calls (run concurrently)

model a {
  system: "Reply with exactly one word."
  temperature: 0.0
}

model b {
  system: "Reply with exactly one word."
  temperature: 0.0
}

parallel {
  x = a("Say hello")
  y = b("Say world")
}

print x
print y
print "conf x:", conf(x), "conf y:", conf(y)
