package extension
inline fun <T> T.applyIf(condition : Boolean, block : T.() -> T) : T {
  if (condition) {
    return block()
  } else {
    return this
  }
}