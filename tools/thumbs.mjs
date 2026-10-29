// Скриншоты обложек для карточек на ysddev.com: 1920×1080 (DPR 2) → webp 400/800/1200/1920/3840
import { chromium } from 'playwright';
import sharp from 'sharp';
import fs from 'node:fs';
import path from 'node:path';
const root = path.resolve('works'); const out = path.resolve('thumbs-out');
fs.mkdirSync(out, { recursive: true });
const only = (process.env.ONLY || '').split(',').filter(Boolean);
const slugs = fs.readdirSync(root).filter(d => fs.existsSync(path.join(root, d, 'index.html')) && (!only.length || only.includes(d)));
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2, reducedMotion: 'reduce', locale: 'ru-RU' });
for (const s of slugs) {
  const page = await ctx.newPage();
  try {
    await page.goto('file://' + path.join(root, s, 'index.html'), { waitUntil: 'networkidle', timeout: 60000 });
    await page.evaluate(() => document.fonts && document.fonts.ready);
    await page.waitForTimeout(2500);
    const png = await page.screenshot({ type: 'png' });
    for (const w of [400, 800, 1200, 1920, 3840]) {
      await sharp(png).resize(w, Math.round(w * 9 / 16)).webp({ quality: w >= 1920 ? 78 : 80 }).toFile(path.join(out, `${s}-${w}.webp`));
    }
    // мобильный вид для проверки
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(800);
    await sharp(await page.screenshot({ type: 'png' })).resize(390).webp({ quality: 75 }).toFile(path.join(out, `${s}-mobile.webp`));
    console.log('ok', s);
  } catch (e) { console.log('FAIL', s, e.message); }
  await page.close();
}
await browser.close();
