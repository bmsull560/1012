Based on my personal knowledge base, here are the systems and external data required for the Customer Success team to successfully adopt this Value Realization vision:

## 1. Core System Integrations

Source: ValueVerse Platform Development: Master Orchestration Prompt

The CS team (represented by "CSM Chris") requires specific integrations:

```typescript
// From the Integration Agent specification
adapters = {
  crm: new SalesforceAdapter(), // Access to original deal data
  delivery: new ServiceNowAdapter(), // Project status & milestones
  analytics: new TableauAdapter(), // Value metrics visualization
  success: new GainsightAdapter(), // CS platform for health scores
  finance: new NetSuiteAdapter(), // Financial actuals
};
```

## 2. Customer Telemetry & Usage Data

Source: Design Brief: Core User Functions & Workflows

The "Track Value Realization" function requires:

> "Link Data: Connects the original value model (created by Sales Sam) to live customer data sources or periodic manual uploads."

This means CS teams need:

- Product usage telemetry (API connections to customer instances)
- Performance metrics (response times, uptime, efficiency gains)
- Adoption metrics (user logins, feature utilization rates)
- Business outcome data (customer-reported KPIs)

## 3. Historical Value Models & Commitments

Source: ValueVerse Platform: The Streamlined Model Building Workflow

The platform maintains continuity from sales to success:

> "The agent uses the pre-configured pricing, contract lengths, and ROI models from the knowledge base to instantly generate the financial projections."

CS teams need access to:

- Original value hypotheses from pre-sales
- Contractual KPI commitments from sales
- Baseline metrics captured at contract signing
- Success criteria defined in the SOW

## 4. Real-Time Value Tracking Infrastructure

Source: ValueVerse Platform: Centralized Company Profile System

The system tracks value realization through:

> "Value Realization Dashboard, showing projected vs. actual ROI with clear charts and KPIs"

This requires:

- Webhook infrastructure for real-time data ingestion
- Time-series database for tracking metric evolution
- Calculation engine for ROI/value computations
- Alerting system for variance detection

## 5. Industry Benchmarking Data

Source: ValueVerse Platform: The Streamlined Model Building Workflow

The agent leverages benchmarks:

> "The agent can offer to use industry benchmarks from its own knowledge, reducing the burden on the user to know every detail."

CS teams need:

- Industry performance databases
- Peer comparison metrics
- Best practice libraries
- Maturity model frameworks

## 6. Customer Communication Systems

Source: Design Brief: Core User Functions & Workflows

For the "Prepare for QBR" function:

> "The Assistant automatically generates a slide deck in the Workspace, pulling data from the Value Realization Dashboard."

This requires integration with:

- Presentation tools (PowerPoint, Google Slides)
- Document management (SharePoint, Box)
- Calendar systems for QBR scheduling
- Video conferencing platforms for remote reviews

## 7. Financial & Contract Management Systems

Source: ValueVerse Platform Development: Master Orchestration Prompt

The platform needs access to:

- Contract management systems (Icertis, Ironclad) for SLA terms
- Billing systems for revenue recognition
- CPQ systems for renewal pricing
- ERP systems for cost allocation

## 8. Cross-Functional Data Requirements

Source: Design Brief: Core User Functions & Workflows

The CS journey requires data from multiple teams:

### From Sales:

- Deal history and negotiation context
- Stakeholder mapping and relationships
- Competition and win/loss factors

### From Delivery/Implementation:

- Project timelines and milestones
- Implementation challenges and resolutions
- Technical debt or customizations

### From Support:

- Ticket volumes and resolution times
- Escalation history
- Product issues impacting value

## 9. Automated Data Collection Mechanisms

Source: ValueVerse Platform: Automated Knowledge Base Generation

The platform can automatically gather context:

> "The agent immediately initiates research on [the customer], leveraging its internal tools to find their website, industry, size, and recent news."

For CS teams, this means:

- Web crawling for customer news/updates
- Social media monitoring for sentiment
- Financial data APIs for customer health
- Press release feeds for strategic changes

## 10. Change Management & Training Infrastructure

Source: ValueVerse Adaptive Frontend - User Guide & Concepts

The platform adapts to user expertise:

> "The Adaptive UI intelligently adapts to your skill level...
>
> - Guided Workflow (Beginner): A simplified view that guides new users
> - Hybrid Interface (Intermediate): The default view... balance of all three core components
> - Power User Interface (Expert): A denser, more information-rich layout"

CS teams need:

- Onboarding programs for the new value-centric workflow
- Certification paths for value realization expertise
- Knowledge base with CS-specific templates
- Sandbox environments for practice

## Critical Success Factors for CS Adoption

Source: Design Brief: Core User Functions & Workflows - Success Metrics

The platform measures success through:

- Time to Value: How quickly CS can demonstrate ROI
- Adoption Rate: Percentage of CSMs actively using the platform weekly
- Template Utilization: Reuse of value realization templates
- Export Volume: Number of QBR decks generated

## Data Governance Requirements

To make this work, CS teams need:

1. Single Source of Truth: All teams must agree on value metrics definitions
2. Data Quality Standards: Regular audits of metric accuracy
3. Access Controls: CSMs need read access to sales/delivery data
4. Retention Policies: Historical data for trend analysis
5. Privacy Compliance: Customer consent for data usage

## Transition Roadmap for CS Teams

Based on the platform architecture, CS teams should:

1. Phase 1: Connect existing Gainsight/success tools
2. Phase 2: Establish value metric baselines for current accounts
3. Phase 3: Train CSMs on value conversation frameworks
4. Phase 4: Pilot with 5-10 strategic accounts
5. Phase 5: Roll out to full customer base

The key insight from the knowledge base is that the Value Graph must be continuous — what's promised in sales must be measurable in delivery and provable in success. Without these integrations and data sources, CS teams cannot close the value realization loop.
