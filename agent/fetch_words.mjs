// Tải google-10000-english (no-swears) → lọc từ 4–8 chữ cái → words.txt (~3–5k từ).
import { writeFileSync } from "node:fs";

const URL =
  "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-no-swears.txt";

const res = await fetch(URL);
if (!res.ok) throw new Error("fetch fail " + res.status);
const raw = await res.text();

const words = raw
  .split("\n")
  .map((w) => w.trim().toUpperCase())
  .filter((w) => /^[A-Z]+$/.test(w) && w.length >= 4 && w.length <= 8);

const uniq = [...new Set(words)];
writeFileSync("words.txt", uniq.join("\n"));
console.log(`Lưu ${uniq.length} từ → words.txt`);
