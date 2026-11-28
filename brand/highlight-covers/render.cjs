// Renders covers.html to 1080x1920 PNGs + a profile-row preview.  node brand/highlight-covers/render.cjs
const { chromium } = require("playwright");
const path = require("path");

(async () => {
  const dir = __dirname;
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await p.goto("file://" + path.join(dir, "covers.html"));
  await p.evaluate(() => document.fonts.ready);
  const names = await p.$$eval("svg.cover", (els) => els.map((e) => e.id));
  for (const [i, n] of names.entries()) {
    await (await p.$("#" + n)).screenshot({ path: path.join(dir, `${i + 1}-${n}.png`) });
  }
  const labels = { reviews: "reviews ;)", highlights: "Highlights", faqs: "FAQs", "dm-for-details": "DM for details" };
  const row = names.map((n, i) => `<div class="h"><div class="ring"><img src="${i + 1}-${n}.png"></div><span>${labels[n] || n}</span></div>`).join("");
  await p.setViewportSize({ width: 900, height: 280 });
  await p.setContent(`<base href="file://${dir}/"><style>body{margin:0;background:#0d0f13;display:flex;gap:44px;padding:36px 40px;font:600 20px system-ui;color:#eee}
    .h{display:flex;flex-direction:column;align-items:center;gap:14px}.ring{width:170px;height:170px;border-radius:50%;border:4px solid #3a3c44;padding:4px;box-sizing:border-box}
    img{width:100%;height:100%;border-radius:50%;object-fit:cover}</style>${row}`);
  await p.waitForTimeout(300);
  await p.screenshot({ path: path.join(dir, "preview.png") });
  await b.close();
  console.log("rendered", names.join(", "));
})();
