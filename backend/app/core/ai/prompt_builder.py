"""
Prompt builder for AI dimensional modeling requests.
Builds deterministic, structured prompts from user intent and schema metadata.

DO NOT forward raw chat history. Build structured payloads instead.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class UserIntent:
    """Structured user analytical intent."""
    business_domain: str
    analytical_goal: str  # reporting, bi, ad-hoc
    time_grain: str  # daily, weekly, monthly
    key_metrics: list[str]
    tables_of_interest: list[dict]  # [{name, is_likely_fact, is_likely_dimension, description}]
    exclusions: list[str]


@dataclass
class PromptPayload:
    """Complete payload for AI request."""
    raw_dbml: str
    annotated_dbml: str
    user_intent: UserIntent
    statistics: Optional[str] = None  # Formatted statistics if enabled
    
    def to_prompt(self) -> str:
        """Convert payload to a structured prompt string."""
        return PromptBuilder.build_prompt(self)


class PromptBuilder:
    """
    Builds structured prompts for AI dimensional modeling.
    
    The prompt is deterministic - same inputs produce same prompt.
    No chat history or conversational context is included.
    """
    
    SYSTEM_PROMPT = """You are an expert data warehouse architect specializing in dimensional modeling.
Your task is to analyze a database schema and propose a dimensional model (star or snowflake schema).

You must:
1. Identify fact tables and their grain (the level of detail each row represents)
2. Identify dimension tables and their attributes
3. Propose measures for fact tables
4. Suggest slowly changing dimension (SCD) strategies where appropriate
5. Justify each decision with clear reasoning
6. List assumptions and potential risks

Output your response in the following structured format:

## Dimensional Model Explanation
[Explain the overall model design]

## Fact Tables
For each fact table:
- Table name
- Grain definition
- Measures (with aggregation type)
- Foreign keys to dimensions

## Dimension Tables
For each dimension:
- Table name
- Key attributes
- SCD type recommendation (Type 1, 2, or 3)
- Hierarchies if applicable

## Assumptions and Uncertainties
[List any assumptions made and areas of uncertainty]

## DBML Output
```dbml
[Generate DBML for the proposed dimensional model]
```
"""
    
    @classmethod
    def build_prompt(cls, payload: PromptPayload) -> str:
        """Build the complete prompt from a payload."""
        sections = []
        
        # Section 1: User Intent
        intent = payload.user_intent
        sections.append("# ANALYTICAL CONTEXT")
        sections.append(f"Business Domain: {intent.business_domain}")
        sections.append(f"Analytical Goal: {intent.analytical_goal}")
        sections.append(f"Preferred Time Grain: {intent.time_grain}")
        sections.append(f"Key Metrics: {', '.join(intent.key_metrics)}")
        sections.append("")
        
        # Section 2: Tables of Interest
        sections.append("# TABLES OF INTEREST")
        for table in intent.tables_of_interest:
            hints = []
            if table.get("is_likely_fact"):
                hints.append("LIKELY FACT")
            if table.get("is_likely_dimension"):
                hints.append("LIKELY DIMENSION")
            hint_str = f" [{', '.join(hints)}]" if hints else ""
            desc = f" - {table.get('description')}" if table.get("description") else ""
            sections.append(f"- {table['name']}{hint_str}{desc}")
        sections.append("")
        
        # Section 3: Exclusions
        if intent.exclusions:
            sections.append("# EXCLUDED TABLES/SCHEMAS")
            sections.append("Do NOT include these in the dimensional model:")
            for exc in intent.exclusions:
                sections.append(f"- {exc}")
            sections.append("")
        
        # Section 4: Raw Schema (DBML)
        sections.append("# SOURCE SCHEMA (DBML)")
        sections.append("```dbml")
        sections.append(payload.raw_dbml)
        sections.append("```")
        sections.append("")
        
        # Section 5: Annotated Schema
        sections.append("# ANNOTATED SCHEMA WITH HINTS")
        sections.append("```dbml")
        sections.append(payload.annotated_dbml)
        sections.append("```")
        sections.append("")
        
        # Section 6: Statistics (if available)
        if payload.statistics:
            sections.append("# OBSERVED STATISTICS")
            sections.append("Note: These are observed values, not guaranteed. They may be stale.")
            sections.append(payload.statistics)
            sections.append("")
        
        # Section 7: Instructions
        sections.append("# INSTRUCTIONS")
        sections.append("Based on the above context and schema, propose a dimensional model.")
        sections.append("Follow the output format specified in the system prompt.")
        
        return "\n".join(sections)
    
    @classmethod
    def get_system_prompt(cls) -> str:
        """Return the system prompt for AI."""
        return cls.SYSTEM_PROMPT

