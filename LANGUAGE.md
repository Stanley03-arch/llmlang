# LlmLang Language Reference (v0.3)

## Models + JSON mode

```ll
model planner {
  system: "Respond with JSON only."
  mode: "json"
  temperature: 0.1
}
r = planner("Plan X in 3 steps")
data = json(r)
```

## Memory + chat

```ll
mem = memory("You are helpful.")
r1 = chat("buddy", "My name is Ada", mem)
r2 = chat("buddy", "What is my name?", mem)
```

Or pass memory as second arg to a model call:

```ll
r = buddy("hello", mem)
```

## plan / critic

```ll
p = plan("thinker", "Ship a product")
c = critic("thinker", draft, "clarity")
```

## Loops

```ll
for i in range(10) {
  if i == 3 { continue }
  if i == 7 { break }
  print i
}
```

See examples/ for full demos.
