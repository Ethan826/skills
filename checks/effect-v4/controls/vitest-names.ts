// Checks the @effect/vitest names the skill mentions (it.effect, layer)
// against @effect/vitest 4.1.1 by compiling a use of each.
import { expect, it, layer } from "@effect/vitest"
import { Context, Effect, Layer } from "effect"

class Greeting extends Context.Service<Greeting, { readonly text: string }>()("check/Greeting") {}
const GreetingTest = Layer.succeed(Greeting, Greeting.of({ text: "hi" }))

it.effect("runs an Effect as a test", () =>
  Effect.gen(function* () {
    expect(1 + 1).toBe(2)
  }))

layer(GreetingTest)("shares a Layer across a describe", (it) => {
  it.effect("reads the service", () =>
    Effect.gen(function* () {
      const greeting = yield* Greeting
      expect(greeting.text).toBe("hi")
    }))
})
