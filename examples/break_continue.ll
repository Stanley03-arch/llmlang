# break / continue

print "--- continue ---"
for i in range(5) {
  if i == 2 {
    continue
  }
  print i
}

print "--- break ---"
for i in range(10) {
  if i == 4 {
    break
  }
  print i
}

print "done"
