// A file-level comment does not document the first export.
export const first = 1

/** Documented. */
export const second = 2

/* A plain block comment is not TSDoc. */
export const third = 3

/** */
export const fourth = 4

const fifth = 5
export { fifth }
