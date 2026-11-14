// Runtime check for the skill's Effect.promise claim: a rejection inside
// Effect.promise ends as a defect (Die), and the same rejection through
// Effect.tryPromise with a catch ends as a typed failure (Fail).
import { Cause, Data, Effect, Exit } from "effect"

class FetchFailed extends Data.TaggedError("FetchFailed")<{ readonly reason: unknown }> {}

const rejecting = () => Promise.reject(new Error("boom"))

const viaPromise = await Effect.runPromiseExit(Effect.promise(rejecting))
const viaTryPromise = await Effect.runPromiseExit(
  Effect.tryPromise({ try: rejecting, catch: (reason) => new FetchFailed({ reason }) }),
)
// A typed handler does not see the defect: catchTag/catch leave it in place.
const caught = await Effect.runPromiseExit(
  Effect.promise(rejecting).pipe(Effect.catch(() => Effect.succeed("recovered"))),
)

const describe = (exit: Exit.Exit<unknown, unknown>) =>
  Exit.isSuccess(exit) ? "success"
    : `failure: hasDies=${Cause.hasDies(exit.cause)} hasFails=${Cause.hasFails(exit.cause)}`

console.log("Effect.promise         ->", describe(viaPromise))
console.log("Effect.tryPromise      ->", describe(viaTryPromise))
console.log("promise + Effect.catch ->", describe(caught))
const ok = Exit.isFailure(viaPromise) && Cause.hasDies(viaPromise.cause) && !Cause.hasFails(viaPromise.cause)
  && Exit.isFailure(viaTryPromise) && Cause.hasFails(viaTryPromise.cause) && !Cause.hasDies(viaTryPromise.cause)
  && Exit.isFailure(caught) && Cause.hasDies(caught.cause)
console.log(ok ? "CLAIM HOLDS" : "CLAIM FAILS")
if (!ok) process.exit(1)
