import { Schema } from "effect"

export const bad = Schema.decodeUnknownSync(Schema.Number)
