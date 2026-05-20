from typing import Optional, Dict, Any
import os
from app.config import settings

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class SupabaseService:
    """Service for Supabase integration"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        if SUPABASE_AVAILABLE and settings.supabase_url and settings.supabase_key:
            try:
                self.client = create_client(
                    settings.supabase_url,
                    settings.supabase_key
                )
            except Exception as e:
                print(f"Error initializing Supabase: {e}")
    
    def is_available(self) -> bool:
        return self.client is not None
    
    async def upload_flight_log(
        self, 
        file_path: str, 
        filename: str, 
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Upload flight log to Supabase Storage"""
        if not self.is_available():
            return None
        
        try:
            # Read file
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Upload to Supabase storage
            bucket_name = "flight-logs"
            destination_path = f"{user_id}/{filename}" if user_id else f"public/{filename}"
            
            self.client.storage.from_(bucket_name).upload(
                destination_path,
                file_content
            )
            
            # Get public URL
            url = self.client.storage.from_(bucket_name).get_public_url(destination_path)
            
            return {
                "success": True,
                "url": url,
                "path": destination_path
            }
        except Exception as e:
            print(f"Supabase upload failed: {e}")
            return None
    
    async def save_analysis(
        self, 
        analysis_data: Dict[str, Any], 
        flight_log_id: int
    ) -> Optional[Dict[str, Any]]:
        """Save analysis results to Supabase"""
        if not self.is_available():
            return None
        
        try:
            result = self.client.table("flight_analyses").insert({
                "flight_log_id": flight_log_id,
                **analysis_data
            }).execute()
            
            return {
                "success": True,
                "data": result.data
            }
        except Exception as e:
            print(f"Supabase save failed: {e}")
            return None
    
    async def get_user_flights(
        self, 
        user_id: int, 
        limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """Get user's flight logs from Supabase"""
        if not self.is_available():
            return None
        
        try:
            result = self.client.table("flight_logs") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            return {
                "success": True,
                "data": result.data
            }
        except Exception as e:
            print(f"Supabase query failed: {e}")
            return None
