import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../../App';
import { api } from '../api';

type Props = NativeStackScreenProps<RootStackParamList, 'Copilot'>;
type Msg = { role: 'user' | 'assistant'; content: string };

export default function CopilotScreen({ route }: Props) {
  const [asset] = useState(route.params?.asset ?? 'BTC/USDT');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Msg[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    if (!input.trim() || busy) return;
    const question = input.trim();
    setInput('');
    setError(null);
    setMessages((m) => [...m, { role: 'user', content: question }]);
    setBusy(true);
    try {
      // Mobile : variante non-stream (plus simple/robuste sur réseau mobile).
      const r = await api.copilotAsk(asset, question);
      setMessages((m) => [...m, { role: 'assistant', content: r.answer }]);
    } catch (e: any) {
      setError(e.message?.includes('402') ? 'Copilot réservé au plan Pro' : e.message ?? 'Erreur');
    } finally {
      setBusy(false);
    }
  }

  return (
    <KeyboardAvoidingView style={s.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Text style={s.asset}>Actif : {asset}</Text>
      <ScrollView style={s.thread} contentContainerStyle={{ gap: 8, padding: 8 }}>
        {messages.length === 0 && <Text style={s.hint}>Pose une question sur l&apos;analyse de {asset}.</Text>}
        {messages.map((m, i) => (
          <View key={i} style={[s.bubble, m.role === 'user' ? s.user : s.assistant]}>
            <Text style={s.bubbleText}>{m.content}</Text>
          </View>
        ))}
        {busy && <ActivityIndicator color="#1D9E75" style={{ marginTop: 8 }} />}
        {error && <Text style={s.error}>{error}</Text>}
      </ScrollView>
      <View style={s.inputRow}>
        <TextInput
          style={s.input}
          placeholder="Ta question…"
          placeholderTextColor="#8A94A6"
          value={input}
          onChangeText={setInput}
          onSubmitEditing={send}
        />
        <TouchableOpacity style={s.send} onPress={send} disabled={busy}>
          <Text style={s.sendText}>Envoyer</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, padding: 12 },
  asset: { color: '#8A94A6', marginBottom: 6 },
  thread: { flex: 1, backgroundColor: '#151A21', borderColor: '#232A33', borderWidth: 1, borderRadius: 12 },
  hint: { color: '#8A94A6', padding: 8 },
  bubble: { maxWidth: '88%', borderRadius: 12, padding: 10 },
  user: { alignSelf: 'flex-end', backgroundColor: '#1D9E7533' },
  assistant: { alignSelf: 'flex-start', backgroundColor: '#1A1A1A' },
  bubbleText: { color: '#E6EAF0', fontSize: 14 },
  inputRow: { flexDirection: 'row', gap: 8, marginTop: 10 },
  input: { flex: 1, backgroundColor: '#151A21', borderColor: '#232A33', borderWidth: 1, borderRadius: 10, padding: 12, color: '#fff' },
  send: { backgroundColor: '#1D9E75', borderRadius: 10, paddingHorizontal: 16, justifyContent: 'center' },
  sendText: { color: '#fff', fontWeight: '600' },
  error: { color: '#E24B4A', padding: 8 },
});
