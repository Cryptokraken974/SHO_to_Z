"""
Chat Service

Provides chat functionality including:
- Message processing and response generation
- Conversation management
- Chat history and context handling
- Integration with AI/LLM services
"""

from typing import Dict, Any, List, Optional, Union
import logging
from pathlib import Path

from .base_service import BaseService, ServiceError

logger = logging.getLogger(__name__)


class ChatService(BaseService):
    """Service for chat operations and AI interactions"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        
    async def send_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to the chat system
        
        Args:
            message: The user message
            context: Optional context information
            conversation_id: Optional conversation identifier
            user_id: Optional user identifier
            
        Returns:
            Dict containing chat response
        """
        try:
            payload = {
                "message": message
            }
            
            if context:
                payload["context"] = context
            if conversation_id:
                payload["conversation_id"] = conversation_id
            if user_id:
                payload["user_id"] = user_id
                
            return await self._make_request('POST', '/api/chat', json_data=payload)
        except Exception as e:
            logger.error(f"Failed to send chat message: {e}")
            raise ServiceError(f"Chat message failed: {str(e)}")
    
    # Convenience methods for different types of interactions
    async def ask_question(
        self,
        question: str,
        domain: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ask a question in a specific domain
        
        Args:
            question: The question to ask
            domain: Domain context (geospatial, lidar, elevation, etc.)
            conversation_id: Optional conversation ID for context
            
        Returns:
            Dict containing answer
        """
        context = {}
        if domain:
            context["domain"] = domain
            context["type"] = "question"
            
        return await self.send_message(
            message=question,
            context=context,
            conversation_id=conversation_id
        )
    
    async def get_help(
        self,
        topic: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get help information on a specific topic
        
        Args:
            topic: Help topic (optional)
            conversation_id: Optional conversation ID
            
        Returns:
            Dict containing help information
        """
        if topic:
            message = f"Help me with {topic}"
        else:
            message = "I need help"
            
        context = {
            "type": "help_request",
            "topic": topic
        }
        
        return await self.send_message(
            message=message,
            context=context,
            conversation_id=conversation_id
        )
    
    async def explain_concept(
        self,
        concept: str,
        level: str = "intermediate",
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get explanation of a technical concept
        
        Args:
            concept: Concept to explain
            level: Explanation level (beginner, intermediate, advanced)
            conversation_id: Optional conversation ID
            
        Returns:
            Dict containing explanation
        """
        message = f"Explain {concept}"
        context = {
            "type": "explanation",
            "concept": concept,
            "level": level
        }
        
        return await self.send_message(
            message=message,
            context=context,
            conversation_id=conversation_id
        )
    
    async def get_processing_advice(
        self,
        data_type: str,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get advice on data processing operations
        
        Args:
            data_type: Type of data (lidar, elevation, satellite)
            operation: Processing operation (dtm, dsm, classification, etc.)
            parameters: Optional processing parameters
            conversation_id: Optional conversation ID
            
        Returns:
            Dict containing processing advice
        """
        message = f"How should I process {data_type} data for {operation}?"
        
        context = {
            "type": "processing_advice",
            "data_type": data_type,
            "operation": operation
        }
        
        if parameters:
            context["parameters"] = parameters
            
        return await self.send_message(
            message=message,
            context=context,
            conversation_id=conversation_id
        )
    
    async def troubleshoot_issue(
        self,
        issue_description: str,
        error_details: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get troubleshooting help for an issue
        
        Args:
            issue_description: Description of the issue
            error_details: Optional error details (logs, codes, etc.)
            conversation_id: Optional conversation ID
            
        Returns:
            Dict containing troubleshooting guidance
        """
        message = f"I'm having an issue: {issue_description}"
        
        context = {
            "type": "troubleshooting",
            "issue": issue_description
        }
        
        if error_details:
            context["error_details"] = error_details
            
        return await self.send_message(
            message=message,
            context=context,
            conversation_id=conversation_id
        )
    
    async def start_conversation(
        self,
        initial_message: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a new conversation
        
        Args:
            initial_message: Optional initial message
            user_id: Optional user identifier
            
        Returns:
            Dict containing conversation details
        """
        if not initial_message:
            initial_message = "Hello, I'd like to start a conversation about geospatial data processing."
            
        context = {
            "type": "conversation_start",
            "new_conversation": True
        }
        
        return await self.send_message(
            message=initial_message,
            context=context,
            user_id=user_id
        )
    
    async def continue_conversation(
        self,
        message: str,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Continue an existing conversation
        
        Args:
            message: Message to send
            conversation_id: ID of existing conversation
            user_id: Optional user identifier
            
        Returns:
            Dict containing response
        """
        context = {
            "type": "conversation_continue"
        }
        
        return await self.send_message(
            message=message,
            context=context,
            conversation_id=conversation_id,
            user_id=user_id
        )
    
    async def get_workflow_guidance(
        self,
        workflow_type: str,
        data_inputs: Optional[List[str]] = None,
        desired_outputs: Optional[List[str]] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get guidance on a specific workflow
        
        Args:
            workflow_type: Type of workflow (lidar_processing, elevation_analysis, etc.)
            data_inputs: Available input data types
            desired_outputs: Desired output products
            conversation_id: Optional conversation ID
            
        Returns:
            Dict containing workflow guidance
        """
        message = f"Guide me through a {workflow_type} workflow"
        
        context = {
            "type": "workflow_guidance",
            "workflow_type": workflow_type
        }
        
        if data_inputs:
            context["data_inputs"] = data_inputs
            message += f" with inputs: {', '.join(data_inputs)}"
            
        if desired_outputs:
            context["desired_outputs"] = desired_outputs
            message += f" to produce: {', '.join(desired_outputs)}"
            
        return await self.send_message(
            message=message,
            context=context,
            conversation_id=conversation_id
        )
    
    async def get_parameter_suggestions(
        self,
        operation: str,
        data_characteristics: Optional[Dict[str, Any]] = None,
        quality_requirements: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get parameter suggestions for a processing operation
        
        Args:
            operation: Processing operation name
            data_characteristics: Characteristics of input data
            quality_requirements: Quality requirements for output
            conversation_id: Optional conversation ID
            
        Returns:
            Dict containing parameter suggestions
        """
        message = f"What parameters should I use for {operation}?"
        
        context = {
            "type": "parameter_suggestions",
            "operation": operation
        }
        
        if data_characteristics:
            context["data_characteristics"] = data_characteristics
        if quality_requirements:
            context["quality_requirements"] = quality_requirements
            
        return await self.send_message(
            message=message,
            context=context,
            conversation_id=conversation_id
        )
    
    async def get_system_status_explanation(
        self,
        status_data: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get explanation of system status and recommendations
        
        Args:
            status_data: Current system status data
            conversation_id: Optional conversation ID
            
        Returns:
            Dict containing status explanation and recommendations
        """
        message = "Please explain my system status and provide recommendations"
        
        context = {
            "type": "status_explanation",
            "status_data": status_data
        }
        
        return await self.send_message(
            message=message,
            context=context,
            conversation_id=conversation_id
        )
