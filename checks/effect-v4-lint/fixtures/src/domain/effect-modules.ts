import {
  Array as Arr,
  Option,
  Predicate,
  Record,
  String,
  Struct,
} from "effect"

interface Judged {
  readonly _tag: "Allows" | "Fails"
  readonly window: string
}

const isPositive = (n: number): boolean => n > 0
const double = (n: number): number => n + n

export const doubled = (xs: ReadonlyArray<number>): ReadonlyArray<number> =>
  Arr.map(Arr.filter(xs, isPositive), double)

export const anyFails = (judged: ReadonlyArray<Judged>): boolean =>
  Arr.some(judged, Predicate.isTagged("Fails"))

export const blocked = (judged: ReadonlyArray<Judged>): ReadonlyArray<string> =>
  Arr.map(
    Arr.filter(judged, Predicate.not(Predicate.isTagged("Allows"))),
    Struct.get("window"),
  )

export const words = (text: string): ReadonlyArray<string> =>
  Arr.map(String.split(text, ","), String.trim)

export const resetAt = (x: number | undefined): Option.Option<number> =>
  Option.fromNullishOr(x)

export const keys = (record: Readonly<Record<string, number>>): Array<string> =>
  Record.keys(record)
