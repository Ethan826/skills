// Stubs for names block 06 uses but does not declare.
import type { Effect as EffectType, Option as OptionType } from "effect"
interface Task { readonly taskId: string }
interface StoreError { readonly _tag: "StoreError" }
declare const find: (taskId: string) => OptionType.Option<Task>
declare const save: (task: Task) => EffectType.Effect<void, StoreError>
