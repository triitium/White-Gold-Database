export function readCookie(name: string): string | null {
  const prefix = `${encodeURIComponent(name)}=`;

  for (const item of document.cookie.split(";")) {
    const cookie = item.trim();

    if (cookie.startsWith(prefix)) {
      return decodeURIComponent(cookie.slice(prefix.length));
    }
  }

  return null;
}
