export const sum = (xs: ReadonlyArray<number>): number => {
  const total = [0]
  for (const x of xs) {
    total.push(x)
  }
  return total.length
}
