"""
Security and Guardrail Component for Real Estate AI Assistant

This module implements input/output filtering and safety measures to ensure
secure and appropriate interactions between users and the LLM-powered agents.

Architecture:
┌─────────────┐
│ User Input  │
└──────┬──────┘
       │
┌──────▼───────┐      ┌─────────────────┐
│ Input Filter │─────►│ Alert Protocol  │
└──────┬───────┘      └─────────────────┘
       │
(safe request)
       │
┌──────▼───────┐
│     LLM      │  <-- streams tokens
└──────┬───────┘
       │
┌──────▼───────┐
│ Output Filter│─────► Return safe response
└──────────────┘
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for different types of content"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FilterAction(Enum):
    """Actions to take based on risk assessment"""
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    ESCALATE = "escalate"


@dataclass
class SecurityCheck:
    """Result of a security check"""
    risk_level: RiskLevel
    action: FilterAction
    reason: str
    confidence: float
    detected_patterns: List[str]


class InputGuardrail:
    """
    Filters and validates user inputs before they reach the LLM
    """
    
    def __init__(self):
        # Malicious patterns for real estate context
        self.harmful_patterns = {
            RiskLevel.CRITICAL: [
                r'(?i)(hack|exploit|bypass|inject|sql|script|xss)',
                r'(?i)(password|token|api[_\s]?key|secret)',
                r'(?i)(delete|drop|truncate|alter)\s+(table|database)',
                r'(?i)(exec|execute|eval|system|shell|cmd)',
            ],
            RiskLevel.HIGH: [
                r'(?i)(fraud|scam|money\s+laundering|illegal)',
                r'(?i)(discriminat\w+|racist|sexist|harassment)',
                r'(?i)(personal\s+information|social\s+security|credit\s+card)',
                r'(?i)(fake|forged|counterfeit)\s+(document|license|permit)',
            ],
            RiskLevel.MEDIUM: [
                r'(?i)(off\s*the\s*books|under\s*the\s*table|cash\s*only)',
                r'(?i)(avoid|evade)\s+(tax|regulation|law)',
                r'(?i)(insider\s+information|market\s+manipulation)',
                r'(?i)(brib\w+|kickback|payoff)',
            ],
            RiskLevel.LOW: [
                r'(?i)(urgent|emergency|immediate|asap)\s*.{0,20}(respond|reply|answer)',
                r'(?i)repeatedly\s+.{0,10}(ask|request|demand)',
            ]
        }
        
        # Inappropriate requests for real estate context
        self.inappropriate_patterns = [
            r'(?i)(illegal|unlawful|criminal)\s+(activity|practice|scheme)',
            r'(?i)(housing|rental)\s+(discrimination|bias)',
            r'(?i)(personal|private)\s+.{0,10}(information|data|details)',
            r'(?i)(bypass|circumvent|avoid)\s+(screening|background\s+check)',
        ]
        
        # Spam and abuse patterns
        self.spam_patterns = [
            r'(.)\1{10,}',  # Repeated characters
            r'(?i)(visit|click|buy|sell)\s+.{0,20}(now|today|here)',
            r'(?i)(earn|make)\s+\$?\d+.{0,20}(quickly|fast|easy)',
            r'(?i)(limited\s+time|act\s+now|don\'t\s+miss)',
        ]

    async def check_input(self, user_input: str, user_id: Optional[str] = None) -> SecurityCheck:
        """
        Perform comprehensive security check on user input
        
        Args:
            user_input: The user's message/query
            user_id: Optional user identifier for logging
            
        Returns:
            SecurityCheck object with risk assessment
        """
        if not user_input or not user_input.strip():
            return SecurityCheck(
                risk_level=RiskLevel.LOW,
                action=FilterAction.WARN,
                reason="Empty or whitespace-only input",
                confidence=1.0,
                detected_patterns=[]
            )
        
        # Clean input for analysis
        cleaned_input = user_input.strip().lower()
        detected_patterns = []
        max_risk = RiskLevel.SAFE
        reasons = []
        
        # Check for harmful patterns
        for risk_level, patterns in self.harmful_patterns.items():
            for pattern in patterns:
                if re.search(pattern, cleaned_input):
                    detected_patterns.append(pattern)
                    if self._is_higher_risk(risk_level, max_risk):
                        max_risk = risk_level
                        reasons.append(f"Detected {risk_level.value} pattern: {pattern}")
        
        # Check for inappropriate content
        for pattern in self.inappropriate_patterns:
            if re.search(pattern, cleaned_input):
                detected_patterns.append(pattern)
                if self._is_higher_risk(RiskLevel.HIGH, max_risk):
                    max_risk = RiskLevel.HIGH
                    reasons.append(f"Inappropriate content detected: {pattern}")
        
        # Check for spam
        for pattern in self.spam_patterns:
            if re.search(pattern, cleaned_input):
                detected_patterns.append(pattern)
                if self._is_higher_risk(RiskLevel.MEDIUM, max_risk):
                    max_risk = RiskLevel.MEDIUM
                    reasons.append(f"Spam pattern detected: {pattern}")
        
        # Length checks
        if len(user_input) > 5000:
            max_risk = RiskLevel.MEDIUM
            reasons.append("Input length exceeds safe limits")
        
        # Determine action based on risk level
        action = self._determine_action(max_risk)
        
        # Calculate confidence
        confidence = min(1.0, len(detected_patterns) * 0.3 + 0.7)
        
        # Log security check
        if max_risk != RiskLevel.SAFE:
            logger.warning(f"Security check - User: {user_id}, Risk: {max_risk.value}, "
                         f"Action: {action.value}, Patterns: {len(detected_patterns)}")
        
        return SecurityCheck(
            risk_level=max_risk,
            action=action,
            reason="; ".join(reasons) if reasons else "Input appears safe",
            confidence=confidence,
            detected_patterns=detected_patterns
        )
    
    def _is_higher_risk(self, new_risk: RiskLevel, current_risk: RiskLevel) -> bool:
        """Compare risk levels"""
        risk_order = [RiskLevel.SAFE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        return risk_order.index(new_risk) > risk_order.index(current_risk)
    
    def _determine_action(self, risk_level: RiskLevel) -> FilterAction:
        """Determine action based on risk level"""
        action_map = {
            RiskLevel.SAFE: FilterAction.ALLOW,
            RiskLevel.LOW: FilterAction.ALLOW,
            RiskLevel.MEDIUM: FilterAction.WARN,
            RiskLevel.HIGH: FilterAction.BLOCK,
            RiskLevel.CRITICAL: FilterAction.ESCALATE
        }
        return action_map.get(risk_level, FilterAction.BLOCK)


class OutputGuardrail:
    """
    Filters and validates LLM outputs before they reach the user
    """
    
    def __init__(self):
        # Unsafe advice patterns for real estate context
        self.unsafe_patterns = {
            RiskLevel.CRITICAL: [
                r'(?i)(guarantee|promise|certain).{0,30}(profit|return|investment)',
                r'(?i)(illegal|unlawful|fraudulent)\s+(advice|recommendation)',
                r'(?i)(no\s+inspection|skip\s+inspection|avoid\s+inspection)',
                r'(?i)(fake|forge|falsify)\s+(document|signature|information)',
            ],
            RiskLevel.HIGH: [
                r'(?i)(discriminat\w+|bias|prejudice)\s+.{0,20}(tenant|buyer|seller)',
                r'(?i)(hide|conceal|omit)\s+.{0,20}(defect|problem|issue)',
                r'(?i)(lie|mislead|deceive)\s+.{0,20}(client|customer|buyer)',
                r'(?i)(under\s+the\s+table|off\s+the\s+books|cash\s+deal)',
            ],
            RiskLevel.MEDIUM: [
                r'(?i)(definite|certain|guaranteed)\s+.{0,20}(appreciation|value\s+increase)',
                r'(?i)(can\'t\s+lose|risk\s*-?\s*free|sure\s+thing)',
                r'(?i)(medical|health|safety)\s+.{0,20}(advice|recommendation)',
                r'(?i)(legal|tax|financial)\s+advice\s+(?!general|basic)',
            ],
            RiskLevel.LOW: [
                r'(?i)(should|must|need\s+to)\s+(buy|sell|invest)\s+.{0,20}(now|immediately)',
                r'(?i)(always|never)\s+.{0,20}(invest|buy|sell)',
            ]
        }
        
        # Compliance violations
        self.compliance_patterns = [
            r'(?i)(personal|private|confidential)\s+.{0,20}(information|data)',
            r'(?i)(ssn|social\s+security|credit\s+score)\s+(?!general)',
            r'(?i)(exact|specific)\s+.{0,20}(address|location)\s+of\s+.{0,20}(person|individual)',
            r'(?i)(contact|call|text)\s+.{0,20}\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # Phone numbers
            r'(?i)[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email addresses
        ]
        
        # Misinformation patterns
        self.misinformation_patterns = [
            r'(?i)(market\s+will\s+definitely|prices\s+will\s+certainly)',
            r'(?i)(never|always)\s+.{0,20}(appreciate|depreciate)',
            r'(?i)(government\s+conspiracy|market\s+manipulation)',
            r'(?i)(insider\s+information|secret\s+knowledge)',
        ]

    async def check_output(self, llm_output: str, context: Optional[Dict] = None) -> SecurityCheck:
        """
        Perform comprehensive security check on LLM output
        
        Args:
            llm_output: The LLM's response
            context: Optional context information
            
        Returns:
            SecurityCheck object with risk assessment
        """
        if not llm_output or not llm_output.strip():
            return SecurityCheck(
                risk_level=RiskLevel.LOW,
                action=FilterAction.WARN,
                reason="Empty output from LLM",
                confidence=1.0,
                detected_patterns=[]
            )
        
        cleaned_output = llm_output.strip().lower()
        detected_patterns = []
        max_risk = RiskLevel.SAFE
        reasons = []
        
        # Check for unsafe patterns
        for risk_level, patterns in self.unsafe_patterns.items():
            for pattern in patterns:
                if re.search(pattern, cleaned_output):
                    detected_patterns.append(pattern)
                    if self._is_higher_risk(risk_level, max_risk):
                        max_risk = risk_level
                        reasons.append(f"Unsafe advice detected: {risk_level.value}")
        
        # Check for compliance violations
        for pattern in self.compliance_patterns:
            if re.search(pattern, cleaned_output):
                detected_patterns.append(pattern)
                if self._is_higher_risk(RiskLevel.HIGH, max_risk):
                    max_risk = RiskLevel.HIGH
                    reasons.append("Privacy/compliance violation detected")
        
        # Check for misinformation
        for pattern in self.misinformation_patterns:
            if re.search(pattern, cleaned_output):
                detected_patterns.append(pattern)
                if self._is_higher_risk(RiskLevel.MEDIUM, max_risk):
                    max_risk = RiskLevel.MEDIUM
                    reasons.append("Potential misinformation detected")
        
        # Check for excessive confidence in predictions
        confidence_words = len(re.findall(r'(?i)(definitely|certainly|guarantee|promise|sure|always|never)', cleaned_output))
        if confidence_words > 3:
            max_risk = RiskLevel.MEDIUM
            reasons.append("Excessive confidence in uncertain predictions")
        
        # Determine action
        action = self._determine_action(max_risk)
        
        # Calculate confidence
        confidence = min(1.0, len(detected_patterns) * 0.2 + 0.8)
        
        # Log security check
        if max_risk != RiskLevel.SAFE:
            logger.warning(f"Output security check - Risk: {max_risk.value}, "
                         f"Action: {action.value}, Patterns: {len(detected_patterns)}")
        
        return SecurityCheck(
            risk_level=max_risk,
            action=action,
            reason="; ".join(reasons) if reasons else "Output appears safe",
            confidence=confidence,
            detected_patterns=detected_patterns
        )
    
    def _is_higher_risk(self, new_risk: RiskLevel, current_risk: RiskLevel) -> bool:
        """Compare risk levels"""
        risk_order = [RiskLevel.SAFE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        return risk_order.index(new_risk) > risk_order.index(current_risk)
    
    def _determine_action(self, risk_level: RiskLevel) -> FilterAction:
        """Determine action based on risk level"""
        action_map = {
            RiskLevel.SAFE: FilterAction.ALLOW,
            RiskLevel.LOW: FilterAction.ALLOW,
            RiskLevel.MEDIUM: FilterAction.WARN,
            RiskLevel.HIGH: FilterAction.BLOCK,
            RiskLevel.CRITICAL: FilterAction.ESCALATE
        }
        return action_map.get(risk_level, FilterAction.BLOCK)


class SecurityGuardrail:
    """
    Main guardrail component that coordinates input and output filtering
    """
    
    def __init__(self):
        self.input_guardrail = InputGuardrail()
        self.output_guardrail = OutputGuardrail()
        self.blocked_users = set()
        self.warning_counts = {}
        
        # Security configuration
        self.max_warnings = 3
        self.block_duration = 3600  # 1 hour in seconds
        
    async def filter_input(self, user_input: str, user_id: Optional[str] = None) -> Tuple[bool, str, SecurityCheck]:
        """
        Filter user input through security checks
        
        Args:
            user_input: User's message
            user_id: Optional user identifier
            
        Returns:
            Tuple of (is_allowed, filtered_message, security_check)
        """
        # Check if user is blocked
        if user_id and user_id in self.blocked_users:
            return False, "Your account has been temporarily restricted due to security concerns. Please contact support.", SecurityCheck(
                risk_level=RiskLevel.CRITICAL,
                action=FilterAction.BLOCK,
                reason="User is currently blocked",
                confidence=1.0,
                detected_patterns=[]
            )
        
        # Perform security check
        check = await self.input_guardrail.check_input(user_input, user_id)
        
        # Handle different actions
        if check.action == FilterAction.ALLOW:
            return True, user_input, check
        
        elif check.action == FilterAction.WARN:
            if user_id:
                self.warning_counts[user_id] = self.warning_counts.get(user_id, 0) + 1
                if self.warning_counts[user_id] >= self.max_warnings:
                    self.blocked_users.add(user_id)
                    logger.warning(f"User {user_id} blocked after {self.max_warnings} warnings")
                    return False, "Your account has been temporarily restricted due to repeated security warnings.", check
            
            warning_msg = "⚠️ Your message contains potentially inappropriate content. Please rephrase your question about real estate in a professional manner."
            return False, warning_msg, check
        
        elif check.action == FilterAction.BLOCK:
            if user_id:
                self.warning_counts[user_id] = self.warning_counts.get(user_id, 0) + 1
            
            block_msg = "❌ Your message has been blocked due to inappropriate content. Please ask questions related to real estate in a respectful and legal manner."
            return False, block_msg, check
        
        elif check.action == FilterAction.ESCALATE:
            if user_id:
                self.blocked_users.add(user_id)
                logger.critical(f"User {user_id} blocked due to critical security violation: {check.reason}")
            
            escalate_msg = "🚨 Your message has been flagged for serious policy violations. Your account has been temporarily restricted."
            return False, escalate_msg, check
        
        return False, "Your message could not be processed due to security concerns.", check
    
    async def filter_output(self, llm_output: str, context: Optional[Dict] = None) -> Tuple[bool, str, SecurityCheck]:
        """
        Filter LLM output through security checks
        
        Args:
            llm_output: LLM's response
            context: Optional context information
            
        Returns:
            Tuple of (is_allowed, filtered_response, security_check)
        """
        check = await self.output_guardrail.check_output(llm_output, context)
        
        if check.action == FilterAction.ALLOW:
            return True, llm_output, check
        
        elif check.action == FilterAction.WARN:
            # Add disclaimer to potentially risky content
            warning_disclaimer = "\n\n⚠️ **Disclaimer**: This information is for general purposes only. Please consult with qualified professionals for specific advice regarding real estate transactions, legal matters, or financial decisions."
            return True, llm_output + warning_disclaimer, check
        
        elif check.action in [FilterAction.BLOCK, FilterAction.ESCALATE]:
            logger.error(f"LLM output blocked: {check.reason}")
            safe_response = "I apologize, but I cannot provide a response to that query. Please ask me about real estate properties, market insights, or general housing information, and I'll be happy to help."
            return False, safe_response, check
        
        return False, "Unable to generate a safe response.", check
    
    def get_safe_error_message(self, error_type: str = "general") -> str:
        """Get appropriate error message for different scenarios"""
        messages = {
            "general": "I apologize, but I encountered an issue processing your request. Please try rephrasing your question about real estate.",
            "inappropriate": "Please keep our conversation focused on real estate topics and maintain a professional tone.",
            "technical": "I'm experiencing technical difficulties. Please try your real estate question again in a moment.",
            "blocked": "Your request cannot be processed. Please ensure you're asking about legitimate real estate topics."
        }
        return messages.get(error_type, messages["general"])
    
    async def log_security_event(self, event_type: str, user_id: Optional[str], details: Dict):
        """Log security events for monitoring and analysis"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details
        }
        
        # In production, this would go to a security monitoring system
        logger.info(f"Security Event: {json.dumps(log_entry)}")
    
    def reset_user_warnings(self, user_id: str):
        """Reset warning count for a user (admin function)"""
        if user_id in self.warning_counts:
            del self.warning_counts[user_id]
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
        logger.info(f"Reset warnings for user: {user_id}")
    
    def get_user_status(self, user_id: str) -> Dict:
        """Get current security status for a user"""
        return {
            "user_id": user_id,
            "warnings": self.warning_counts.get(user_id, 0),
            "is_blocked": user_id in self.blocked_users,
            "max_warnings": self.max_warnings
        }


# Global instance
security_guardrail = SecurityGuardrail()


# Utility functions for easy integration
async def secure_input(user_input: str, user_id: Optional[str] = None) -> Tuple[bool, str]:
    """
    Convenience function for input filtering
    
    Returns:
        Tuple of (is_allowed, message)
    """
    allowed, message, _ = await security_guardrail.filter_input(user_input, user_id)
    return allowed, message


async def secure_output(llm_output: str, context: Optional[Dict] = None) -> Tuple[bool, str]:
    """
    Convenience function for output filtering
    
    Returns:
        Tuple of (is_allowed, filtered_response)
    """
    allowed, response, _ = await security_guardrail.filter_output(llm_output, context)
    return allowed, response


# Decorator for securing API endpoints
def secure_endpoint(func):
    """Decorator to add security checks to API endpoints"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Security error in endpoint: {str(e)}")
            return {"error": security_guardrail.get_safe_error_message("technical")}
    return wrapper
