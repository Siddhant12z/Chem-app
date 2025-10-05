"""
Post-processing module for adding Nepali mixing and follow-up questions to AI responses.
This ensures consistent formatting regardless of model behavior.
"""

import re
import random
from typing import List, Tuple


class ResponseProcessor:
    """Processes AI responses to add Nepali mixing and follow-up questions."""
    
    # Nepali phrases for natural mixing
    NEPALI_PHRASES = [
        # Roman Nepali variants as per UX preference
        "Thik cha",
        "Ramro cha",
        "Dherai important cha",
        "Ho",
        "Hoin",
        "Ke",
        "Kasari",
        "Bujhnu bhayo?"
    ]
    
    # Follow-up question templates
    FOLLOW_UP_TEMPLATES = [
        "Want to know more about {topic}, bujhnu bhayo?",
        "Ke bujhnu bhayo? Want to learn more about {topic}?",
        "Ramro cha, want to know more about {topic}, ke?",
        "Dherai interesting cha, haina? Want to explore {topic}, bujhnu bhayo?",
        "Thik cha, want to know more about {topic}, bujhnu bhayo?"
    ]
    
    def __init__(self):
        self.nepali_phrases = self.NEPALI_PHRASES.copy()
        self.follow_up_templates = self.FOLLOW_UP_TEMPLATES.copy()
    
    def extract_main_topic(self, response: str) -> str:
        """Extract the main topic from the response for follow-up questions."""
        # Simple topic extraction - look for chemical names, concepts
        chemical_patterns = [
            r'\b(?:benzene|water|H2O|methane|ethane|alcohol|acid|base|molecule|atom|bond|reaction|organic chemistry|inorganic chemistry)\b',
            r'\b(?:carbon|hydrogen|oxygen|nitrogen|sulfur|phosphorus)\b',
            r'\b(?:alkane|alkene|alkyne|aromatic|hydrocarbon)\b'
        ]
        
        for pattern in chemical_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                return matches[0].lower()
        
        # Fallback topics
        fallback_topics = [
            "this topic",
            "organic chemistry", 
            "chemical reactions",
            "molecular structures"
        ]
        
        return random.choice(fallback_topics)
    
    def add_nepali_mixing(self, response: str) -> str:
        """Add Nepali mixing to the response."""
        # Remove sources section if present
        main_response = re.split(r'\n\nSources?:', response)[0].strip()
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', main_response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 2:
            return response
        
        # Add Nepali mixing to the first or second sentence
        target_sentence_idx = min(1, len(sentences) - 1)
        target_sentence = sentences[target_sentence_idx]
        
        # Choose a random Nepali phrase
        nepali_phrase = random.choice(self.nepali_phrases)
        
        # Insert Nepali phrase naturally
        if target_sentence.endswith('.'):
            target_sentence = target_sentence[:-1]
        
        # Add Nepali mixing
        mixed_sentence = f"{target_sentence}. {nepali_phrase}, it's धेरै important in chemistry."
        sentences[target_sentence_idx] = mixed_sentence
        
        return '. '.join(sentences) + '.'
    
    def add_follow_up_question(self, response: str) -> str:
        """Add a mixed follow-up question to the response."""
        # Extract topic for follow-up
        topic = self.extract_main_topic(response)
        
        # Choose a random follow-up template
        template = random.choice(self.follow_up_templates)
        follow_up = template.format(topic=topic)
        
        return f"{response} {follow_up}"
    
    def process_response(self, response: str) -> str:
        """Main processing function that adds Nepali mixing and follow-up questions."""
        if not response or len(response.strip()) < 10:
            return response
        
        # Step 1: Add Nepali mixing
        processed_response = self.add_nepali_mixing(response)
        
        # Step 2: Add follow-up question
        processed_response = self.add_follow_up_question(processed_response)
        
        return processed_response
    
    def process_with_sources(self, response: str) -> str:
        """Process response while preserving sources section."""
        # Split response and sources
        parts = re.split(r'(\n\nSources?:.*)', response, flags=re.IGNORECASE)
        
        if len(parts) >= 2:
            main_response = parts[0]
            sources_section = ''.join(parts[1:])
            
            # Process main response
            processed_main = self.process_response(main_response)
            
            # Combine with sources
            return processed_main + sources_section
        else:
            # No sources section, process normally
            return self.process_response(response)


# Global instance
response_processor = ResponseProcessor()


def enhance_response(response: str) -> str:
    """Enhance a response with Nepali mixing and follow-up questions."""
    return response_processor.process_with_sources(response)
