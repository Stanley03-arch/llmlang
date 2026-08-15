# Multi-turn memory / chat

model buddy {
  system: "You are a friendly assistant. Keep answers short."
  temperature: 0.3
}

mem = memory("You are a friendly assistant. Keep answers short.")

r1 = chat("buddy", "My name is Stanley", mem)
print "turn1:", r1

r2 = chat("buddy", "What is my name?", mem)
print "turn2:", r2
print "confidence:", conf(r2)
