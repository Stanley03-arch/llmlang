# LlmLang Language Reference (v0.2)

## Models

```ll
model name {
  system: "role instructions"
  temperature: 0.2
  mode: "free"
  tools: ["calc" "now"]
}
result = name("your prompt")
if conf(result) > 0.85 {
  print "accepted"
}
```

## Control flow

```ll
if cond { ... } else { ... }
while cond { ... }
for x in xs { ... }
try { ... } catch err { ... }
parallel {
  a = m1("one")
  b = m2("two")
}
```

## Tools

```ll
r = calc("12 * 8")
t = now("%Y-%m-%d")
j = json_parse('{"a": 1}')
print tools()   # list tool names
```

## Collections

```ll
xs = [1, 2, 3]
xs[0] = 99
person = {"name": "Ada", "id": 1}
print person["name"]
for i in range(3) { print i }
```

## Other

```ll
def double(x) { return x * 2 }
label = conf(r) > 0.7 ? "ok" : "retry"
print fmt("hi {}", "world")
import "stdlib/prelude.ll"
```

See VISION.md and examples/ for more.
