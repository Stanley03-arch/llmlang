# LlmLang hello world

model greeter {
  system: "You are friendly and concise."
  temperature: 0.3
  mode: "free"
}

msg = greeter("Say hello to the world of LlmLang in one short sentence.")
print msg
print "confidence:", conf(msg)

if conf(msg) > 0.5 {
  print "Looks good!"
} else {
  print "Hmm, low confidence."
}
