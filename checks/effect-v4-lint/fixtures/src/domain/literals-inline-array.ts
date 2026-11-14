import { Schema } from "effect"

export const Suit = Schema.Literals(["hearts", "spades"])
export const Level = Schema.Literals([1, 2, 3])
