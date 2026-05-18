import { View, type ViewStyle } from "react-native";
import { Colors } from "@/lib/theme";

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  elevated?: boolean;
}

export function Card({ children, style, elevated }: CardProps) {
  return (
    <View
      style={[
        {
          backgroundColor: elevated
            ? Colors.surface.level2
            : Colors.surface.level1,
          borderRadius: 16,
          borderWidth: 1,
          borderColor: Colors.surface.border,
          overflow: "hidden",
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}
