import { Redirect, Stack } from "expo-router";
import { useAuthStore } from "@/stores/auth.store";

export default function AuthLayout() {
  const { session } = useAuthStore();
  if (session) return <Redirect href="/(tabs)" />;

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="login" />
    </Stack>
  );
}
