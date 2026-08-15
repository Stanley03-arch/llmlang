# Shared agent-oriented helpers (models must be declared by the host program)

def accept_or_retry(answer, threshold) {
  if conf(answer) > threshold {
    return answer
  } else {
    print "retry suggested"
    return answer
  }
}
