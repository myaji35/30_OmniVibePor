/**
 * i18n 다국어 지원 설정
 */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// 번역 파일 import
import ko from '../locales/ko.json';
import en from '../locales/en.json';
import ja from '../locales/ja.json';

i18n
  .use(LanguageDetector) // 브라우저 언어 자동 감지
  .use(initReactI18next) // React i18next 초기화
  .init({
    resources: {
      ko: { translation: ko },
      en: { translation: en },
      ja: { translation: ja },
    },
    fallbackLng: 'en', // 기본 언어
    debug: process.env.NODE_ENV === 'development',

    interpolation: {
      escapeValue: false, // React가 XSS 방지를 처리
    },

    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
    },
  });

export default i18n;
