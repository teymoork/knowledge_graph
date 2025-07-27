from enum import Enum

class NodeLabel(str, Enum):
    """
    Defines the labels for the nodes (entities) in our knowledge graph.
    """
    PERSON = "شخص"
    LOCATION = "مکان"
    EVENT = "رویداد"
    ORGANIZATION = "سازمان"
    DATE = "تاریخ"
    CONCEPT = "مفهوم"
    LEGAL_CASE = "پرونده_قضایی"
    GOVERNMENT_ROLE = "منصب_دولتی"
    VIOLENT_ACT = "اقدام_خشونت‌آمیز" # Changed from SEXUAL_ASSAULT

class RelationshipLabel(str, Enum):
    """
    Defines the labels for the relationships (edges) between nodes.
    """
    # --- Factual & Event Relationships ---
    BORN_IN = "متولد_شد_در"
    DIED_IN = "درگذشت_در"
    PARTICIPATED_IN = "شرکت_کرد_در"
    OCCURRED_IN = "رخ_داد_در"
    STARTED_ON = "شروع_شد_در"
    ENDED_ON = "پایان_یافت_در"
    OCCURRED_ON = "رخ_داد_در_تاریخ"
    
    # --- Family Relationships ---
    FATHER_OF = "پدر_بود"
    MOTHER_OF = "مادر_بود"
    CHILD_OF = "فرزند_بود"
    SPOUSE_OF = "همسر_بود"
    SIBLING_OF = "خواهر_برادر_بود"

    # --- Interpersonal & Violent Events ---
    LIED_TO = "دروغ_گفت_به"
    BETRAYED = "خیانت_کرد_به"
    INFORMED_ON = "خبرچینی_کرد_علیه"
    FOUGHT_AGAINST = "جنگید_علیه"
    PRETENDED_TO_BE = "تظاهر_کرد_به"
    SPOKE_ABOUT = "صحبت_کرد_درباره"
    PERPETRATOR_OF = "مرتکب_شد" # Connects Person to VIOLENT_ACT
    VICTIM_OF = "قربانی_بود"   # Connects Person to VIOLENT_ACT

    # --- Governmental Relationships ---
    MEMBER_OF = "عضو_بود_در"
    HEAD_OF = "رئیس_بود"
    HELD_ROLE = "منصب_داشت"
    AFFILIATED_WITH = "وابسته_بود_به"
    SUCCEEDED = "جانشین_شد"

    # --- Legal Court Relationships ---
    PROSECUTOR_IN = "دادستان_بود_در"
    DEFENDANT_IN = "متهم_بود_در"
    JUDGE_IN = "قاضی_بود_در"
    WITNESS_IN = "شاهد_بود_در"
    LAWYER_FOR = "وکیل_بود_برای"
    FILED_CASE = "پرونده_تشکیل_داد"
    CONVICTED_OF = "محکوم_شد_به"
    ACQUITTED_IN = "تبرئه_شد_در"

    # --- AI Suggested Relationships ---
    INITIATED_DESTRUCTION_OF = "مبتکر_نابودی"
    AIDED_DESTRUCTION_OF = "همراهی_در_نابودی"
    IMPOSED = "تحمیل_کرد"
    HOSTILE_TOWARDS = "ضدیت_داشت_با"
    ALLIED_WITH = "همراهی_کرد_با"
    FABRICATED_CASE_AGAINST = "پرونده‌سازی_کرد_برای"
    ESTABLISHED = "راه‌اندازی_کرد"
    THREATENED = "تهدید_کرد"
    PARTICIPATED_IN_MASSACRE = "مشارکت_در_کشتار"
    BYPASSED = "دور_زد"
    DISMISSED_DUE_TO = "برکنار_شد_به_خاطر"
    SUPPORTED = "حمایت_کرد_از"
    RESPONSIBLE_FOR = "مسئول_بود_در"
    PAVED_WAY_FOR = "زمینه‌ساز_بود_برای"
    LED = "رهبری_کرد"
    ACCUSED = "متهم_کرد"
    LED_TO = "منجر_شد_به"
    ACQUAINTED_WITH = "آشنایی_داشت_با"
    COLLABORATED_WITH = "همکاری_کرد_با"
    TRAINED_BY = "آموزش_دید_از"
    APPOINTED = "منصوب_کرد"
    REPRESENTED = "نماینده_بود_از"
    OPPOSED = "مخالفت_کرد_با"
    DEFENDED = "دفاع_کرد_از"
    COVERED_UP = "سرپوش_گذاشت_بر"

# A list of all possible relationship types for the LLM.
POSSIBLE_RELATIONSHIPS = [
    # Factual
    (NodeLabel.PERSON, RelationshipLabel.BORN_IN, NodeLabel.LOCATION),
    (NodeLabel.PERSON, RelationshipLabel.DIED_IN, NodeLabel.LOCATION),
    (NodeLabel.PERSON, RelationshipLabel.PARTICIPATED_IN, NodeLabel.EVENT),
    (NodeLabel.EVENT, RelationshipLabel.OCCURRED_IN, NodeLabel.LOCATION),
    
    # Time-based
    (NodeLabel.EVENT, RelationshipLabel.STARTED_ON, NodeLabel.DATE),
    (NodeLabel.EVENT, RelationshipLabel.ENDED_ON, NodeLabel.DATE),
    (NodeLabel.EVENT, RelationshipLabel.OCCURRED_ON, NodeLabel.DATE),
    (NodeLabel.LEGAL_CASE, RelationshipLabel.STARTED_ON, NodeLabel.DATE),
    (NodeLabel.LEGAL_CASE, RelationshipLabel.ENDED_ON, NodeLabel.DATE),
    (NodeLabel.VIOLENT_ACT, RelationshipLabel.OCCURRED_ON, NodeLabel.DATE), # Changed

    # Family
    (NodeLabel.PERSON, RelationshipLabel.FATHER_OF, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.MOTHER_OF, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.CHILD_OF, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.SPOUSE_OF, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.SIBLING_OF, NodeLabel.PERSON),

    # Interpersonal & Violent
    (NodeLabel.PERSON, RelationshipLabel.LIED_TO, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.BETRAYED, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.INFORMED_ON, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.FOUGHT_AGAINST, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.SPOKE_ABOUT, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.PERPETRATOR_OF, NodeLabel.VIOLENT_ACT), # Changed
    (NodeLabel.PERSON, RelationshipLabel.VICTIM_OF, NodeLabel.VIOLENT_ACT),       # Changed
    (NodeLabel.VIOLENT_ACT, RelationshipLabel.OCCURRED_IN, NodeLabel.LOCATION), # Changed

    # Governmental
    (NodeLabel.PERSON, RelationshipLabel.MEMBER_OF, NodeLabel.ORGANIZATION),
    (NodeLabel.PERSON, RelationshipLabel.HEAD_OF, NodeLabel.ORGANIZATION),
    (NodeLabel.PERSON, RelationshipLabel.HELD_ROLE, NodeLabel.GOVERNMENT_ROLE),
    (NodeLabel.ORGANIZATION, RelationshipLabel.AFFILIATED_WITH, NodeLabel.ORGANIZATION),
    (NodeLabel.PERSON, RelationshipLabel.SUCCEEDED, NodeLabel.PERSON),

    # Legal
    (NodeLabel.PERSON, RelationshipLabel.PROSECUTOR_IN, NodeLabel.LEGAL_CASE),
    (NodeLabel.PERSON, RelationshipLabel.DEFENDANT_IN, NodeLabel.LEGAL_CASE),
    (NodeLabel.PERSON, RelationshipLabel.JUDGE_IN, NodeLabel.LEGAL_CASE),
    (NodeLabel.PERSON, RelationshipLabel.WITNESS_IN, NodeLabel.LEGAL_CASE),
    (NodeLabel.PERSON, RelationshipLabel.LAWYER_FOR, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.FILED_CASE, NodeLabel.LEGAL_CASE),
    (NodeLabel.ORGANIZATION, RelationshipLabel.FILED_CASE, NodeLabel.LEGAL_CASE),
    (NodeLabel.PERSON, RelationshipLabel.CONVICTED_OF, NodeLabel.CONCEPT),
    (NodeLabel.PERSON, RelationshipLabel.ACQUITTED_IN, NodeLabel.LEGAL_CASE),

    # --- AI Suggested Relationships ---
    (NodeLabel.PERSON, RelationshipLabel.INITIATED_DESTRUCTION_OF, NodeLabel.ORGANIZATION),
    (NodeLabel.PERSON, RelationshipLabel.AIDED_DESTRUCTION_OF, NodeLabel.ORGANIZATION),
    (NodeLabel.PERSON, RelationshipLabel.IMPOSED, NodeLabel.CONCEPT),
    (NodeLabel.PERSON, RelationshipLabel.HOSTILE_TOWARDS, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.HOSTILE_TOWARDS, NodeLabel.ORGANIZATION),
    (NodeLabel.PERSON, RelationshipLabel.ALLIED_WITH, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.ALLIED_WITH, NodeLabel.ORGANIZATION),
    (NodeLabel.PERSON, RelationshipLabel.FABRICATED_CASE_AGAINST, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.ESTABLISHED, NodeLabel.ORGANIZATION),
    (NodeLabel.PERSON, RelationshipLabel.THREATENED, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.PARTICIPATED_IN_MASSACRE, NodeLabel.EVENT),
    (NodeLabel.PERSON, RelationshipLabel.BYPASSED, NodeLabel.ORGANIZATION),
    (NodeLabel.PERSON, RelationshipLabel.DISMISSED_DUE_TO, NodeLabel.CONCEPT),
    (NodeLabel.PERSON, RelationshipLabel.SUPPORTED, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.SUPPORTED, NodeLabel.CONCEPT),
    (NodeLabel.PERSON, RelationshipLabel.RESPONSIBLE_FOR, NodeLabel.EVENT),
    (NodeLabel.EVENT, RelationshipLabel.PAVED_WAY_FOR, NodeLabel.EVENT),
    (NodeLabel.PERSON, RelationshipLabel.LED, NodeLabel.ORGANIZATION),
    (NodeLabel.PERSON, RelationshipLabel.LED, NodeLabel.EVENT),
    (NodeLabel.PERSON, RelationshipLabel.ACCUSED, NodeLabel.PERSON),
    (NodeLabel.ORGANIZATION, RelationshipLabel.ACCUSED, NodeLabel.PERSON),
    (NodeLabel.EVENT, RelationshipLabel.LED_TO, NodeLabel.EVENT),
    (NodeLabel.PERSON, RelationshipLabel.ACQUAINTED_WITH, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.COLLABORATED_WITH, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.COLLABORATED_WITH, NodeLabel.ORGANIZATION),
    (NodeLabel.PERSON, RelationshipLabel.TRAINED_BY, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.APPOINTED, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.REPRESENTED, NodeLabel.LOCATION),
    (NodeLabel.PERSON, RelationshipLabel.OPPOSED, NodeLabel.CONCEPT),
    (NodeLabel.PERSON, RelationshipLabel.OPPOSED, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.DEFENDED, NodeLabel.PERSON),
    (NodeLabel.PERSON, RelationshipLabel.DEFENDED, NodeLabel.CONCEPT),
    (NodeLabel.PERSON, RelationshipLabel.COVERED_UP, NodeLabel.EVENT),
    (NodeLabel.ORGANIZATION, RelationshipLabel.COVERED_UP, NodeLabel.EVENT),
]