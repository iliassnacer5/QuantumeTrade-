import { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../../App';
import { api, setToken } from '../api';

type Props = NativeStackScreenProps<RootStackParamList, 'Login'>;

export default function LoginScreen({ navigation }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const r = mode === 'login' ? await api.login(email, password) : await api.register(email, password);
      await setToken(r.access_token);
      navigation.replace('Signals');
    } catch (e: any) {
      setError(e.message ?? 'Échec');
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={s.container}>
      <Text style={s.title}>Quantum Trade AI</Text>
      <Text style={s.subtitle}>{mode === 'login' ? 'Connexion' : 'Créer un compte'}</Text>

      <TextInput
        style={s.input}
        placeholder="Email"
        placeholderTextColor="#8A94A6"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={s.input}
        placeholder="Mot de passe"
        placeholderTextColor="#8A94A6"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />

      {error && <Text style={s.error}>{error}</Text>}

      <TouchableOpacity style={s.button} onPress={submit} disabled={busy}>
        {busy ? <ActivityIndicator color="#fff" /> : <Text style={s.buttonText}>{mode === 'login' ? 'Se connecter' : "S'inscrire"}</Text>}
      </TouchableOpacity>

      <TouchableOpacity onPress={() => setMode(mode === 'login' ? 'register' : 'login')}>
        <Text style={s.switch}>
          {mode === 'login' ? "Pas de compte ? S'inscrire" : 'Déjà inscrit ? Se connecter'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 24, gap: 12 },
  title: { color: '#fff', fontSize: 28, fontWeight: '700', textAlign: 'center' },
  subtitle: { color: '#8A94A6', textAlign: 'center', marginBottom: 12 },
  input: { backgroundColor: '#151A21', borderColor: '#232A33', borderWidth: 1, borderRadius: 10, padding: 14, color: '#fff' },
  button: { backgroundColor: '#1D9E75', borderRadius: 10, padding: 16, alignItems: 'center', marginTop: 4 },
  buttonText: { color: '#fff', fontWeight: '600' },
  switch: { color: '#1D9E75', textAlign: 'center', marginTop: 8 },
  error: { color: '#E24B4A', textAlign: 'center' },
});
