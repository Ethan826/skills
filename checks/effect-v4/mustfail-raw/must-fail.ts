// The control lines of controls/must-fail.ts without their @ts-expect-error
// directives. run.sh compiles this file alone and requires tsc to report
// exactly the errors listed under mustFailAt in expected.json (line:code),
// so the must-fail check cannot pass by reporting nothing.
import { Context, Effect, Option, Record, Schema } from "effect"

const User = Schema.Struct({ name: Schema.String })
declare const input: unknown

Effect.catchAll
Effect.either
Context.Tag
Option.fromNullable
Schema.decode(User)(input)

export const yieldsOption = Effect.gen(function* () {
  const value: number = yield* Option.some(1)
  return value
})

const Channels = { Email: "email", Sms: "sms" } as const
const ChannelFlags = Schema.Record(Schema.Literals(Record.values(Channels)), Schema.Boolean)
export const missingMember: typeof ChannelFlags.Type = { [Channels.Email]: true }

export {}
