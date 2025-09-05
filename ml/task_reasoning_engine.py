"""
Task Reasoning Engine
Analyzes task complexity for intelligent provider selection
"""

import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ComplexityLevel(Enum):
    """Task complexity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class ComplexityScore:
    """Detailed complexity scoring"""
    reasoning: float = 0.0
    knowledge: float = 0.0
    computation: float = 0.0
    coordination: float = 0.0
    
    @property
    def total_score(self) -> float:
        return (self.reasoning + self.knowledge + self.computation + self.coordination) / 4
    
    @property
    def complexity_level(self) -> str:
        if self.total_score < 0.4:
            return ComplexityLevel.LOW.value
        elif self.total_score < 0.7:
            return ComplexityLevel.MEDIUM.value
        else:
            return ComplexityLevel.HIGH.value

class TaskReasoningEngine:
    """
    Analyzes task complexity to help select appropriate AI providers
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Keywords that indicate different types of complexity
        self.reasoning_keywords = [
            'analyze', 'explain', 'reason', 'logic', 'because', 'therefore',
            'conclude', 'infer', 'deduce', 'argue', 'justify', 'prove'
        ]
        
        self.knowledge_keywords = [
            'history', 'science', 'literature', 'mathematics', 'physics',
            'chemistry', 'biology', 'geography', 'philosophy', 'psychology',
            'economics', 'politics', 'law', 'medicine', 'technology'
        ]
        
        self.computation_keywords = [
            'calculate', 'compute', 'solve', 'equation', 'formula', 'algorithm',
            'programming', 'code', 'debug', 'optimize', 'data', 'statistics'
        ]
        
        self.coordination_keywords = [
            'plan', 'schedule', 'organize', 'coordinate', 'manage', 'workflow',
            'steps', 'process', 'sequence', 'timeline', 'project', 'task'
        ]
        
        # Patterns that indicate high complexity
        self.high_complexity_patterns = [
            r'multi-step|multiple steps',
            r'complex|complicated|sophisticated',
            r'detailed analysis|in-depth',
            r'comprehensive|thorough',
            r'advanced|expert level'
        ]
    
    def analyze_complexity(self, content: str, context: Optional[Dict[str, Any]] = None) -> ComplexityScore:
        """
        Analyze the complexity of a given task/content
        
        Args:
            content: The text content to analyze
            context: Additional context that might affect complexity
            
        Returns:
            ComplexityScore with detailed breakdown
        """
        content_lower = content.lower()
        
        # Base scores
        reasoning_score = self._calculate_reasoning_score(content_lower)
        knowledge_score = self._calculate_knowledge_score(content_lower)
        computation_score = self._calculate_computation_score(content_lower)
        coordination_score = self._calculate_coordination_score(content_lower)
        
        # Apply context modifiers
        if context:
            reasoning_score *= self._get_context_modifier(context, 'reasoning')
            knowledge_score *= self._get_context_modifier(context, 'knowledge')
            computation_score *= self._get_context_modifier(context, 'computation')
            coordination_score *= self._get_context_modifier(context, 'coordination')
        
        # Apply length and pattern modifiers
        length_modifier = self._get_length_modifier(content)
        pattern_modifier = self._get_pattern_modifier(content_lower)
        
        reasoning_score = min(1.0, reasoning_score * length_modifier * pattern_modifier)
        knowledge_score = min(1.0, knowledge_score * length_modifier * pattern_modifier)
        computation_score = min(1.0, computation_score * length_modifier * pattern_modifier)
        coordination_score = min(1.0, coordination_score * length_modifier * pattern_modifier)
        
        score = ComplexityScore(
            reasoning=reasoning_score,
            knowledge=knowledge_score,
            computation=computation_score,
            coordination=coordination_score
        )
        
        self.logger.debug(f"Complexity analysis: {score.complexity_level} (total: {score.total_score:.3f})")
        
        return score
    
    def _calculate_reasoning_score(self, content: str) -> float:
        """Calculate reasoning complexity score"""
        score = 0.0
        
        # Count reasoning keywords
        keyword_count = sum(1 for keyword in self.reasoning_keywords if keyword in content)
        score += min(0.5, keyword_count * 0.1)
        
        # Look for logical connectors
        logical_patterns = ['if.*then', 'because.*therefore', 'since.*thus', 'given.*conclude']
        for pattern in logical_patterns:
            if re.search(pattern, content):
                score += 0.2
        
        # Look for question words that indicate reasoning
        question_words = ['why', 'how', 'what if', 'suppose']
        for word in question_words:
            if word in content:
                score += 0.15
        
        return min(1.0, score)
    
    def _calculate_knowledge_score(self, content: str) -> float:
        """Calculate knowledge complexity score"""
        score = 0.0
        
        # Count knowledge domain keywords
        keyword_count = sum(1 for keyword in self.knowledge_keywords if keyword in content)
        score += min(0.6, keyword_count * 0.1)
        
        # Look for specific knowledge indicators
        if any(term in content for term in ['research', 'study', 'theory', 'concept']):
            score += 0.2
        
        # Look for proper nouns (likely knowledge-specific terms)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', content)
        if len(proper_nouns) > 3:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_computation_score(self, content: str) -> float:
        """Calculate computational complexity score"""
        score = 0.0
        
        # Count computation keywords
        keyword_count = sum(1 for keyword in self.computation_keywords if keyword in content)
        score += min(0.5, keyword_count * 0.15)
        
        # Look for numbers and mathematical expressions
        numbers = re.findall(r'\d+', content)
        if len(numbers) > 2:
            score += 0.2
        
        # Look for mathematical operators
        math_operators = ['+', '-', '*', '/', '=', '<', '>', '%']
        if any(op in content for op in math_operators):
            score += 0.2
        
        # Look for code-related terms
        code_terms = ['function', 'variable', 'loop', 'condition', 'array', 'object']
        if any(term in content for term in code_terms):
            score += 0.3
        
        return min(1.0, score)
    
    def _calculate_coordination_score(self, content: str) -> float:
        """Calculate coordination complexity score"""
        score = 0.0
        
        # Count coordination keywords
        keyword_count = sum(1 for keyword in self.coordination_keywords if keyword in content)
        score += min(0.4, keyword_count * 0.1)
        
        # Look for sequential indicators
        sequential_terms = ['first', 'second', 'third', 'next', 'then', 'finally', 'step']
        seq_count = sum(1 for term in sequential_terms if term in content)
        if seq_count > 2:
            score += 0.3
        
        # Look for coordination indicators
        coord_terms = ['coordinate', 'collaborate', 'integrate', 'combine', 'merge']
        if any(term in content for term in coord_terms):
            score += 0.3
        
        return min(1.0, score)
    
    def _get_length_modifier(self, content: str) -> float:
        """Get complexity modifier based on content length"""
        word_count = len(content.split())
        
        if word_count < 10:
            return 0.8  # Short content is likely simpler
        elif word_count < 50:
            return 1.0
        elif word_count < 200:
            return 1.2  # Longer content is likely more complex
        else:
            return 1.4
    
    def _get_pattern_modifier(self, content: str) -> float:
        """Get complexity modifier based on high-complexity patterns"""
        modifier = 1.0
        
        for pattern in self.high_complexity_patterns:
            if re.search(pattern, content):
                modifier += 0.2
        
        return min(2.0, modifier)
    
    def _get_context_modifier(self, context: Dict[str, Any], dimension: str) -> float:
        """Get complexity modifier based on context"""
        modifier = 1.0
        
        # Check for context hints about complexity
        if context.get('complexity_hint'):
            hint = context['complexity_hint'].lower()
            if hint in ['high', 'complex', 'advanced']:
                modifier = 1.5
            elif hint in ['low', 'simple', 'basic']:
                modifier = 0.7
        
        # Check for domain-specific context
        if context.get('domain'):
            domain = context['domain'].lower()
            if dimension == 'knowledge' and domain in ['academic', 'research', 'technical']:
                modifier *= 1.3
            elif dimension == 'computation' and domain in ['programming', 'math', 'engineering']:
                modifier *= 1.4
        
        return modifier