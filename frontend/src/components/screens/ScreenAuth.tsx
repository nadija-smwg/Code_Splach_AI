import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

interface Props { onTriggerToast: (t: { title: string; message: string }) => void; }

export function ScreenSignIn({ onTriggerToast }: Props) {
  const navigate = useNavigate();
  const [authMode, setAuthMode] = useState('credentials');
  const [email, setEmail] = useState('broker.id@freightforwarder.lk');
  const [password, setPassword] = useState('password123');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    onTriggerToast({ title: 'Access Granted', message: 'Authenticated into ASYCUDA Clearance Corridor.' });
    navigate('/');
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col items-center justify-center min-h-[calc(100vh-10rem)]">
      <div className="w-full max-w-md bg-surface-container-lowest rounded-xl p-6 md:p-8 shadow-md border border-outline-variant/20 flex flex-col gap-4 text-xs">
        <div className="text-center relative">
          <Link to="/" className="absolute left-0 top-0 text-on-surface-variant hover:text-on-surface flex items-center justify-center p-1 rounded-md hover:bg-surface-container-low transition-colors" title="Back to Home">
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
          </Link>
          <span className="text-[10px] text-secondary font-bold uppercase tracking-widest block mb-1 mt-1">Authorized Broker Gateway</span>
          <h1 className="text-xl font-bold text-on-surface">Sign in to ClearanceX</h1>
          <p className="text-[11px] text-outline mt-1">Enter your broker credentials to access the clearance terminal.</p>
        </div>

        {/* Demo Mode Notice */}
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 flex flex-col gap-1.5">
          <div className="flex items-center gap-1.5 text-amber-400 font-bold text-[11px] uppercase tracking-wider">
            <span className="material-symbols-outlined text-[14px]">info</span>
            Demo Mode — Authentication is simulated
          </div>
          <p className="text-[11px] text-on-surface-variant leading-relaxed">
            Any credentials will grant access. Use the pre-filled demo values or enter your own.
          </p>
          <div className="font-mono text-[10px] bg-surface-container-highest rounded px-2 py-1 text-on-surface mt-0.5">
            Email: <span className="text-primary">broker.id@freightforwarder.lk</span>
            &nbsp;·&nbsp;
            Password: <span className="text-primary">password123</span>
          </div>
        </div>

        <div className="bg-surface-container-low p-1 rounded-lg flex items-center">
          <button onClick={() => setAuthMode('credentials')}
            className={`flex-1 py-1.5 rounded-md font-semibold text-[11px] transition-all ${authMode === 'credentials' ? 'bg-white shadow-sm text-on-surface' : 'text-outline'}`}>
            Email & PIN
          </button>
          <button onClick={() => setAuthMode('pki')}
            className={`flex-1 py-1.5 rounded-md font-semibold text-[11px] transition-all ${authMode === 'pki' ? 'bg-white shadow-sm text-on-surface' : 'text-outline'}`}>
            PKI SmartCard
          </button>
        </div>

        {authMode === 'credentials' ? (
          <form onSubmit={handleLogin} className="space-y-3">
            <div>
              <label className="text-[10px] text-outline uppercase block mb-1 font-semibold">Licensed Broker ID / Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                className="w-full px-3 py-2 bg-surface-container-low rounded-lg text-on-surface focus:outline-none focus:bg-white" />
            </div>
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-[10px] text-outline uppercase font-semibold">Password</label>
                <Link to="/auth/recovery" className="text-[11px] text-primary hover:underline">Forgot?</Link>
              </div>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                className="w-full px-3 py-2 bg-surface-container-low rounded-lg text-on-surface focus:outline-none focus:bg-white" />
            </div>
            <button type="submit" className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary-container text-white font-semibold text-xs shadow-md transition-all mt-2">
              Sign In to Workspace
            </button>
          </form>
        ) : (
          <div className="p-4 bg-surface-container-low rounded-lg text-center space-y-2">
            <span className="material-symbols-outlined text-primary text-[32px]">contactless</span>
            <div className="font-semibold text-on-surface">Detecting Sri Lanka Customs PKI Card...</div>
            <button onClick={() => { onTriggerToast({ title: 'PKI Token Verified', message: 'Session signed via Gov-CA LK.' }); navigate('/'); }}
              className="w-full py-2 bg-primary text-white rounded-lg font-semibold mt-2">
              Authenticate Token
            </button>
          </div>
        )}

        <div className="text-center pt-2 border-t border-outline-variant/20">
          <span className="text-outline">Unregistered freight forwarder? </span>
          <Link to="/auth/signup" className="text-primary font-semibold hover:underline">Register Firm →</Link>
        </div>
      </div>
    </div>
  );
}

export function ScreenSignUp({ onTriggerToast }: Props) {
  const navigate = useNavigate();
  const [tin, setTin] = useState('TIN-90823412-CHB-LK');
  const [firmName, setFirmName] = useState('Ceylon Ocean & Air Logistics Ltd');

  const handleOnboard = (e: React.FormEvent) => {
    e.preventDefault();
    onTriggerToast({ title: 'Customs License Validated', message: 'Firm profile registered. Direct ASYCUDA routing unlocked.' });
    navigate('/');
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      <div className="max-w-2xl mx-auto w-full bg-surface-container-lowest p-6 md:p-8 rounded-xl shadow-md border border-outline-variant/20 text-xs">
        <div className="mb-4 relative text-center">
          <Link to="/" className="absolute left-0 top-0 text-on-surface-variant hover:text-on-surface flex items-center justify-center p-1 rounded-md hover:bg-surface-container-low transition-colors" title="Back to Home">
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
          </Link>
          <span className="text-[10px] text-primary font-bold uppercase tracking-wider block mt-1">Step 1 of 3 • Enterprise Onboarding</span>
          <h1 className="text-xl font-bold text-on-surface mt-1">Create your ClearanceX Enterprise Account</h1>
          <p className="text-[11px] text-outline mt-0.5">Connect your freight brokerage or trading house to direct customs clearing infrastructure.</p>
        </div>
        <form onSubmit={handleOnboard} className="space-y-3">
          <div>
            <label className="text-[10px] text-outline uppercase block mb-1 font-semibold">Organization Legal Name</label>
            <input type="text" value={firmName} onChange={(e) => setFirmName(e.target.value)} required
              className="w-full px-3 py-2 bg-surface-container-low rounded-lg text-on-surface" />
          </div>
          <div>
            <label className="text-[10px] text-outline uppercase block mb-1 font-semibold">Customs Broker License / TIN No.</label>
            <input type="text" value={tin} onChange={(e) => setTin(e.target.value.toUpperCase())} required
              className="w-full px-3 py-2 bg-surface-container-low rounded-lg font-mono font-semibold text-primary uppercase" />
            <div className="text-[10px] text-secondary font-medium mt-1 flex items-center gap-1">
              <span className="material-symbols-outlined text-[13px]">verified</span> Validated against Sri Lanka Customs CHB Registry
            </div>
          </div>
          <div className="pt-2">
            <button type="submit" className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary-container text-white font-bold text-xs shadow-md transition-all">
              Continue to EDI Key Verification →
            </button>
          </div>
        </form>
        <div className="text-center pt-3 border-t border-outline-variant/20 mt-4 text-[11px]">
          <span className="text-outline">Already registered? </span>
          <Link to="/auth/signin" className="text-primary font-semibold hover:underline">Sign In</Link>
        </div>
      </div>
    </div>
  );
}

export function ScreenRecovery({ onTriggerToast }: Props) {
  const [email, setEmail] = useState('');

  const handleRecover = (e: React.FormEvent) => {
    e.preventDefault();
    onTriggerToast({ title: 'Recovery Package Dispatched', message: 'Encrypted TOTP link sent to corporate inbox.' });
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col items-center justify-center min-h-[calc(100vh-10rem)]">
      <div className="w-full max-w-md bg-surface-container-lowest rounded-xl p-6 md:p-8 shadow-md border border-outline-variant/20 text-xs text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-primary-fixed flex items-center justify-center mx-auto text-primary">
          <span className="material-symbols-outlined text-[24px]">lock_reset</span>
        </div>
        <div>
          <h1 className="text-lg font-bold text-on-surface">Reset Enterprise Security Credentials</h1>
          <p className="text-[11px] text-outline mt-1">Enter your registered customs email or broker ID for cryptographic recovery token.</p>
        </div>
        <form onSubmit={handleRecover} className="space-y-3 text-left">
          <div>
            <label className="text-[10px] text-outline uppercase block mb-1 font-semibold">Corporate Email or Broker ID</label>
            <input type="text" placeholder="trader.clearance@colombologistics.lk" value={email} onChange={(e) => setEmail(e.target.value)} required
              className="w-full px-3 py-2 bg-surface-container-low rounded-lg text-on-surface" />
          </div>
          <button type="submit" className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary-container text-white font-bold text-xs shadow-md transition-all">
            Send Cryptographic Reset Link
          </button>
        </form>
        <div className="pt-2 border-t border-outline-variant/20">
          <Link to="/auth/signin" className="text-primary font-semibold hover:underline">← Back to Institutional Sign In</Link>
        </div>
      </div>
    </div>
  );
}
