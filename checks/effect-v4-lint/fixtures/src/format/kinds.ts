// Canonical module of a vocabulary that only this Format decoder knows: wire
// tags live beside the decoder that owns them, not in Domain.
import { Record, Schema } from "effect"

export const Kinds = { Result: "result", Failure: "failure" } as const
export const Kind = Schema.Literals(Record.values(Kinds))
