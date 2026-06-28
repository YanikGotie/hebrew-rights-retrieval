/* Build the Hebrew (RTL) project presentation.
   Run: NODE_PATH=$(npm root -g) node reports/build_deck.js
   The deck is authored in a normal left-origin coordinate system and every draw
   call is routed through a mirror wrapper (x -> W-x-w, align left<->right), which
   produces a clean right-to-left layout. Technical terms (TF-IDF, AlephBERT, MRR…)
   are kept in Latin, as is standard in Hebrew NLP writing. */
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const FA = require("react-icons/fa");

// ---------- palette ----------
const INK = "0B3B45", INK2 = "10303A", TEAL = "0E8A8F", TEALLT = "5FBDB6";
const AMBER = "E0852F", PAPER = "FFFFFF", MIST = "EAF4F4", MIST2 = "F4F9F9";
const MUTE = "5C6B72", INKTX = "153139";
const FH = "Cambria", FB = "Calibri";

const pres = new pptxgen();
pres.defineLayout({ name: "W", width: 13.333, height: 7.5 });
pres.layout = "W";
pres.author = "Yanik Gotie";
pres.title = "Hebrew Semantic Rights Retrieval";
pres.rtlMode = true;
const W = 13.333, H = 7.5;

const shS = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 90, opacity: 0.12 });

// ---------- RTL mirror wrappers ----------
// Only the x-position is mirrored (so the layout reads right-to-left). Text
// alignment is NOT flipped: Hebrew defaults to right-aligned + paragraph rtl=1.
// Pass `ltr: true` for all-Latin / math / ordered-Latin lines so their run order
// is preserved (otherwise the bidi engine reverses "TF-IDF · BM25 · AlephBERT").
function T(s, text, o) {
  const oo = { ...o, x: W - o.x - o.w };
  if (o.ltr) { oo.rtlMode = false; oo.align = o.align || "left"; }
  else { oo.rtlMode = true; oo.align = o.align || "right"; }
  delete oo.ltr;
  s.addText(text, oo);
}
function SH(s, type, o) { s.addShape(type, { ...o, x: W - o.x - o.w }); }
function IMG(s, o) { s.addImage({ ...o, x: W - o.x - o.w }); }
function CH(s, type, data, o) { s.addChart(type, data, { ...o, x: W - o.x - o.w }); }
function TB(s, rows, o) {
  const rev = rows.map(r => [...r].reverse());   // reverse columns -> RTL reading order
  const oo = { ...o, x: W - o.x - o.w, rtlMode: true };
  if (oo.colW) oo.colW = [...oo.colW].reverse();
  s.addTable(rev, oo);
}

// ---------- icons ----------
async function icon(IconComponent, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(IconComponent, { color, size: String(size) }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}
const ICN = {};
async function loadIcons() {
  const need = {
    scale: FA.FaBalanceScale, search: FA.FaSearch, db: FA.FaDatabase, robot: FA.FaRobot,
    chart: FA.FaChartBar, layers: FA.FaLayerGroup, check: FA.FaCheckCircle, times: FA.FaTimesCircle,
    scroll: FA.FaScroll, filter: FA.FaFilter, cut: FA.FaCut, tags: FA.FaTags, globe: FA.FaGlobe,
    brain: FA.FaBrain, bolt: FA.FaBolt, lightbulb: FA.FaLightbulb, shield: FA.FaShieldAlt,
    comments: FA.FaCommentDots, trophy: FA.FaTrophy, hash: FA.FaHashtag, sitemap: FA.FaSitemap,
  };
  for (const [k, C] of Object.entries(need)) {
    ICN[k] = { white: await icon(C, "#FFFFFF"), teal: await icon(C, "#0E8A8F"), amber: await icon(C, "#E0852F") };
  }
}

// ---------- helpers (all routed through mirror wrappers) ----------
function motif(s, x, y, scale = 1, color = TEAL) {
  SH(s, pres.shapes.OVAL, { x, y, w: 0.34 * scale, h: 0.34 * scale, fill: { type: "none" }, line: { color, width: 2 } });
  SH(s, pres.shapes.OVAL, { x: x + 0.11 * scale, y: y + 0.11 * scale, w: 0.12 * scale, h: 0.12 * scale, fill: { color } });
}
function header(s, kicker, title) {
  motif(s, 0.62, 0.5, 1);
  T(s, kicker, { x: 1.08, y: 0.46, w: 10, h: 0.3, fontFace: FB, fontSize: 12, bold: true, color: TEAL, charSpacing: 1, margin: 0 });
  T(s, title, { x: 0.6, y: 0.78, w: 12.1, h: 0.7, fontFace: FH, fontSize: 30, bold: true, color: INKTX, margin: 0 });
}
function pageNum(s, n) {
  T(s, String(n), { x: 12.7, y: 7.0, w: 0.5, h: 0.3, fontFace: FB, fontSize: 10, color: MUTE, align: "right", margin: 0 });
}
function card(s, x, y, w, h, fill = PAPER) {
  SH(s, pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: "DDE8E8", width: 1 }, shadow: shS() });
}
function iconChip(s, x, y, d, data, bg = TEAL) {
  SH(s, pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: bg }, shadow: shS() });
  const p = d * 0.27;
  IMG(s, { data, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p });
}

let PN = 0;
function content(kicker, title) {
  const s = pres.addSlide();
  s.background = { color: PAPER };
  header(s, kicker, title);
  PN++; pageNum(s, PN);
  return s;
}

async function build() {
  await loadIcons();

  // ---------- 1. TITLE ----------
  {
    const s = pres.addSlide();
    s.background = { color: INK };
    for (let i = 0; i < 4; i++) {
      const r = 1.2 + i * 1.0;
      SH(s, pres.shapes.OVAL, { x: 10.6 - r / 2, y: 5.4 - r / 2, w: r, h: r, fill: { type: "none" }, line: { color: TEALLT, width: 1, transparency: 55 } });
    }
    iconChip(s, 11.55, 0.85, 0.9, ICN.scale.white, TEAL);
    T(s, "פרויקט גמר NLP  ·  מסלול 3 — פרויקט מבוסס-נתונים", { x: 0.9, y: 0.95, w: 10.4, h: 0.4, fontFace: FB, fontSize: 13, bold: true, color: TEALLT, margin: 0 });
    T(s, "הנגשת זכויות חברתיות באמצעות NLP", { x: 0.9, y: 2.0, w: 11.5, h: 1.0, fontFace: FH, fontSize: 40, bold: true, color: PAPER, margin: 0 });
    T(s, "אחזור סמנטי בעברית לשאלות על זכויות חברתיות", { x: 0.9, y: 3.1, w: 11.5, h: 0.7, fontFace: FH, fontSize: 24, italic: true, color: TEALLT, margin: 0 });
    T(s, "האם חיפוש מבוסס-משמעות מנצח חיפוש מבוסס-מילים בשאלות יומיומיות של אזרחים — והאם שילוב השניים מנצח את שניהם?",
      { x: 5.0, y: 3.95, w: 7.4, h: 0.95, fontFace: FB, fontSize: 15, color: "CFE6E4", lineSpacingMultiple: 1.15, margin: 0 });
    SH(s, pres.shapes.LINE, { x: 8.2, y: 5.55, w: 4.2, h: 0, line: { color: TEAL, width: 1.5 } });
    T(s, [
      { text: "יניק גוטיה", options: { bold: true, color: PAPER } },
      { text: "   ·   ת.ז. 318553526   ·   HIT   ·   ד\"ר איגור קליינר", options: { color: "AFCDCB" } },
    ], { x: 0.9, y: 5.7, w: 11.5, h: 0.4, fontFace: FB, fontSize: 14, margin: 0 });
  }

  // ---------- 2. THE PROBLEM ----------
  {
    const s = content("הבעיה", "הפער בין איך שואלים לבין איך הזכויות מנוסחות");
    T(s, "אזרחים מתארים את מצבם בשפה יומיומית ורגשית. המקורות הרשמיים עונים בעברית פורמלית-משפטית. חיפוש מבוסס-מילים נופל בדיוק בפער שביניהם.",
      { x: 0.6, y: 1.62, w: 12.1, h: 0.7, fontFace: FB, fontSize: 15, color: MUTE, margin: 0 });

    card(s, 6.95, 2.55, 5.75, 3.2, MIST2);
    iconChip(s, 11.95, 2.9, 0.7, ICN.comments.white, AMBER);
    T(s, "איך אנשים שואלים", { x: 7.3, y: 3.02, w: 4.3, h: 0.4, fontFace: FB, fontSize: 13, bold: true, color: AMBER, margin: 0 });
    T(s, [
      { text: "”פיטרו אותי מהעבודה, מה מגיע לי?“", options: { breakLine: true, bold: true } },
      { text: "”התינוק שלי מתעכב בהתפתחות, לאן פונים?“", options: { breakLine: true } },
      { text: "”יש לי אוטו, זה פוסל אותי מקצבה?“", options: {} },
    ], { x: 7.3, y: 3.6, w: 5.1, h: 2.0, fontFace: FB, fontSize: 16, color: INKTX, lineSpacingMultiple: 1.35, align: "right", margin: 0 });

    card(s, 0.6, 2.55, 5.75, 3.2, MIST);
    iconChip(s, 5.6, 2.9, 0.7, ICN.scroll.white, TEAL);
    T(s, "איך המקורות מנוסחים", { x: 0.95, y: 3.02, w: 4.3, h: 0.4, fontFace: FB, fontSize: 13, bold: true, color: TEAL, margin: 0 });
    T(s, [
      { text: "”זכאות לדמי אבטלה“", options: { breakLine: true, bold: true } },
      { text: "”אבחון רפואי התפתחותי לילדים“", options: { breakLine: true } },
      { text: "”זכאות לגמלת הבטחת הכנסה ובעלות על רכב“", options: {} },
    ], { x: 0.95, y: 3.6, w: 5.1, h: 2.0, fontFace: FB, fontSize: 16, color: INKTX, lineSpacingMultiple: 1.35, align: "right", margin: 0 });

    T(s, "אותה משמעות · לעיתים קרובות ללא מילים משותפות", { x: 0.6, y: 6.05, w: 12.1, h: 0.5, fontFace: FB, fontSize: 15, italic: true, bold: true, color: TEAL, align: "center", margin: 0 });
  }

  // ---------- 3. RESEARCH QUESTION ----------
  {
    const s = pres.addSlide();
    s.background = { color: INK2 };
    motif(s, 0.62, 0.55, 1, TEALLT);
    T(s, "שאלת המחקר", { x: 1.08, y: 0.5, w: 10, h: 0.3, fontFace: FB, fontSize: 12.5, bold: true, color: TEALLT, margin: 0 });
    T(s, "האם אחזור מבוסס-משמעות עוזר — והאם שילובו עם חיפוש מילים עוזר יותר?",
      { x: 0.6, y: 1.05, w: 12.1, h: 1.3, fontFace: FH, fontSize: 27, bold: true, color: PAPER, margin: 0 });

    const hyp = [
      ["H1", "סמנטי > לקסיקלי", "ההטמעות של AlephBERT מנצחות את TF-IDF, במיוחד כששאלה מנוסחת רחוק מנוסח המקור."],
      ["H2", "היברידי > שניהם", "שילוב דירוגים לקסיקלי + סמנטי מנצח כל שיטה בודדת באיכות הדירוג (MRR, nDCG)."],
    ];
    let x = 0.6;
    for (const [tag, t, d] of hyp) {
      card(s, x, 2.9, 6.05, 3.5, INK);
      SH(s, pres.shapes.ROUNDED_RECTANGLE, { x: x + 4.65, y: 3.3, w: 1.0, h: 1.0, rectRadius: 0.5, fill: { color: TEAL } });
      T(s, tag, { x: x + 4.65, y: 3.3, w: 1.0, h: 1.0, fontFace: FH, fontSize: 26, bold: true, color: PAPER, align: "center", valign: "middle", margin: 0 });
      T(s, t, { x: x + 0.2, y: 3.45, w: 4.2, h: 0.7, fontFace: FH, fontSize: 21, bold: true, color: TEALLT, align: "right", margin: 0 });
      T(s, d, { x: x + 0.45, y: 4.55, w: 5.3, h: 1.7, fontFace: FB, fontSize: 14.5, color: "D7E8E6", lineSpacingMultiple: 1.25, align: "right", margin: 0 });
      x += 6.45;
    }
    T(s, "ספוילר: השערה אחת מתאשרת, אחת נדחית — והניגוד הזה הוא הממצא.",
      { x: 0.6, y: 6.65, w: 12.1, h: 0.4, fontFace: FB, fontSize: 14, italic: true, color: AMBER, align: "center", margin: 0 });
  }

  // ---------- 4. PIPELINE ----------
  {
    const s = content("סקירה כללית", "צינור העיבוד מקצה לקצה");
    const steps = [
      [ICN.globe.white, "איסוף", "API של כל-זכות + סריקת ביטוח לאומי", TEAL, false],
      [ICN.filter.white, "עיבוד מקדים", "ניקוי · טוקניזציה · מילות עצירה · חלוקה", TEAL, false],
      [ICN.tags.white, "אינדוקס", "TF-IDF · BM25 · AlephBERT", TEAL, true],
      [ICN.layers.white, "שילוב", "היברידי: RRF + משוקלל", AMBER, false],
      [ICN.chart.white, "הערכה", "Recall@k · MRR · nDCG · MAP", TEAL, true],
    ];
    const n = steps.length, cw = 2.2, gap = (W - 1.2 - n * cw) / (n - 1);
    let x = 0.6;
    steps.forEach(([ic, t, d, col, dltr], i) => {
      const y = 2.3;
      card(s, x, y, cw, 2.7, i === 3 ? "FFF4E8" : MIST2);
      iconChip(s, x + cw / 2 - 0.45, y + 0.35, 0.9, ic, col);
      T(s, t, { x: x, y: y + 1.4, w: cw, h: 0.45, fontFace: FH, fontSize: 17, bold: true, color: INKTX, align: "center", margin: 0 });
      T(s, d, { x: x + 0.18, y: y + 1.9, w: cw - 0.36, h: 0.7, fontFace: FB, fontSize: 12, color: MUTE, align: "center", margin: 0, ltr: dltr });
      if (i < n - 1) T(s, "‹", { x: x + cw - 0.05, y: y + 0.9, w: gap + 0.1, h: 0.8, fontFace: FB, fontSize: 30, bold: true, color: TEALLT, align: "center", margin: 0, ltr: true });
      x += cw + gap;
    });
    T(s, [
      { text: "הרצה בפקודה אחת:  ", options: { color: MUTE } },
      { text: "python src/run_all.py", options: { fontFace: "Consolas", bold: true, color: INKTX } },
    ], { x: 0.6, y: 5.75, w: 12.1, h: 0.5, fontFace: FB, fontSize: 14, align: "center", margin: 0 });
  }

  // ---------- 5. DATA ----------
  {
    const s = content("נתונים", "קורפוס עברי של זכויות שנאסף עצמאית");
    const stats = [["296", "מסמכים"], ["1,602", "פסקאות"], ["122,928", "טוקנים"], ["6", "תחומי חיים"]];
    let x = 0.6;
    for (const [big, lab] of stats) {
      card(s, x, 1.75, 2.95, 1.5, INK);
      T(s, big, { x: x, y: 1.85, w: 2.95, h: 0.7, fontFace: FH, fontSize: 33, bold: true, color: TEALLT, align: "center", margin: 0 });
      T(s, lab, { x: x, y: 2.62, w: 2.95, h: 0.4, fontFace: FB, fontSize: 13, bold: true, color: "CFE6E4", align: "center", margin: 0 });
      x += 3.07;
    }
    card(s, 6.65, 3.5, 6.05, 3.1, MIST);
    iconChip(s, 11.95, 3.85, 0.7, ICN.db.white, TEAL);
    T(s, "כל-זכות  ·  מקור עיקרי", { x: 7.0, y: 3.95, w: 4.6, h: 0.5, fontFace: FH, fontSize: 19, bold: true, color: INKTX, align: "right", margin: 0 });
    T(s, [
      { text: "API רשמי של MediaWiki שמחזיר טקסט נקי ומובנה", options: { bullet: true, breakLine: true } },
      { text: "שש קטגוריות: נכות, אבטלה, בריאות, ילדים, הבטחת הכנסה, הורות", options: { bullet: true, breakLine: true } },
      { text: "רישיון: CC-BY-SA (שימוש חוזר עם ייחוס)", options: { bullet: true } },
    ], { x: 7.1, y: 4.6, w: 5.4, h: 1.85, fontFace: FB, fontSize: 13.5, color: INKTX, lineSpacingMultiple: 1.2, align: "right", margin: 0 });

    card(s, 0.6, 3.5, 5.85, 3.1, MIST2);
    iconChip(s, 5.75, 3.85, 0.7, ICN.shield.white, AMBER);
    T(s, "ביטוח לאומי  ·  מקור משלים", { x: 0.95, y: 3.95, w: 4.5, h: 0.5, fontFace: FH, fontSize: 19, bold: true, color: INKTX, align: "right", margin: 0 });
    T(s, [
      { text: "דפי זכאות נבחרים, #mainContent בלבד", options: { bullet: true, breakLine: true } },
      { text: "נבדק robots.txt · קצב מוגבל · User-Agent מזוהה", options: { bullet: true, breakLine: true } },
      { text: "מוסיף את המשלב הפורמלי המנוגד לכל-זכות", options: { bullet: true } },
    ], { x: 0.8, y: 4.6, w: 5.3, h: 1.85, fontFace: FB, fontSize: 13.5, color: INKTX, lineSpacingMultiple: 1.2, align: "right", margin: 0 });

    T(s, "סט הערכה: 40 שאלות יומיומיות שחוברו ידנית, ממופות למסמכי אמת ומתויגות לפי פער-הניסוח.",
      { x: 0.6, y: 6.75, w: 12.1, h: 0.35, fontFace: FB, fontSize: 13, italic: true, color: TEAL, align: "right", margin: 0 });
  }

  // ---------- 6. PREPROCESS I ----------
  {
    const s = content("NLP קלאסי · 1", "מטקסט עברי גולמי לטוקנים נקיים");
    T(s, "כל פסקה עוברת שרשרת עיבוד מקדים קלאסית לפני האינדוקס הלקסיקלי.",
      { x: 0.6, y: 1.6, w: 12, h: 0.4, fontFace: FB, fontSize: 14.5, color: MUTE, align: "right", margin: 0 });
    const rows = [
      ["גולמי", "...שכירים שפוטרו או התפטרו, כולל מי שעבדו בשני מקומות עבודה...", "DDE8E8"],
      ["נרמול", "הסרת ניקוד · הסרת פיסוק ולטינית · אותיות קטנות · צמצום רווחים", MIST],
      ["טוקניזציה", "שכירים · שפוטרו · או · התפטרו · כולל · מי · שעבדו · בשני · מקומות · עבודה", MIST],
      ["הסרת מילות עצירה", "הוסרו: או · מי · וכן · כדי · על · עד  ·  נותרו 26 מתוך 33 טוקנים", "FFF4E8"],
    ];
    let y = 2.25;
    for (const [tag, txt, col] of rows) {
      card(s, 0.6, y, 12.1, 0.92, col);
      T(s, tag, { x: 9.95, y: y, w: 2.7, h: 0.92, fontFace: FH, fontSize: 15, bold: true, color: TEAL, valign: "middle", align: "right", margin: 0.1 });
      T(s, txt, { x: 0.85, y: y, w: 8.9, h: 0.92, fontFace: FB, fontSize: 14, color: INKTX, valign: "middle", align: "right", margin: 0.05 });
      y += 1.06;
    }
    T(s, "זרם הטוקנים הנקי מוזן למודלים הלקסיקליים TF-IDF ו-BM25", { x: 0.6, y: 6.72, w: 12.1, h: 0.35, fontFace: FB, fontSize: 13, italic: true, color: MUTE, align: "right", margin: 0 });
  }

  // ---------- 7. TF-IDF ----------
  {
    const s = content("NLP קלאסי · 2", "וקטוריזציה של הקורפוס עם TF-IDF");
    card(s, 7.15, 1.8, 5.55, 4.8, MIST2);
    T(s, "מטריצת מסמך–מונח", { x: 7.7, y: 2.0, w: 4.7, h: 0.5, fontFace: FH, fontSize: 18, bold: true, color: INKTX, align: "right", margin: 0 });
    const facts = [["צורה", "1,602 × 20,981"], ["אוצר מילים", "20,981 מונחים"], ["יוניגרמים / ביגרמים", "7,323 / 13,658"], ["ערכים שאינם אפס", "141,493"], ["דלילות", "99.58%"]];
    let y = 2.65;
    for (const [k, v] of facts) {
      T(s, k, { x: 7.35, y: y, w: 2.5, h: 0.55, fontFace: FB, fontSize: 14, color: MUTE, valign: "middle", align: "right", margin: 0 });
      T(s, v, { x: 10.25, y: y, w: 2.3, h: 0.55, fontFace: FH, fontSize: 16, bold: true, color: TEAL, align: "left", valign: "middle", margin: 0, ltr: true });
      if (y < 5.6) SH(s, pres.shapes.LINE, { x: 7.35, y: y + 0.6, w: 5.2, h: 0, line: { color: "D7E6E6", width: 0.75 } });
      y += 0.72;
    }
    card(s, 0.6, 1.8, 6.3, 4.8, PAPER);
    iconChip(s, 6.18, 2.05, 0.62, ICN.hash.white, AMBER);
    T(s, "פסקה אחת כוקטור דליל", { x: 0.95, y: 2.12, w: 5.0, h: 0.5, fontFace: FH, fontSize: 17, bold: true, color: INKTX, align: "right", margin: 0 });
    T(s, "פסקה: ”דמי אבטלה“ — המונחים בעלי המשקל הגבוה ביותר", { x: 0.85, y: 2.7, w: 5.8, h: 0.35, fontFace: FB, fontSize: 12.5, italic: true, color: MUTE, align: "right", margin: 0 });
    const vec = [["לחל ת", 0.175], ["לעבוד", 0.160], ["בקצרה שכירים", 0.157], ["בתנאים מסוימים", 0.157], ["זכאי דמי", 0.157], ["לשכירים", 0.157]];
    let vy = 3.15;
    const barX = 1.05, maxw = 2.1;
    for (const [term, wt] of vec) {
      T(s, term, { x: 4.1, y: vy, w: 2.55, h: 0.42, fontFace: FB, fontSize: 13.5, color: INKTX, align: "right", valign: "middle", margin: 0 });
      T(s, wt.toFixed(3), { x: 3.33, y: vy, w: 0.72, h: 0.42, fontFace: "Consolas", fontSize: 11, color: MUTE, align: "left", valign: "middle", margin: 0, ltr: true });
      SH(s, pres.shapes.ROUNDED_RECTANGLE, { x: barX, y: vy + 0.07, w: maxw * (wt / 0.18), h: 0.28, rectRadius: 0.04, fill: { color: TEAL } });
      vy += 0.5;
    }
    T(s, "כל פסקה = נקודה במרחב בן 20,981 ממדים; הדירוג = דמיון קוסינוס לוקטור השאילתה.",
      { x: 0.85, y: 5.95, w: 5.7, h: 0.55, fontFace: FB, fontSize: 12, italic: true, color: MUTE, align: "right", margin: 0 });
  }

  // ---------- 8. MORPHOLOGY ----------
  {
    const s = content("NLP קלאסי · 3", "המורפולוגיה העברית מנפחת את אוצר המילים");
    T(s, "העברית מדביקה מיליות (ב·ל·מ·ה·ו·ש·כ) לתחילת המילים, כך שאותו שורש מופיע בצורות רבות — אתגר אמיתי לחיפוש מבוסס-מילים.",
      { x: 0.6, y: 1.6, w: 12.1, h: 0.7, fontFace: FB, fontSize: 15, color: MUTE, align: "right", margin: 0 });

    card(s, 6.7, 2.6, 6.0, 4.0, MIST2);
    iconChip(s, 11.95, 2.95, 0.65, ICN.cut.white, TEAL);
    T(s, "הסרת תחיליות קלה (הדגמת stemming)", { x: 7.05, y: 3.02, w: 4.7, h: 0.55, fontFace: FH, fontSize: 16.5, bold: true, color: INKTX, align: "right", margin: 0 });
    const ex = [["לעובדים", "עובדים"], ["והמעסיק", "המעסיק"], ["כשעובד", "עובד"], ["בתקופת", "תקופת"], ["מהמוסד", "מוסד"]];
    let y = 3.75;
    for (const [a, b] of ex) {
      T(s, a, { x: 10.45, y: y, w: 2.1, h: 0.45, fontFace: FB, fontSize: 15, color: INKTX, align: "right", valign: "middle", margin: 0 });
      T(s, "‹", { x: 9.65, y: y, w: 0.7, h: 0.45, fontFace: FB, fontSize: 16, bold: true, color: AMBER, align: "center", valign: "middle", margin: 0 });
      T(s, b, { x: 7.05, y: y, w: 2.5, h: 0.45, fontFace: FB, fontSize: 15, bold: true, color: TEAL, align: "right", valign: "middle", margin: 0 });
      y += 0.55;
    }
    card(s, 0.6, 2.6, 5.85, 4.0, INK);
    T(s, "ההשפעה על אוצר המילים", { x: 0.95, y: 3.0, w: 5, h: 0.4, fontFace: FB, fontSize: 13, bold: true, color: TEALLT, align: "right", margin: 0 });
    T(s, "8,963", { x: 0.95, y: 3.5, w: 2.0, h: 1.0, fontFace: FH, fontSize: 40, bold: true, color: AMBER, align: "left", valign: "middle", margin: 0, ltr: true });
    T(s, "‹", { x: 3.0, y: 3.5, w: 0.7, h: 1.0, fontFace: FH, fontSize: 30, color: TEALLT, align: "center", valign: "middle", margin: 0, ltr: true });
    T(s, "13,415", { x: 3.7, y: 3.5, w: 2.4, h: 1.0, fontFace: FH, fontSize: 40, bold: true, color: PAPER, align: "right", valign: "middle", margin: 0, ltr: true });
    T(s, "סוגי מילים, לאחר הסרת תחילית אחת", { x: 0.95, y: 4.55, w: 5.2, h: 0.4, fontFace: FB, fontSize: 13, color: "CFE6E4", align: "right", margin: 0 });
    T(s, "−33%", { x: 0.95, y: 5.05, w: 5.2, h: 0.9, fontFace: FH, fontSize: 34, bold: true, color: TEALLT, align: "right", margin: 0, ltr: true });
    T(s, "המורפולוגיה — לא הנושא — אחראית לרוב הדלילות. למטיזציה מלאה היא עבודה עתידית.",
      { x: 0.95, y: 5.95, w: 5.2, h: 0.55, fontFace: FB, fontSize: 12, italic: true, color: "AFCDCB", align: "right", margin: 0 });
  }

  // ---------- 9. FIVE RETRIEVERS ----------
  {
    const s = content("מודלים", "חמישה מאחזרים, ממשק אחד");
    const models = [
      [ICN.tags.white, "TF-IDF", "בסיס לקסיקלי", "קוסינוס דליל מעל מטריצת המונחים", TEAL],
      [ICN.search.white, "BM25", "לקסיקלי (בונוס)", "דירוג Okapi BM25", TEAL],
      [ICN.brain.white, "AlephBERT", "סמנטי", "הטמעות משפט בעברית, קוסינוס צפוף", AMBER],
      [ICN.layers.white, "Hybrid-RRF", "שילוב", "שילוב דירוגים הופכיים של לקסיקלי + סמנטי", TEAL],
      [ICN.layers.white, "Hybrid-wtd", "שילוב", "שילוב ציוני min-max: α·סמנטי + (1-α)·לקסיקלי", TEAL],
    ];
    const cw = 3.95, chh = 2.05;
    const place = [[0.6, 2.0], [4.82, 2.0], [9.04, 2.0], [2.7, 4.35], [6.93, 4.35]];
    models.forEach(([ic, name, kind, desc, col], i) => {
      const [x, y] = place[i];
      card(s, x, y, cw, chh, col === AMBER ? "FFF4E8" : MIST2);
      iconChip(s, x + cw - 1.0, y + 0.32, 0.7, ic, col);
      T(s, name, { x: x + 0.25, y: y + 0.28, w: cw - 1.3, h: 0.45, fontFace: FH, fontSize: 18, bold: true, color: INKTX, align: "right", margin: 0, ltr: true });
      T(s, kind, { x: x + 0.25, y: y + 0.74, w: cw - 1.3, h: 0.3, fontFace: FB, fontSize: 11.5, bold: true, color: col === AMBER ? AMBER : TEAL, align: "right", margin: 0 });
      T(s, desc, { x: x + 0.28, y: y + 1.18, w: cw - 0.56, h: 0.75, fontFace: FB, fontSize: 12.5, color: MUTE, align: "right", margin: 0 });
    });
  }

  // ---------- 9b. CLOSE-UP DEMO (one real query) ----------
  {
    const s = content("מבט מקרוב", "שאילתה אחת, שלושה מודלים");
    card(s, 0.6, 1.7, 12.1, 1.15, INK);
    T(s, [
      { text: "השאילתה:  ", options: { color: TEALLT, bold: true } },
      { text: "”פיטרו אותי מהעבודה, מה מגיע לי?“", options: { color: PAPER, bold: true } },
    ], { x: 0.6, y: 1.82, w: 11.9, h: 0.5, fontFace: FH, fontSize: 19, align: "right", margin: 0.25 });
    T(s, "מסמך הזהב: ”דמי אבטלה“ · ”זכאות לדמי אבטלה“", { x: 0.6, y: 2.34, w: 11.9, h: 0.4, fontFace: FB, fontSize: 13, italic: true, color: "CFE6E4", align: "right", margin: 0.25 });

    // Right card — TF-IDF (lexical, fails)
    card(s, 6.95, 3.05, 5.75, 2.6, MIST2);
    iconChip(s, 11.95, 3.32, 0.62, ICN.tags.white, TEAL);
    T(s, "TF-IDF · לקסיקלי", { x: 7.3, y: 3.38, w: 4.4, h: 0.4, fontFace: FH, fontSize: 16, bold: true, color: INKTX, align: "right", margin: 0, ltr: true });
    const lex = ["זכאות לגמלת הבטחת הכנסה ובעלות על רכב", "ניכוי הכנסות מדמי אבטלה", "איסור ניכוי שכר מנער הנעדר מעבודתו…"];
    lex.forEach((t, i) => T(s, `${i + 1}.  ${t}`, { x: 7.15, y: 4.0 + i * 0.42, w: 5.4, h: 0.4, fontFace: FB, fontSize: 12.5, color: MUTE, align: "right", margin: 0 }));
    T(s, "✗  מסמך הזהב לא הופיע ב-top-10", { x: 7.15, y: 5.28, w: 5.4, h: 0.35, fontFace: FB, fontSize: 12, bold: true, color: "C2603A", align: "right", margin: 0 });

    // Left card — AlephBERT (semantic, nails it)
    card(s, 0.6, 3.05, 5.75, 2.6, MIST);
    iconChip(s, 5.6, 3.32, 0.62, ICN.brain.white, TEAL);
    T(s, "AlephBERT · סמנטי", { x: 0.95, y: 3.38, w: 4.4, h: 0.4, fontFace: FH, fontSize: 16, bold: true, color: INKTX, align: "right", margin: 0, ltr: true });
    const sem = [["דמי אבטלה", true], ["דמי אבטלה בתקופת מלחמת חרבות ברזל", false], ["התפטרות בנסיבות המזכות בדמי אבטלה", false]];
    sem.forEach(([t, gold], i) => T(s, `${i + 1}.  ${t}`, { x: 0.8, y: 4.0 + i * 0.42, w: 5.4, h: 0.4, fontFace: FB, fontSize: 12.5, bold: gold, color: gold ? TEAL : MUTE, align: "right", margin: 0 }));
    T(s, "✓  מסמך הזהב במקום 1", { x: 0.8, y: 5.28, w: 5.4, h: 0.35, fontFace: FB, fontSize: 12, bold: true, color: TEAL, align: "right", margin: 0 });

    // Bottom strip — gold-doc rank per model + takeaway
    card(s, 0.6, 5.85, 12.1, 1.0, INK);
    T(s, [
      { text: "דירוג מסמך הזהב —  ", options: { color: PAPER, bold: true } },
      { text: "TF-IDF: ✗   ·   AlephBERT: 1   ·   Hybrid-RRF: 4", options: { color: "CFE6E4" } },
    ], { x: 0.6, y: 5.95, w: 11.9, h: 0.45, fontFace: FB, fontSize: 14, align: "right", margin: 0.25 });
    T(s, "אפס מילים משותפות → הלקסיקלי מחמיץ, הסמנטי מגשר על פער הניסוח. ההיברידי אינו ראשון בכל שאלה — יתרונו הוא במצטבר על פני 40 השאלות.",
      { x: 0.6, y: 6.42, w: 11.9, h: 0.4, fontFace: FB, fontSize: 12, italic: true, color: TEALLT, align: "right", margin: 0.25 });
  }

  // ---------- 10. HYBRID + METRICS ----------
  {
    const s = content("איך משלבים ומודדים", "שילוב היברידי והמדדים");
    card(s, 6.7, 1.9, 6.0, 4.6, MIST);
    iconChip(s, 11.95, 2.25, 0.7, ICN.layers.white, TEAL);
    T(s, "Reciprocal Rank Fusion", { x: 7.05, y: 2.33, w: 4.6, h: 0.5, fontFace: FH, fontSize: 18, bold: true, color: INKTX, align: "right", margin: 0, ltr: true });
    SH(s, pres.shapes.ROUNDED_RECTANGLE, { x: 7.05, y: 3.1, w: 5.3, h: 0.95, rectRadius: 0.06, fill: { color: PAPER }, line: { color: "D7E6E6", width: 1 } });
    T(s, "score(d) = Σ  1 / (k + rank_i(d))", { x: 7.05, y: 3.1, w: 5.3, h: 0.95, fontFace: "Cambria", fontSize: 20, italic: true, bold: true, color: TEAL, align: "center", valign: "middle", margin: 0, ltr: true });
    T(s, [
      { text: "מבוסס-דירוג — לא נדרש כיול ציונים", options: { bullet: true, breakLine: true } },
      { text: "מסמך שדורג גבוה ע\"י אחד המודלים עולה", options: { bullet: true, breakLine: true } },
      { text: "נבדק גם שילוב ציונים משוקלל (min-max)", options: { bullet: true } },
    ], { x: 7.1, y: 4.25, w: 5.3, h: 2.1, fontFace: FB, fontSize: 14, color: INKTX, lineSpacingMultiple: 1.25, align: "right", margin: 0 });

    card(s, 0.6, 1.9, 5.85, 4.6, MIST2);
    iconChip(s, 5.75, 2.25, 0.7, ICN.chart.white, AMBER);
    T(s, "מדדי הערכה", { x: 0.95, y: 2.33, w: 4.5, h: 0.5, fontFace: FH, fontSize: 18, bold: true, color: INKTX, align: "right", margin: 0 });
    const mets = [["Recall@k", "האם מסמך רלוונטי נמצא ב-top-k?"], ["MRR", "1 חלקי דירוג המסמך הרלוונטי הראשון"], ["nDCG@10", "מתגמל מסמכים רלוונטיים בדירוג גבוה"], ["MAP", "דיוק ממוצע על פני כל הדירוג"]];
    let y = 3.15;
    for (const [m, d] of mets) {
      T(s, m, { x: 4.45, y: y, w: 1.85, h: 0.5, fontFace: FH, fontSize: 15, bold: true, color: TEAL, valign: "middle", align: "left", margin: 0, ltr: true });
      T(s, d, { x: 0.85, y: y, w: 3.5, h: 0.5, fontFace: FB, fontSize: 12.5, color: MUTE, valign: "middle", align: "right", margin: 0 });
      y += 0.78;
    }
    T(s, "המדידה היא ברמת המסמך: פסקה נחשבת עבור הדף שאליו היא שייכת.", { x: 0.8, y: 6.2, w: 5.5, h: 0.4, fontFace: FB, fontSize: 11.5, italic: true, color: MUTE, align: "right", margin: 0 });
  }

  // ---------- 10b. EVALUATION PROTOCOL (train/val/test split) ----------
  {
    const s = content("פרוטוקול הערכה", "חלוקה לאימון · ולידציה · טסט");
    T(s, "זהו אחזור מידע, ולכן החלוקה היא ברמת השאילתה: הקורפוס משמש כאינדקס (נלמד ללא תוויות), ו-40 השאלות המתויגות מחולקות לולידציה ולטסט.",
      { x: 0.6, y: 1.62, w: 12.1, h: 0.7, fontFace: FB, fontSize: 15, color: MUTE, align: "right", margin: 0 });
    const cards = [
      [ICN.db.white, "קורפוס · אינדקס", "296 מסמכים · 1,602 פסקאות", "ללא תוויות — TF-IDF/BM25 נלמדים עליו ו-AlephBERT מקודד אותו", TEAL],
      [ICN.filter.white, "ולידציה (dev)", "14 שאלות · 35%", "בחירת מודל והיפר-פרמטרים (שיטת השילוב, k, α)", TEAL],
      [ICN.check.white, "טסט (מוחזק)", "26 שאלות · 65%", "מדדים סופיים ובלתי-מוטים — לא השפיעו על אף בחירה", AMBER],
    ];
    const cw = 3.95, place = [0.6, 4.74, 8.88];
    cards.forEach(([ic, t, big, d, col], i) => {
      const x = place[i], y = 2.5;
      card(s, x, y, cw, 2.7, col === AMBER ? "FFF4E8" : MIST2);
      iconChip(s, x + cw - 1.0, y + 0.3, 0.7, ic, col);
      T(s, t, { x: x + 0.25, y: y + 0.28, w: cw - 1.3, h: 0.45, fontFace: FH, fontSize: 17, bold: true, color: INKTX, align: "right", margin: 0 });
      T(s, big, { x: x + 0.3, y: y + 0.98, w: cw - 0.6, h: 0.4, fontFace: FH, fontSize: 15, bold: true, color: col === AMBER ? AMBER : TEAL, align: "right", margin: 0 });
      T(s, d, { x: x + 0.3, y: y + 1.5, w: cw - 0.6, h: 1.05, fontFace: FB, fontSize: 12.5, color: MUTE, align: "right", lineSpacingMultiple: 1.2, margin: 0 });
    });
    card(s, 0.6, 5.5, 12.1, 1.0, INK);
    T(s, [
      { text: "על הטסט המוחזק (26 שאלות) — MRR:   ", options: { color: PAPER, bold: true } },
      { text: "Hybrid-RRF 0.690 · Hybrid-wtd 0.659 · BM25 0.606 · TF-IDF 0.603 · AlephBERT 0.585", options: { color: "CFE6E4" } },
    ], { x: 0.6, y: 5.5, w: 11.9, h: 1.0, fontFace: FB, fontSize: 14, align: "right", valign: "middle", margin: 0.25 });
    T(s, "היתרון של ההיברידי נשמר — ואף גדל — על שאלות שלא השתתפו בשום בחירה.",
      { x: 0.6, y: 6.62, w: 12.1, h: 0.35, fontFace: FB, fontSize: 12, italic: true, color: TEAL, align: "right", margin: 0 });
  }

  // ---------- 11. RESULTS chart + table ----------
  {
    const s = content("תוצאות", "השוואת חמשת המודלים");
    T(s, "דירוג הדדי ממוצע (MRR)", { x: 7.3, y: 1.65, w: 5.4, h: 0.4, fontFace: FH, fontSize: 16, bold: true, color: INKTX, align: "right", margin: 0 });
    CH(s, pres.charts.BAR, [{
      name: "MRR", labels: ["TF-IDF", "BM25", "AlephBERT", "Hybrid-RRF", "Hybrid-wtd"], values: [0.618, 0.612, 0.579, 0.668, 0.653],
    }], {
      x: 6.9, y: 2.1, w: 6.1, h: 4.5, barDir: "col", chartColors: [TEAL, TEAL, AMBER, "0B6E72", TEALLT],
      chartArea: { fill: { color: "FFFFFF" } }, plotArea: { fill: { color: "FFFFFF" } },
      catAxisLabelColor: MUTE, catAxisLabelFontSize: 11, valAxisLabelColor: MUTE,
      valAxisMinVal: 0.5, valAxisMaxVal: 0.7, valGridLine: { color: "E7EEEE", size: 0.5 }, catGridLine: { style: "none" },
      showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INKTX, dataLabelFontSize: 11, dataLabelFormatCode: "0.000",
      showLegend: false, showTitle: false,
    });
    const head = ["", "R@1", "R@5", "R@10", "MRR", "nDCG", "MAP"];
    const data = [
      ["TF-IDF", "0.475", "0.825", "0.850", "0.618", "0.649", "0.588"],
      ["BM25", "0.500", "0.825", "0.875", "0.612", "0.647", "0.578"],
      ["AlephBERT", "0.475", "0.725", "0.775", "0.579", "0.597", "0.540"],
      ["Hybrid-RRF", "0.550", "0.800", "0.875", "0.668", "0.704", "0.652"],
      ["Hybrid-wtd", "0.550", "0.800", "0.850", "0.653", "0.681", "0.632"],
    ];
    const rows = [head.map(h => ({ text: h, options: { fill: { color: INK }, color: "FFFFFF", bold: true, fontSize: 12, align: "center", valign: "middle" } }))];
    data.forEach((r, ri) => {
      const win = r[0].startsWith("Hybrid-RRF");
      rows.push(r.map((c, ci) => ({
        text: c,
        options: { fill: { color: win ? "FFF0DD" : (ri % 2 ? "F4F9F9" : "FFFFFF") }, color: win ? "9A5A12" : INKTX, bold: win || ci === 0, fontSize: 12.5, align: ci === 0 ? "right" : "center", valign: "middle" },
      })));
    });
    TB(s, rows, { x: 0.6, y: 2.25, w: 5.9, colW: [1.7, 0.7, 0.7, 0.75, 0.7, 0.7, 0.65], rowH: 0.62, fontFace: FB, border: { type: "solid", pt: 0.5, color: "E2ECEC" } });
    T(s, "שורה מודגשת = הטוב ביותר. Hybrid-RRF מוביל בכל מדדי הדירוג.", { x: 0.6, y: 6.05, w: 5.9, h: 0.4, fontFace: FB, fontSize: 12, italic: true, color: AMBER, align: "right", margin: 0 });
  }

  // ---------- 12. THE FINDING ----------
  {
    const s = pres.addSlide();
    s.background = { color: INK };
    motif(s, 0.62, 0.55, 1, TEALLT);
    T(s, "הממצא", { x: 1.08, y: 0.5, w: 10, h: 0.3, fontFace: FB, fontSize: 12.5, bold: true, color: TEALLT, margin: 0 });
    T(s, "הסמנטי לבדו הפסיד. ההיברידי ניצח.", { x: 0.6, y: 0.95, w: 12, h: 0.8, fontFace: FH, fontSize: 30, bold: true, color: PAPER, margin: 0 });
    const cards = [
      [ICN.times.white, "H1 נדחתה", "AlephBERT לבדו הוא המודל החלש ביותר — MRR 0.579, 9 מתוך 40 החטאות — ואינו מנצח את הלקסיקלי אפילו בשאלות עם פער-ניסוח גבוה (R@1 0.44 מול 0.48).", "C2603A"],
      [ICN.trophy.white, "H2 אושרה", "Hybrid-RRF מוביל בכול: MRR 0.668, nDCG 0.704, והכי מעט החטאות (5/40). השילוב הוא המנצח המעשי.", TEAL],
      [ICN.lightbulb.white, "מדוע", "שני המודלים נכשלים אחרת. הסמנטי מציל פראפרזות ללא מילים משותפות שהלקסיקלי לא; משולבים, נשמר הדיוק ונוסף כיסוי — משלימים, לא עדיפים.", "0B6E72"],
    ];
    let x = 0.6;
    for (const [ic, t, d, col] of cards) {
      card(s, x, 2.1, 3.95, 4.4, INK2);
      iconChip(s, x + 2.83, 2.45, 0.8, ic, col);
      T(s, t, { x: x + 0.32, y: 3.45, w: 3.3, h: 0.5, fontFace: FH, fontSize: 20, bold: true, color: PAPER, align: "right", margin: 0 });
      T(s, d, { x: x + 0.34, y: 4.05, w: 3.35, h: 2.3, fontFace: FB, fontSize: 14, color: "D7E8E6", lineSpacingMultiple: 1.25, align: "right", margin: 0 });
      x += 4.12;
    }
    pageNum(s, ++PN);
  }

  // ---------- 13. RECALL CURVE + phrasing gap ----------
  {
    const s = content("תוצאות · פירוט", "Recall@k ומבחן פער-הניסוח");
    T(s, "Recall@k כתלות ב-k", { x: 7.3, y: 1.65, w: 5.4, h: 0.4, fontFace: FH, fontSize: 16, bold: true, color: INKTX, align: "right", margin: 0 });
    CH(s, pres.charts.LINE, [
      { name: "TF-IDF", labels: ["1", "3", "5", "10"], values: [0.475, 0.725, 0.825, 0.850] },
      { name: "AlephBERT", labels: ["1", "3", "5", "10"], values: [0.475, 0.700, 0.725, 0.775] },
      { name: "Hybrid-RRF", labels: ["1", "3", "5", "10"], values: [0.550, 0.750, 0.800, 0.875] },
    ], {
      x: 6.8, y: 2.05, w: 6.2, h: 4.4, chartColors: [TEAL, AMBER, "0B3B45"], lineSize: 3, lineSmooth: false,
      showLegend: true, legendPos: "b", legendColor: MUTE, legendFontSize: 11,
      catAxisLabelColor: MUTE, valAxisLabelColor: MUTE, valAxisMinVal: 0.4, valAxisMaxVal: 0.9,
      valGridLine: { color: "E7EEEE", size: 0.5 }, catGridLine: { style: "none" },
    });
    T(s, "Recall@1 לפי פער-הניסוח  (מבחן H1)", { x: 0.65, y: 1.65, w: 6, h: 0.4, fontFace: FH, fontSize: 16, bold: true, color: INKTX, align: "right", margin: 0 });
    const rows = [["פער", "n", "TF-IDF", "AlephBERT", "היברידי"].map(h => ({ text: h, options: { fill: { color: INK }, color: "FFFFFF", bold: true, fontSize: 12.5, align: "center", valign: "middle" } }))];
    [["נמוך", "4", "0.25", "0.50", "0.75"], ["בינוני", "11", "0.55", "0.55", "0.64"], ["גבוה", "25", "0.48", "0.44", "0.48"]].forEach((r, i) => {
      rows.push(r.map((c, ci) => ({ text: c, options: { fill: { color: i % 2 ? "F4F9F9" : "FFFFFF" }, color: (ci === 3 && r[0] === "גבוה") ? "C2603A" : INKTX, bold: ci === 0 || (ci === 3 && r[0] === "גבוה"), fontSize: 13, align: ci === 0 ? "right" : "center", valign: "middle" } })));
    });
    TB(s, rows, { x: 0.65, y: 2.15, w: 5.75, colW: [1.4, 0.75, 1.2, 1.5, 0.9], rowH: 0.62, fontFace: FB, border: { type: "solid", pt: 0.5, color: "E2ECEC" } });
    card(s, 0.65, 4.55, 5.75, 1.95, "FFF4E8");
    iconChip(s, 5.73, 4.85, 0.62, ICN.bolt.white, AMBER);
    T(s, "אפילו בשאלות הקשות והמנוסחות-מחדש ביותר, הסמנטי אינו מקדים (0.44 מול 0.48). היתרון הסמנטי הצפוי פשוט אינו קיים במודל מדף זה.",
      { x: 0.95, y: 4.75, w: 4.4, h: 1.6, fontFace: FB, fontSize: 13.5, color: "8A5A1E", lineSpacingMultiple: 1.2, valign: "middle", align: "right", margin: 0 });
  }

  // ---------- 14. WIN/LOSS heatmap ----------
  {
    const s = content("תוצאות · לכל שאילתה", "היכן כל מודל מנצח, שאלה אחר שאלה");
    IMG(s, { path: "results/figures/winloss_heatmap.png", x: 9.0, y: 1.7, h: 5.6, w: 5.6 * (701 / 1439) });
    card(s, 0.6, 2.1, 7.1, 3.9, MIST2);
    T(s, "כיצד לקרוא את מפת החום", { x: 1.0, y: 2.35, w: 6.3, h: 0.5, fontFace: FH, fontSize: 18, bold: true, color: INKTX, align: "right", margin: 0 });
    T(s, [
      { text: "כל שורה היא אחת מ-40 השאלות; הצבע = דירוג המסמך הנכון הראשון (ירוק = למעלה, אדום = עמוק, אפור = הוחמץ).", options: { bullet: true, breakLine: true } },
      { text: "ירוקים ואפורים מתחלפים בין העמודות — המודלים מצליחים ונכשלים בשאלות שונות.", options: { bullet: true, breakLine: true } },
      { text: "אי-ההסכמה הזו היא בדיוק מה שהופך את השילוב למשתלם.", options: { bullet: true } },
    ], { x: 0.9, y: 3.05, w: 6.5, h: 2.6, fontFace: FB, fontSize: 14.5, color: INKTX, lineSpacingMultiple: 1.3, align: "right", margin: 0 });
    card(s, 0.6, 6.2, 7.1, 0.85, INK);
    T(s, [
      { text: "החטאות (מסמך האמת לא ב-top-10):   ", options: { color: "CFE6E4" } },
      { text: "TF-IDF 6   ·   AlephBERT 9   ·   היברידי 5", options: { color: PAPER, bold: true } },
    ], { x: 0.85, y: 6.2, w: 6.6, h: 0.85, fontFace: FB, fontSize: 14, valign: "middle", align: "right", margin: 0 });
  }

  // ---------- 15. ERROR ANALYSIS ----------
  {
    const s = content("ניתוח שגיאות", "שלוש תבניות, דוגמאות אמיתיות");
    const blocks = [
      [ICN.check.white, TEAL, "A · הסמנטי מנצח", "”חייבים להגיע ללשכת התעסוקה כל הזמן?“", "אמת: התייצבות בשירות התעסוקה.  אפס מילים משותפות → לקסיקלי דירוג 4, סמנטי דירוג 1.", "4 מקרים"],
      [ICN.times.white, AMBER, "B · הלקסיקלי מנצח", "”כיסא גלגלים ומכשירי שיקום?“", "אמת: אביזרי ומכשירי שיקום.  מונח מדויק וחד → לקסיקלי דירוג 1, סמנטי מחמיץ.", "5 מקרים"],
      [ICN.search.white, "8A8F94", "C · שניהם נכשלים", "”איך מקבלים קצבת נכות?“", "הדף הקרוב ביותר הוא קצרמר של ביטוח לאומי, מוצף בדפי ”קביעת נכות“ ספציפיים.", "7 מקרים"],
    ];
    let y = 1.85;
    for (const [ic, col, title, q, d, tag] of blocks) {
      card(s, 0.6, y, 12.1, 1.5, MIST2);
      iconChip(s, 11.95, y + 0.4, 0.7, ic, col);
      T(s, title, { x: 7.55, y: y + 0.18, w: 4.0, h: 0.45, fontFace: FH, fontSize: 17, bold: true, color: INKTX, align: "right", margin: 0 });
      T(s, tag, { x: 7.55, y: y + 0.66, w: 4.0, h: 0.35, fontFace: FB, fontSize: 11.5, bold: true, color: col === "8A8F94" ? MUTE : col, align: "right", margin: 0 });
      T(s, q, { x: 0.8, y: y + 0.18, w: 6.5, h: 0.5, fontFace: FB, fontSize: 15, bold: true, color: INKTX, align: "right", margin: 0 });
      T(s, d, { x: 0.8, y: y + 0.72, w: 6.5, h: 0.65, fontFace: FB, fontSize: 12.5, color: MUTE, align: "right", margin: 0 });
      y += 1.62;
    }
  }

  // ---------- 16. EMBEDDING SPACE ----------
  {
    const s = content("בתוך המודל", "כך נראה מרחב ההטמעות");
    IMG(s, { path: "results/figures/embedding_tsne.png", x: 6.79, y: 2.0, h: 4.6, w: 4.6 * (1153 / 893) });
    card(s, 0.6, 2.3, 5.2, 3.4, MIST);
    iconChip(s, 4.95, 2.65, 0.7, ICN.brain.white, TEAL);
    T(s, "t-SNE של וקטורי הפסקאות", { x: 0.95, y: 2.72, w: 3.8, h: 0.5, fontFace: FH, fontSize: 17, bold: true, color: INKTX, align: "right", margin: 0 });
    T(s, [
      { text: "הטמעות AlephBERT מוטלות ל-2 ממדים, צבועות לפי תחום חיים.", options: { bullet: true, breakLine: true } },
      { text: "התחומים יוצרים אשכולות — המודל אכן לוכד משמעות נושאית.", options: { bullet: true, breakLine: true } },
      { text: "אך האשכולות חופפים, ולכן דירוג עדין עדיין זקוק לאות הלקסיקלי.", options: { bullet: true } },
    ], { x: 0.8, y: 3.4, w: 4.6, h: 2.2, fontFace: FB, fontSize: 13.5, color: INKTX, lineSpacingMultiple: 1.25, align: "right", margin: 0 });
  }

  // ---------- 17. CONCLUSIONS ----------
  {
    const s = pres.addSlide();
    s.background = { color: INK };
    motif(s, 0.62, 0.55, 1, TEALLT);
    T(s, "מסקנות", { x: 1.08, y: 0.5, w: 10, h: 0.3, fontFace: FB, fontSize: 12.5, bold: true, color: TEALLT, margin: 0 });
    T(s, "מה הפרויקט מראה", { x: 0.6, y: 0.95, w: 12, h: 0.7, fontFace: FH, fontSize: 30, bold: true, color: PAPER, margin: 0 });
    const pts = [
      [ICN.sitemap.white, "צינור IR עברי מלא", "קורפוס שנאסף עצמאית → עיבוד מקדים → 5 מאחזרים → הערכה קפדנית, ניתן לשחזור מלא."],
      [ICN.trophy.white, "ההיברידי הוא ההמלצה", "המודל היחיד שמנצח את שני קווי הבסיס בכל מדדי הדירוג."],
      [ICN.lightbulb.white, "מדף ≠ ניצחון חינם", "מקודד עברי מבוסס masked-LM הוא משלים שימושי, לא שדרוג מיידי לאחזור."],
      [ICN.bolt.white, "המשך", "מודל מכוון-אחזור (E5), למטיזציה עברית, וסט הערכה גדול ומדורג יותר."],
    ];
    for (let i = 0; i < pts.length; i++) {
      const [ic, t, d] = pts[i];
      const x = i % 2 === 0 ? 6.75 : 0.6;
      const yy = 2.05 + Math.floor(i / 2) * 2.35;
      card(s, x, yy, 5.95, 2.05, INK2);
      iconChip(s, x + 5.0, yy + 0.35, 0.72, ic, TEAL);
      T(s, t, { x: x + 0.3, y: yy + 0.32, w: 4.55, h: 0.75, fontFace: FH, fontSize: 17.5, bold: true, color: PAPER, valign: "middle", align: "right", margin: 0 });
      T(s, d, { x: x + 0.34, y: yy + 1.12, w: 5.3, h: 0.85, fontFace: FB, fontSize: 13, color: "D7E8E6", lineSpacingMultiple: 1.15, align: "right", margin: 0 });
    }
    pageNum(s, ++PN);
  }

  // ---------- 18. ETHICS ----------
  {
    const s = content("NLP אחראי", "אתיקה ומגבלות");
    const items = [
      [ICN.globe.white, "נתונים ציבוריים ומורשים", "כל-זכות (CC-BY-SA) + מידע ציבורי של ביטוח לאומי. ללא מידע אישי, ללא סריקת תוכן משתמשים.", TEAL],
      [ICN.shield.white, "אינו ייעוץ משפטי", "אב-טיפוס מחקרי. שימוש אמיתי חייב להציג קישורי מקור ולהפנות לרשות המוסמכת.", AMBER],
      [ICN.comments.white, "הטיה וכיסוי", "שישה תחומים בלבד; המורפולוגיה העברית פוגעת בלקסיקלי; ל-AlephBERT ייתכנו הטיות מקדם-אימון.", TEAL],
      [ICN.scroll.white, "סט הערכה קטן", "40 שאלות, מתייג יחיד: מצביע על מגמה, אך אינו מובהק סטטיסטית.", TEAL],
    ];
    let i = 0;
    for (const [ic, t, d, col] of items) {
      const x = i % 2 === 0 ? 6.75 : 0.6;
      const y = 1.95 + Math.floor(i / 2) * 2.35;
      card(s, x, y, 5.95, 2.05, i < 2 ? MIST : MIST2);
      iconChip(s, x + 5.0, y + 0.35, 0.72, ic, col);
      T(s, t, { x: x + 0.3, y: y + 0.3, w: 4.55, h: 0.75, fontFace: FH, fontSize: 17, bold: true, color: INKTX, valign: "middle", align: "right", margin: 0 });
      T(s, d, { x: x + 0.34, y: y + 1.1, w: 5.35, h: 0.85, fontFace: FB, fontSize: 12.5, color: MUTE, lineSpacingMultiple: 1.15, align: "right", margin: 0 });
      i++;
    }
  }

  // ---------- 19. CLOSING ----------
  {
    const s = pres.addSlide();
    s.background = { color: INK };
    for (let i = 0; i < 4; i++) {
      const r = 1.2 + i * 1.0;
      SH(s, pres.shapes.OVAL, { x: 2.0 - r / 2, y: 6.0 - r / 2, w: r, h: r, fill: { type: "none" }, line: { color: TEALLT, width: 1, transparency: 60 } });
    }
    iconChip(s, 2.55, 0.8, 0.85, ICN.scale.white, TEAL);
    T(s, "תודה", { x: 2.3, y: 2.2, w: 10.1, h: 1.0, fontFace: FH, fontSize: 44, bold: true, color: PAPER, align: "right", margin: 0 });
    T(s, "אחזור סמנטי בעברית לשאלות על זכויות חברתיות", { x: 2.3, y: 3.25, w: 10.1, h: 0.6, fontFace: FH, fontSize: 20, italic: true, color: TEALLT, align: "right", margin: 0 });
    T(s, [
      { text: "github.com/YanikGotie/hebrew-rights-retrieval   ·   ", options: { color: "AFCDCB" } },
      { text: "יניק גוטיה", options: { bold: true, color: PAPER } },
    ], { x: 2.3, y: 4.05, w: 10.1, h: 0.4, fontFace: FB, fontSize: 14, align: "right", margin: 0 });

    card(s, 0.9, 4.9, 11.5, 1.5, INK2);
    iconChip(s, 11.75, 5.25, 0.7, ICN.robot.white, TEAL);
    T(s, "גילוי נאות על שימוש ב-AI", { x: 6.8, y: 5.3, w: 4.7, h: 0.45, fontFace: FH, fontSize: 16, bold: true, color: PAPER, align: "right", margin: 0 });
    T(s, "נעשה שימוש בעוזר AI ככלי לכתיבת קוד (תבניות, תיעוד, ניפוי שגיאות). תכנון המחקר, הנתונים, סט ההערכה והמסקנות הם של המחבר; כל הקוד נבדק והובן.",
      { x: 1.15, y: 5.78, w: 10.4, h: 0.6, fontFace: FB, fontSize: 12.5, color: "CFE6E4", lineSpacingMultiple: 1.1, align: "right", margin: 0 });
  }

  await pres.writeFile({ fileName: "reports/presentation.pptx" });
  console.log("wrote reports/presentation.pptx (Hebrew RTL)");
}
build().catch(e => { console.error(e); process.exit(1); });
