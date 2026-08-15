# min_conf + max_retries on the model, plus require()

model careful {
  system: "Answer briefly and accurately."
  temperature: 0.1
  mode: "free"
  min_conf: 0.5
  max_retries: 2
}

r = careful("What is 2 + 2?")
print "result:", r
print "conf:", conf(r)
print "schema_ok:", schema_ok(r)

# require() records a check into the trace
checked = require(r, 0.5, 1)
print "required conf ok at", conf(checked)
