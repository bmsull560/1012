# AI UI Generation Agents

This directory contains the 5 specialized AI agents that work together to generate production-ready React/TypeScript components from design documentation.

## Agent Overview

```
Design Analyzer (Claude-3-Opus)
    ↓ component_spec.json
Architecture Planner (Claude-3-Sonnet)
    ↓ architecture_plan.json  
Component Generator (GPT-4)
    ↓ generated_code/
Integration Engineer (Claude-3-Sonnet)
    ↓ integrated_code/
Quality Reviewer (GPT-4)
    ↓ quality_report.json + PR
```

## Installation

```bash
pip install -r requirements.txt
```

## Required Environment Variables

```bash
export ANTHROPIC_API_KEY="your_anthropic_key"
export OPENAI_API_KEY="your_openai_key"
export GITHUB_TOKEN="your_github_token"  # For parse_request.py
```

## Individual Agent Usage

### 1. Parse Request
```bash
export ISSUE_NUMBER=123
python parse_request.py
# Output: output/request.json
```

### 2. Design Analyzer
```bash
export COMPONENT_NAME="UnifiedWorkspace"
python design_analyzer.py
# Output: output/component_spec.json
```

### 3. Architecture Planner
```bash
python architecture_planner.py
# Input: output/component_spec.json
# Output: output/architecture_plan.json
```

### 4. Component Generator
```bash
python component_generator.py
# Input: output/architecture_plan.json
# Output: output/generated_code/
```

### 5. Integration Engineer
```bash
python integration_engineer.py
# Input: output/generated_code/
# Output: output/integrated_code/
```

### 6. Quality Reviewer
```bash
python quality_reviewer.py
# Input: output/generated_code/ + output/integrated_code/
# Output: output/quality_report.json
```

## Full Pipeline

```bash
# Set environment variables
export COMPONENT_NAME="MyComponent"
export ANTHROPIC_API_KEY="..."
export OPENAI_API_KEY="..."

# Run all agents in sequence
python design_analyzer.py && \
python architecture_planner.py && \
python component_generator.py && \
python integration_engineer.py && \
python quality_reviewer.py

# View results
ls -la output/
```

## File Structure

```
scripts/agents/
├── api_clients.py              # AI API wrappers with rate limiting
├── prompt_templates.py         # Engineered prompts for each agent
├── code_validators.py          # Automated code quality checks
├── parse_request.py            # GitHub issue parser
├── design_analyzer.py          # Agent 1: Design analysis
├── architecture_planner.py     # Agent 2: Architecture planning
├── component_generator.py      # Agent 3: Code generation
├── integration_engineer.py     # Agent 4: API integration
├── quality_reviewer.py         # Agent 5: Quality review
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Output Structure

```
output/
├── request.json                # Parsed component request
├── component_spec.json         # Design specification
├── architecture_plan.json      # Architecture plan
├── generation_metadata.json    # Code generation metadata
├── integration_metadata.json   # Integration metadata
├── quality_report.json         # Quality review report
├── generated_code/             # Generated component files
│   └── components/
│       └── ComponentName/
│           ├── index.tsx
│           ├── types.ts
│           └── ...
└── integrated_code/            # Integrated component files
    └── ...
```

## Agent Details

### Agent 1: Design Analyzer (Claude-3-Opus)

**Purpose**: Parse 2,400+ lines of design docs and extract component specifications

**Model**: Claude-3-Opus (100K context window)  
**Input**: All `/docs/*.md` files + component name  
**Output**: `component_spec.json` with structured requirements  
**Cost**: ~$0.50-1.00 per run  
**Time**: ~2-3 minutes  

### Agent 2: Architecture Planner (Claude-3-Sonnet)

**Purpose**: Design file structure, component hierarchy, and data flow

**Model**: Claude-3-Sonnet (balanced performance/cost)  
**Input**: `component_spec.json` + existing codebase structure  
**Output**: `architecture_plan.json` with file paths and dependencies  
**Cost**: ~$0.30-0.50 per run  
**Time**: ~3-4 minutes  

### Agent 3: Component Generator (GPT-4)

**Purpose**: Generate production-ready React/TypeScript code

**Model**: GPT-4-Turbo (best code quality)  
**Input**: `architecture_plan.json` + design tokens + patterns  
**Output**: Complete component files in `generated_code/`  
**Cost**: ~$2.00-4.00 per run  
**Time**: ~8-12 minutes  

### Agent 4: Integration Engineer (Claude-3-Sonnet)

**Purpose**: Add API integrations and real-time WebSocket features

**Model**: Claude-3-Sonnet  
**Input**: Generated code + API documentation  
**Output**: Enhanced code in `integrated_code/`  
**Cost**: ~$0.40-0.60 per run  
**Time**: ~4-5 minutes  

### Agent 5: Quality Reviewer (GPT-4 + Validators)

**Purpose**: Review code quality, security, accessibility

**Components**:
- Automated validators (TypeScript, React, a11y, security)
- AI review (GPT-4)

**Input**: All generated and integrated code  
**Output**: `quality_report.json` with scores and recommendations  
**Cost**: ~$0.80-1.20 per run  
**Time**: ~4-5 minutes  

## Total Pipeline Metrics

- **Total Time**: 25-35 minutes
- **Total Cost**: $4-8 per component
- **Quality Score**: Target >8/10
- **Success Rate**: >90% (with fallbacks)

## Error Handling

Each agent includes:
- Exponential backoff for rate limits
- Fallback implementations
- Detailed error logging
- Graceful degradation

If any agent fails:
1. Check API keys are set
2. Review error logs
3. Check internet connectivity
4. Verify input files exist
5. Try running agent individually

## Testing

Test individual agents:

```bash
# Test API clients
python api_clients.py

# Test code validators
python code_validators.py

# Test with sample component
export COMPONENT_NAME="Button"
python design_analyzer.py
# Check output/component_spec.json
```

## Cost Optimization

- Use Claude for analysis (cheaper, large context)
- Use GPT-4 only for code generation
- Cache intermediate results
- Reuse specifications when possible

## Quality Standards

Generated code must meet:
- ✅ TypeScript strict mode (no `any` types)
- ✅ React best practices (hooks, memoization)
- ✅ WCAG 2.1 AA accessibility
- ✅ No security vulnerabilities
- ✅ Proper error handling
- ✅ Loading states
- ✅ Mobile responsive

## Troubleshooting

### "API key not found"
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

### "Rate limit exceeded"
Wait 60 seconds and retry. The agents include automatic retry logic.

### "No files generated"
Check that input files exist:
```bash
ls output/component_spec.json
ls output/architecture_plan.json
```

### "Invalid JSON response"
This usually means the AI response wasn't properly formatted. The agents include fallback implementations.

## Development

### Adding a New Agent

1. Create `new_agent.py` with same structure
2. Add to `prompt_templates.py`
3. Update workflow in `.github/workflows/ai-ui-generator.yml`
4. Test individually before integration

### Improving Prompts

Edit `prompt_templates.py` and test with:
```bash
python design_analyzer.py
# Review output quality
# Iterate on prompt
```

## Support

For issues or questions:
1. Check agent logs in console output
2. Review output JSON files
3. Test API connectivity
4. Verify input format

---

**Status**: ✅ Production Ready  
**Version**: 1.0  
**Last Updated**: 2025-10-12
