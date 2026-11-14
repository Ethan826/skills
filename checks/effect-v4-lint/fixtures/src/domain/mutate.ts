export const grow = (xs: Array<number>): ReadonlyArray<number> => {
  xs.push(1)
  return xs
}
