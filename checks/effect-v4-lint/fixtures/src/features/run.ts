import { Effect } from "effect"

export const bad = Effect.runSync(Effect.succeed(1))
