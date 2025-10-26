"use client";

import React, { useState, useEffect } from 'react';
import { Shield, Smartphone, Mail, Key, Copy, Check, AlertCircle } from 'lucide-react';
import QRCode from 'qrcode';

interface MFASetupProps {
  userId: string;
  onComplete: () => void;
}

export const MFASetup: React.FC<MFASetupProps> = ({ userId, onComplete }) => {
  const [method, setMethod] = useState<'totp' | 'sms' | 'email' | null>(null);
  const [step, setStep] = useState<'select' | 'setup' | 'verify'>('select');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // TOTP setup state
  const [qrCodeUrl, setQrCodeUrl] = useState<string>('');
  const [secret, setSecret] = useState<string>('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  
  // SMS/Email setup state
  const [phoneNumber, setPhoneNumber] = useState('');
  const [email, setEmail] = useState('');
  
  // Verification state
  const [verificationCode, setVerificationCode] = useState('');
  const [copiedSecret, setCopiedSecret] = useState(false);
  const [copiedCodes, setCopiedCodes] = useState(false);

  const setupTOTP = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/auth/mfa/setup-totp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ userId }),
      });
      
      if (!response.ok) throw new Error('Failed to setup TOTP');
      
      const data = await response.json();
      
      // Generate QR code
      const qrCode = await QRCode.toDataURL(data.uri);
      setQrCodeUrl(qrCode);
      setSecret(data.secret);
      setBackupCodes(data.backupCodes);
      setStep('setup');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const setupSMS = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/auth/mfa/setup-sms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ userId, phoneNumber }),
      });
      
      if (!response.ok) throw new Error('Failed to setup SMS MFA');
      
      setStep('verify');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const setupEmail = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/auth/mfa/setup-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ userId, email }),
      });
      
      if (!response.ok) throw new Error('Failed to setup Email MFA');
      
      setStep('verify');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const verifyMFA = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/auth/mfa/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ 
          userId,
          method,
          code: verificationCode,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Invalid verification code');
      }
      
      onComplete();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text: string, type: 'secret' | 'codes') => {
    try {
      await navigator.clipboard.writeText(text);
      if (type === 'secret') {
        setCopiedSecret(true);
        setTimeout(() => setCopiedSecret(false), 2000);
      } else {
        setCopiedCodes(true);
        setTimeout(() => setCopiedCodes(false), 2000);
      }
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  if (step === 'select') {
    return (
      <div className="max-w-md mx-auto p-6">
        <div className="text-center mb-8">
          <Shield className="w-16 h-16 text-blue-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Enable Two-Factor Authentication</h2>
          <p className="text-gray-600">
            Add an extra layer of security to your account
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-start">
            <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div className="space-y-4">
          <button
            onClick={() => {
              setMethod('totp');
              setupTOTP();
            }}
            disabled={loading}
            className="w-full p-4 border border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
          >
            <div className="flex items-start">
              <Smartphone className="w-6 h-6 text-blue-600 mr-3 mt-1" />
              <div>
                <h3 className="font-semibold mb-1">Authenticator App</h3>
                <p className="text-sm text-gray-600">
                  Use an app like Google Authenticator or Authy
                </p>
              </div>
            </div>
          </button>

          <button
            onClick={() => {
              setMethod('sms');
              setStep('setup');
            }}
            disabled={loading}
            className="w-full p-4 border border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
          >
            <div className="flex items-start">
              <Smartphone className="w-6 h-6 text-blue-600 mr-3 mt-1" />
              <div>
                <h3 className="font-semibold mb-1">SMS Text Message</h3>
                <p className="text-sm text-gray-600">
                  Receive codes via text message
                </p>
              </div>
            </div>
          </button>

          <button
            onClick={() => {
              setMethod('email');
              setStep('setup');
            }}
            disabled={loading}
            className="w-full p-4 border border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
          >
            <div className="flex items-start">
              <Mail className="w-6 h-6 text-blue-600 mr-3 mt-1" />
              <div>
                <h3 className="font-semibold mb-1">Email</h3>
                <p className="text-sm text-gray-600">
                  Receive codes via email
                </p>
              </div>
            </div>
          </button>
        </div>
      </div>
    );
  }

  if (step === 'setup') {
    if (method === 'totp') {
      return (
        <div className="max-w-md mx-auto p-6">
          <h2 className="text-2xl font-bold mb-6">Set Up Authenticator App</h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold mb-2">1. Scan QR Code</h3>
              <p className="text-sm text-gray-600 mb-4">
                Scan this QR code with your authenticator app
              </p>
              {qrCodeUrl && (
                <div className="bg-white p-4 rounded-lg border border-gray-200 inline-block">
                  <img src={qrCodeUrl} alt="MFA QR Code" className="w-48 h-48" />
                </div>
              )}
            </div>

            <div>
              <h3 className="font-semibold mb-2">2. Or Enter Code Manually</h3>
              <div className="flex items-center space-x-2">
                <code className="flex-1 p-2 bg-gray-100 rounded font-mono text-sm">
                  {secret}
                </code>
                <button
                  onClick={() => copyToClipboard(secret, 'secret')}
                  className="p-2 hover:bg-gray-100 rounded transition-colors"
                >
                  {copiedSecret ? (
                    <Check className="w-5 h-5 text-green-600" />
                  ) : (
                    <Copy className="w-5 h-5 text-gray-600" />
                  )}
                </button>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-2">3. Save Backup Codes</h3>
              <p className="text-sm text-gray-600 mb-2">
                Save these codes in a safe place. You can use them to access your account if you lose your device.
              </p>
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                {backupCodes.map((code, index) => (
                  <div key={index} className="font-mono text-sm">
                    {code}
                  </div>
                ))}
              </div>
              <button
                onClick={() => copyToClipboard(backupCodes.join('\n'), 'codes')}
                className="mt-2 flex items-center space-x-2 text-blue-600 hover:text-blue-700"
              >
                {copiedCodes ? (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>Copy All Codes</span>
                  </>
                )}
              </button>
            </div>

            <button
              onClick={() => setStep('verify')}
              className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Continue to Verification
            </button>
          </div>
        </div>
      );
    }

    if (method === 'sms') {
      return (
        <div className="max-w-md mx-auto p-6">
          <h2 className="text-2xl font-bold mb-6">Set Up SMS Authentication</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone Number
              </label>
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="+1 (555) 123-4567"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={setupSMS}
              disabled={loading || !phoneNumber}
              className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
            >
              {loading ? 'Sending Code...' : 'Send Verification Code'}
            </button>
          </div>
        </div>
      );
    }

    if (method === 'email') {
      return (
        <div className="max-w-md mx-auto p-6">
          <h2 className="text-2xl font-bold mb-6">Set Up Email Authentication</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={setupEmail}
              disabled={loading || !email}
              className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
            >
              {loading ? 'Sending Code...' : 'Send Verification Code'}
            </button>
          </div>
        </div>
      );
    }
  }

  if (step === 'verify') {
    return (
      <div className="max-w-md mx-auto p-6">
        <h2 className="text-2xl font-bold mb-6">Verify Your Setup</h2>
        
        <p className="text-gray-600 mb-6">
          {method === 'totp' && 'Enter the 6-digit code from your authenticator app'}
          {method === 'sms' && `Enter the code we sent to ${phoneNumber}`}
          {method === 'email' && `Enter the code we sent to ${email}`}
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Verification Code
            </label>
            <input
              type="text"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              maxLength={6}
              className="w-full px-3 py-2 text-center text-2xl font-mono border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            onClick={verifyMFA}
            disabled={loading || verificationCode.length !== 6}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          >
            {loading ? 'Verifying...' : 'Verify and Enable MFA'}
          </button>

          {method !== 'totp' && (
            <button
              onClick={() => {
                if (method === 'sms') setupSMS();
                if (method === 'email') setupEmail();
              }}
              disabled={loading}
              className="w-full py-2 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Resend Code
            </button>
          )}
        </div>
      </div>
    );
  }

  return null;
};
