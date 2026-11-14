// Stubs for names block 07 uses but does not declare.
import { Option } from "effect"
declare const Draft: Schema.Struct<{ readonly body: typeof Schema.String }>
declare const readStoredDraft: Effect.Effect<Option.Option<string>>
declare const showDraft: (draft: { readonly body: string }) => Effect.Effect<void>
