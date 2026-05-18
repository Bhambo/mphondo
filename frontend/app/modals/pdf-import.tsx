import { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from "react-native";
import { router } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import * as DocumentPicker from "expo-document-picker";
import { Colors } from "@/lib/theme";
import { api } from "@/lib/api";
import { supabase } from "@/lib/supabase";

interface ParseResult {
  statement_id: string;
  parsed_count: number;
  needs_review_count: number;
  message: string;
}

export default function PdfImportModal() {
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileUri, setFileUri] = useState<string | null>(null);
  const [result, setResult] = useState<ParseResult | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const pickPdf = async () => {
    const res = await DocumentPicker.getDocumentAsync({
      type: "application/pdf",
      copyToCacheDirectory: true,
    });
    if (res.canceled) return;
    const file = res.assets[0];
    setFileName(file.name);
    setFileUri(file.uri);
    setResult(null);
  };

  const handleUpload = async () => {
    if (!fileUri || !fileName) return;
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", {
        uri: fileUri,
        name: fileName,
        type: "application/pdf",
      } as unknown as Blob);

      // Use fetch directly for multipart/form-data
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error("Sem sessão");

      const apiBase = process.env.EXPO_PUBLIC_API_URL ?? "https://mphondo.local/api/v1";
      const fetchRes = await fetch(`${apiBase}/mpesa/upload-pdf`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
        body: formData,
      });
      if (!fetchRes.ok) {
        const err = await fetchRes.json().catch(() => ({}));
        throw new Error(err.detail ?? "Erro no upload");
      }
      const data: ParseResult = await fetchRes.json();
      setResult(data);
    } catch (err) {
      Alert.alert("Erro", err instanceof Error ? err.message : "Erro no upload");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: Colors.surface.bg }}
      edges={["top", "bottom"]}
    >
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={{ color: Colors.mz.primary, fontSize: 15 }}>Cancelar</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Importar PDF M-Pesa</Text>
        <View style={{ width: 60 }} />
      </View>

      <ScrollView contentContainerStyle={{ padding: 16, gap: 16 }}>
        <Text style={styles.hint}>
          Selecciona o extracto PDF do M-Pesa. O sistema analisa automaticamente e
          apresenta as operações para confirmação.
        </Text>

        {/* Pick file */}
        <TouchableOpacity
          onPress={pickPdf}
          activeOpacity={0.8}
          style={styles.pickArea}
        >
          {fileName ? (
            <View style={{ alignItems: "center", gap: 6 }}>
              <Text style={{ fontSize: 32 }}>📄</Text>
              <Text style={styles.fileName}>{fileName}</Text>
              <Text style={{ color: Colors.mz.primary, fontSize: 13 }}>
                Alterar ficheiro
              </Text>
            </View>
          ) : (
            <View style={{ alignItems: "center", gap: 8 }}>
              <Text style={{ fontSize: 40 }}>📁</Text>
              <Text style={styles.pickText}>Seleccionar PDF</Text>
              <Text style={{ color: Colors.ink.faint, fontSize: 12 }}>
                Extracto M-Pesa em formato PDF
              </Text>
            </View>
          )}
        </TouchableOpacity>

        {fileName && !result && (
          <TouchableOpacity
            onPress={handleUpload}
            disabled={isUploading}
            activeOpacity={0.8}
            style={[
              styles.btn,
              { backgroundColor: Colors.mz.primary },
              isUploading && { opacity: 0.7 },
            ]}
          >
            {isUploading ? (
              <View style={{ flexDirection: "row", gap: 8, alignItems: "center" }}>
                <ActivityIndicator color="#fff" />
                <Text style={styles.btnText}>A analisar...</Text>
              </View>
            ) : (
              <Text style={styles.btnText}>Analisar PDF</Text>
            )}
          </TouchableOpacity>
        )}

        {/* Result */}
        {result && (
          <View style={styles.resultCard}>
            <Text style={styles.resultTitle}>✓ PDF analisado</Text>
            <Text style={styles.resultRow}>
              Operações encontradas:{" "}
              <Text style={{ color: Colors.ink.primary, fontWeight: "600" }}>
                {result.parsed_count}
              </Text>
            </Text>
            {result.needs_review_count > 0 && (
              <Text style={[styles.resultRow, { color: Colors.warning }]}>
                ⚠ {result.needs_review_count} a rever manualmente
              </Text>
            )}
            <Text style={[styles.resultRow, { color: Colors.ink.muted }]}>
              {result.message}
            </Text>
            <TouchableOpacity
              onPress={() => router.back()}
              activeOpacity={0.8}
              style={[styles.btn, { backgroundColor: Colors.positive, marginTop: 8 }]}
            >
              <Text style={styles.btnText}>Ver transações</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.surface.border,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: Colors.ink.primary,
  },
  hint: {
    fontSize: 14,
    color: Colors.ink.muted,
    lineHeight: 20,
  },
  pickArea: {
    backgroundColor: Colors.surface.level1,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: Colors.surface.border,
    borderStyle: "dashed",
    padding: 40,
    alignItems: "center",
    justifyContent: "center",
  },
  pickText: {
    fontSize: 16,
    fontWeight: "600",
    color: Colors.ink.primary,
  },
  fileName: {
    fontSize: 14,
    color: Colors.ink.primary,
    fontWeight: "500",
    maxWidth: 250,
    textAlign: "center",
  },
  btn: {
    borderRadius: 12,
    padding: 15,
    alignItems: "center",
  },
  btnText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "700",
  },
  resultCard: {
    backgroundColor: Colors.surface.level1,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.positive + "60",
    gap: 6,
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.positive,
    marginBottom: 4,
  },
  resultRow: {
    fontSize: 14,
    color: Colors.ink.muted,
    lineHeight: 20,
  },
});
