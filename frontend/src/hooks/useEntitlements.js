/**
 * useEntitlements.js — Frontend Entitlement Hook
 * 
 * Provides capability checking and limit querying for the current user.
 * 
 * Usage:
 *   const { tier, canAccess, getLimit, isUnlimited, entitlements } = useEntitlements();
 *   
 *   if (canAccess('publish.analytics')) {
 *     // Show analytics panel
 *   }
 *   
 *   const projectLimit = getLimit('projects');
 *   if (projectLimit === -1) {
 *     // Unlimited projects
 *   }
 */

import { useMemo } from 'react';
import { useAuth } from '../context/AuthContext';

// Tier level mapping for comparisons
const TIER_LEVELS = { free: 0, creator: 1, pro: 2, studio: 3, director: 4 };

// Default entitlements for free tier (fallback)
const DEFAULT_ENTITLEMENTS = {
  tier: 'free',
  capabilities: {
    'nam.chat': true,
    'nam.memory': false,
    'nam.coaching': false,
    'nam.orchestration': false,
    'nam.autonomous': false,
    'create.projects': 3,
    'create.ai_assist': false,
    'create.advanced_formatting': false,
    'create.collaboration': false,
    'create.white_label': false,
    'publish.create': true,
    'publish.marketplace': false,
    'publish.analytics': false,
    'publish.distribution': false,
    'publish.scheduling': false,
    'learn.courses': 1,
    'learn.ai_tutor': false,
    'learn.coaching': false,
    'learn.certificates': false,
    'learn.create_courses': false,
    'community.read': true,
    'community.post': true,
    'community.create_hub': false,
    'community.moderate': false,
    'community.guild': false,
    'marketplace.browse': true,
    'marketplace.sell': false,
    'marketplace.storefront': false,
    'marketplace.analytics': false,
    'marketplace.vendor_mgmt': false,
    'sanctuary.journal': true,
    'sanctuary.ai_reflection': false,
    'sanctuary.mood_tracking': false,
    'sanctuary.group': false,
    'sanctuary.org_wellness': false,
    'music.compose': true,
    'music.studio': false,
    'music.ai_production': false,
    'music.collaboration': false,
    'music.label_tools': false,
    'games.play': true,
    'games.compete': false,
    'games.create': false,
    'director.analytics': false,
    'director.governance': false,
    'director.api': false,
    'director.compliance': false,
  },
  limits: {
    ai_daily_tokens: 1000,
    storage_mb: 100,
    projects: 3,
    courses: 1,
    marketplace_fee: 0.30,
  },
};

export function useEntitlements() {
  const { user } = useAuth();
  
  const entitlements = useMemo(() => {
    if (!user?.membership) {
      return DEFAULT_ENTITLEMENTS;
    }
    
    const tier = user.membership.tier || 'free';
    const tierConfig = DEFAULT_ENTITLEMENTS; // In production, fetch from API
    
    // Apply user overrides
    const userOverrides = user.membership.features || {};
    const capabilities = { ...tierConfig.capabilities, ...userOverrides };
    
    const resourceKeys = ['ai_daily_tokens', 'storage_mb', 'projects', 'courses', 'marketplace_fee'];
    const caps = Object.fromEntries(
      Object.entries(capabilities).filter(([k]) => !resourceKeys.includes(k))
    );
    const limits = Object.fromEntries(
      Object.entries(capabilities).filter(([k]) => resourceKeys.includes(k))
    );
    
    return { tier, capabilities: caps, limits };
  }, [user]);
  
  const tier = entitlements.tier;
  
  /**
   * Check if the user can access a specific capability.
   * Returns true if enabled, false if disabled.
   */
  const canAccess = useMemo(() => {
    return (capability) => {
      const value = entitlements.capabilities[capability];
      
      // Boolean capabilities
      if (typeof value === 'boolean') return value;
      
      // Numeric capabilities (e.g., project limits)
      // A value of -1 means unlimited, 0 means disabled
      if (typeof value === 'number') return value !== 0;
      
      return false;
    };
  }, [entitlements]);
  
  /**
   * Get a resource limit for the current user.
   * Returns -1 for unlimited, 0 for disabled, or a positive number.
   */
  const getLimit = useMemo(() => {
    return (resource) => {
      return entitlements.limits[resource] ?? 0;
    };
  }, [entitlements]);
  
  /**
   * Check if a resource is unlimited for the current user.
   */
  const isUnlimited = useMemo(() => {
    return (resource) => {
      return entitlements.limits[resource] === -1;
    };
  }, [entitlements]);
  
  /**
   * Check if the user's tier is at or above a required tier.
   */
  const hasTier = useMemo(() => {
    return (requiredTier) => {
      return (TIER_LEVELS[tier] || 0) >= (TIER_LEVELS[requiredTier] || 0);
    };
  }, [tier]);
  
  /**
   * Get the marketplace fee for the current user.
   */
  const marketplaceFee = entitlements.limits.marketplace_fee || 0.30;
  
  /**
   * Get a human-readable tier label.
   */
  const tierLabel = useMemo(() => {
    const labels = {
      free: 'Free',
      creator: 'Creator',
      pro: 'Pro',
      studio: 'Studio',
      director: 'Director',
    };
    return labels[tier] || 'Free';
  }, [tier]);
  
  /**
   * Check if the user is on the free tier.
   */
  const isFree = tier === 'free';
  
  /**
   * Get the next tier in the upgrade path.
   */
  const nextTier = useMemo(() => {
    const tiers = ['free', 'creator', 'pro', 'studio', 'director'];
    const currentIndex = tiers.indexOf(tier);
    if (currentIndex < tiers.length - 1) {
      return tiers[currentIndex + 1];
    }
    return null;
  }, [tier]);
  
  return {
    tier,
    tierLabel,
    isFree,
    nextTier,
    entitlements,
    canAccess,
    getLimit,
    isUnlimited,
    hasTier,
    marketplaceFee,
  };
}

export default useEntitlements;
