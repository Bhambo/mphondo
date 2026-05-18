import { create } from "zustand";
import { api } from "@/lib/api";

export interface Transaction {
  id: string;
  description: string;
  occurred_at: string;
  module: "mz" | "es";
  category_name: string | null;
  category_color: string | null;
  net_amount: number;
  currency: "MZN" | "EUR";
  deleted_at: string | null;
}

interface TransactionsState {
  transactions: Transaction[];
  isLoading: boolean;
  error: string | null;
  page: number;
  hasMore: boolean;
  fetchTransactions: (reset?: boolean) => Promise<void>;
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

  fetchTransactions: async (reset = false) => {
    const { isLoading, hasMore, page } = get();
    if (isLoading || (!reset && !hasMore)) return;

    const nextPage = reset ? 0 : page;
    set({ isLoading: true, error: null });

    try {
      const offset = nextPage * PAGE_SIZE;
      const data = await api.get<Transaction[]>(
        `/ledger/transactions?limit=${PAGE_SIZE}&offset=${offset}`,
      );
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
