import { useEffect, useCallback } from "react";
import { View, Text, StyleSheet, RefreshControl } from "react-native";
import { FlashList } from "@shopify/flash-list";
import { SafeAreaView } from "react-native-safe-area-context";
import { useModuleStore } from "@/stores/module.store";
import {
  useTransactionsStore,
  type Transaction,
} from "@/stores/transactions.store";
import { Colors, moduleColors } from "@/lib/theme";
import { formatCurrency, formatRelativeDate } from "@/lib/formatters";

function TxItem({ item }: { item: Transaction }) {
  const isPositive = item.net_amount >= 0;
  return (
    <View style={styles.item}>
      <View
        style={[
          styles.colorBar,
          { backgroundColor: item.category_color ?? Colors.ink.faint },
        ]}
      />
      <View style={{ flex: 1, paddingVertical: 14, paddingHorizontal: 12 }}>
        <View style={styles.itemTop}>
          <Text style={styles.itemDesc} numberOfLines={1}>
            {item.description}
          </Text>
          <Text
            style={[
              styles.itemAmount,
              { color: isPositive ? Colors.positive : Colors.negative },
            ]}
          >
            {isPositive ? "+" : "-"}
            {formatCurrency(Math.abs(item.net_amount), item.currency)}
          </Text>
        </View>
        <View style={styles.itemBottom}>
          {item.category_name && (
            <Text style={styles.categoryChip}>{item.category_name}</Text>
          )}
          <Text style={styles.itemDate}>
            {formatRelativeDate(item.occurred_at)}
          </Text>
        </View>
      </View>
    </View>
  );
}

function SeparatorLine() {
  return (
    <View
      style={{ height: 1, backgroundColor: Colors.surface.borderFaint }}
    />
  );
}

export default function TransacoesScreen() {
  const { activeModule } = useModuleStore();
  const { transactions, fetchTransactions, isLoading, hasMore } =
    useTransactionsStore();
  const mc = moduleColors(activeModule);

  useEffect(() => {
    fetchTransactions(true);
  }, [activeModule, fetchTransactions]);

  const onEndReached = useCallback(() => {
    if (hasMore && !isLoading) fetchTransactions();
  }, [hasMore, isLoading, fetchTransactions]);

  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: Colors.surface.bg }}
      edges={["bottom"]}
    >
      <FlashList
        data={transactions}
        keyExtractor={(t) => t.id}
        renderItem={({ item }) => <TxItem item={item} />}
        estimatedItemSize={68}
        ItemSeparatorComponent={SeparatorLine}
        contentContainerStyle={{ paddingBottom: 80 }}
        onEndReached={onEndReached}
        onEndReachedThreshold={0.3}
        refreshControl={
          <RefreshControl
            refreshing={isLoading && transactions.length === 0}
            onRefresh={() => fetchTransactions(true)}
            tintColor={mc.primary}
          />
        }
        ListEmptyComponent={
          !isLoading ? (
            <View style={styles.empty}>
              <Text style={styles.emptyTitle}>Sem transações</Text>
              <Text style={styles.emptySubtitle}>
                Usa o botão + para registar a primeira operação.
              </Text>
            </View>
          ) : null
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  item: {
    flexDirection: "row",
    backgroundColor: Colors.surface.level1,
  },
  colorBar: {
    width: 4,
  },
  itemTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 8,
  },
  itemDesc: {
    flex: 1,
    fontSize: 15,
    color: Colors.ink.primary,
    fontWeight: "500",
  },
  itemAmount: {
    fontSize: 15,
    fontWeight: "600",
  },
  itemBottom: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 4,
  },
  categoryChip: {
    fontSize: 11,
    color: Colors.ink.muted,
    backgroundColor: Colors.surface.level3,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  itemDate: {
    fontSize: 12,
    color: Colors.ink.muted,
  },
  empty: {
    padding: 48,
    alignItems: "center",
    gap: 8,
  },
  emptyTitle: {
    fontSize: 17,
    fontWeight: "600",
    color: Colors.ink.primary,
  },
  emptySubtitle: {
    fontSize: 14,
    color: Colors.ink.muted,
    textAlign: "center",
    lineHeight: 20,
  },
});
