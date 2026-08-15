# Agent-style flow that leaves a rich execution trace

model agent {
  system: "You solve small problems. Prefer short answers."
  temperature: 0.2
  min_conf: 0.4
  max_retries: 1
}

goal = "Compute 12 * 8"
answer = agent(goal)
print "model:", answer, "conf=", conf(answer)

if conf(answer) < 0.7 {
  t = calc("12 * 8")
  print "tool fallback:", t
} else {
  print "accepted model answer"
}

# structured critique
model critic_m {
  system: "You critique briefly."
  mode: "json"
  schema: "critique"
}
c = critic("critic_m", answer, "numeric correctness")
print "critique:", json(c)
