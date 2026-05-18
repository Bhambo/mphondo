import { useEffect } from "react";
import { ScrollView, View, Text, StyleSheet, RefreshControl } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useModuleStore } from "@/stores/module.store";
import { useTransactionsStore } from "@/stores/transactions.store";
import { Colors, moduleColors } from "@/lib/theme";
import { formatCurrency, formatRelativeDate } from "@/lib/formatters";

function BalanceCard({
  balance,
  currency,
  label,
  accent,
}: {
  balance: number;
  currency: "MZN" | "EUR";
  label: string;
  accent: string;
}) {
  return (
    <View style={[styles.balanceCard, { borderColor: accent + "40" }]}>
      <Text style={styles.balanceLabel}>{label}</Text>
      <Text style={[styles.balanceAmount, { color: accent }]}>
        {formatCurrency(balance, currency)}
      </Text>
    </View>
  );
}

function RecentTxRow({
  description,
  amount,
  currency,
  date,
  categoryColor,
}: {
  description: string;
  amount: number;
  currency: "MZN" | "EUR";
  date: string;
  categoryColor: string | null;
}) {
  const isPositive = amount >= 0;
  return (
    <View style={styles.txRow}>
      <View
        style={[
          styles.txDot,
          { backgroundColor: categoryColor ?? Colors.ink.faint },
        ]}
      />
      <View style={{ flex: 1 }}>
        <Text style={styles.txDesc} numberOfLines={1}>
          {description}
        </Text>
        <Text style={styles.txDate}>{formatRelativeDate(date)}</Text>
      </View>
      <Text
        style={[
          styles.txAmount,
          { color: isPositive ? Colors.positive : Colors.negative },
        ]}
      >
        {formatCurrency(Math.abs(amount), currency)}
      </Text>
    </View>
  );
}

export default function DashboardScreen() {
  const { activeModule } = useModuleStore();
  const { transactions, fetchTransactions, isLoading } = useTransactionsStore();
  const mc = moduleColors(activeModule);

  useEffect(() => {
    fetchTransactions(true);
  }, [activeModule, fetchTransactions]);

  const recent = transactions.slice(0, 8);

  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: Colors.surface.bg }}
      edges={["bottom"]}
    >
      <ScrollView
        contentContainerStyle={{ padding: 16, gap: 16 }}
        refreshControl={
          <RefreshControl
            refreshing={isLoading}
            onRefresh={() => fetchTransactions(true)}
            tintColor={mc.primary}
          />
        }
      >
        {/* Balance cards */}
        <BalanceCard
          balance={0}
          currency={activeModule === "mz" ? "MZN" : "EUR"}
          label={activeModule === "mz" ? "Saldo M-Pesa" : "Saldo total"}
          accent={mc.primary}
        />

        {/* Recent transactions */}
        <View>
          <Text style={styles.sectionTitle}>Recentes</Text>
          <View style={styles.txCard}>
            {recent.length === 0 ? (
              <Text style={styles.emptyText}>
                Nenhuma transação ainda.{"\n"}Usa o + para adicionar.
              </Text>
            ) : (
              recent.map((tx) => (
                <RecentTxRow
                  key={tx.id}
                  description={tx.description}
                  amount={tx.net_amount}
                  currency={tx.currency}
                  date={tx.occurred_at}
                  categoryColor={tx.category_color}
                />
              ))
            )}
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  balanceCard: {
    backgroundColor: Colors.surface.level1,
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
  },
  balanceLabel: {
    fontSize: 13,
    color: Colors.ink.muted,
    marginBottom: 8,
    textTransform: "uppercase",
    letterSpacing: 0.8,
  },
  balanceAmount: {
    fontSize: 32,
    fontWeight: "700",
    letterSpacing: -0.5,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.ink.muted,
    textTransform: "uppercase",
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  txCard: {
    backgroundColor: Colors.surface.level1,
    borderRadius: 16,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: Colors.surface.border,
  },
  txRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.surface.borderFaint,
  },
  txDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  txDesc: {
    fontSize: 15,
    color: Colors.ink.primary,
    fontWeight: "500",
  },
  txDate: {
    fontSize: 12,
    color: Colors.ink.muted,
    marginTop: 2,
  },
  txAmount: {
    fontSize: 15,
    fontWeight: "600",
  },
  emptyText: {
    textAlign: "center",
    color: Colors.ink.muted,
    padding: 32,
    lineHeight: 22,
  },
});
