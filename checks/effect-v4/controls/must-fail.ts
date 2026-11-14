// Controls: each line marked @ts-expect-error must fail to compile, or tsc
// reports an unused directive. This shows the check is not vacuous and backs
// the skill's claims about v3 names.
import { Context, Effect, Option, Schema } from "effect"

const User = Schema.Struct({ name: Schema.String })
declare const input: unknown

// @ts-expect-error  v3 name, gone in v4
Effect.catchAll
// @ts-expect-error  v3 name, gone in v4
Effect.either
// @ts-expect-error  v3 name, gone in v4
Context.Tag
// @ts-expect-error  v3 name, gone in v4
Option.fromNullable
// @ts-expect-error  Schema.decode exists in v4 but does not run a decoder
Schema.decode(User)(input)

// @ts-expect-error  Option is not yieldable inside Effect.gen in v4 (reported at the call)
export const yieldsOption = Effect.gen(function* () {
  const value: number = yield* Option.some(1)
  return value
})

export {}
