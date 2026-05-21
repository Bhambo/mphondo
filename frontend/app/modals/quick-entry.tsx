import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from "react-native";
import { router } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import { useModuleStore } from "@/stores/module.store";
import { useTransactionsStore } from "@/stores/transactions.store";
import { Colors, moduleColors } from "@/lib/theme";
import { api } from "@/lib/api";

type OpDirection = "entrada" | "saida";

const MZ_TYPES = [
  { key: "ingresso", label: "Ingresso", dir: "entrada" as OpDirection },
  { key: "recebido", label: "Recebido", dir: "entrada" as OpDirection },
  { key: "deposito", label: "Depósito", dir: "entrada" as OpDirection },
  { key: "envio_es", label: "Envio de ES", dir: "saida" as OpDirection },
  { key: "xitiqui", label: "Xitiqui", dir: "saida" as OpDirection },
  { key: "emprestimo", label: "Empréstimo", dir: "saida" as OpDirection },
  { key: "compra", label: "Compra", dir: "saida" as OpDirection },
  { key: "taxa", label: "Taxa M-Pesa", dir: "saida" as OpDirection },
];

const ES_TYPES = [
  { key: "income", label: "Rendimento", dir: "entrada" as OpDirection },
  { key: "transfer_in", label: "Transferência entrada", dir: "entrada" as OpDirection },
  { key: "purchase", label: "Compra", dir: "saida" as OpDirection },
  { key: "transfer_out", label: "Transferência saída", dir: "saida" as OpDirection },
  { key: "remesa", label: "Remessa p/ MZ", dir: "saida" as OpDirection },
];

export default function QuickEntryModal() {
  const { activeModule } = useModuleStore();
  const { appendTransaction } = useTransactionsStore();
  const mc = moduleColors(activeModule);
  const types = activeModule === "mz" ? MZ_TYPES : ES_TYPES;

  const [opType, setOpType] = useState(types[0].key);
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [counterpart, setCounterpart] = useState("");
  const [reference, setReference] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const selectedType = types.find((t) => t.key === opType) ?? types[0];

  const handleSave = async () => {
    const parsed = parseFloat(amount.replace(",", "."));
    if (!parsed || parsed <= 0) {
      Alert.alert("Valor inválido", "Insere um valor maior que zero.");
      return;
    }
    if (!description.trim()) {
      Alert.alert("Descrição em falta", "Adiciona uma descrição.");
      return;
    }

    setIsSaving(true);
    try {
      const payload = {
        op_type: opType,
        direction: selectedType.dir,
        amount: parsed,
        description: description.trim(),
        counterpart: counterpart.trim() || null,
        reference: reference.trim() || null,
        module: activeModule,
        occurred_at: new Date().toISOString(),
      };
      const tx = await api.post<{ transaction_id: string }>("/mpesa/manual", payload);
      // Optimistic update — full data fetched on next screen refresh
      appendTransaction({
        id: tx.transaction_id,
        description: description.trim(),
        occurred_at: new Date().toISOString(),
        module: activeModule,
        status: "confirmed",
        is_transfer: false,
        category_id: null,
        category_name: null,
        category_color: null,
        net_amount: selectedType.dir === "entrada" ? parsed : -parsed,
        currency: activeModule === "mz" ? "MZN" : "EUR",
      });
      router.back();
    } catch (err) {
      Alert.alert("Erro", err instanceof Error ? err.message : "Erro ao guardar");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: Colors.surface.bg }}
      edges={["top", "bottom"]}
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={[styles.cancelBtn, { color: mc.primary }]}>Cancelar</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Nova operação</Text>
        <TouchableOpacity onPress={handleSave} disabled={isSaving}>
          {isSaving ? (
            <ActivityIndicator color={mc.primary} />
          ) : (
            <Text style={[styles.saveBtn, { color: mc.primary }]}>Guardar</Text>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={{ padding: 16, gap: 16 }}>
        {/* Op type selector */}
        <View>
          <Text style={styles.label}>Tipo de operação</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={{ flexDirection: "row", gap: 8 }}>
              {types.map((t) => {
                const active = t.key === opType;
                return (
                  <TouchableOpacity
                    key={t.key}
                    onPress={() => setOpType(t.key)}
                    style={[
                      styles.typeChip,
                      active
                        ? { backgroundColor: mc.primary }
                        : {
                            backgroundColor: Colors.surface.level2,
                            borderColor: Colors.surface.border,
                            borderWidth: 1,
                          },
                    ]}
                  >
                    <Text
                      style={[
                        styles.typeChipText,
                        { color: active ? "#fff" : Colors.ink.muted },
                      ]}
                    >
                      {t.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </ScrollView>
        </View>

        {/* Amount */}
        <View>
          <Text style={styles.label}>
            Valor ({activeModule === "mz" ? "MZN" : "EUR"})
          </Text>
          <TextInput
            value={amount}
            onChangeText={setAmount}
            placeholder="0,00"
            placeholderTextColor={Colors.ink.faint}
            keyboardType="decimal-pad"
            style={[
              styles.input,
              { fontSize: 28, fontWeight: "700", color: mc.primary },
            ]}
          />
        </View>

        {/* Description */}
        <View>
          <Text style={styles.label}>Descrição</Text>
          <TextInput
            value={description}
            onChangeText={setDescription}
            placeholder="Ex: Envio para Mamã"
            placeholderTextColor={Colors.ink.faint}
            style={styles.input}
          />
        </View>

        {/* Counterpart (MZ only) */}
        {activeModule === "mz" && (
          <View>
            <Text style={styles.label}>Pessoa (opcional)</Text>
            <TextInput
              value={counterpart}
              onChangeText={setCounterpart}
              placeholder="Ex: Mamã, João..."
              placeholderTextColor={Colors.ink.faint}
              style={styles.input}
            />
          </View>
        )}

        {/* Reference */}
        <View>
          <Text style={styles.label}>Referência (opcional)</Text>
          <TextInput
            value={reference}
            onChangeText={setReference}
            placeholder="Ex: MPSA12345"
            placeholderTextColor={Colors.ink.faint}
            autoCapitalize="characters"
            style={styles.input}
          />
        </View>

        {/* Direction indicator */}
        <View
          style={[
            styles.dirBadge,
            {
              backgroundColor:
                selectedType.dir === "entrada"
                  ? Colors.positive + "20"
                  : Colors.negative + "20",
            },
          ]}
        >
          <Text
            style={{
              color:
                selectedType.dir === "entrada"
                  ? Colors.positive
                  : Colors.negative,
              fontWeight: "600",
              fontSize: 13,
            }}
          >
            {selectedType.dir === "entrada" ? "↑ Entrada" : "↓ Saída"}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.surface.border,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: Colors.ink.primary,
  },
  cancelBtn: { fontSize: 15 },
  saveBtn: { fontSize: 15, fontWeight: "700" },
  label: {
    fontSize: 12,
    color: Colors.ink.muted,
    marginBottom: 8,
    textTransform: "uppercase",
    letterSpacing: 0.6,
  },
  input: {
    backgroundColor: Colors.surface.level2,
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    color: Colors.ink.primary,
    borderWidth: 1,
    borderColor: Colors.surface.border,
  },
  typeChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  typeChipText: {
    fontSize: 13,
    fontWeight: "600",
  },
  dirBadge: {
    borderRadius: 8,
    padding: 10,
    alignItems: "center",
  },
});
