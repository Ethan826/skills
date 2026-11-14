const xs: ReadonlyArray<number> = [1, 2]
const double = (n: number): number => n * 2
const { filter } = xs

export const all = [xs["map"](double), filter, [].map.call(xs, double)]
