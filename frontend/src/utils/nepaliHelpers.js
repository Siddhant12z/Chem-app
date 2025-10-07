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

// Roman to Devanagari conversion for TTS
function romanToDev(s) {
  if (!s) return s;
  
  // Enhanced Roman to Devanagari mapping
  const romanToDevMap = {
    // Vowels
    'a': 'अ', 'aa': 'आ', 'i': 'इ', 'ii': 'ई', 'u': 'उ', 'uu': 'ऊ', 
    'e': 'ए', 'ai': 'ऐ', 'o': 'ओ', 'au': 'औ',
    
    // Consonants
    'ka': 'क', 'kha': 'ख', 'ga': 'ग', 'gha': 'घ', 'nga': 'ङ',
    'cha': 'च', 'chha': 'छ', 'ja': 'ज', 'jha': 'झ', 'nya': 'ञ',
    'ta': 'ट', 'tha': 'ठ', 'da': 'ड', 'dha': 'ढ', 'na': 'ण',
    'ta': 'त', 'tha': 'थ', 'da': 'द', 'dha': 'ध', 'na': 'न',
    'pa': 'प', 'pha': 'फ', 'ba': 'ब', 'bha': 'भ', 'ma': 'म',
    'ya': 'य', 'ra': 'र', 'la': 'ल', 'wa': 'व', 'va': 'व',
    'sha': 'श', 'sa': 'स', 'ha': 'ह',
    
    // Common Nepali words
    'thik': 'ठिक', 'cha': 'छ', 'ramro': 'राम्रो', 'dherai': 'धेरै',
    'important': 'महत्वपूर्ण', 'ho': 'हो', 'hoin': 'होइन', 'ke': 'के',
    'kasari': 'कसरी', 'bujhnu': 'बुझ्नु', 'bhayo': 'भयो',
    'mahattwopurna': 'महत्वपूर्ण', 'kura': 'कुरा', 'tha': 'थ',
    'pauna': 'पाउनु', 'yo': 'यो', 'haina': 'हैन', 'haina': 'हैन',
    'interesting': 'रोचक', 'cha': 'छ'
  };
  
  // Sort by length (longest first) to handle compound words
  const sortedEntries = Object.entries(romanToDevMap).sort((a, b) => b[0].length - a[0].length);
  
  let result = s;
  
  // Convert common phrases first
  const phrases = [
    ['thik cha', 'ठिक छ'],
    ['ramro cha', 'राम्रो छ'],
    ['dherai important cha', 'धेरै महत्वपूर्ण छ'],
    ['bujhnu bhayo', 'बुझ्नु भयो'],
    ['ke bujhnu bhayo', 'के बुझ्नु भयो'],
    ['ramro cha,', 'राम्रो छ,'],
    ['dherai interesting cha,', 'धेरै रोचक छ,'],
    ['thik cha,', 'ठिक छ,']
  ];
  
  // Apply phrase replacements first
  for (const [roman, dev] of phrases) {
    const regex = new RegExp(roman, 'gi');
    result = result.replace(regex, dev);
  }
  
  // Then apply individual word replacements
  for (const [roman, dev] of sortedEntries) {
    const regex = new RegExp('\\b' + roman + '\\b', 'gi');
    result = result.replace(regex, dev);
  }
  
  return result;
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

// Function to convert Roman Nepali to Devanagari for TTS
function convertRomanToNepaliForTTS(text) {
  if (!text) return text;
  
  // First check if text already contains Devanagari
  if (containsDevanagari(text)) {
    return text; // Already in Devanagari
  }
  
  // Convert Roman Nepali to Devanagari
  return romanToDev(text);
}

// Export for use in components
window.nepaliHelpers = {
  containsDevanagari,
  devToRoman,
  romanToDev,
  toNepEngMix,
  maybeMixNepEng,
  convertRomanToNepaliForTTS
};
