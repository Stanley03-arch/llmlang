# Pure subset — runs on the bytecode VM
x = 1 + 2 * 3
print x
ys = [10, 20, 30]
print ys[0]
print ys[2]
n = 0
while n < 4 {
  print n
  n = n + 1
}
if n == 4 {
  print "loop done"
} else {
  print "unexpected"
}
