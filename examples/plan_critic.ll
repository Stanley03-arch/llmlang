# plan() + critic() helpers

model thinker {
  system: "You are careful and structured."
  temperature: 0.2
}

p = plan("thinker", "Write a haiku about coding")
print "plan:", p
print "plan json:", json(p)

# produce some content then critique it
model writer {
  system: "You write short creative text."
  mode: "free"
}
draft = writer("Write a one-line slogan for LlmLang")
print "draft:", draft

c = critic("thinker", draft, "clarity and originality")
print "critique:", c
print "critique json:", json(c)
