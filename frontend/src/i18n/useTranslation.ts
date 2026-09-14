import { create } from "zustand";
import { pt } from "./pt";
import { en } from "./en";

export type Language = "pt" | "en";

interface TranslationStore {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: keyof typeof pt) => string;
}

export const useTranslation = create<TranslationStore>((set, get) => ({
  language: (localStorage.getItem("nexusfleet_lang") as Language) || "pt",
  setLanguage: (lang: Language) => {
    localStorage.setItem("nexusfleet_lang", lang);
    set({ language: lang });
  },
  t: (key: keyof typeof pt) => {
    const lang = get().language;
    const dict = lang === "pt" ? pt : en;
    return dict[key] || pt[key] || key;
  },
}));
