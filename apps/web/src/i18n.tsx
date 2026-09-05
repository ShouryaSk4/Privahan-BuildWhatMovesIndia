// Lightweight bilingual layer (English / हिंदी) for the portal chrome.
//
// The original portal mixes languages with no toggle; this gives the citizen
// one explicit switch, persisted locally, that flips every landing/journey
// chrome string. A module-level store (useSyncExternalStore) keeps it usable
// from any component without restructuring the app around a provider.

import { useSyncExternalStore } from "react";

export type Lang = "en" | "hi";

const LANG_KEY = "parivahan_lang";

let lang: Lang = (() => {
  try {
    return localStorage.getItem(LANG_KEY) === "hi" ? "hi" : "en";
  } catch {
    return "en";
  }
})();

const listeners = new Set<() => void>();

export function setLang(next: Lang): void {
  lang = next;
  try {
    localStorage.setItem(LANG_KEY, next);
  } catch {
    /* storage unavailable — toggle still works for this visit */
  }
  document.documentElement.lang = next;
  listeners.forEach((fn) => fn());
}

export function useLang(): Lang {
  return useSyncExternalStore(
    (cb) => {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    () => lang,
    () => "en",
  );
}

export interface StepStrings {
  title: string;
  subtitle: string;
}

const EN = {
    // Header chrome
    ministry: "Ministry of Road Transport & Highways (MoRTH)",
    helpline: "24x7 Helpline: 1800-180-0147 (toll-free)",
    tagline: "Official portal for driving licences & transport services",
    signIn: "Sign in (OTP)",
    ekycReady: "e-KYC ready",
    switchExit: "Switch / Exit",
    voiceButton: "🎙️ Bol Ke Apply · Voice help",
    voiceTitle: "Apply, check status, or ask questions by speaking — Hindi, English, or Hinglish",
    skipToContent: "Skip to main content",
    fontSmaller: "Decrease text size",
    fontReset: "Default text size",
    fontLarger: "Increase text size",
    highContrast: "High contrast",

    // Journey progress
    youAreHere: "You are here",
    stepWord: "Step",
    ofWord: "of",
    stepProgress: "Step {n} of {total}",
    nextWord: "Next",
    journeyDone: "Journey complete",
    showAllSteps: "View all 9 milestones",
    hideAllSteps: "Hide milestones",
    steps: [
      { title: "Discover & Intent", subtitle: "Portal landing" },
      { title: "e-KYC & Auth", subtitle: "Aadhaar / OTP" },
      { title: "Licence Class", subtitle: "LMV / MCWG" },
      { title: "Zero-Form Dossier", subtitle: "DigiLocker verified" },
      { title: "Learner's Test", subtitle: "Online or centre" },
      { title: "LL Issued", subtitle: "Digital permit" },
      { title: "30-Day Practice", subtitle: "Safety academy" },
      { title: "Track-Test Slot", subtitle: "ADTT booking" },
      { title: "DL Issued", subtitle: "Smart card" },
    ] as StepStrings[],

    // Hero
    heroEyebrow: "Ministry of Road Transport & Highways · Government of India",
    heroHeading: "What would you like to do today?",
    heroSub:
      "Zero paperwork, transparent statutory rules, and instant verification through DigiLocker & Aadhaar e-KYC.",
    statsTitle: "Your journey, guaranteed by rules",
    statCost: "total statutory fee",
    statDays: "days, end to end",
    statVisits: "RTO visit — just the track test",
    statsNote: "Fixed by Delhi RTO rules shown up-front — no surprises, no agents.",

    // Task cards
    recommendedBadge: "★ Recommended — first-time applicants",
    card1Title: "Apply for a New Driving Licence",
    card1Points: [
      "Zero forms — details auto-filled via Aadhaar e-KYC",
      "Learner's test online from home, AI-proctored",
      "One RTO visit, with a pre-booked track test",
    ],
    card1Cta: "Start New Application",
    card2Title: "Apply from Another State",
    card2Points: [
      "Away from your Aadhaar address? No affidavits",
      "Pick your home-state or local RTO — your choice",
      "Same zero-form flow; jurisdiction handled for you",
    ],
    card2Cta: "Start Inter-State Application",
    card3Title: "Check Rejection Risk First",
    card3Points: [
      "Cross-checks Aadhaar ↔ PAN before you pay",
      "Catches name / DOB / address mismatches early",
      "Fix issues before the RTO ever sees them",
    ],
    card3Cta: "Run Free Pre-Check",
    card4Title: "Bol Ke Apply — Voice Assistant",
    card4Points: [
      "Speak Hindi, English, or Hinglish",
      "Check status, book slots, ask RTO rules",
      "Built for assisted and low-literacy use",
    ],
    card4Cta: "Start Speaking",

    // Sign-in / resume
    welcomeBack: "Welcome back.",
    resumeBody: "is exactly where you left it — nothing was lost.",
    resumeCta: "Continue where I left off →",
    signinHeading: "Select a Citizen Profile or Enter Reference ID",
    signinSub: "Choose a verified persona below to experience the complete citizen journey end-to-end:",
    personaTitle: "Verified demo citizen profiles:",
    startFresh: "Start Fresh →",
    customIdLabel: "Or enter a custom Citizen Reference ID:",
    continueCta: "Continue Application →",
    formatHint: "Format: 4–32 letters, numbers, or underscores (e.g.",
};

export type Strings = typeof EN;

const HI: Strings = {
    ministry: "सड़क परिवहन और राजमार्ग मंत्रालय (MoRTH)",
    helpline: "24x7 हेल्पलाइन: 1800-180-0147 (टोल-फ्री)",
    tagline: "ड्राइविंग लाइसेंस और परिवहन सेवाओं का आधिकारिक पोर्टल",
    signIn: "साइन इन (OTP)",
    ekycReady: "e-KYC तैयार",
    switchExit: "बदलें / बाहर निकलें",
    voiceButton: "🎙️ बोल के अप्लाई · आवाज़ से मदद",
    voiceTitle: "बोलकर आवेदन करें, स्थिति जाँचें या सवाल पूछें — हिंदी, अंग्रेज़ी या हिंग्लिश में",
    skipToContent: "मुख्य सामग्री पर जाएँ",
    fontSmaller: "अक्षर छोटे करें",
    fontReset: "सामान्य आकार",
    fontLarger: "अक्षर बड़े करें",
    highContrast: "उच्च कंट्रास्ट",

    youAreHere: "आप यहाँ हैं",
    stepWord: "चरण",
    ofWord: "में से",
    stepProgress: "{total} में से चरण {n}",
    nextWord: "आगे",
    journeyDone: "यात्रा पूर्ण",
    showAllSteps: "सभी 9 पड़ाव देखें",
    hideAllSteps: "पड़ाव छिपाएँ",
    steps: [
      { title: "शुरुआत", subtitle: "पोर्टल होम" },
      { title: "e-KYC व प्रमाणीकरण", subtitle: "आधार / OTP" },
      { title: "लाइसेंस श्रेणी", subtitle: "LMV / MCWG" },
      { title: "ज़ीरो-फ़ॉर्म दस्तावेज़", subtitle: "डिजिलॉकर सत्यापित" },
      { title: "लर्नर टेस्ट", subtitle: "ऑनलाइन या केंद्र" },
      { title: "LL जारी", subtitle: "डिजिटल परमिट" },
      { title: "30-दिन अभ्यास", subtitle: "सेफ़्टी अकादमी" },
      { title: "ट्रैक-टेस्ट स्लॉट", subtitle: "ADTT बुकिंग" },
      { title: "DL जारी", subtitle: "स्मार्ट कार्ड" },
    ] as StepStrings[],

    heroEyebrow: "सड़क परिवहन और राजमार्ग मंत्रालय · भारत सरकार",
    heroHeading: "आज आप क्या करना चाहेंगे?",
    heroSub:
      "कोई काग़ज़ी कार्रवाई नहीं, पारदर्शी नियम, और डिजिलॉकर व आधार e-KYC से तुरंत सत्यापन।",
    statsTitle: "आपकी यात्रा — नियमों की गारंटी के साथ",
    statCost: "कुल सरकारी शुल्क",
    statDays: "दिन, शुरू से अंत तक",
    statVisits: "RTO विज़िट — सिर्फ़ ट्रैक टेस्ट",
    statsNote: "दिल्ली RTO के नियम पहले से दिखाए गए — न कोई चौंकाने वाला शुल्क, न एजेंट।",

    recommendedBadge: "★ अनुशंसित — पहली बार आवेदन करने वालों के लिए",
    card1Title: "नया ड्राइविंग लाइसेंस बनवाएँ",
    card1Points: [
      "कोई फ़ॉर्म नहीं — आधार e-KYC से विवरण अपने-आप",
      "लर्नर टेस्ट घर से ऑनलाइन, AI निगरानी में",
      "सिर्फ़ एक RTO विज़िट, ट्रैक टेस्ट पहले से बुक",
    ],
    card1Cta: "नया आवेदन शुरू करें",
    card2Title: "दूसरे राज्य से आवेदन करें",
    card2Points: [
      "आधार पते से दूर रहते हैं? कोई शपथ-पत्र नहीं",
      "गृह-राज्य या स्थानीय RTO — चुनाव आपका",
      "वही ज़ीरो-फ़ॉर्म प्रक्रिया; क्षेत्राधिकार हम सँभालेंगे",
    ],
    card2Cta: "अंतर-राज्य आवेदन शुरू करें",
    card3Title: "पहले अस्वीकृति का जोखिम जाँचें",
    card3Points: [
      "भुगतान से पहले आधार ↔ PAN का मिलान",
      "नाम / जन्मतिथि / पते की गड़बड़ी पहले पकड़ें",
      "RTO तक पहुँचने से पहले ही सुधार लें",
    ],
    card3Cta: "मुफ़्त प्री-चेक चलाएँ",
    card4Title: "बोल के अप्लाई — वॉइस असिस्टेंट",
    card4Points: [
      "हिंदी, अंग्रेज़ी या हिंग्लिश में बोलें",
      "स्थिति जाँचें, स्लॉट बुक करें, नियम पूछें",
      "सहायता-प्राप्त व कम-साक्षरता उपयोग के लिए",
    ],
    card4Cta: "बोलना शुरू करें",

    welcomeBack: "फिर से स्वागत है।",
    resumeBody: "ठीक वहीं है जहाँ आपने छोड़ा था — कुछ भी नहीं खोया।",
    resumeCta: "जहाँ छोड़ा था वहीं से जारी रखें →",
    signinHeading: "नागरिक प्रोफ़ाइल चुनें या संदर्भ ID दर्ज करें",
    signinSub: "पूरी नागरिक यात्रा अनुभव करने के लिए नीचे एक सत्यापित प्रोफ़ाइल चुनें:",
    personaTitle: "सत्यापित डेमो नागरिक प्रोफ़ाइल:",
    startFresh: "नई शुरुआत →",
    customIdLabel: "या अपनी नागरिक संदर्भ ID दर्ज करें:",
    continueCta: "आवेदन जारी रखें →",
    formatHint: "प्रारूप: 4–32 अक्षर, अंक या अंडरस्कोर (जैसे",
};

const STRINGS: Record<Lang, Strings> = { en: EN, hi: HI };

export function useT(): Strings {
  return STRINGS[useLang()];
}

/** Fill a "{n} … {total}" style template. */
export function fmt(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) => String(vars[k] ?? ""));
}
