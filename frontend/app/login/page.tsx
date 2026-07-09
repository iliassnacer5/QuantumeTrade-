import { AuthForm } from '@/components/AuthForm';
import { HeroBackground } from '@/components/marketing/HeroBackground';

export default function LoginPage() {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden p-8">
      <HeroBackground />
      <div className="relative z-10">
        <AuthForm mode="login" />
      </div>
    </main>
  );
}
