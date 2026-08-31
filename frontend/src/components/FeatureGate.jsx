/**
 * FeatureGate.jsx — Capability Gate Component
 * 
 * Wraps content to enforce entitlement checks.
 * If the user doesn't have access, shows an upgrade prompt.
 * 
 * Usage:
 *   <FeatureGate feature="publish.analytics">
 *     <AdvancedAnalyticsPanel />
 *   </FeatureGate>
 *   
 *   <FeatureGate feature="nam.coaching" fallback={<BasicChat />}>
 *     <CoachingSession />
 *   </FeatureGate>
 *   
 *   <FeatureGate feature="create.projects" showLimit>
 *     <ProjectCreator />
 *   </FeatureGate>
 */

import React from 'react';
import { useEntitlements } from '../hooks/useEntitlements';

// Human-readable feature names for upgrade prompts
const FEATURE_NAMES = {
  'nam.chat': 'AI Chat',
  'nam.memory': 'AI Memory',
  'nam.coaching': 'AI Coaching',
  'nam.orchestration': 'AI Orchestration',
  'nam.autonomous': 'Autonomous AI',
  'create.projects': 'Projects',
  'create.ai_assist': 'AI Writing Assist',
  'create.advanced_formatting': 'Advanced Formatting',
  'create.collaboration': 'Team Collaboration',
  'create.white_label': 'White Label',
  'publish.create': 'Publishing',
  'publish.marketplace': 'Marketplace Publishing',
  'publish.analytics': 'Publishing Analytics',
  'publish.distribution': 'Distribution',
  'publish.scheduling': 'Scheduled Publishing',
  'learn.courses': 'Courses',
  'learn.ai_tutor': 'AI Tutor',
  'learn.coaching': 'Learning Coaching',
  'learn.certificates': 'Certificates',
  'learn.create_courses': 'Course Creation',
  'community.read': 'Community',
  'community.post': 'Community Posting',
  'community.create_hub': 'Hub Creation',
  'community.moderate': 'Moderation',
  'community.guild': 'Guild Management',
  'marketplace.browse': 'Marketplace',
  'marketplace.sell': 'Selling',
  'marketplace.storefront': 'Custom Storefront',
  'marketplace.analytics': 'Sales Analytics',
  'marketplace.vendor_mgmt': 'Vendor Management',
  'sanctuary.journal': 'Journaling',
  'sanctuary.ai_reflection': 'AI Reflection',
  'sanctuary.mood_tracking': 'Mood Tracking',
  'sanctuary.group': 'Group Sessions',
  'sanctuary.org_wellness': 'Organization Wellness',
  'music.compose': 'Music Composition',
  'music.studio': 'Production Studio',
  'music.ai_production': 'AI Production',
  'music.collaboration': 'Team Production',
  'music.label_tools': 'Label Tools',
  'games.play': 'Games',
  'games.compete': 'Competitive Ranking',
  'games.create': 'Game Creation',
  'story.vonns_saga': "Vonn's Saga",
  'story.progress': 'Story Progress Saving',
  'story.music': 'Integrated Music',
  'ascension.access': 'Ascension Protocols',
  'ascension.phases': 'Advanced Ascension Phases',
  'ascension.audio': 'Audio Narration',
  'ascension.video': 'Video Content',
  'director.governance': 'Governance',
  'director.api': 'API Access',
  'director.compliance': 'Compliance Tools',
};

// Minimum tier required for each feature
const FEATURE_MIN_TIER = {
  'nam.chat': 'free',
  'nam.memory': 'creator',
  'nam.coaching': 'pro',
  'nam.orchestration': 'pro',
  'nam.autonomous': 'studio',
  'create.projects': 'free',
  'create.ai_assist': 'creator',
  'create.advanced_formatting': 'pro',
  'create.collaboration': 'pro',
  'create.white_label': 'studio',
  'publish.create': 'free',
  'publish.marketplace': 'creator',
  'publish.analytics': 'creator',
  'publish.distribution': 'pro',
  'publish.scheduling': 'pro',
  'learn.courses': 'free',
  'learn.ai_tutor': 'creator',
  'learn.coaching': 'pro',
  'learn.certificates': 'creator',
  'learn.create_courses': 'studio',
  'community.read': 'free',
  'community.post': 'free',
  'community.create_hub': 'creator',
  'community.moderate': 'pro',
  'community.guild': 'studio',
  'marketplace.browse': 'free',
  'marketplace.sell': 'creator',
  'marketplace.storefront': 'pro',
  'marketplace.analytics': 'pro',
  'marketplace.vendor_mgmt': 'studio',
  'sanctuary.journal': 'free',
  'sanctuary.ai_reflection': 'creator',
  'sanctuary.mood_tracking': 'pro',
  'sanctuary.group': 'studio',
  'sanctuary.org_wellness': 'director',
  'music.compose': 'free',
  'music.studio': 'creator',
  'music.ai_production': 'pro',
  'music.collaboration': 'studio',
  'music.label_tools': 'director',
  'games.play': 'free',
  'games.compete': 'creator',
  'games.create': 'studio',
  'story.vonns_saga': 'free',
  'story.progress': 'creator',
  'story.music': 'creator',
  'ascension.access': 'free',
  'ascension.phases': 'creator',
  'ascension.audio': 'creator',
  'ascension.video': 'pro',
  'director.analytics': 'director',
  'director.governance': 'director',
  'director.api': 'director',
  'director.compliance': 'director',
};

const TIER_LABELS = {
  free: 'Free',
  creator: 'Creator',
  pro: 'Pro',
  studio: 'Studio',
  director: 'Director',
};

export function FeatureGate({
  feature,
  children,
  fallback = null,
  showLimit = false,
  className = '',
}) {
  const { canAccess, getLimit, tier, isUnlimited } = useEntitlements();
  
  const hasAccess = canAccess(feature);
  const featureName = FEATURE_NAMES[feature] || feature;
  const requiredTier = FEATURE_MIN_TIER[feature] || 'creator';
  
  // If user has access, render children
  if (hasAccess) {
    return (
      <div className={className}>
        {children}
        {showLimit && (
          <UsageIndicator feature={feature} />
        )}
      </div>
    );
  }
  
  // If fallback is provided, render it
  if (fallback) {
    return <div className={className}>{fallback}</div>;
  }
  
  // Otherwise, render upgrade prompt
  return (
    <div className={`feature-gate ${className}`}>
      <div className="feature-gate-content">
        <div className="feature-gate-icon">🔒</div>
        <h3 className="feature-gate-title">{featureName}</h3>
        <p className="feature-gate-description">
          This feature requires the <strong>{TIER_LABELS[requiredTier]}</strong> plan or higher.
        </p>
        <a href="/plans" className="feature-gate-cta">
          Upgrade to {TIER_LABELS[requiredTier]}
        </a>
      </div>
    </div>
  );
}

function UsageIndicator({ feature }) {
  const { getLimit, isUnlimited } = useEntitlements();
  
  // Only show for numeric limits
  const limit = getLimit(feature);
  if (typeof limit !== 'number' || limit === -1) return null;
  
  return (
    <div className="usage-indicator">
      <span className="usage-label">Limit: {limit}</span>
    </div>
  );
}

export default FeatureGate;
