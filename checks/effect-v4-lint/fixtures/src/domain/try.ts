export const safe = (): number => {
  try {
    return 1
  } catch {
    return 0
  }
}
