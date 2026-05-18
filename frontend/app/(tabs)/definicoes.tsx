import { View, Text, TouchableOpacity, StyleSheet, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useAuthStore } from "@/stores/auth.store";
import { useModuleStore } from "@/stores/module.store";
import { Colors, moduleColors } from "@/lib/theme";

function SettingsRow({
  label,
  value,
  onPress,
}: {
  label: string;
  value?: string;
  onPress?: () => void;
}) {
  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={onPress ? 0.7 : 1}
      style={styles.row}
    >
      <Text style={styles.rowLabel}>{label}</Text>
      {value && <Text style={styles.rowValue}>{value}</Text>}
    </TouchableOpacity>
  );
}

export default function DefinicoesScreen() {
  const { user, signOut } = useAuthStore();
  const { activeModule, toggleModule } = useModuleStore();
  const mc = moduleColors(activeModule);

  const handleSignOut = () => {
    Alert.alert("Terminar sessão", "Tens a certeza?", [
      { text: "Cancelar", style: "cancel" },
      { text: "Sair", style: "destructive", onPress: signOut },
    ]);
  };

  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: Colors.surface.bg }}
      edges={["bottom"]}
    >
      <View style={{ padding: 16, gap: 16 }}>
        {/* Account */}
        <View>
          <Text style={styles.sectionTitle}>Conta</Text>
          <View style={styles.card}>
            <SettingsRow label="Email" value={user?.email ?? "—"} />
            <SettingsRow
              label="Módulo activo"
              value={activeModule === "mz" ? "🇲🇿 Mozambique (MZN)" : "🇪🇸 España (EUR)"}
              onPress={toggleModule}
            />
          </View>
        </View>

        {/* App */}
        <View>
          <Text style={styles.sectionTitle}>Aplicação</Text>
          <View style={styles.card}>
            <SettingsRow label="Versão" value="0.1.0 (Sprint 1)" />
            <SettingsRow label="Servidor" value="self-hosted · Tailscale" />
          </View>
        </View>

        {/* Logout */}
        <TouchableOpacity
          onPress={handleSignOut}
          activeOpacity={0.8}
          style={[styles.logoutBtn, { borderColor: Colors.negative }]}
        >
          <Text style={[styles.logoutText, { color: Colors.negative }]}>
            Terminar sessão
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  sectionTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: Colors.ink.muted,
    textTransform: "uppercase",
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  card: {
    backgroundColor: Colors.surface.level1,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: Colors.surface.border,
    overflow: "hidden",
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.surface.borderFaint,
  },
  rowLabel: {
    fontSize: 15,
    color: Colors.ink.primary,
  },
  rowValue: {
    fontSize: 14,
    color: Colors.ink.muted,
    maxWidth: "55%",
    textAlign: "right",
  },
  logoutBtn: {
    borderWidth: 1.5,
    borderRadius: 12,
    padding: 14,
    alignItems: "center",
  },
  logoutText: {
    fontSize: 15,
    fontWeight: "600",
  },
});
