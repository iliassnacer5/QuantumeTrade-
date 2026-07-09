/** Concaténation conditionnelle de classes (mini-clsx, zéro dépendance). */
export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ');
}
