import { Schema } from "effect"
import { double } from "./ok.ts"

export const Count = Schema.Number
export const decodeCount = Schema.decodeUnknownResult(Count)
export const twice = (n: number): number => double(n) + double(0)
