import { useEffect } from "react";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import * as SplashScreen from "expo-splash-screen";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { supabase } from "@/lib/supabase";
import { useAuthStore } from "@/stores/auth.store";

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const { setSession, isLoading } = useAuthStore();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    const { data: listener } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session);
      },
    );

    return () => listener.subscription.unsubscribe();
  }, [setSession]);

  useEffect(() => {
    if (!isLoading) SplashScreen.hideAsync();
  }, [isLoading]);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <StatusBar style="light" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="modals/quick-entry" options={{ presentation: "modal" }} />
        <Stack.Screen name="modals/sms-import" options={{ presentation: "modal" }} />
        <Stack.Screen name="modals/pdf-import" options={{ presentation: "modal" }} />
      </Stack>
    </GestureHandlerRootView>
  );
}
