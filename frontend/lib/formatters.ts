import { format, parseISO } from "date-fns";
import { ptBR } from "date-fns/locale";

export function formatCurrency(
  amount: number,
  currency: "MZN" | "EUR",
): string {
  if (currency === "EUR") {
    return new Intl.NumberFormat("pt-PT", {
      style: "currency",
      currency: "EUR",
      minimumFractionDigits: 2,
    }).format(amount);
  }
  return `${new Intl.NumberFormat("pt-MZ", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)} MZN`;
}

export function formatDate(isoString: string, fmt = "dd MMM yyyy"): string {
  return format(parseISO(isoString), fmt, { locale: ptBR });
}

export function formatRelativeDate(isoString: string): string {
  const date = parseISO(isoString);
  const now = new Date();
  const diffDays = Math.floor(
    (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24),
  );
  if (diffDays === 0) return "Hoje";
  if (diffDays === 1) return "Ontem";
  if (diffDays < 7) return `Há ${diffDays} dias`;
  return format(date, "dd MMM", { locale: ptBR });
}

export function formatAmount(amount: number, showSign = false): string {
  const abs = Math.abs(amount);
  const formatted = new Intl.NumberFormat("pt-PT", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(abs);
  if (!showSign) return formatted;
  return amount >= 0 ? `+${formatted}` : `-${formatted}`;
}
