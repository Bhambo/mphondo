import { View, Text, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Colors } from "@/lib/theme";

// Sprint 9 — Analytics dashboard (EUR+MZN consolidado)
export default function RelatoriosScreen() {
  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: Colors.surface.bg }}
      edges={["bottom"]}
    >
      <View style={styles.placeholder}>
        <Text style={styles.icon}>📊</Text>
        <Text style={styles.title}>Relatórios</Text>
        <Text style={styles.subtitle}>Disponível no Sprint 9</Text>
        <Text style={styles.desc}>
          Dashboard consolidado EUR+MZN, patrimônio neto, gráficos de gastos e
          análise por categoria.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  placeholder: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 40,
    gap: 12,
  },
  icon: { fontSize: 48 },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: Colors.ink.primary,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.es.primary,
    fontWeight: "600",
  },
  desc: {
    fontSize: 14,
    color: Colors.ink.muted,
    textAlign: "center",
    lineHeight: 22,
    marginTop: 8,
  },
});
