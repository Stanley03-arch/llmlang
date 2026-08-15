# Confidence-based control flow example

model calc {
  system: "You are a precise calculator. Reply with only the final number."
  temperature: 0.0
  mode: "free"
}

answer = calc("What is 17 * 3?")
print "Answer:", answer
print "Confidence:", conf(answer)

if conf(answer) > 0.8 {
  print "High confidence — accepting result"
} else {
  print "Low confidence — would re-ask or use a tool in a fuller program"
}
