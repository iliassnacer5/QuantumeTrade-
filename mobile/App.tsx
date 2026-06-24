import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';

import { getToken } from './src/api';
import LoginScreen from './src/screens/LoginScreen';
import SignalsScreen from './src/screens/SignalsScreen';
import CopilotScreen from './src/screens/CopilotScreen';

export type RootStackParamList = {
  Login: undefined;
  Signals: undefined;
  Copilot: { asset?: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

const theme = {
  ...DefaultTheme,
  dark: true,
  colors: {
    ...DefaultTheme.colors,
    background: '#0B0E11',
    card: '#151A21',
    text: '#FFFFFF',
    border: '#232A33',
    primary: '#1D9E75',
  },
};

export default function App() {
  const [ready, setReady] = useState(false);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    getToken().then((t) => {
      setAuthed(!!t);
      setReady(true);
    });
  }, []);

  if (!ready) {
    return (
      <View style={{ flex: 1, backgroundColor: '#0B0E11', justifyContent: 'center' }}>
        <ActivityIndicator color="#1D9E75" />
      </View>
    );
  }

  return (
    <NavigationContainer theme={theme}>
      <StatusBar style="light" />
      <Stack.Navigator
        initialRouteName={authed ? 'Signals' : 'Login'}
        screenOptions={{
          headerStyle: { backgroundColor: '#151A21' },
          headerTintColor: '#FFFFFF',
          contentStyle: { backgroundColor: '#0B0E11' },
        }}
      >
        <Stack.Screen name="Login" component={LoginScreen} options={{ title: 'Quantum Trade AI' }} />
        <Stack.Screen name="Signals" component={SignalsScreen} options={{ title: 'Signaux' }} />
        <Stack.Screen name="Copilot" component={CopilotScreen} options={{ title: 'AI Copilot' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
