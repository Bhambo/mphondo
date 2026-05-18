import { View, Text } from "react-native";
import { Colors } from "@/lib/theme";

interface EmptyStateProps {
  icon?: string;
  title: string;
  subtitle?: string;
}

export function EmptyState({ icon, title, subtitle }: EmptyStateProps) {
  return (
    <View
      style={{
        flex: 1,
        alignItems: "center",
        justifyContent: "center",
        padding: 48,
        gap: 12,
      }}
    >
      {icon && <Text style={{ fontSize: 48 }}>{icon}</Text>}
      <Text
        style={{ fontSize: 17, fontWeight: "600", color: Colors.ink.primary }}
      >
        {title}
      </Text>
      {subtitle && (
        <Text
          style={{
            fontSize: 14,
            color: Colors.ink.muted,
            textAlign: "center",
            lineHeight: 20,
          }}
        >
          {subtitle}
        </Text>
      )}
    </View>
  );
}
