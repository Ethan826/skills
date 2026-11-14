// Draws a decision-core application's layers as concentric rings, with each
// layer's import list beside them, as an SVG. The ring data is a parameter:
// a project copies this file, replaces `defaultSpec` with its own layers, and
// regenerates with
//
//   bun diagram/onion.ts > diagram/onion.svg
//
// The output is a pure function of the spec, so a test can require the
// committed SVG to equal renderOnion(spec) byte for byte, and layerTable(spec)
// to equal the project's lint layer table. No dependencies: bun or any
// TypeScript runner can execute it.
//
// The SVG has no background, uses plain CSS classes (no var(), which
// rsvg-convert ignores), and switches colors under
// @media (prefers-color-scheme: dark).

export interface OnionLayer {
  /** Directory of the layer, as the lint layer table names it. */
  readonly dir: string
  /** Name drawn in the ring and the legend. */
  readonly name: string
  /** Short subtitle under the name. */
  readonly note: string
  /** Planned layers are drawn dashed and marked "(planned)". */
  readonly planned: boolean
  /** Names of the layers this one may import. */
  readonly imports: ReadonlyArray<string>
}

export interface OnionSpec {
  /** Rings from the center outward; a ring with two layers is split in half. */
  readonly rings: ReadonlyArray<ReadonlyArray<OnionLayer>>
  /** Caption under the legend, wrapped to fit. */
  readonly caption: string
  /** Accessible title of the SVG. */
  readonly title: string
}

// The layers of the decision-core-architecture skill, with its import table.
export const defaultSpec: OnionSpec = {
  rings: [
    [{ dir: "domain", name: "Domain", note: "model, invariants", planned: false, imports: [] }],
    [
      { dir: "format", name: "Format", note: "translation", planned: false, imports: ["Domain", "Features"] },
      { dir: "features", name: "Features", note: "decisions", planned: false, imports: ["Domain"] },
    ],
    [{ dir: "runtime", name: "Runtime", note: "capabilities", planned: false, imports: ["Domain"] }],
    [{ dir: "program", name: "Program", note: "wiring", planned: false, imports: ["Domain", "Features", "Format", "Runtime"] }],
    [{ dir: "facade", name: "Facade", note: "plain data, no logic", planned: false, imports: ["Domain", "Features", "Format", "Program"] }],
  ],
  caption:
    "Every import points inward, and the rules are narrower than a strict onion: Runtime imports only Domain, Format imports only the value types of Features, and the facade does not import Runtime. The app shell sits outside the facade and calls only the facade.",
  title: "Layers of a decision core: Domain at the center, then Features and Format, Runtime, Program and the facade; imports point inward",
}

/** Each layer's directory mapped to the directories it may import. */
export const layerTable = (spec: OnionSpec): Record<string, ReadonlyArray<string>> => {
  const layers = spec.rings.flat()
  const dirOf = (name: string): string => {
    const layer = layers.find((candidate) => candidate.name === name)
    if (layer === undefined) throw new Error(`onion: ${name} is imported but is not a layer`)
    return layer.dir
  }
  return Object.fromEntries(layers.map((layer) => [layer.dir, layer.imports.map(dirOf)]))
}

const centerRadius = 70
const splitWidth = 96
const ringWidth = 50
const margin = 20
const legendGap = 60
const legendWidth = 300
const entryHeight = 52
const lineHeight = 17
const captionChars = 44

const num = (n: number): string => n.toFixed(2).replace(/\.?0+$/, "")

const escapeXml = (text: string): string =>
  text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;")

const wrap = (text: string, width: number): ReadonlyArray<string> =>
  text.split(/\s+/).filter((word) => word !== "").reduce<ReadonlyArray<string>>((lines, word) => {
    const last = lines[lines.length - 1]
    return last !== undefined && last.length + 1 + word.length <= width
      ? [...lines.slice(0, -1), `${last} ${word}`]
      : [...lines, word]
  }, [])

const style = `
    text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: #1f2328; }
    .name { font-size: 15px; font-weight: 600; }
    .note, .small { font-size: 12px; fill: #59636e; }
    .ring { stroke: #59636e; stroke-width: 1.5; }
    .planned { stroke-dasharray: 6 5; }
    .divider { stroke: #59636e; stroke-width: 1.5; }
    .arrow { stroke: #1f2328; stroke-width: 2; fill: none; }
    .arrowhead { fill: #1f2328; }
    .f0 { fill: #ddf4ff; }
    .f1 { fill: #dafbe1; }
    .f2 { fill: #fff8c5; }
    .f3 { fill: #ffeff7; }
    .f4 { fill: #f6f8fa; }
    @media (prefers-color-scheme: dark) {
      text { fill: #f0f6fc; }
      .note, .small { fill: #9198a1; }
      .ring, .divider { stroke: #9198a1; }
      .arrow { stroke: #f0f6fc; }
      .arrowhead { fill: #f0f6fc; }
      .f0 { fill: #0d2a4a; }
      .f1 { fill: #12361f; }
      .f2 { fill: #3a3210; }
      .f3 { fill: #3b1d33; }
      .f4 { fill: #1e2530; }
    }`

export const renderOnion = (spec: OnionSpec = defaultSpec): string => {
  const { rings } = spec
  if (rings.length === 0) throw new Error("onion: no rings")
  for (const ring of rings) {
    if (ring.length < 1 || ring.length > 2) throw new Error("onion: each ring holds one or two layers")
  }
  layerTable(spec) // throws on an import that names no layer

  // Outer radius of each ring, center first. A split ring is wider so its
  // two half labels fit side by side.
  const radii = rings.reduce<ReadonlyArray<number>>((acc, ring, i) => {
    const inner = i === 0 ? 0 : (acc[i - 1] ?? 0)
    const width = i === 0 ? centerRadius : ring.length === 2 ? splitWidth : ringWidth
    return [...acc, inner + width]
  }, [])
  const radiusOf = (ring: number): number => radii[ring] ?? 0
  const innerRadiusOf = (ring: number): number => (ring === 0 ? 0 : radiusOf(ring - 1))
  const outerRadius = radiusOf(rings.length - 1)
  const cx = margin + outerRadius
  const cy = margin + outerRadius
  const legendX = cx + outerRadius + legendGap

  // Outermost layer first in the legend.
  const flat = [...rings].reverse().flat()
  const captionLines = wrap(spec.caption, captionChars)
  const captionY = 40 + flat.length * entryHeight + 24
  const width = legendX + legendWidth
  const height = Math.max(2 * (outerRadius + margin), captionY + captionLines.length * lineHeight + margin)

  const circle = (ring: number): string => {
    const planned = (rings[ring] ?? []).some((layer) => layer.planned)
    return `<circle class="ring f${ring % 5}${planned ? " planned" : ""}" cx="${num(cx)}" cy="${num(cy)}" r="${num(radiusOf(ring))}"/>`
  }

  const label = (x: number, y: number, layer: OnionLayer): string =>
    `<text x="${num(x)}" y="${num(y)}" text-anchor="middle"><tspan class="name" x="${num(x)}">${escapeXml(layer.name)}</tspan>` +
    `<tspan class="note" x="${num(x)}" dy="16">${escapeXml(layer.note)}${layer.planned ? " (planned)" : ""}</tspan></text>`

  const ringLabels = (ring: number): ReadonlyArray<string> => {
    const layers = rings[ring] ?? []
    const mid = (radiusOf(ring) + innerRadiusOf(ring)) / 2
    return layers.length === 1
      ? layers.map((layer) => label(cx, ring === 0 ? cy - 8 : cy - mid - 6, layer))
      : layers.map((layer, i) => label(cx + (i === 0 ? -mid : mid), cy - 8, layer))
  }

  const divider = (ring: number): string =>
    `<line class="divider" x1="${num(cx)}" y1="${num(cy - radiusOf(ring))}" x2="${num(cx)}" y2="${num(cy - innerRadiusOf(ring))}"/>` +
    `<line class="divider" x1="${num(cx)}" y1="${num(cy + innerRadiusOf(ring))}" x2="${num(cx)}" y2="${num(cy + radiusOf(ring))}"/>`

  const arrow = (): string => {
    const d = Math.SQRT1_2
    const from = outerRadius - 8
    const to = innerRadiusOf(Math.min(1, rings.length - 1)) + 6
    return (
      `<line class="arrow" x1="${num(cx + from * d)}" y1="${num(cy + from * d)}" ` +
      `x2="${num(cx + to * d)}" y2="${num(cy + to * d)}" marker-end="url(#head)"/>`
    )
  }

  const legend = flat.flatMap((layer, i) => {
    const y = 40 + i * entryHeight
    const imports = layer.imports.length === 0 ? "nothing" : layer.imports.join(", ")
    return [
      `<text class="name" x="${num(legendX)}" y="${num(y)}">${escapeXml(layer.name)}</text>`,
      `<text class="small" x="${num(legendX)}" y="${num(y + lineHeight)}">imports ${escapeXml(imports)}</text>`,
    ]
  })
  const caption = captionLines.map(
    (line, i) => `<text class="small" x="${num(legendX)}" y="${num(captionY + i * lineHeight)}">${escapeXml(line)}</text>`,
  )

  return [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${num(width)} ${num(height)}" width="${num(width)}" height="${num(height)}" role="img" aria-labelledby="t">`,
    `<title id="t">${escapeXml(spec.title)}</title>`,
    `<style>${style}\n  </style>`,
    `<defs><marker id="head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path class="arrowhead" d="M 0 0 L 10 5 L 0 10 z"/></marker></defs>`,
    ...rings.map((_, i) => rings.length - 1 - i).map(circle),
    ...rings.flatMap((ring, i) => (ring.length === 2 && i > 0 ? [divider(i)] : [])),
    ...rings.flatMap((_, i) => ringLabels(i)),
    ...(rings.length > 1 ? [arrow()] : []),
    ...legend,
    ...caption,
    `</svg>`,
    ``,
  ].join("\n")
}

if (import.meta.main) {
  process.stdout.write(renderOnion())
}
