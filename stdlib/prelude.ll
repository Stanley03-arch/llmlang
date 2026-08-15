# LlmLang standard prelude
# Usage: import "prelude.ll"

def clamp(x, lo, hi) {
  if conf(x) > 0 {
    return x
  } else {
    return lo
  }
}

def sum_list(xs) {
  s = 0
  for x in xs {
    s = s + x
  }
  return s
}

def count_items(xs) {
  return len(xs)
}
