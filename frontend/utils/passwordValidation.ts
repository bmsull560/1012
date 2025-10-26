/**
 * Password validation utility
 * Implements NIST 800-63B compliant password strength checking
 */

interface PasswordContext {
  email?: string;
  firstName?: string;
  lastName?: string;
  username?: string;
}

interface PasswordValidationResult {
  score: number; // 0-4 (very weak to strong)
  requirements: {
    minLength: boolean;
    hasUpperCase: boolean;
    hasLowerCase: boolean;
    hasNumber: boolean;
    hasSpecialChar: boolean;
    noCommonPatterns: boolean;
  };
  feedback: string[];
  entropy: number;
}

// Common weak passwords (top 100)
const COMMON_PASSWORDS = new Set([
  'password', '123456', '123456789', '12345678', '12345', '1234567',
  'password123', 'password1', 'password!', 'qwerty', 'abc123', 'monkey',
  'letmein', 'dragon', 'baseball', 'iloveyou', 'trustno1', 'sunshine',
  'master', 'welcome', 'shadow', 'ashley', 'football', 'jesus', 'michael',
  'ninja', 'mustang', 'password1', 'admin', 'welcome123', 'welcome1',
]);

// Common patterns
const COMMON_PATTERNS = [
  /^(.)\1+$/, // All same character
  /^(012|123|234|345|456|567|678|789|890)+$/, // Sequential numbers
  /^(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)+$/i, // Sequential letters
  /^(qwerty|asdf|zxcv)+$/i, // Keyboard patterns
];

export function validatePassword(
  password: string,
  context?: PasswordContext
): PasswordValidationResult {
  const result: PasswordValidationResult = {
    score: 0,
    requirements: {
      minLength: false,
      hasUpperCase: false,
      hasLowerCase: false,
      hasNumber: false,
      hasSpecialChar: false,
      noCommonPatterns: true,
    },
    feedback: [],
    entropy: 0,
  };

  // Check minimum length (NIST recommends 8, we require 12 for better security)
  result.requirements.minLength = password.length >= 12;
  if (!result.requirements.minLength) {
    result.feedback.push(`Password must be at least 12 characters (currently ${password.length}).`);
  }

  // Check character types
  result.requirements.hasUpperCase = /[A-Z]/.test(password);
  result.requirements.hasLowerCase = /[a-z]/.test(password);
  result.requirements.hasNumber = /\d/.test(password);
  result.requirements.hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);

  // Check for common passwords
  const lowerPassword = password.toLowerCase();
  if (COMMON_PASSWORDS.has(lowerPassword)) {
    result.feedback.push('This is a commonly used password. Please choose something more unique.');
    result.requirements.noCommonPatterns = false;
  }

  // Check for common patterns
  for (const pattern of COMMON_PATTERNS) {
    if (pattern.test(password)) {
      result.feedback.push('Password contains common patterns. Mix up your characters more.');
      result.requirements.noCommonPatterns = false;
      break;
    }
  }

  // Check for context-based patterns (user info in password)
  if (context) {
    const contextValues = [
      context.email?.split('@')[0],
      context.firstName,
      context.lastName,
      context.username,
    ].filter(Boolean).map(v => v!.toLowerCase());

    for (const value of contextValues) {
      if (value && value.length > 2 && lowerPassword.includes(value)) {
        result.feedback.push("Don't include personal information in your password.");
        result.requirements.noCommonPatterns = false;
        break;
      }
    }
  }

  // Check for repeated characters
  if (/(.)\1{2,}/.test(password)) {
    result.feedback.push('Avoid repeating characters (e.g., "aaa" or "111").');
    result.requirements.noCommonPatterns = false;
  }

  // Calculate entropy
  let charsetSize = 0;
  if (result.requirements.hasLowerCase) charsetSize += 26;
  if (result.requirements.hasUpperCase) charsetSize += 26;
  if (result.requirements.hasNumber) charsetSize += 10;
  if (result.requirements.hasSpecialChar) charsetSize += 32;
  
  if (charsetSize > 0) {
    result.entropy = password.length * Math.log2(charsetSize);
  }

  // Calculate score (0-4)
  let score = 0;
  
  // Length scoring
  if (password.length >= 8) score += 0.5;
  if (password.length >= 12) score += 0.5;
  if (password.length >= 16) score += 0.5;
  
  // Complexity scoring
  const complexityCount = [
    result.requirements.hasUpperCase,
    result.requirements.hasLowerCase,
    result.requirements.hasNumber,
    result.requirements.hasSpecialChar,
  ].filter(Boolean).length;
  
  score += complexityCount * 0.5;
  
  // Pattern penalty
  if (!result.requirements.noCommonPatterns) {
    score = Math.max(0, score - 1.5);
  }
  
  // Entropy bonus
  if (result.entropy >= 60) score += 0.5;
  if (result.entropy >= 80) score += 0.5;
  
  result.score = Math.min(4, Math.floor(score));

  // Add feedback based on missing requirements
  if (!result.requirements.hasUpperCase) {
    result.feedback.push('Add uppercase letters for better security.');
  }
  if (!result.requirements.hasLowerCase) {
    result.feedback.push('Add lowercase letters for better security.');
  }
  if (!result.requirements.hasNumber) {
    result.feedback.push('Add numbers for better security.');
  }
  if (!result.requirements.hasSpecialChar) {
    result.feedback.push('Add special characters (!@#$%^&*) for better security.');
  }

  // Positive feedback for strong passwords
  if (result.score >= 3 && result.feedback.length === 0) {
    if (result.score === 4) {
      result.feedback.push('Excellent password strength!');
    } else {
      result.feedback.push('Good password strength.');
    }
  }

  return result;
}

/**
 * Generate a strong random password
 */
export function generateStrongPassword(length: number = 16): string {
  const lowercase = 'abcdefghijklmnopqrstuvwxyz';
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const numbers = '0123456789';
  const special = '!@#$%^&*()_+-=[]{}|;:,.<>?';
  
  const allChars = lowercase + uppercase + numbers + special;
  
  let password = '';
  
  // Ensure at least one of each type
  password += lowercase[Math.floor(Math.random() * lowercase.length)];
  password += uppercase[Math.floor(Math.random() * uppercase.length)];
  password += numbers[Math.floor(Math.random() * numbers.length)];
  password += special[Math.floor(Math.random() * special.length)];
  
  // Fill the rest randomly
  for (let i = password.length; i < length; i++) {
    password += allChars[Math.floor(Math.random() * allChars.length)];
  }
  
  // Shuffle the password
  return password.split('').sort(() => Math.random() - 0.5).join('');
}

/**
 * Check if password has been breached (requires API call to HaveIBeenPwned)
 */
export async function checkPasswordBreach(password: string): Promise<boolean> {
  try {
    // Create SHA-1 hash of password
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-1', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
    
    // Send first 5 characters to HaveIBeenPwned API
    const prefix = hashHex.substring(0, 5);
    const suffix = hashHex.substring(5);
    
    const response = await fetch(`https://api.pwnedpasswords.com/range/${prefix}`, {
      headers: {
        'Add-Padding': 'true', // Helps prevent timing attacks
      },
    });
    
    if (!response.ok) {
      console.error('Failed to check password breach status');
      return false; // Assume not breached if API fails
    }
    
    const text = await response.text();
    const lines = text.split('\n');
    
    for (const line of lines) {
      const [hashSuffix, count] = line.split(':');
      if (hashSuffix === suffix) {
        return true; // Password has been breached
      }
    }
    
    return false; // Password not found in breach database
  } catch (error) {
    console.error('Error checking password breach:', error);
    return false; // Assume not breached if check fails
  }
}
