import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import AsyncStorage from "@react-native-async-storage/async-storage";
import type { ModuleType } from "@/lib/theme";

interface ModuleState {
  activeModule: ModuleType;
  setModule: (module: ModuleType) => void;
  toggleModule: () => void;
}

export const useModuleStore = create<ModuleState>()(
  persist(
    (set, get) => ({
      activeModule: "mz",
      setModule: (module) => set({ activeModule: module }),
      toggleModule: () =>
        set({ activeModule: get().activeModule === "mz" ? "es" : "mz" }),
    }),
    {
      name: "mphondo-active-module",
      storage: createJSONStorage(() => AsyncStorage),
    },
  ),
);
