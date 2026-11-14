// Runtime is not a core layer, so it may import platform modules. No
// @types/node is installed, so the import is only named, never used as a
// value.
import type * as Fs from "node:fs"

export type FileSystem = typeof Fs
