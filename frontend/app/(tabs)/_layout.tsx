import { Tabs, Redirect, router } from "expo-router";
import { TouchableOpacity, View, Text, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useAuthStore } from "@/stores/auth.store";
import { useModuleStore } from "@/stores/module.store";
import { Colors } from "@/lib/theme";

// Inline SVG-like tab icons (Unicode symbols as placeholders; swap for Lucide later)
const ICONS: Record<string, { active: string; inactive: string }> = {
  dashboard: { active: "⬛", inactive: "⬜" },
  transacoes: { active: "◾", inactive: "◽" },
  relatorios: { active: "▪", inactive: "▫" },
  definicoes: { active: "⚙", inactive: "⚙" },
};

function ModuleToggle() {
  const { activeModule, toggleModule } = useModuleStore();
  const isMZ = activeModule === "mz";
  const color = isMZ ? Colors.mz.primary : Colors.es.primary;
  return (
    <TouchableOpacity
      onPress={toggleModule}
      activeOpacity={0.8}
      style={[styles.toggle, { borderColor: color }]}
    >
      <View style={[styles.togglePill, { backgroundColor: color }]}>
        <Text style={styles.toggleText}>{isMZ ? "MZ" : "ES"}</Text>
      </View>
    </TouchableOpacity>
  );
}

function FAB() {
  const { activeModule } = useModuleStore();
  const color =
    activeModule === "mz" ? Colors.mz.primary : Colors.es.primary;
  return (
    <TouchableOpacity
      onPress={() => router.push("/modals/quick-entry")}
      activeOpacity={0.85}
      style={[styles.fab, { backgroundColor: color }]}
    >
      <Text style={styles.fabIcon}>＋</Text>
    </TouchableOpacity>
  );
}

export default function TabsLayout() {
  const { session } = useAuthStore();
  const { activeModule } = useModuleStore();
  if (!session) return <Redirect href="/(auth)/login" />;

  const accent =
    activeModule === "mz" ? Colors.mz.primary : Colors.es.primary;

  return (
    <View style={{ flex: 1 }}>
      <Tabs
        screenOptions={{
          headerShown: true,
          headerStyle: { backgroundColor: Colors.surface.level1 },
          headerTintColor: Colors.ink.primary,
          headerShadowVisible: false,
          headerRight: () => <ModuleToggle />,
          tabBarStyle: {
            backgroundColor: Colors.surface.level1,
            borderTopColor: Colors.surface.border,
            borderTopWidth: 1,
            height: 60,
            paddingBottom: 8,
          },
          tabBarActiveTintColor: accent,
          tabBarInactiveTintColor: Colors.ink.faint,
          tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            title: "Dashboard",
            tabBarLabel: "Início",
            tabBarIcon: ({ focused, color }) => (
              <Text style={{ color, fontSize: 20 }}>
                {focused ? "■" : "□"}
              </Text>
            ),
          }}
        />
        <Tabs.Screen
          name="transacoes"
          options={{
            title: "Transações",
            tabBarIcon: ({ focused, color }) => (
              <Text style={{ color, fontSize: 20 }}>
                {focused ? "≡" : "≡"}
              </Text>
            ),
          }}
        />
        {/* FAB spacer tab */}
        <Tabs.Screen
          name="fab-placeholder"
          options={{
            title: "",
            tabBarButton: () => <FAB />,
            tabBarLabel: () => null,
          }}
        />
        <Tabs.Screen
          name="relatorios"
          options={{
            title: "Relatórios",
            tabBarIcon: ({ focused, color }) => (
              <Text style={{ color, fontSize: 20 }}>
                {focused ? "◈" : "◇"}
              </Text>
            ),
          }}
        />
        <Tabs.Screen
          name="definicoes"
          options={{
            title: "Definições",
            tabBarIcon: ({ focused, color }) => (
              <Text style={{ color, fontSize: 18 }}>⚙</Text>
            ),
          }}
        />
      </Tabs>
    </View>
  );
}

const styles = StyleSheet.create({
  toggle: {
    marginRight: 12,
    borderWidth: 1.5,
    borderRadius: 20,
    overflow: "hidden",
  },
  togglePill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  toggleText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  fab: {
    position: "absolute",
    bottom: 10,
    alignSelf: "center",
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 10,
  },
  fabIcon: {
    color: "#fff",
    fontSize: 28,
    lineHeight: 32,
  },
});
