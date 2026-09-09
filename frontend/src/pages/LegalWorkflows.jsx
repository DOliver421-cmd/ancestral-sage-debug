/**
 * /resources → Legal tab — Legal Workflow Engine
 *
 * Hypothetical Lawyer v3.0 converted to React.
 * ALL existing functionality preserved: Case Type, Strategy, Evidence,
 * Calculator, Document Generator, Protection, Nuclear Options.
 *
 * 12 NEW enhancements added as workflows:
 * 1. Resource Hub bridge
 * 2. Legal Issue Navigator
 * 3. Legal Readiness Workflow
 * 4. Contract Workflow
 * 5. Grant Legal Readiness
 * 6. Fundraising Compliance
 * 7. Business Legal Setup
 * 8. Intellectual Property Workflow
 * 9. Employment/Contractor Workflow
 * 10. Dispute Preparation
 * 11. Attorney Preparation Packet
 * 12. Extended Document Generator
 */

import { useState, useCallback, useMemo, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Scale, Shield, Target, FileText, Calculator, Zap, Swords,
  ChevronRight, ChevronDown, ChevronUp, CheckCircle2, Circle,
  AlertTriangle, BookOpen, Briefcase, Heart, DollarSign, Award,
  Users, Lightbulb, Search, ArrowRight, Download, Printer,
  Clock, TrendingUp, Star, Gavel, Landmark, ShieldCheck, Lock,
  Mail, Phone, MapPin, Plus, Trash2, Eye, EyeOff, Copy, Check,
  Layers, Flag, Flame, Compass, Link as LinkIcon, Rocket,
  UserCheck, FileCheck, FolderOpen, ScrollText, ClipboardList,
  PenTool, ShieldAlert, FileWarning, Handshake, Building2, Globe,
} from "lucide-react";
