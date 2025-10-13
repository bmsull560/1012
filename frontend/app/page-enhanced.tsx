"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import {
  Brain,
  Sparkles,
  Target,
  TrendingUp,
  Users,
  BarChart3,
  FileText,
  MessageSquare,
  Settings,
  ChevronRight,
  ArrowRight,
  CheckCircle,
  Clock,
  DollarSign,
  Shield,
  Zap,
  Globe,
  Award,
  Briefcase,
  Building2,
  GitBranch,
  Layers,
  Database,
  Cloud,
  Lock,
  Play,
  BookOpen,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Star,
  Activity,
  PieChart,
  LineChart,
  Cpu,
  Smartphone,
  Monitor,
  Server,
  Code2,
  Palette,
  Lightbulb,
  Rocket,
  Heart,
  ThumbsUp,
  TrendingDown,
  AlertCircle,
  Info,
  HelpCircle,
  ExternalLink,
  Download,
  Upload,
  RefreshCw,
  Search,
  Filter,
  Menu,
  X,
  Plus,
  Minus,
  Edit,
  Trash2,
  Copy,
  Clipboard,
  Share2,
  Send,
  Archive,
  Folder,
  FolderOpen,
  File,
  FileCheck,
  FilePlus,
  FileX,
  Printer,
  Save,
  Eye,
  EyeOff,
  Link as LinkIcon,
  Unlink,
  Anchor,
  Navigation,
  Map,
  Compass,
  Flag,
  Pin,
  Navigation2,
  Crosshair,
  Move,
  Maximize,
  Minimize,
  Maximize2,
  Minimize2,
  Square,
  Circle,
  Triangle,
  Hexagon,
  Octagon,
  Star as StarIcon,
  Heart as HeartIcon,
  Calculator,
} from "lucide-react";

export default function EnhancedHomePage() {
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);

  const features = [
    {
      icon: Brain,
      title: "AI-Powered Intelligence",
      description: "Four specialized AI agents work together to maximize value realization",
      color: "from-purple-500 to-blue-500",
    },
    {
      icon: Layers,
      title: "Living Value Graph",
      description: "Multi-dimensional tracking of value from hypothesis to amplification",
      color: "from-blue-500 to-cyan-500",
    },
    {
      icon: Target,
      title: "Proven ROI",
      description: "Average 285% ROI with 8-month payback period across deployments",
      color: "from-cyan-500 to-green-500",
    },
    {
      icon: Shield,
      title: "Enterprise Ready",
      description: "Bank-grade security, SOC2 compliant, with 99.99% uptime SLA",
      color: "from-green-500 to-emerald-500",
    },
  ];

  const stats = [
    { value: "$2.3M", label: "Average Annual Value", icon: DollarSign },
    { value: "285%", label: "Average ROI", icon: TrendingUp },
    { value: "8mo", label: "Payback Period", icon: Clock },
    { value: "94%", label: "Success Rate", icon: Award },
  ];

  const useCases = [
    {
      title: "Sales Teams",
      icon: Briefcase,
      benefits: ["Close deals 40% faster", "2.5x larger deal sizes", "85% win rate improvement"],
    },
    {
      title: "Customer Success",
      icon: Users,
      benefits: ["90% renewal rate", "3x expansion revenue", "50% reduction in churn"],
    },
    {
      title: "Value Engineers",
      icon: LineChart,
      benefits: ["10x faster modeling", "Real-time ROI tracking", "Automated reporting"],
    },
  ];

  const capabilities = [
    {
      category: "Discovery & Analysis",
      icon: MessageSquare,
      items: [
        "AI-powered discovery calls",
        "Automated pain point mapping",
        "Industry benchmark analysis",
        "Competitive positioning",
      ],
    },
    {
      category: "Value Modeling",
      icon: Calculator,
      items: [
        "Dynamic ROI calculations",
        "Scenario planning",
        "Risk assessment",
        "Custom KPI tracking",
      ],
    },
    {
      category: "Execution & Tracking",
      icon: Activity,
      items: [
        "Real-time progress monitoring",
        "Automated alerts",
        "Milestone tracking",
        "Success metrics",
      ],
    },
    {
      category: "Reporting & Analytics",
      icon: FileText,
      items: [
        "Executive dashboards",
        "QBR automation",
        "Value proof generation",
        "Predictive insights",
      ],
    },
  ];

  const integrations = [
    { name: "Salesforce", icon: "☁️" },
    { name: "HubSpot", icon: "🔧" },
    { name: "Slack", icon: "💬" },
    { name: "Microsoft Teams", icon: "📊" },
    { name: "Jira", icon: "🎯" },
    { name: "Tableau", icon: "📈" },
  ];

  const testimonials = [
    {
      quote: "ValueVerse transformed how we demonstrate ROI. Our win rate increased by 85% in just 6 months.",
      author: "Sarah Chen",
      role: "VP of Sales",
      company: "TechCorp Solutions",
      rating: 5,
    },
    {
      quote: "The AI agents feel like having a team of value consultants working 24/7. Game-changing.",
      author: "Michael Rodriguez",
      role: "Chief Revenue Officer",
      company: "DataFlow Inc",
      rating: 5,
    },
    {
      quote: "We've reduced time-to-value by 60% and our NRR is now at 125%. Incredible platform.",
      author: "Emily Thompson",
      role: "Head of Customer Success",
      company: "CloudScale Pro",
      rating: 5,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-blue-50">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md z-50 border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold">ValueVerse</span>
            </div>
            
            <div className="hidden md:flex items-center gap-8">
              <Link href="/demo" className="text-sm font-medium hover:text-primary transition-colors">
                Product Demo
              </Link>
              <Link href="/agent-demo" className="text-sm font-medium hover:text-primary transition-colors">
                AI Agents
              </Link>
              <a href="#features" className="text-sm font-medium hover:text-primary transition-colors">
                Features
              </a>
              <a href="#pricing" className="text-sm font-medium hover:text-primary transition-colors">
                Pricing
              </a>
            </div>
            
            <div className="flex items-center gap-3">
              <Button variant="outline" size="sm">
                Sign In
              </Button>
              <Button size="sm">
                Start Free Trial
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <Badge className="mb-4" variant="outline">
              <Sparkles className="w-3 h-3 mr-1" />
              Powered by Advanced AI
            </Badge>
            
            <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-slate-900 via-blue-900 to-purple-900 bg-clip-text text-transparent">
              Turn Value Hypotheses
              <br />
              Into Realized Revenue
            </h1>
            
            <p className="text-xl text-slate-600 mb-8 max-w-3xl mx-auto">
              The first AI-powered Value Realization Operating System that transforms how B2B companies 
              create, deliver, and prove value throughout the customer lifecycle.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Button size="lg" className="text-lg px-8">
                <Play className="w-5 h-5 mr-2" />
                Watch 2-min Demo
              </Button>
              <Button size="lg" variant="outline" className="gap-2">
                <Link href="/demo">
                  Try Interactive Demo
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Link>
              </Button>
            </div>
            
            <div className="flex items-center justify-center gap-8 text-sm text-slate-500">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                No credit card required
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                14-day free trial
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                Setup in 5 minutes
              </div>
            </div>
          </motion.div>

          {/* Hero Image/Demo */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-16 relative"
          >
            <div className="relative rounded-2xl overflow-hidden shadow-2xl border bg-white">
              <div className="aspect-video bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
                {!isVideoPlaying ? (
                  <button
                    onClick={() => setIsVideoPlaying(true)}
                    className="group relative"
                  >
                    <div className="absolute inset-0 bg-blue-600 rounded-full blur-xl group-hover:blur-2xl transition-all opacity-20" />
                    <div className="relative w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                      <Play className="w-8 h-8 text-blue-600 ml-1" />
                    </div>
                  </button>
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <p className="text-slate-500">Video player would load here</p>
                  </div>
                )}
              </div>
            </div>
            
            {/* Floating badges */}
            <div className="absolute -top-4 -left-4 bg-white rounded-lg shadow-lg px-3 py-2 flex items-center gap-2">
              <Activity className="w-4 h-4 text-green-500" />
              <span className="text-sm font-medium">Live Demo</span>
            </div>
            
            <div className="absolute -bottom-4 -right-4 bg-white rounded-lg shadow-lg px-3 py-2 flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-medium">1,247 active users</span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-white border-y">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="text-center"
              >
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-blue-100 mb-3">
                  <stat.icon className="w-6 h-6 text-blue-600" />
                </div>
                <div className="text-3xl font-bold text-slate-900">{stat.value}</div>
                <div className="text-sm text-slate-500">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <Badge className="mb-4" variant="outline">
              Platform Features
            </Badge>
            <h2 className="text-4xl font-bold mb-4">Everything You Need for Value Realization</h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              A complete platform that brings together AI, automation, and analytics to transform 
              how you create and deliver value.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="h-full hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start gap-4">
                      <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${feature.color} flex items-center justify-center flex-shrink-0`}>
                        <feature.icon className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <CardTitle>{feature.title}</CardTitle>
                        <CardDescription className="mt-2">
                          {feature.description}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Capabilities Grid */}
      <section className="py-20 px-4 bg-slate-50">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <Badge className="mb-4" variant="outline">
              Platform Capabilities
            </Badge>
            <h2 className="text-4xl font-bold mb-4">Comprehensive Value Management</h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              Everything you need to create, track, and prove value at every stage
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {capabilities.map((cap, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="h-full">
                  <CardHeader>
                    <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center mb-3">
                      <cap.icon className="w-5 h-5 text-blue-600" />
                    </div>
                    <CardTitle className="text-lg">{cap.category}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {cap.items.map((item, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                          <span className="text-sm text-slate-600">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="py-20 px-4 bg-white">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <Badge className="mb-4" variant="outline">
              Use Cases
            </Badge>
            <h2 className="text-4xl font-bold mb-4">Built for Every Revenue Team</h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              Whether you're closing deals, ensuring renewals, or proving value, 
              ValueVerse accelerates your success.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            {useCases.map((useCase, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="h-full">
                  <CardHeader>
                    <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center mb-4">
                      <useCase.icon className="w-6 h-6 text-blue-600" />
                    </div>
                    <CardTitle>{useCase.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3">
                      {useCase.benefits.map((benefit, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                          <span className="text-sm text-slate-600">{benefit}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 px-4 bg-slate-50">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <Badge className="mb-4" variant="outline">
              Customer Stories
            </Badge>
            <h2 className="text-4xl font-bold mb-4">Trusted by Industry Leaders</h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              See how companies are transforming their value realization with ValueVerse
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((testimonial, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="h-full">
                  <CardContent className="pt-6">
                    <div className="flex gap-1 mb-4">
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                      ))}
                    </div>
                    <p className="text-slate-600 mb-6 italic">"{testimonial.quote}"</p>
                    <div className="border-t pt-4">
                      <p className="font-semibold text-slate-900">{testimonial.author}</p>
                      <p className="text-sm text-slate-500">{testimonial.role}</p>
                      <p className="text-sm text-slate-500">{testimonial.company}</p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Integrations */}
      <section className="py-20 px-4 bg-white">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <Badge className="mb-4" variant="outline">
              Integrations
            </Badge>
            <h2 className="text-4xl font-bold mb-4">Works With Your Tech Stack</h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              Seamlessly integrate with the tools your team already uses
            </p>
          </div>
          
          <div className="flex flex-wrap justify-center gap-8">
            {integrations.map((integration, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.05 }}
                viewport={{ once: true }}
                className="bg-slate-50 rounded-lg px-6 py-4 flex items-center gap-3 hover:shadow-md transition-shadow"
              >
                <span className="text-2xl">{integration.icon}</span>
                <span className="font-medium text-slate-700">{integration.name}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-gradient-to-r from-blue-600 to-purple-600">
        <div className="container mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl font-bold text-white mb-4">
              Ready to Transform Your Value Realization?
            </h2>
            <p className="text-xl text-blue-100 mb-8">
              Join leading B2B companies already using ValueVerse to accelerate revenue growth.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" variant="secondary" className="text-lg px-8">
                Start Free Trial
                <Rocket className="w-5 h-5 ml-2" />
              </Button>
              <Button size="lg" variant="outline" className="text-lg px-8 bg-white/10 text-white border-white/20 hover:bg-white/20">
                Schedule Demo
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
            </div>
            
            <div className="mt-12 flex items-center justify-center gap-8">
              <div className="flex items-center gap-2 text-white/80">
                <Star className="w-5 h-5 text-yellow-400" />
                <span>4.9/5 on G2</span>
              </div>
              <div className="flex items-center gap-2 text-white/80">
                <Award className="w-5 h-5 text-yellow-400" />
                <span>Leader in Value Realization</span>
              </div>
              <div className="flex items-center gap-2 text-white/80">
                <Globe className="w-5 h-5 text-yellow-400" />
                <span>500+ Companies</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 bg-slate-900">
        <div className="container mx-auto max-w-6xl">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <span className="text-lg font-bold text-white">ValueVerse</span>
              </div>
              <p className="text-sm text-slate-400">
                The AI-powered Value Realization Operating System for B2B companies.
              </p>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold text-white mb-4">Product</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><Link href="/demo" className="hover:text-white transition-colors">Demo</Link></li>
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Integrations</a></li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold text-white mb-4">Company</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><a href="#" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold text-white mb-4">Legal</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Security</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Compliance</a></li>
              </ul>
            </div>
          </div>
          
          <div className="mt-12 pt-8 border-t border-slate-800 text-center text-sm text-slate-400">
            © 2024 ValueVerse. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
