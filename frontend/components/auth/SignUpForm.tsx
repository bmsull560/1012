"use client";

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { validatePassword } from '@/utils/passwordValidation';
import { Eye, EyeOff, Check, X, AlertCircle } from 'lucide-react';

interface SignUpFormData {
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  organizationName: string;
  acceptTerms: boolean;
}

export const SignUpForm: React.FC = () => {
  const { signUp } = useAuth();
  const [formData, setFormData] = useState<SignUpFormData>({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    organizationName: '',
    acceptTerms: false,
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [emailVerificationSent, setEmailVerificationSent] = useState(false);
  
  // Password validation state
  const [passwordStrength, setPasswordStrength] = useState<{
    score: number;
    requirements: {
      minLength: boolean;
      hasUpperCase: boolean;
      hasLowerCase: boolean;
      hasNumber: boolean;
      hasSpecialChar: boolean;
      noCommonPatterns: boolean;
    };
    feedback: string[];
  } | null>(null);

  const handlePasswordChange = (password: string) => {
    setFormData({ ...formData, password });
    
    // Validate password strength
    const validation = validatePassword(password, {
      email: formData.email,
      firstName: formData.firstName,
      lastName: formData.lastName,
    });
    
    setPasswordStrength(validation);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    // Validation
    if (!formData.acceptTerms) {
      setError('You must accept the terms and conditions');
      return;
    }
    
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (!passwordStrength || passwordStrength.score < 3) {
      setError('Password is too weak. Please choose a stronger password.');
      return;
    }
    
    setLoading(true);
    
    try {
      const result = await signUp({
        email: formData.email,
        password: formData.password,
        firstName: formData.firstName,
        lastName: formData.lastName,
        organizationName: formData.organizationName,
      });
      
      if (result.error) {
        setError(result.error);
      } else {
        // Show email verification message
        setEmailVerificationSent(true);
      }
    } catch (err: any) {
      setError(err.message || 'Sign up failed');
    } finally {
      setLoading(false);
    }
  };

  if (emailVerificationSent) {
    return (
      <div className="text-center p-8">
        <div className="mb-4">
          <Check className="w-16 h-16 text-green-500 mx-auto" />
        </div>
        <h2 className="text-2xl font-bold mb-4">Check Your Email</h2>
        <p className="text-gray-600 mb-4">
          We've sent a verification email to <strong>{formData.email}</strong>
        </p>
        <p className="text-sm text-gray-500">
          Please click the link in the email to verify your account and complete registration.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start">
          <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            First Name
          </label>
          <input
            type="text"
            required
            value={formData.firstName}
            onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Last Name
          </label>
          <input
            type="text"
            required
            value={formData.lastName}
            onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Organization Name
        </label>
        <input
          type="text"
          required
          value={formData.organizationName}
          onChange={(e) => setFormData({ ...formData, organizationName: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Email Address
        </label>
        <input
          type="email"
          required
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Password
        </label>
        <div className="relative">
          <input
            type={showPassword ? 'text' : 'password'}
            required
            value={formData.password}
            onChange={(e) => handlePasswordChange(e.target.value)}
            className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>
        
        {passwordStrength && formData.password && (
          <div className="mt-2 space-y-2">
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${
                    passwordStrength.score === 0 ? 'bg-red-500 w-1/5' :
                    passwordStrength.score === 1 ? 'bg-orange-500 w-2/5' :
                    passwordStrength.score === 2 ? 'bg-yellow-500 w-3/5' :
                    passwordStrength.score === 3 ? 'bg-green-500 w-4/5' :
                    'bg-green-600 w-full'
                  }`}
                />
              </div>
              <span className={`text-sm font-medium ${
                passwordStrength.score < 2 ? 'text-red-600' :
                passwordStrength.score < 3 ? 'text-yellow-600' :
                'text-green-600'
              }`}>
                {passwordStrength.score === 0 ? 'Very Weak' :
                 passwordStrength.score === 1 ? 'Weak' :
                 passwordStrength.score === 2 ? 'Fair' :
                 passwordStrength.score === 3 ? 'Good' :
                 'Strong'}
              </span>
            </div>
            
            <div className="space-y-1">
              {Object.entries(passwordStrength.requirements).map(([key, met]) => (
                <div key={key} className="flex items-center gap-2 text-sm">
                  {met ? (
                    <Check className="w-4 h-4 text-green-500" />
                  ) : (
                    <X className="w-4 h-4 text-gray-400" />
                  )}
                  <span className={met ? 'text-green-700' : 'text-gray-500'}>
                    {key === 'minLength' && 'At least 12 characters'}
                    {key === 'hasUpperCase' && 'Contains uppercase letter'}
                    {key === 'hasLowerCase' && 'Contains lowercase letter'}
                    {key === 'hasNumber' && 'Contains number'}
                    {key === 'hasSpecialChar' && 'Contains special character'}
                    {key === 'noCommonPatterns' && 'No common patterns'}
                  </span>
                </div>
              ))}
            </div>
            
            {passwordStrength.feedback.length > 0 && (
              <div className="text-sm text-amber-600 bg-amber-50 p-2 rounded">
                {passwordStrength.feedback.join(' ')}
              </div>
            )}
          </div>
        )}
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Confirm Password
        </label>
        <div className="relative">
          <input
            type={showConfirmPassword ? 'text' : 'password'}
            required
            value={formData.confirmPassword}
            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
            className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
          >
            {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>
        {formData.confirmPassword && formData.password !== formData.confirmPassword && (
          <p className="text-sm text-red-600 mt-1">Passwords do not match</p>
        )}
      </div>
      
      <div className="flex items-start">
        <input
          type="checkbox"
          id="acceptTerms"
          checked={formData.acceptTerms}
          onChange={(e) => setFormData({ ...formData, acceptTerms: e.target.checked })}
          className="mt-1 mr-2"
        />
        <label htmlFor="acceptTerms" className="text-sm text-gray-600">
          I accept the{' '}
          <a href="/terms" target="_blank" className="text-blue-600 hover:underline">
            Terms and Conditions
          </a>{' '}
          and{' '}
          <a href="/privacy" target="_blank" className="text-blue-600 hover:underline">
            Privacy Policy
          </a>
        </label>
      </div>
      
      <button
        type="submit"
        disabled={loading || !formData.acceptTerms || (passwordStrength?.score ?? 0) < 3}
        className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Creating Account...' : 'Sign Up'}
      </button>
      
      <p className="text-center text-sm text-gray-600">
        Already have an account?{' '}
        <a href="/login" className="text-blue-600 hover:underline">
          Sign In
        </a>
      </p>
    </form>
  );
};
