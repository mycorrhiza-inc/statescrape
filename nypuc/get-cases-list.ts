
import { JSDOM } from 'jsdom';

export interface DocketInfo {
  docketId: string;
  href: string;
}

export function extractDocketDetails(htmlContent: string): DocketInfo[] {
  const dom = new JSDOM(htmlContent);
  const doc = dom.window.document;
  const links = doc.querySelectorAll('a[href*="MatterSeq"]');

  return Array.from(links).map(link => ({
    docketId: link.textContent?.trim() || '',
    href: link.getAttribute('href') || ''
  })).filter(info => info.docketId.match(/\d{2}-[A-Z]-\d{4}/));
}

export function extractDocketIds(htmlContent: string): string[] {
  const docketPattern = /\d{2}-[A-Z]-\d{4}/g;
  const matches = htmlContent.match(docketPattern);
  return matches || [];
}
