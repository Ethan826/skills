const parsed: unknown = JSON.parse("[1]")
const items: Array<number> = []
for (const n of [1, 2]) {
  items.push(n)
}
const double = (n: number): number => n * 2
export const doubled = items.map(double)
export const missing = parsed === undefined
export const all = [parsed, items]
