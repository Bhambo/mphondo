import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  type ViewStyle,
} from "react-native";
import { Colors } from "@/lib/theme";

interface ButtonProps {
  label: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "danger";
  accent?: string;
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
}

export function Button({
  label,
  onPress,
  variant = "primary",
  accent,
  loading,
  disabled,
  style,
}: ButtonProps) {
  const bg =
    variant === "danger"
      ? Colors.negative
      : variant === "secondary"
        ? Colors.surface.level2
        : (accent ?? Colors.mz.primary);

  const textColor =
    variant === "secondary" ? Colors.ink.primary : "#fff";

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
      style={[
        {
          backgroundColor: bg,
          borderRadius: 12,
          padding: 15,
          alignItems: "center",
          opacity: disabled || loading ? 0.6 : 1,
          borderWidth: variant === "secondary" ? 1 : 0,
          borderColor: Colors.surface.border,
        },
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={textColor} />
      ) : (
        <Text
          style={{ color: textColor, fontSize: 15, fontWeight: "700" }}
        >
          {label}
        </Text>
      )}
    </TouchableOpacity>
  );
}
