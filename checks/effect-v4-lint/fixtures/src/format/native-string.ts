const text = " Hello, World "

export const all = [
  text.split(","),
  text.trim(),
  text.trimStart(),
  text.trimEnd(),
  text.toLowerCase(),
  text.toUpperCase(),
  text.startsWith("H"),
  text.endsWith("d"),
  text.replace("H", "J"),
  text.replaceAll("l", "L"),
  text.padStart(20),
  text.padEnd(20),
  text.substring(1),
  text.charAt(0),
  text.repeat(2),
  text.localeCompare("x"),
  text.normalize(),
]
