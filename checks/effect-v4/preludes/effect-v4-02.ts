// Stubs for names block 02 uses but does not declare.
import { Context, Option, Result } from "effect"  // Data comes from the block
interface Task { readonly rawTitle: string }
class InvalidTitle extends Data.TaggedError("InvalidTitle")<{ readonly rawTitle: string }> {}
declare const parseTitle: (rawTitle: string) => Result.Result<string, InvalidTitle>
class TaskStore extends Context.Service<TaskStore, {
  readonly find: (taskId: string) => Option.Option<Task>
}>()("stub/TaskStore") {}
