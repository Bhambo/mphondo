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
import { Colors } from "@/lib/theme";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/formatters";

interface ParsedOp {
  op_type: string;
  amount: number;
  counterpart: string | null;
  reference: string | null;
  balance_after: number | null;
  fee: number | null;
  confidence: number;
}

export default function SmsImportModal() {
  const [smsText, setSmsText] = useState("");
  const [parsed, setParsed] = useState<ParsedOp[] | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);

  const handleParse = async () => {
    if (!smsText.trim()) return;
    setIsParsing(true);
    try {
      const ops = await api.post<ParsedOp[]>("/mpesa/parse-sms", {
        text: smsText.trim(),
      });
      setParsed(ops);
    } catch (err) {
      Alert.alert("Erro", err instanceof Error ? err.message : "Erro ao analisar");
    } finally {
      setIsParsing(false);
    }
  };

  const handleConfirm = async () => {
    if (!parsed?.length) return;
    setIsConfirming(true);
    try {
      await api.post("/mpesa/confirm-sms", { operations: parsed });
      Alert.alert("Importado!", `${parsed.length} operação(ões) registadas.`, [
        { text: "OK", onPress: () => router.back() },
      ]);
    } catch (err) {
      Alert.alert("Erro", err instanceof Error ? err.message : "Erro ao confirmar");
    } finally {
      setIsConfirming(false);
    }
  };

  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: Colors.surface.bg }}
      edges={["top", "bottom"]}
    >
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={{ color: Colors.mz.primary, fontSize: 15 }}>Cancelar</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Importar SMS</Text>
        <View style={{ width: 60 }} />
      </View>

      <ScrollView contentContainerStyle={{ padding: 16, gap: 16 }}>
        <Text style={styles.hint}>
          Cola aqui o texto do SMS M-Pesa. Podes incluir vários SMSs de uma vez.
        </Text>

        <TextInput
          value={smsText}
          onChangeText={(t) => {
            setSmsText(t);
            setParsed(null);
          }}
          placeholder={"Voce enviou 500.00 MZN para Mamã. Saldo: 1234.56. Taxa: 5.00. Ref: MPSA12345"}
          placeholderTextColor={Colors.ink.faint}
          multiline
          numberOfLines={6}
          style={styles.smsInput}
          textAlignVertical="top"
        />

        <TouchableOpacity
          onPress={handleParse}
          disabled={!smsText.trim() || isParsing}
          activeOpacity={0.8}
          style={[
            styles.btn,
            { backgroundColor: Colors.mz.primary },
            (!smsText.trim() || isParsing) && { opacity: 0.5 },
          ]}
        >
          {isParsing ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.btnText}>Analisar SMS</Text>
          )}
        </TouchableOpacity>

        {/* Results */}
        {parsed !== null && (
          <View style={{ gap: 12 }}>
            <Text style={styles.sectionTitle}>
              {parsed.length === 0
                ? "Nenhuma operação reconhecida"
                : `${parsed.length} operação(ões) encontrada(s)`}
            </Text>

            {parsed.map((op, i) => (
              <View key={i} style={styles.opCard}>
                <View style={styles.opRow}>
                  <Text style={styles.opType}>{op.op_type}</Text>
                  <Text
                    style={[
                      styles.opAmount,
                      {
                        color:
                          op.op_type.includes("envio") ||
                          op.op_type.includes("saida")
                            ? Colors.negative
                            : Colors.positive,
                      },
                    ]}
                  >
                    {formatCurrency(op.amount, "MZN")}
                  </Text>
                </View>
                {op.counterpart && (
                  <Text style={styles.opDetail}>Pessoa: {op.counterpart}</Text>
                )}
                {op.reference && (
                  <Text style={styles.opDetail}>Ref: {op.reference}</Text>
                )}
                {op.balance_after !== null && (
                  <Text style={styles.opDetail}>
                    Saldo após: {formatCurrency(op.balance_after, "MZN")}
                  </Text>
                )}
                <View
                  style={[
                    styles.confidenceBadge,
                    {
                      backgroundColor:
                        op.confidence >= 0.85
                          ? Colors.positive + "25"
                          : Colors.warning + "25",
                    },
                  ]}
                >
                  <Text
                    style={{
                      fontSize: 11,
                      color:
                        op.confidence >= 0.85 ? Colors.positive : Colors.warning,
                    }}
                  >
                    Confiança: {Math.round(op.confidence * 100)}%
                    {op.confidence < 0.85 ? " — rever" : ""}
                  </Text>
                </View>
              </View>
            ))}

            {parsed.length > 0 && (
              <TouchableOpacity
                onPress={handleConfirm}
                disabled={isConfirming}
                activeOpacity={0.8}
                style={[styles.btn, { backgroundColor: Colors.positive }]}
              >
                {isConfirming ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.btnText}>Confirmar e guardar</Text>
                )}
              </TouchableOpacity>
            )}
          </View>
        )}
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
  hint: {
    fontSize: 14,
    color: Colors.ink.muted,
    lineHeight: 20,
  },
  smsInput: {
    backgroundColor: Colors.surface.level2,
    borderRadius: 12,
    padding: 14,
    fontSize: 14,
    color: Colors.ink.primary,
    borderWidth: 1,
    borderColor: Colors.surface.border,
    minHeight: 120,
    fontFamily: "monospace",
  },
  btn: {
    borderRadius: 12,
    padding: 15,
    alignItems: "center",
  },
  btnText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "700",
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.ink.muted,
    textTransform: "uppercase",
    letterSpacing: 0.8,
  },
  opCard: {
    backgroundColor: Colors.surface.level1,
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: Colors.surface.border,
    gap: 4,
  },
  opRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  opType: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.ink.primary,
    textTransform: "capitalize",
  },
  opAmount: {
    fontSize: 16,
    fontWeight: "700",
  },
  opDetail: {
    fontSize: 13,
    color: Colors.ink.muted,
  },
  confidenceBadge: {
    borderRadius: 6,
    padding: 4,
    marginTop: 4,
    alignSelf: "flex-start",
    paddingHorizontal: 8,
  },
});
