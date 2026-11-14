// Type assertions on what the stubs plus block 02 infer, so a block that
// silently types as `any` would fail here.
import { Data, Effect, Option, Result, Context } from "effect"
class TaskNotFound extends Data.TaggedError("TaskNotFound")<{ readonly taskId: string }> {}
class InvalidTitle extends Data.TaggedError("InvalidTitle")<{ readonly rawTitle: string }> {}
interface Task { readonly rawTitle: string }
declare const parseTitle: (rawTitle: string) => Result.Result<string, InvalidTitle>
class TaskStore extends Context.Service<TaskStore, {
  readonly find: (taskId: string) => Option.Option<Task>
}>()("stub/TaskStore") {}
const taskTitle = Effect.fn("taskTitle")(function* (taskId: string) {
  const store = yield* TaskStore
  const task = yield* Effect.fromOption(store.find(taskId), () =>
    new TaskNotFound({ taskId }))
  return yield* Effect.fromResult(parseTitle(task.rawTitle))
})
export const check: (id: string) => Effect.Effect<string, TaskNotFound | InvalidTitle, TaskStore> = taskTitle
// @ts-expect-error  the requirement is not dropped
export const noR: (id: string) => Effect.Effect<string, TaskNotFound | InvalidTitle, never> = taskTitle
