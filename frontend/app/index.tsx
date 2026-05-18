import { Redirect } from "expo-router";
import { useAuthStore } from "@/stores/auth.store";

export default function Index() {
  const { session, isLoading } = useAuthStore();
  if (isLoading) return null;
  return <Redirect href={session ? "/(tabs)" : "/(auth)/login"} />;
}
