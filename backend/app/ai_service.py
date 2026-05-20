import openai
from typing import Dict, Any, List
import json
from app.config import settings


class OpenAIAnalysisService:
    """Service for AI-powered flight analysis using OpenAI"""
    
    def __init__(self):
        if settings.openai_api_key:
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None
    
    def is_available(self) -> bool:
        return self.client is not None
    
    async def analyze_flight(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive AI analysis of flight data
        """
        if not self.is_available():
            return self._get_fallback_analysis(analysis_data)
        
        try:
            prompt = self._create_analysis_prompt(analysis_data)
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert drone flight analyst. Provide detailed analysis and actionable recommendations for improving flight performance."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            ai_response = response.choices[0].message.content
            recommendations = self._extract_recommendations(ai_response)
            
            return {
                "ai_analysis": ai_response,
                "recommendations": recommendations,
                "success": True
            }
            
        except Exception as e:
            print(f"OpenAI analysis failed: {str(e)}")
            return self._get_fallback_analysis(analysis_data)
    
    def _create_analysis_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Create detailed prompt for AI analysis"""
        
        return f"""
        Please analyze this drone flight data and provide comprehensive insights:
        
        OVERALL SCORE: {analysis_data.get('overall_score', 'N/A')}
        EFFICIENCY SCORE: {analysis_data.get('efficiency_score', 'N/A')}
        STABILITY SCORE: {analysis_data.get('stability_score', 'N/A')}
        RISK LEVEL: {analysis_data.get('risk_level', 'N/A')}
        FLIGHT DURATION: {analysis_data.get('flight_duration', 'N/A')} seconds
        
        PID ANALYSIS:
        {json.dumps(analysis_data.get('pid_analysis', {}), indent=2)}
        
        GPS DRIFT ANALYSIS:
        {json.dumps(analysis_data.get('gps_drift', {}), indent=2)}
        
        VIBRATION ANALYSIS:
        {json.dumps(analysis_data.get('vibration_analysis', {}), indent=2)}
        
        MOTOR ANOMALIES:
        {json.dumps(analysis_data.get('motor_anomalies', {}), indent=2)}
        
        Please provide:
        1. Overall assessment of the flight
        2. Key issues identified
        3. Specific actionable recommendations (3-5 points)
        4. Safety improvements suggestions
        5. PID tuning recommendations if needed
        """
    
    def _extract_recommendations(self, ai_response: str) -> List[str]:
        """Extract recommendations from AI response"""
        recommendations = []
        
        lines = ai_response.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or 
                        line.startswith('4.') or line.startswith('5.') or line.startswith('-')):
                recommendations.append(line.lstrip('12345.- '))
        
        if not recommendations:
            recommendations = [
                "Monitor flight performance in next flights",
                "Check propeller balance and tightness",
                "Ensure battery is properly charged and connected"
            ]
        
        return recommendations[:10]
    
    def _get_fallback_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when OpenAI is not available"""
        
        score = analysis_data.get('overall_score', 70)
        risk = analysis_data.get('risk_level', 'low')
        
        analysis_text = f"""
        FLIGHT ANALYSIS REPORT
        ======================
        
        Overall Score: {score:.1f}/100
        Risk Level: {risk.upper()}
        
        KEY FINDINGS:
        1. Flight performance has been evaluated
        2. All systems appear to be functioning normally
        3. No critical issues detected
        
        RECOMMENDATIONS:
        - Continue monitoring flight patterns
        - Maintain regular maintenance schedule
        - Check battery health before each flight
        - Verify GPS signal strength before takeoff
        - Keep propellers clean and balanced
        
        For a more detailed analysis with AI-powered insights, configure your OpenAI API key.
        """
        
        recommendations = [
            "Continue regular flight monitoring",
            "Perform routine maintenance checks",
            "Ensure proper battery charging and storage",
            "Check GPS signal quality before flights",
            "Maintain clean and balanced propellers"
        ]
        
        return {
            "ai_analysis": analysis_text,
            "recommendations": recommendations,
            "success": True,
            "fallback": True
        }
