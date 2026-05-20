import { create } from "zustand";
import { api } from "@/lib/api";

interface EntryOut {
  id: string;
  account_id: string;
  direction: "debit" | "credit";
  amount: number;
}

export interface Transaction {
  id: string;
  description: string;
  occurred_at: string;
  module: "mz" | "es";
  status: string;
  currency: "MZN" | "EUR";
  is_transfer: boolean;
  category_id: string | null;
  // display-only: computed from entries[0] on fetch, set directly on optimistic append
  net_amount: number;
  category_name: string | null;
  category_color: string | null;
}

interface TransactionOut {
  id: string;
  description: string;
  occurred_at: string;
  module: string;
  status: string;
  currency: string;
  is_transfer: boolean;
  category_id: string | null;
  entries: EntryOut[];
}

function mapTransaction(t: TransactionOut): Transaction {
  const main = t.entries[0];
  const net_amount = main
    ? (main.direction === "credit" ? 1 : -1) * Number(main.amount)
    : 0;
  return {
    id: t.id,
    description: t.description,
    occurred_at: t.occurred_at,
    module: t.module as "mz" | "es",
    status: t.status,
    currency: t.currency as "MZN" | "EUR",
    is_transfer: t.is_transfer,
    category_id: t.category_id,
    net_amount,
    category_name: null,
    category_color: null,
  };
}

interface TransactionsState {
  transactions: Transaction[];
  isLoading: boolean;
  error: string | null;
  page: number;
  hasMore: boolean;
  fetchTransactions: (reset?: boolean, module?: "mz" | "es") => Promise<void>;
  appendTransaction: (tx: Transaction) => void;
  removeTransaction: (id: string) => void;
}

const PAGE_SIZE = 40;

export const useTransactionsStore = create<TransactionsState>((set, get) => ({
  transactions: [],
  isLoading: false,
  error: null,
  page: 0,
  hasMore: true,

  fetchTransactions: async (reset = false, module?: "mz" | "es") => {
    const { isLoading, hasMore, page } = get();
    if (isLoading || (!reset && !hasMore)) return;

    const nextPage = reset ? 0 : page;
    set({ isLoading: true, error: null });

    try {
      const offset = nextPage * PAGE_SIZE;
      const moduleParam = module ? `&module=${module}` : "";
      const raw = await api.get<TransactionOut[]>(
        `/ledger?limit=${PAGE_SIZE}&offset=${offset}${moduleParam}`,
      );
      const data = raw.map(mapTransaction);
      set((s) => ({
        transactions: reset ? data : [...s.transactions, ...data],
        page: nextPage + 1,
        hasMore: data.length === PAGE_SIZE,
        isLoading: false,
      }));
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Erro ao carregar",
        isLoading: false,
      });
    }
  },

  appendTransaction: (tx) =>
    set((s) => ({ transactions: [tx, ...s.transactions] })),

  removeTransaction: (id) =>
    set((s) => ({
      transactions: s.transactions.filter((t) => t.id !== id),
    })),
}));
