/**
 * Nepali-English mixing helpers for client-side text processing
 */

// Check if text contains Devanagari script
function containsDevanagari(s) {
  return /[\u0900-\u097F]/.test(s || '');
}

// Basic Devanagari to Roman transliteration
function devToRoman(s) {
  if (!s) return s;
  const table = {
    'अ':'a','आ':'aa','इ':'i','ई':'ii','उ':'u','ऊ':'uu','ए':'e','ऐ':'ai','ओ':'o','औ':'au','ऋ':'ri',
    'ा':'a','ि':'i','ी':'i','ु':'u','ू':'u','े':'e','ै':'ai','ो':'o','ौ':'au','ं':'n','ः':'h','ँ':'n',
    'क':'ka','ख':'kha','ग':'ga','घ':'gha','ङ':'nga',
    'च':'cha','छ':'chha','ज':'ja','झ':'jha','ञ':'nya',
    'ट':'ta','ठ':'tha','ड':'da','ढ':'dha','ण':'na',
    'त':'ta','थ':'tha','द':'da','ध':'dha','न':'na',
    'प':'pa','फ':'pha','ब':'ba','भ':'bha','म':'ma',
    'य':'ya','र':'ra','ल':'la','व':'wa','स':'sa','ह':'ha','श':'sha','ष':'sha','क्ष':'ksha','त्र':'tra','ज्ञ':'gya'
  };
  let out = '';
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    out += table[ch] || ch;
  }
  return out;
}

// Mix English with Nepali words
function toNepEngMix(s) {
  if (!s) return s;
  const map = [
    [/\bOrganic chemistry\b/gi, 'Organic chemistry'],
    [/\bbranch of chemistry\b/gi, 'chemistry को शाखा'],
    [/\bchemistry\b/gi, 'chemistry'],
    [/\bcarbon[- ]based compounds\b/gi, 'carbon-आधारित compounds'],
    [/\bproperties\b/gi, 'properties/गुणहरू'],
    [/\bstructures\b/gi, 'structures/संरचनाहरू'],
    [/\breactions\b/gi, 'reactions/प्रतिक्रियाहरू'],
    [/\bcompounds\b/gi, 'compounds/यौगिकहरू'],
    [/\binclude\b/gi, 'समावेश गर्छन्'],
    [/\bexamples of\b/gi, 'केही examples of'],
    [/\bsolids\b/gi, 'Solids/ठोस'],
    [/\bliquids\b/gi, 'Liquids/तरल'],
    [/\bgases\b/gi, 'Gases/ग्यास'],
    [/\bartificial(ly)?\b/gi, 'artificial/कृत्रिम'],
    [/\bindustries\b/gi, 'industries/उद्योगहरू'],
    [/\bpharmaceuticals\b/gi, 'pharmaceuticals'],
    [/\bfood production\b/gi, 'food production'],
    [/\btherefore\b/gi, 'त्यसैले'],
    [/\balso\b/gi, 'पनि'],
    [/\bthat\b/gi, ''],
  ];
  let out = s;
  for (const [re, rep] of map) out = out.replace(re, rep);
  
  // Add Nepali framing if it looks like a single-line definition
  if (/\bOrganic chemistry\b/i.test(out)) {
    out = out.replace(/^[\s\S]*?Organic chemistry/i, 'Organic chemistry भनेको');
    out = out.replace(/\bis\b/i, 'हो');
  }
  return out;
}

// Main function to process text for Nepali mixing
function maybeMixNepEng(text) {
  const base = containsDevanagari(text) ? devToRoman(text) : toNepEngMix(text);
  return base;
}

// Export for use in components
window.nepaliHelpers = {
  containsDevanagari,
  devToRoman,
  toNepEngMix,
  maybeMixNepEng
};
