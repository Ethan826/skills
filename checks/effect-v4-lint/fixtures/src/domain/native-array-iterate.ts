const xs: ReadonlyArray<number> = [1, 2]
const positive = (n: number): boolean => n > 0
const add = (a: number, b: number): number => a + b
const pair = (n: number): ReadonlyArray<number> => [n, n]
const ignore = (n: number): void => {
  positive(n)
}

export const all = [
  xs.map(add.bind(null, 1)),
  xs.filter(positive),
  xs.some(positive),
  xs.every(positive),
  xs.find(positive),
  xs.findIndex(positive),
  xs.findLast(positive),
  xs.findLastIndex(positive),
  xs.reduce(add, 0),
  xs.reduceRight(add, 0),
  xs.flatMap(pair),
  [xs].flat(),
  xs.forEach(ignore),
]
