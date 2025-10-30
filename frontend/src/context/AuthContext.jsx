/**
 * AuthContext - Firebase Authentication Context
 *
 * Provides authentication state and methods throughout the application.
 * Handles user login, logout, registration, and token management.
 */

import { createContext, useContext, useEffect, useState } from 'react';
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  sendPasswordResetEmail,
} from 'firebase/auth';
import { auth, googleProvider } from '../config/firebase';
import api from '../services/api';

// Create Auth Context
const AuthContext = createContext({});

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth Provider Component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [idToken, setIdToken] = useState(null);

  /**
   * Sign up with email and password
   */
  const signUp = async (email, password) => {
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const token = await userCredential.user.getIdToken();

      // Call backend to create user record
      await api.post('/api/auth/register', {}, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      return userCredential.user;
    } catch (error) {
      console.error('Sign up error:', error);
      throw error;
    }
  };

  /**
   * Sign in with email and password
   */
  const signIn = async (email, password) => {
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const token = await userCredential.user.getIdToken();

      // Call backend to sync user data
      await api.post('/api/auth/login', {}, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      return userCredential.user;
    } catch (error) {
      console.error('Sign in error:', error);
      throw error;
    }
  };

  /**
   * Sign in with Google OAuth
   */
  const signInWithGoogle = async () => {
    try {
      // Use popup for OAuth flow
      const userCredential = await signInWithPopup(auth, googleProvider);
      const token = await userCredential.user.getIdToken();

      // Call backend to sync user data (creates user if first time)
      try {
        await api.post('/api/auth/login', {}, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
      } catch (apiError) {
        // If backend sync fails, still allow login but log the error
        console.warn('Backend sync failed, but user is authenticated:', apiError);
        // Don't throw - user is still authenticated on Firebase
      }

      return userCredential.user;
    } catch (error) {
      console.error('Google sign in error:', error);
      
      // Provide user-friendly error messages
      if (error.code === 'auth/popup-blocked') {
        throw new Error('Popup was blocked. Please allow popups for this site.');
      } else if (error.code === 'auth/popup-closed-by-user') {
        throw new Error('Sign-in was cancelled.');
      } else if (error.code === 'auth/network-request-failed') {
        throw new Error('Network error. Please check your connection and try again.');
      } else if (error.code === 'auth/cancelled-popup-request') {
        // Don't show error for cancelled popup - user might be clicking multiple times
        return null;
      }
      
      throw error;
    }
  };

  /**
   * Sign out
   */
  const signOut = async () => {
    try {
      await firebaseSignOut(auth);
      setUser(null);
      setIdToken(null);
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  };

  /**
   * Send password reset email
   */
  const resetPassword = async (email) => {
    try {
      await sendPasswordResetEmail(auth, email);
    } catch (error) {
      console.error('Password reset error:', error);
      throw error;
    }
  };

  /**
   * Get current ID token
   */
  const getToken = async () => {
    if (auth.currentUser) {
      return await auth.currentUser.getIdToken();
    }
    return null;
  };

  // Listen to auth state changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        // User is signed in
        setUser(firebaseUser);

        // Get and store ID token
        const token = await firebaseUser.getIdToken();
        setIdToken(token);
      } else {
        // User is signed out
        setUser(null);
        setIdToken(null);
      }

      setLoading(false);
    });

    // Cleanup subscription
    return () => unsubscribe();
  }, []);

  // Listen to token changes (auto-refresh every hour)
  useEffect(() => {
    if (!auth.currentUser) return;

    const unsubscribe = auth.onIdTokenChanged(async (firebaseUser) => {
      if (firebaseUser) {
        const token = await firebaseUser.getIdToken();
        setIdToken(token);
      } else {
        setIdToken(null);
      }
    });

    return () => unsubscribe();
  }, []);

  // Context value
  const value = {
    user,
    loading,
    idToken,
    signUp,
    signIn,
    signInWithGoogle,
    signOut,
    resetPassword,
    getToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
