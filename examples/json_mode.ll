# Structured JSON mode

model planner {
  system: "You produce structured plans as JSON."
  temperature: 0.1
  mode: "json"
}

r = planner("Plan how to learn LlmLang in 3 steps")
print "raw:", r
print "conf:", conf(r)

data = json(r)
print "parsed:", data

if data {
  print "goal-ish keys available"
}
