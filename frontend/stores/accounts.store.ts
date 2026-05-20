import { create } from "zustand";
import { api } from "@/lib/api";

const ASSET_TYPES = new Set(["mpesa", "bank_es", "cash_mz", "cash_es"]);

export interface Account {
  id: string;
  name: string;
  account_type: string;
  currency: "MZN" | "EUR";
  module_context: "mz" | "es";
  balance: number;
  is_active: boolean;
  color: string | null;
  icon: string | null;
  phone: string | null;
  iban: string | null;
}

interface AccountsState {
  accounts: Account[];
  isLoading: boolean;
  error: string | null;
  fetchAccounts: () => Promise<void>;
  totalBalance: (module: "mz" | "es") => number;
}

export const useAccountsStore = create<AccountsState>((set, get) => ({
  accounts: [],
  isLoading: false,
  error: null,

  fetchAccounts: async () => {
    set({ isLoading: true, error: null });
    try {
      const raw = await api.get<Account[]>("/accounts");
      set({ accounts: raw, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Erro ao carregar contas",
        isLoading: false,
      });
    }
  },

  totalBalance: (module) => {
    const { accounts } = get();
    return accounts
      .filter(
        (a) =>
          a.is_active &&
          a.module_context === module &&
          ASSET_TYPES.has(a.account_type),
      )
      .reduce((sum, a) => sum + Number(a.balance), 0);
  },
}));
