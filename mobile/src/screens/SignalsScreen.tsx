import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../../App';
import { api, clearToken, Me, Signal } from '../api';
import { registerForPush } from '../push';

type Props = NativeStackScreenProps<RootStackParamList, 'Signals'>;

const dirColor = (d: string) => (d === 'BUY' ? '#1D9E75' : d === 'SELL' ? '#E24B4A' : '#8A94A6');

export default function SignalsScreen({ navigation }: Props) {
  const [me, setMe] = useState<Me | null>(null);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [m, sigs] = await Promise.all([api.me(), api.signals()]);
      setMe(m);
      setSignals(sigs);
    } catch {
      // token expiré -> retour login
      await clearToken();
      navigation.replace('Login');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [navigation]);

  useEffect(() => {
    load();
    // Enregistre le token push et le transmet au backend (best-effort).
    registerForPush().then((tok) => {
      if (tok) api.registerPushToken(tok);
    });
  }, [load]);

  async function logout() {
    await clearToken();
    navigation.replace('Login');
  }

  async function generate() {
    const asset = me?.watchlist?.[0] ?? 'BTC/USDT';
    setRefreshing(true);
    try {
      await api.generate(asset);
      await load();
    } catch {
      setRefreshing(false);
    }
  }

  if (loading) {
    return (
      <View style={s.center}>
        <ActivityIndicator color="#1D9E75" />
      </View>
    );
  }

  return (
    <View style={s.container}>
      <View style={s.header}>
        <View>
          <Text style={s.email}>{me?.email}</Text>
          <Text style={s.plan}>plan {me?.plan?.toUpperCase()} · {me?.capital} USDT</Text>
        </View>
        <TouchableOpacity onPress={logout}>
          <Text style={s.logout}>Déconnexion</Text>
        </TouchableOpacity>
      </View>

      <View style={s.actions}>
        <TouchableOpacity style={s.primaryBtn} onPress={generate}>
          <Text style={s.primaryBtnText}>Générer un signal</Text>
        </TouchableOpacity>
        <TouchableOpacity style={s.secondaryBtn} onPress={() => navigation.navigate('Copilot', {})}>
          <Text style={s.secondaryBtnText}>AI Copilot</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={signals}
        keyExtractor={(item, i) => item.id ?? String(i)}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={load} tintColor="#1D9E75" />}
        ListEmptyComponent={<Text style={s.empty}>Aucun signal pour le moment.</Text>}
        renderItem={({ item }) => (
          <View style={s.card}>
            <View style={s.cardTop}>
              <Text style={s.asset}>{item.asset}</Text>
              <Text style={[s.dir, { color: dirColor(item.direction) }]}>{item.direction}</Text>
            </View>
            <Text style={s.meta}>
              Entrée {item.entry} · SL {item.stop_loss} · TP {item.take_profit_1} · conf {item.confidence}%
            </Text>
            <Text style={s.rationale} numberOfLines={3}>
              {item.rationale}
            </Text>
          </View>
        )}
      />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  center: { flex: 1, justifyContent: 'center', backgroundColor: '#0B0E11' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  email: { color: '#fff', fontWeight: '600' },
  plan: { color: '#8A94A6', fontSize: 12 },
  logout: { color: '#8A94A6' },
  actions: { flexDirection: 'row', gap: 10, marginBottom: 12 },
  primaryBtn: { flex: 1, backgroundColor: '#1D9E75', borderRadius: 10, padding: 12, alignItems: 'center' },
  primaryBtnText: { color: '#fff', fontWeight: '600' },
  secondaryBtn: { flex: 1, borderColor: '#232A33', borderWidth: 1, borderRadius: 10, padding: 12, alignItems: 'center' },
  secondaryBtnText: { color: '#fff' },
  empty: { color: '#8A94A6', textAlign: 'center', marginTop: 40 },
  card: { backgroundColor: '#151A21', borderColor: '#232A33', borderWidth: 1, borderRadius: 12, padding: 14, marginBottom: 10 },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between' },
  asset: { color: '#fff', fontWeight: '700', fontSize: 16 },
  dir: { fontWeight: '700' },
  meta: { color: '#8A94A6', fontSize: 12, marginTop: 4 },
  rationale: { color: '#C7CFDA', fontSize: 13, marginTop: 6 },
});
