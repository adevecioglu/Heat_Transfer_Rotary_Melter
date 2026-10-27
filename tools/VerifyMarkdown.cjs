/* Strict KaTeX validation and a standalone, offline HTML preview. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const modules = path.join(root, '.tools/formatters/node_modules');
const katex = require(path.join(modules, 'katex'));
const MarkdownIt = require(path.join(modules, 'markdown-it'));
const input = path.resolve(root, process.argv[2] || 'docs/CPP_CALCULATION_EQUATIONS.md');
const document = fs.readFileSync(input, 'utf8');
const fragments = [];
let displayCount = 0, inlineCount = 0;
function placeholder(value) {
  const token = `ROTARYPLACEHOLDER${fragments.length}Z`;
  fragments.push({token, value});
  return token;
}
function math(tex, displayMode) {
  return placeholder(katex.renderToString(tex, {
    displayMode, throwOnError: true, strict: 'error', trust: false,
    output: 'htmlAndMathml',
  }));
}
const markdown = new MarkdownIt({html: false, linkify: true});
let body = document.replace(/^```[^\n]*\n[\s\S]*?^```/gm, code => placeholder(markdown.render(code)));
body = body.replace(/\$\$([\s\S]*?)\$\$/g, (_, tex) => {displayCount++; return math(tex, true);});
body = body.split(/(`[^`\n]*`)/g).map(part => part.startsWith('`') ? part :
  part.replace(/(?<!\$)\$(?!\$)([^$\n]+?)\$(?!\$)/g, (_, tex) => {inlineCount++; return math(tex, false);})).join('');
let html = markdown.render(body);
for (const {token, value} of fragments) html = html.replace(token, value);
if (html.includes('ROTARYPLACEHOLDER') || html.includes('katex-error')) throw Error('Unrendered equation');
const distribution = path.join(modules, 'katex/dist');
const css = fs.readFileSync(path.join(distribution, 'katex.min.css'), 'utf8').replace(/url\((fonts\/[^)]+)\)/g, (_, name) => {
  const extension = path.extname(name).slice(1);
  const mime = extension === 'ttf' ? 'font/ttf' : `font/${extension}`;
  return `url(data:${mime};base64,${fs.readFileSync(path.join(distribution, name)).toString('base64')})`;
});
const output = path.join(root, 'outputs/markdown');
fs.mkdirSync(output, {recursive: true});
const basename = path.basename(input, '.md');
html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${basename}</title><style>${css}
body{font:15px/1.7 system-ui;max-width:1150px;padding:24px;margin:auto;color:#1b3446;background:#fafcfd}h1,h2{color:#125867}h2{border-top:1px solid #dce5eb;padding-top:25px;margin-top:35px}table{border-collapse:collapse;width:100%;font-size:12px}td,th{border:1px solid #d1dce5;padding:8px;text-align:left;overflow-wrap:anywhere}pre{background:#eaf1f5;padding:15px;overflow:auto}code{font-size:.85em}a{color:#06758a}.katex-display{overflow:auto;padding:8px}.katex{font-size:1.05em}@media print{body{background:white}h2{break-after:avoid}}
</style></head><body>${html}</body></html>`;
fs.writeFileSync(path.join(output, basename+'.html'), html);
const report = {file:path.relative(root,input).replaceAll('\\','/'),sourceSha256:crypto.createHash('sha256').update(document).digest('hex'),renderer:'KaTeX '+katex.version,displayEquationGroups:displayCount,inlineExpressions:inlineCount,errors:0,offlineFonts:true};
fs.writeFileSync(path.join(output, basename+'.render.json'), JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
