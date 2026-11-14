// Stubs for names block 04 uses but does not declare.
import { Data } from "effect"
class Started extends Data.TaggedClass("Started")<{ readonly at: number }> {}
class Finished extends Data.TaggedClass("Finished")<{ readonly at: number }> {}
type TaskEvent = Started | Finished
declare const describeStarted: (event: Started) => string
declare const describeFinished: (event: Finished) => string
