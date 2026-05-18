import { TouchableOpacity, View, Text, StyleSheet } from "react-native";
import type { Transaction } from "@/stores/transactions.store";
import { Colors } from "@/lib/theme";
import { formatCurrency, formatRelativeDate } from "@/lib/formatters";

interface Props {
  transaction: Transaction;
  onPress?: (tx: Transaction) => void;
}

export function TransactionRow({ transaction: tx, onPress }: Props) {
  const isPositive = tx.net_amount >= 0;

  return (
    <TouchableOpacity
      onPress={() => onPress?.(tx)}
      activeOpacity={0.7}
      style={styles.container}
    >
      <View
        style={[
          styles.colorBar,
          { backgroundColor: tx.category_color ?? Colors.ink.faint },
        ]}
      />
      <View style={{ flex: 1, paddingVertical: 13, paddingHorizontal: 12 }}>
        <View style={styles.top}>
          <Text style={styles.desc} numberOfLines={1}>
            {tx.description}
          </Text>
          <Text
            style={[
              styles.amount,
              { color: isPositive ? Colors.positive : Colors.negative },
            ]}
          >
            {isPositive ? "+" : ""}
            {formatCurrency(tx.net_amount, tx.currency)}
          </Text>
        </View>
        <View style={styles.bottom}>
          {tx.category_name && (
            <View style={styles.chip}>
              <Text style={styles.chipText}>{tx.category_name}</Text>
            </View>
          )}
          <Text style={styles.date}>
            {formatRelativeDate(tx.occurred_at)}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    backgroundColor: Colors.surface.level1,
  },
  colorBar: { width: 4 },
  top: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 8,
  },
  desc: {
    flex: 1,
    fontSize: 15,
    color: Colors.ink.primary,
    fontWeight: "500",
  },
  amount: {
    fontSize: 15,
    fontWeight: "600",
  },
  bottom: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 4,
  },
  chip: {
    backgroundColor: Colors.surface.level3,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  chipText: {
    fontSize: 11,
    color: Colors.ink.muted,
  },
  date: {
    fontSize: 12,
    color: Colors.ink.muted,
  },
});
