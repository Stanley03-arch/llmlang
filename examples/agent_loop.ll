# Simple agent-style loop with tools + confidence

model agent {
  system: "You solve small problems. Prefer short answers."
  temperature: 0.2
}

goal = "Compute 12 * 8 and report only the number"
answer = agent(goal)
print "model said:", answer, "conf=", conf(answer)

if conf(answer) < 0.7 {
  # fall back to deterministic tool
  t = calc("12 * 8")
  print "tool fallback:", t
} else {
  print "accepted model answer"
}

# ternary
label = conf(answer) > 0.7 ? "trusted" : "verify"
print "label:", label
