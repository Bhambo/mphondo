import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useAuthStore } from "@/stores/auth.store";
import { Colors } from "@/lib/theme";

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { signIn, isLoading } = useAuthStore();

  const handleLogin = async () => {
    if (!email.trim() || !password) return;
    try {
      await signIn(email.trim(), password);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Erro ao iniciar sessão";
      Alert.alert("Erro de autenticação", message);
    }
  };

  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: Colors.surface.bg }}
    >
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <View style={{ flex: 1, justifyContent: "center", paddingHorizontal: 32 }}>
          {/* Logo / Brand */}
          <View style={{ marginBottom: 48 }}>
            <Text
              style={{
                fontSize: 36,
                fontWeight: "800",
                color: Colors.mz.primary,
                letterSpacing: -1,
              }}
            >
              Mphondo
            </Text>
            <Text
              style={{
                fontSize: 15,
                color: Colors.ink.muted,
                marginTop: 6,
                letterSpacing: 0.3,
              }}
            >
              As tuas finanças. Organizadas.
            </Text>
          </View>

          {/* Fields */}
          <View style={{ gap: 12 }}>
            <View>
              <Text style={{ fontSize: 12, color: Colors.ink.muted, marginBottom: 6 }}>
                Email
              </Text>
              <TextInput
                value={email}
                onChangeText={setEmail}
                placeholder="tu@email.com"
                placeholderTextColor={Colors.ink.faint}
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
                style={{
                  backgroundColor: Colors.surface.level2,
                  borderRadius: 12,
                  padding: 14,
                  fontSize: 16,
                  color: Colors.ink.primary,
                  borderWidth: 1,
                  borderColor: Colors.surface.border,
                }}
              />
            </View>

            <View>
              <Text style={{ fontSize: 12, color: Colors.ink.muted, marginBottom: 6 }}>
                Palavra-passe
              </Text>
              <TextInput
                value={password}
                onChangeText={setPassword}
                placeholder="••••••••"
                placeholderTextColor={Colors.ink.faint}
                secureTextEntry
                autoComplete="password"
                style={{
                  backgroundColor: Colors.surface.level2,
                  borderRadius: 12,
                  padding: 14,
                  fontSize: 16,
                  color: Colors.ink.primary,
                  borderWidth: 1,
                  borderColor: Colors.surface.border,
                }}
              />
            </View>

            <TouchableOpacity
              onPress={handleLogin}
              disabled={isLoading}
              activeOpacity={0.8}
              style={{
                backgroundColor: Colors.mz.primary,
                borderRadius: 12,
                padding: 16,
                alignItems: "center",
                marginTop: 8,
                opacity: isLoading ? 0.7 : 1,
              }}
            >
              {isLoading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={{ fontSize: 16, fontWeight: "700", color: "#fff" }}>
                  Entrar
                </Text>
              )}
            </TouchableOpacity>
          </View>

          <Text
            style={{
              textAlign: "center",
              color: Colors.ink.faint,
              fontSize: 12,
              marginTop: 40,
            }}
          >
            Self-hosted · Dados seguros · Sem partilha
          </Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
