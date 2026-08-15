# Named schema validation on JSON mode models

model extractor {
  system: "Extract structured answers as JSON with answer and confidence."
  mode: "json"
  schema: "answer"
  min_conf: 0.5
  max_retries: 1
}

r = extractor("What is the capital of Kenya? Put the city in answer.")
print "raw:", r
print "conf:", conf(r)
print "schema_ok:", schema_ok(r)
print "data:", json(r)

model planner {
  system: "Produce a plan JSON."
  mode: "json"
  schema: "plan"
}

p = planner("Plan learning LlmLang in 2 steps")
print "plan:", json(p)
print "plan schema_ok:", schema_ok(p)
