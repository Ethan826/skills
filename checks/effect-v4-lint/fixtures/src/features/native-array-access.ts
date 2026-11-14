const xs: Array<number> = [3, 1, 2]

export const all = [
  xs.includes(1),
  xs.indexOf(1),
  xs.lastIndexOf(1),
  xs.slice(1),
  xs.concat([4]),
  xs.join(","),
  xs.sort(),
  xs.toSorted(),
  xs.reverse(),
  xs.toReversed(),
  xs.at(0),
  xs.fill(0),
  xs.splice(0, 1),
  xs.toSpliced(0, 1),
]
