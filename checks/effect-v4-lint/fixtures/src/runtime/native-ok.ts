// Outside the core layers the native-method and null-check bans do not
// apply (the Runtime adapts native APIs).
const double = (n: number): number => n * 2

export const doubled = (xs: ReadonlyArray<number>): ReadonlyArray<number> =>
  xs.map(double)

export const missing = (x: number | undefined): boolean => x === undefined
