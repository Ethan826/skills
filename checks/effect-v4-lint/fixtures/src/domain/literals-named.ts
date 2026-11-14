import { Record, Schema } from "effect"
import { Channels } from "./channels.ts"

export const Suits = { Hearts: "hearts", Spades: "spades" } as const
const suitNames = ["hearts", "spades"] as const

export const SuitFromTuple = Schema.Literals(suitNames)
export const SuitFromObject = Schema.Literals(Record.values(Suits))
export const Hearts = Schema.Literal(Suits.Hearts)
export const Channel = Schema.Literals(Record.values(Channels))
export const EmailEnabled = Schema.Record(Channel, Schema.Boolean)
