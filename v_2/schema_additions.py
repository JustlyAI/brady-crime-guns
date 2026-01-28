"""
Schema Additions for Crime Gun DB Integration

CLAUDE CODE INSTRUCTIONS:
=========================

These fields need to be added to the unified schema in brady_unified_etl.py.
Merge these into the existing UNIFIED_SCHEMA dict.

After adding, update:
1. The DataFrame column creation in the main ETL
2. The Excel output column ordering
3. Any dashboard queries that filter by source
"""

# New fields to add to unified schema
CRIME_GUN_DB_SCHEMA_ADDITIONS = {
    # Case/Court fields (new)
    "case_reference": {
        "type": "string",
        "description": "Full case reference (e.g., 'U.S. v. Smith, E.D. Pa., No. 23-cr-17')",
        "source": "Column N",
        "nullable": True,
    },
    "case_court": {
        "type": "string",
        "description": "Parsed court code (e.g., 'E.D. Pa.')",
        "source": "Extracted from case_reference",
        "nullable": True,
    },
    "case_court_state": {
        "type": "string",
        "description": "State derived from court code",
        "source": "Extracted from case_court",
        "nullable": True,
    },
    "case_subject": {
        "type": "string",
        "description": "Case subject line with trafficking indicators",
        "source": "Column P",
        "nullable": True,
    },

    # Trafficking fields (new)
    "trafficking_source_state": {
        "type": "string",
        "description": "Source state in trafficking flow (from 'XX-->YY' pattern)",
        "source": "Extracted from case_subject",
        "nullable": True,
    },
    "trafficking_dest_state": {
        "type": "string",
        "description": "Destination state in trafficking flow",
        "source": "Extracted from case_subject",
        "nullable": True,
    },
    "is_domestic_violence": {
        "type": "boolean",
        "description": "DV* indicator in case subject",
        "source": "Extracted from case_subject",
        "nullable": True,
    },
    "is_swb_trafficking": {
        "type": "boolean",
        "description": "Southwest border (Mexico) trafficking indicator",
        "source": "Extracted from case_subject",
        "nullable": True,
    },

    # Narrative fields (new)
    "facts_narrative": {
        "type": "text",
        "description": "Detailed case facts narrative",
        "source": "Column U",
        "nullable": True,
    },
    "recovery_info": {
        "type": "text",
        "description": "Information on recoveries including associated crimes",
        "source": "Column S",
        "nullable": True,
    },

    # FFL status fields (may overlap with existing - merge logic needed)
    "is_top_trace_ffl": {
        "type": "boolean",
        "description": "ATF top trace FFL designation",
        "source": "Column I",
        "nullable": True,
    },
    "is_revoked": {
        "type": "boolean",
        "description": "FFL license revoked",
        "source": "Column J",
        "nullable": True,
    },
    "is_charged_or_sued": {
        "type": "boolean",
        "description": "FFL has been charged or sued",
        "source": "Column K",
        "nullable": True,
    },

    # Jurisdiction confidence tracking (new)
    "jurisdiction_method": {
        "type": "string",
        "description": "Method used to determine jurisdiction",
        "enum": ["EXPLICIT_RECOVERY", "CASE_COURT", "TRAFFICKING_FLOW", "NLP", "IMPLICIT", "UNKNOWN"],
        "source": "Computed during ETL",
        "nullable": False,
        "default": "UNKNOWN",
    },
    "jurisdiction_confidence": {
        "type": "string",
        "description": "Confidence level of jurisdiction determination",
        "enum": ["HIGH", "MEDIUM", "LOW", "NONE"],
        "source": "Computed during ETL",
        "nullable": False,
        "default": "NONE",
    },

    # Source traceability (new)
    "source_sheet": {
        "type": "string",
        "description": "Original sheet name within source file",
        "source": "ETL metadata",
        "nullable": True,
    },
}

# Column ordering for Excel output (append these after existing columns)
CRIME_GUN_DB_OUTPUT_COLUMNS = [
    # Group: Case Information
    "case_reference",
    "case_court",
    "case_court_state",
    "case_subject",

    # Group: Trafficking
    "trafficking_source_state",
    "trafficking_dest_state",
    "is_domestic_violence",
    "is_swb_trafficking",

    # Group: Narratives
    "facts_narrative",
    "recovery_info",

    # Group: FFL Status
    "is_top_trace_ffl",
    "is_revoked",
    "is_charged_or_sued",

    # Group: Metadata
    "jurisdiction_method",
    "jurisdiction_confidence",
    "source_sheet",
]


def get_default_values() -> dict:
    """
    Return default values for new schema fields.

    CLAUDE CODE: Use this when creating empty rows or handling missing data.
    """
    return {
        "case_reference": None,
        "case_court": None,
        "case_court_state": None,
        "case_subject": None,
        "trafficking_source_state": None,
        "trafficking_dest_state": None,
        "is_domestic_violence": None,
        "is_swb_trafficking": None,
        "facts_narrative": None,
        "recovery_info": None,
        "is_top_trace_ffl": None,
        "is_revoked": None,
        "is_charged_or_sued": None,
        "jurisdiction_method": "UNKNOWN",
        "jurisdiction_confidence": "NONE",
        "source_sheet": None,
    }
