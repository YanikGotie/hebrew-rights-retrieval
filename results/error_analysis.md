# Error Analysis — Lexical (TF-IDF) vs. Semantic (AlephBERT)

Each query is judged at document level (top-3). Rank `None` means the gold document was not retrieved in the top results. The diagnosis combines the manual `phrasing_gap` tag with the literal word overlap between the query and the gold title.


**Summary:** 4 semantic-wins, 5 lexical-wins, 7 both-fail (out of 40 queries).


## A. Semantic wins, lexical fails (synonymy / colloquial → formal)

**1. [q01 · unemployment] “פיטרו אותי מהעבודה, מה מגיע לי?”**  
- Gold: זכאות לדמי אבטלה, דמי אבטלה, דמי אבטלה  
- Lexical top-3: זכאות לגמלת הבטחת הכנסה ובעלות על רכב, ניכוי הכנסות מדמי אבטלה, איסור ניכוי שכר מנער הנעדר מעבודתו לצורך לימודי ערב בבית ספר מקצועי  
- Semantic top-3: דמי אבטלה, דמי אבטלה בתקופת מלחמת חרבות ברזל (מלחמת התקומה), התפטרות בנסיבות המזכות בדמי אבטלה ללא תקופת המתנה  
- Gold rank — lexical: 11, semantic: 1  
- Diagnosis: phrasing_gap=`high`, query↔gold-title word overlap=`0`. Zero shared content words — lexical had nothing to match; embeddings bridged the vocabulary gap.

**2. [q07 · unemployment] “חייבים להגיע ללשכת התעסוקה כל הזמן?”**  
- Gold: התייצבות בשירות התעסוקה  
- Lexical top-3: מדריך לקבלת הבטחת הכנסה, חיפוש משרות ושליחת קורות חיים ישירות למעסיקים באמצעות אתר שירות התעסוקה, זכאות לגמלת הבטחת הכנסה  
- Semantic top-3: התייצבות בשירות התעסוקה, דמי אבטלה בתקופת מלחמת חרבות ברזל (מלחמת התקומה), הכשרה מקצועית לדורשי עבודה  
- Gold rank — lexical: 4, semantic: 1  
- Diagnosis: phrasing_gap=`high`, query↔gold-title word overlap=`1`. Low surface overlap; the embedding captured meaning the sparse model under-weighted.

**3. [q09 · welfare] “אין לי הכנסה בכלל, איזו קצבה אפשר לקבל?”**  
- Gold: גמלת הבטחת הכנסה (השלמת הכנסה), זכאות לגמלת הבטחת הכנסה, הבטחת הכנסה  
- Lexical top-3: דמי אבטלה, אלי"ע, קצבת שאירים למקבלי קצבאות נוספות  
- Semantic top-3: הבטחת הכנסה, זכאות לגמלת הבטחת הכנסה, מדריך לקבלת הבטחת הכנסה  
- Gold rank — lexical: 9, semantic: 1  
- Diagnosis: phrasing_gap=`high`, query↔gold-title word overlap=`1`. Low surface overlap; the embedding captured meaning the sparse model under-weighted.

**4. [q18 · disability] “הבן שלי נכה, יש ועדה רפואית מיוחדת לילדים?”**  
- Gold: ועדה רפואית לילד נכה מעל גיל 3, ועדה רפואית לילד נכה עד גיל 3  
- Lexical top-3: קביעת נכות לחולי סוכרת, בדיקת תלות לגמלת ילד נכה, הקלות לחולי סרטן בפניות אל המוסד לביטוח לאומי לצורך קביעת נכות  
- Semantic top-3: בדיקת תלות לגמלת ילד נכה, ועדה רפואית לילד נכה מעל גיל 3, מדריך להורים של ילדים עם מוגבלות  
- Gold rank — lexical: 4, semantic: 2  
- Diagnosis: phrasing_gap=`high`, query↔gold-title word overlap=`3`. Low surface overlap; the embedding captured meaning the sparse model under-weighted.


## B. Lexical wins, semantic fails (exact-term advantage)

**5. [q05 · unemployment] “כמה חודשים צריך לעבוד כדי לקבל דמי אבטלה?”**  
- Gold: זכאות לדמי אבטלה, מבוטח בביטוח אבטלה  
- Lexical top-3: מבוטח בביטוח אבטלה, דמי אבטלה, התייצבות בשירות התעסוקה  
- Semantic top-3: מענק למובטל העובד בשכר נמוך, דמי אבטלה, דמי אבטלה לעובדים עצמאים  
- Gold rank — lexical: 1, semantic: 16  
- Diagnosis: phrasing_gap=`medium`, query↔gold-title word overlap=`1`. Distinctive shared term(s) gave the sparse model a precise signal the embedding diffused.

**6. [q28 · family] “מה זה אומנה ואיך זה עובד?”**  
- Gold: אומנה  
- Lexical top-3: חוק אומנה לילדים, אומנה, איסור פיטורי הורה במשפחת אומנה לפני קבלת הילד לביתו  
- Semantic top-3: מדריך להורים של בוגרים עם מוגבלות, אי הסכמת הורה ביולוגי לשילוב ילדו באומנה, הבטחת הכנסה  
- Gold rank — lexical: 2, semantic: 5  
- Diagnosis: phrasing_gap=`low`, query↔gold-title word overlap=`1`. Distinctive shared term(s) gave the sparse model a precise signal the embedding diffused.

**7. [q36 · health] “אפשר לקבל כיסא גלגלים ומכשירי שיקום?”**  
- Gold: אביזרי ומכשירי שיקום  
- Lexical top-3: אביזרי ומכשירי שיקום, אמבולנס המשאלות לחולים במחלה קשה או סופנית, מדריך להורים של בוגרים עם מוגבלות  
- Semantic top-3: אור לעולם, מדריך להורים של ילדים עם מוגבלות, מדריך להורים של בוגרים עם מוגבלות  
- Gold rank — lexical: 1, semantic: None  
- Diagnosis: phrasing_gap=`high`, query↔gold-title word overlap=`2`. Distinctive shared term(s) gave the sparse model a precise signal the embedding diffused.

**8. [q37 · health] “התינוק שלי מתעכב בהתפתחות, לאן פונים לאבחון?”**  
- Gold: אבחון רפואי התפתחותי לילדים (שירותי התפתחות הילד)  
- Lexical top-3: ביטול הנוהל המחייב עובדת זרה שילדה לעזוב את ישראל עם התינוק, אבחון רפואי התפתחותי לילדים (שירותי התפתחות הילד), אוטיזם קלאסי  
- Semantic top-3: קביעת נכות בגין מחלות כבד, קביעת נכות בגלל הפרעת קשב ופעלתנות יתר, ועדה רפואית לילד נכה עד גיל 3  
- Gold rank — lexical: 2, semantic: 27  
- Diagnosis: phrasing_gap=`high`, query↔gold-title word overlap=`0`. Distinctive shared term(s) gave the sparse model a precise signal the embedding diffused.

**9. [q40 · elderly] “הגעתי לגיל פרישה ואין לי קצבה, מה עושים?”**  
- Gold: הבטחת הכנסה מגיל פרישה למי שלא זכאים לקצבת אזרח ותיק  
- Lexical top-3: זכאות לגמלת הבטחת הכנסה ובעלות על רכב, הבטחת הכנסה מגיל פרישה למי שלא זכאים לקצבת אזרח ותיק, מדריך לקבלת הבטחת הכנסה  
- Semantic top-3: הטבה בחשבון המים למקבלי קצבת שאירים עם השלמת הכנסה בגיל פרישה, הטבה בחשבון המים למקבלי קצבת זיקנה עם השלמת הכנסה, הגשת תביעה לגמלת הבטחת הכנסה  
- Gold rank — lexical: 2, semantic: 13  
- Diagnosis: phrasing_gap=`high`, query↔gold-title word overlap=`1`. Distinctive shared term(s) gave the sparse model a precise signal the embedding diffused.


## C. Both fail (hard cases)

**10. [q02 · unemployment] “איך מגישים בקשה לדמי אבטלה?”**  
- Gold: הגשת תביעה לדמי אבטלה  
- Lexical top-3: זכאות לדמי אבטלה, דמי אבטלה לעובדים עצמאים, הגשת תביעה חוזרת לדמי אבטלה  
- Semantic top-3: דמי אבטלה, הגשת תביעה חוזרת לדמי אבטלה, התייצבות בשירות התעסוקה  
- Gold rank — lexical: 4, semantic: 6  
- Diagnosis: phrasing_gap=`low`, query↔gold-title word overlap=`2`. Sparse corpus coverage / ambiguous phrasing — neither signal was strong enough.

**11. [q03 · unemployment] “התפטרתי כי עברתי דירה רחוק, אקבל דמי אבטלה?”**  
- Gold: התפטרות בנסיבות המזכות בדמי אבטלה ללא תקופת המתנה  
- Lexical top-3: דמי אבטלה בתקופת מלחמת חרבות ברזל (מלחמת התקומה), דמי אבטלה, ניכוי הכנסות מדמי אבטלה  
- Semantic top-3: דמי אבטלה, אבטלה וזכויות מובטלים/פסקי דין, דמי אבטלה  
- Gold rank — lexical: None, semantic: 12  
- Diagnosis: phrasing_gap=`high`, query↔gold-title word overlap=`1`. Sparse corpus coverage / ambiguous phrasing — neither signal was strong enough.

**12. [q13 · welfare] “אני מקבל קצבה, מגיעה לי הנחה בחשמל?”**  
- Gold: הנחה בחשבון חשמל למקבלי הבטחת הכנסה  
- Lexical top-3: קצבת נכות כללית, קצבת זקנה, הבטחת הכנסה  
- Semantic top-3: דמי אבטלה, הבטחת הכנסה לאסירים משוחררים, אטקסיה טלנגיאקטזיה (AT)  
- Gold rank — lexical: 5, semantic: 9  
- Diagnosis: phrasing_gap=`high`, query↔gold-title word overlap=`1`. Sparse corpus coverage / ambiguous phrasing — neither signal was strong enough.

**13. [q15 · disability] “איך מקבלים קצבת נכות?”**  
- Gold: קצבת נכות כללית  
- Lexical top-3: דמי אבטלה בתקופת מלחמת חרבות ברזל (מלחמת התקומה), זכאות לגמלת הבטחת הכנסה ובעלות על רכב, מדריך להורים של בוגרים עם מוגבלות  
- Semantic top-3: קביעת נכות לחולי סרטן, קביעת נכות לחולי פרקינסון, קביעת נכות לחולי כליות  
- Gold rank — lexical: 12, semantic: 23  
- Diagnosis: phrasing_gap=`medium`, query↔gold-title word overlap=`2`. Sparse corpus coverage / ambiguous phrasing — neither signal was strong enough.

**14. [q19 · disability] “אני חולה סרטן, איך קובעים לי אחוזי נכות?”**  
- Gold: הקלות לחולי סרטן בפניות אל המוסד לביטוח לאומי לצורך קביעת נכות, קביעת זכאות לקצבת שירותים מיוחדים לחולי סרטן ללא נוכחות בוועדה רפואית  
- Lexical top-3: קביעת נכות לחולי סרטן, קביעת נכות בגין מחלות דם, קביעת נכות בגין בעיות אורתופדיות  
- Semantic top-3: קביעת נכות לחולי סרטן, קביעת נכות בגין מחלות דם, קביעת נכות בגין מחלות של הוורידים  
- Gold rank — lexical: None, semantic: None  
- Diagnosis: phrasing_gap=`high`, query↔gold-title word overlap=`2`. Sparse corpus coverage / ambiguous phrasing — neither signal was strong enough.

**15. [q22 · parenting] “אני בהריון, מותר למעסיק לפטר אותי?”**  
- Gold: איסור אפליית עובדת בשל היותה בהיריון  
- Lexical top-3: איסור פגיעה בהיקף משרה או בהכנסה של עובדת או עובד הנמצא/ת בחופשת לידה ולאחריה, איסור פיטורי עובד/ת במהלך חופשת לידה, איסור פיטורי הורה מיועד לפי חוק הסכמים לנשיאת עוברים במהלך ההיריון  
- Semantic top-3: איסור פיטורי עובד/ת במהלך חופשת לידה, איסור פיטורי עובד/ת במהלך טיפולי פוריות, איסור פיטורי הורה מיועד לפי חוק הסכמים לנשיאת עוברים במהלך ההיריון  
- Gold rank — lexical: 11, semantic: 8  
- Diagnosis: phrasing_gap=`high`, query↔gold-title word overlap=`0`. Sparse corpus coverage / ambiguous phrasing — neither signal was strong enough.

**16. [q25 · parenting] “כמה כסף מקבלים על חופשת לידה?”**  
- Gold: דמי לידה  
- Lexical top-3: איסור פגיעה בהיקף משרה או בהכנסה של עובדת או עובד הנמצא/ת בחופשת לידה ולאחריה, איסור פיטורים של עובד/ת בחל"ת לאחר חופשת לידה ואחריה, איסור פיטורי עובד/ת לאחר חופשת לידה  
- Semantic top-3: קצבת ילדים, מענק לימודים למשפחות שבראשן הורה עצמאי (משפחות חד הוריות), מדריך לקבלת הבטחת הכנסה  
- Gold rank — lexical: 12, semantic: None  
- Diagnosis: phrasing_gap=`medium`, query↔gold-title word overlap=`1`. Sparse corpus coverage / ambiguous phrasing — neither signal was strong enough.
