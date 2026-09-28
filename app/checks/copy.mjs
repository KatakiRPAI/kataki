// Build-time copy checks (README › Copy rules 6 and Definition of done):
// 1. no product-owner placeholder ([UPDATE HOST], [MODEL HOST], …) may ship: a release build
//    (--release) fails on one, a dev build lists them;
// 2. no English sentence written straight into a component (strings come from strings/*.json).
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

const PLACEHOLDER = /\[(UPDATE HOST|MODEL HOST|FEEDBACK HOST|KATAKI LICENCE|MODEL LICENCE|ART LICENCE|FIRST LINE OF ITS RELEASE NOTES)\]/
const walk = (dir) => readdirSync(dir).flatMap((f) => { const p = join(dir, f); return statSync(p).isDirectory() ? walk(p) : [p] })
const problems = []
const waiting = []
for (const file of walk('src').filter((f) => /\.(tsx?|json)$/.test(f) && !f.includes(`${join('src', 'ds')}`))) {
  const text = readFileSync(file, 'utf8')
  if (PLACEHOLDER.test(text)) (process.argv.includes('--release') ? problems : waiting).push(`${file}: ${text.match(PLACEHOLDER)[0]} is the product owner's to fill`)
  if (file.endsWith('.tsx')) {
    // JSX text between tags that reads like a sentence: >Two words<
    text.split('\n').forEach((line, i) => {
      if (/^\s*(\/\/|\*|\/\*)/.test(line)) return
      const m = line.match(/>\s*([A-Z][a-z]+(?: [a-z’']+){1,})\s*</)
      if (m) problems.push(`${file}:${i + 1}: English in a component: "${m[1]}"`)
    })
  }
}
if (problems.length) {
  console.error(problems.join('\n'))
  process.exit(1)
}
if (waiting.length) console.log(waiting.join('\n'))
console.log('copy: ok')
