// Stubs for names block 07 uses but does not declare: the service from
// block 06 and the function from block 02.
import { Context, Data, Effect as E, Option as O } from "effect"
interface Task { readonly taskId: string; readonly rawTitle: string }
class TaskNotFound extends Data.TaggedError("TaskNotFound")<{ readonly taskId: string }> {}
class TaskStore extends Context.Service<TaskStore, {
  readonly find: (taskId: string) => O.Option<Task>
  readonly save: (task: Task) => E.Effect<void>
}>()("stub/TaskStore") {}
declare const sampleTask: Task
declare const taskTitle: (taskId: string) => E.Effect<string, TaskNotFound, TaskStore>
