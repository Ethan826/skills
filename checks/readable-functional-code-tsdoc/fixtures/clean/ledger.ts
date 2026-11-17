// Ledger fixture: every export documented, in each spelling the gate checks.
import { helper } from "./helper.ts"

/** The number of entries a page holds. */
export const pageSize = 20

/** Adds two amounts, in cents. */
export const add = (a: number, b: number): number => helper(a) + b

/** A ledger entry: an amount in cents and its memo. */
export interface Entry {
  readonly cents: number
  readonly memo: string
}

/** A ledger: entries in the order they were made. */
export type Ledger = ReadonlyArray<Entry>

/** Whether an entry is a credit or a debit. */
export enum Side {
  Credit,
  Debit,
}

/** Raised when an entry's amount is not a whole number of cents. */
export class FractionalCents {}

/** Sums a ledger, in cents. */
export function total(ledger: Ledger): number {
  return ledger.reduce((sum, entry) => sum + entry.cents, 0)
}

const unexported = 3

/** A private count, exported by name below. */
const listed = unexported

export { listed }
export { helper } from "./helper.ts"
